---
name: run-de-dag
description: 在本地 Docker Airflow 上觸發 Taipei-City-Dashboard-DE 的任一 DAG（如 `mrt_a11y_alert`、`mrt_a11y_elevator`、`D020105`、`flu_hospitals_tpe`、`R0085` 等任何 dags/proj_city_dashboard/ 底下的 DAG）並驗證寫入結果。**主動使用情境**：使用者說「跑 XXX DAG」「測試 XXX」「觸發 XXX 一次」「跑一下 XXX 看看」「跑 alert/elevator」「跑這支 DAG」「驗證 XXX DAG 寫入」「smoke test XXX」「test XXX dag」等等，無論 XXX 是哪一支 DAG，也無論使用者有沒有講「Docker」「Airflow」「Postgres」字眼都要使用此 skill。**不要使用**：使用者只想看 DAG 程式碼或 schema、或要跑非此 repo 的工作流。
---

# 在 Docker Airflow 上跑任一 DE DAG 並驗證

通用 ops skill：給定一個 DAG ID，觸發本地 Docker Airflow 執行 + poll 完成狀態 + 用通用驗證確認資料正確落入 Postgres + 印出 first 3 rows 預覽。可選地呼叫 DAG 客製驗證器追加業務邏輯斷言。

## 何時使用此 skill

- 改了任一支 [`Taipei-City-Dashboard-DE/dags/proj_city_dashboard/<DAG_ID>/<DAG_ID>.py`](Taipei-City-Dashboard-DE/dags/proj_city_dashboard/) 的 transform 邏輯，想快速看結果
- 部署前 smoke test：跑一次某 DAG 確認沒爆
- 比賽 / hackathon 當場新建 DAG，要快速驗證能跑通
- 修 bug 後要確認真的修好
- 不確定資料源欄位是否變動，想實機驗看看資料樣貌

## 用法

skill 主要參數是 `<DAG_ID>`，可一次給一個或多個（依序執行）。`<DAG_ID>` 必須是 `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/<DAG_ID>/` 目錄下的有效 DAG。

對話範例：
- 「跑 D020105 DAG」 → 觸發 `D020105`
- 「mrt_a11y_alert 跑一遍」 → 觸發 `mrt_a11y_alert`
- 「兩支無障礙 DAG 都跑」 → 依序觸發 `mrt_a11y_alert`、`mrt_a11y_elevator`
- 「測試 flu_hospitals_tpe」 → 觸發 `flu_hospitals_tpe`

## 環境前提

- Skill 安裝在 repo root：[`.claude/skills/run-de-dag/`](.claude/skills/run-de-dag/)
- Working directory 必須是 [`Taipei-City-Dashboard-DE/`](Taipei-City-Dashboard-DE/)（docker-compose 路徑相對於該目錄）。skill 自動 `cd` 到 `$REPO_ROOT/Taipei-City-Dashboard-DE`
- Docker compose stack 須已啟動（`airflow-scheduler` 容器 running）— skill 不擅自 `docker compose up`
- DAG 目標表須已建立（`current+history` / `replace` 開頭都會 `TRUNCATE`，表不存在會 fail）
- Airflow connection `postgres_default` 已設好

## 工作流（針對單一 DAG）

按下列順序執行，每步成功才前進。任一步失敗，立即中止並報告失敗原因。

### Step 1. 取得 repo root + 切到 DE + 環境檢查

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
SKILL_DIR="$REPO_ROOT/.claude/skills/run-de-dag"
cd "$REPO_ROOT/Taipei-City-Dashboard-DE"
DC="docker compose -f docker/develop/docker-compose.yaml"

# 確認 DAG 目錄與 job_config.json 存在
DAG_ID="<使用者指定>"
DAG_DIR="dags/proj_city_dashboard/$DAG_ID"
[ -f "$DAG_DIR/job_config.json" ] || {
  echo "❌ DAG not found: $DAG_DIR/job_config.json"
  echo "   可用 DAG："
  ls dags/proj_city_dashboard/ | head -20
  exit 1
}

# 確認 airflow-scheduler running
$DC ps --status running --services | grep -q '^airflow-scheduler$' || {
  echo "❌ airflow-scheduler not running. 請先 cd 到 docker/develop && docker compose up -d"
  exit 1
}
```

### Step 2. 觸發 DAG 並取得 run_id

```bash
RUN_ID="manual_$(date +%Y%m%dT%H%M%S)"
$DC exec -T airflow-scheduler airflow dags trigger "$DAG_ID" --run-id "$RUN_ID"
```

`airflow dags trigger` 立刻 return（非阻塞）。下一步要 polling。

### Step 3. Poll DAG run 狀態到 terminal

預設超時 5 分鐘，輕量 ETL 多在 30–60 秒內完成。每 5 秒 poll，每 30 秒對 user 印一次 progress 不洗版。

```bash
TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  STATE=$($DC exec -T airflow-scheduler airflow dags list-runs -d "$DAG_ID" --output json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((r['state'] for r in d if r['run_id']=='$RUN_ID'), 'unknown'))")
  case "$STATE" in
    success) echo "✅ DAG run finished: $DAG_ID ($RUN_ID)"; break ;;
    failed)  echo "❌ DAG run failed: $DAG_ID ($RUN_ID)"; exit 1 ;;
    queued|running|unknown) sleep 5; ELAPSED=$((ELAPSED + 5)) ;;
  esac
done
[ $ELAPSED -lt $TIMEOUT ] || { echo "❌ Timeout after ${TIMEOUT}s"; exit 1; }
```

失敗時抓最新 task log 給 user：

```bash
$DC exec -T airflow-scheduler airflow tasks logs --try-number 1 "$DAG_ID" "$RUN_ID" 2>/dev/null | tail -50
```

### Step 4. 通用驗證 + 客製驗證

把 [`scripts/generic_verify.py`](.claude/skills/run-de-dag/scripts/generic_verify.py) 透過 stdin 餵進 airflow-scheduler 容器內執行。它會：

1. 讀 `JOB_CONFIG_PATH` 指向的 `job_config.json` 取得 `default_table` / `history_table` / `load_behavior` / `is_geometry`
2. 跑通用斷言（見下節）
3. 印 first 3 rows 預覽
4. 若 skill 內 `verifications/<DAG_ID>.py` 存在，把它的程式碼當作 `CUSTOM_VERIFIER_SRC` 一併傳入，generic_verify 會 dynamically import 並追加客製斷言

```bash
# 容器內 dags 路徑相對於 mount 點 /opt/airflow/dags
JOB_CONFIG_IN_CONTAINER="/opt/airflow/dags/proj_city_dashboard/$DAG_ID/job_config.json"

# 客製 verifier source（若不存在就空字串）
CUSTOM_SRC=""
if [ -f "$SKILL_DIR/scripts/verifications/$DAG_ID.py" ]; then
  CUSTOM_SRC="$(cat "$SKILL_DIR/scripts/verifications/$DAG_ID.py")"
fi

cat "$SKILL_DIR/scripts/generic_verify.py" | $DC exec -T \
  -e DAG_ID="$DAG_ID" \
  -e JOB_CONFIG_PATH="$JOB_CONFIG_IN_CONTAINER" \
  -e CUSTOM_VERIFIER_SRC="$CUSTOM_SRC" \
  airflow-scheduler python -
```

Exit code 0 = all PASS、非 0 = 至少一項 FAIL。

### Step 5. 彙整報告

對 user 印 summary：

```
✅ mrt_a11y_alert
   - DAG run: success (8.3s)
   - Generic: 4/4 passed
   - Custom (mrt_a11y_alert.py): 3/3 passed
✅ D020105
   - DAG run: success (12.1s)
   - Generic: 4/4 passed
   - Custom: (none)
```

若有 FAIL，列失敗的 assertion 名稱與實際值。

## 通用驗證項目（generic_verify.py 跑的）

讀 `job_config.json["dag_infos"]` 取得設定，根據設定條件性執行下列斷言：

| 條件 | 斷言 |
|---|---|
| 永遠 | `default_table` 存在且 row count >= 1 |
| `load_behavior == "current+history"` | `history_table` 存在且 row >= default |
| `data_infos.is_geometry == 1` | `wkb_geometry` 全部非 NULL |
| 永遠 | `dataset_info.lasttime_in_data` 對該 dag_id 在最近 10 分鐘內被更新 |
| 永遠（觀察用，不算斷言） | 印出 default 表 first 3 rows 預覽 |

「最近 10 分鐘」可由環境變數 `LASTTIME_FRESHNESS_MIN` 覆寫。

## 客製驗證（DAG-specific，可選）

每支 DAG 可選擇性提供 `.claude/skills/run-de-dag/scripts/verifications/<DAG_ID>.py`，定義：

```python
def verify(hook, config) -> List[Tuple[str, bool, str]]:
    """
    hook:   Airflow PostgresHook 已連到 postgres_default
    config: job_config.json["dag_infos"] dict
    return: [(name, passed, detail), ...]
    """
```

### 已附範例

- [`scripts/verifications/mrt_a11y_alert.py`](.claude/skills/run-de-dag/scripts/verifications/mrt_a11y_alert.py)：驗 status keyword、station 字尾 strip、line 非空
- [`scripts/verifications/mrt_a11y_elevator.py`](.claude/skills/run-de-dag/scripts/verifications/mrt_a11y_elevator.py)：驗 row count ≈ 188、facility_type 集合、unique stations、other 比例

### 新建客製驗證

要為新 DAG 加客製驗證，建一個 `verifications/<DAG_ID>.py` 即可，無需改 SKILL.md 或 generic_verify.py。

```python
# verifications/<DAG_ID>.py
def verify(hook, config):
    table = config["ready_data_default_table"]
    results = []
    # 各種業務斷言...
    return results
```

## 處理常見錯誤

| 錯誤訊息 | 根因 | 處理 |
|---|---|---|
| `DAG not found: dags/.../job_config.json` | DAG ID 拼錯或不在 proj_city_dashboard | Step 1 已自動列出可用 DAG |
| `relation "xxx" does not exist` | 表沒建（current+history / replace 都會 TRUNCATE） | 提示 user 建表；可參考 [`scripts/examples/mrt_a11y_setup_tables.sql`](.claude/skills/run-de-dag/scripts/examples/mrt_a11y_setup_tables.sql) 風格自製，或從 dag 程式 reverse-engineer 欄位 |
| `airflow-scheduler: No such service` | docker compose 未起 | 提示 `cd Taipei-City-Dashboard-DE/docker/develop && docker compose up -d` |
| Timeout (>5 min) | DAG 卡 queue / worker 沒起 | 檢查 `airflow-worker-default` / `airflow-worker-realtime` 是否 running，或 schedule_interval 對應 queue 是否啟動 |
| `KeyError: '_importdate'` | data.taipei API 回空 | 偶發，重試；或仿 `childcare_etl` 加 CSV fallback |

## 為什麼這樣設計

- **通用 + 可擴充**：通用 workflow 對所有 DAG 一致，DAG-specific 業務斷言透過 `verifications/<dag_id>.py` 隨用隨加，**比賽當天遇到完全沒寫客製 verifier 的新 DAG 也能跑**（只是少業務斷言，通用斷言仍會跑）
- **從 job_config.json 動態抓設定**：不需 skill 維護一份「table → DAG」的對照，DAG 改設定後 skill 自動跟上
- **不自動建表**：表 schema 是 DBA 職責；skill 自動建會掩蓋 schema drift。偵測到 missing table 時清楚回報並提供範例 SQL
- **不自動 docker compose up**：啟動 stack 需要 .env 齊備，盲目 up 會誤導
- **驗證在 scheduler 容器內**：複用 Airflow connection、避開 host 端裝 psycopg2/PostGIS driver
- **通用驗證項目意義**：(a) row >= 1 catch 「跑成功但寫零筆」假性成功；(b) `lasttime_in_data` freshness catch 「DAG 看起來成功但其實 silent fail（utility 註解掉沒呼叫 update）」；(c) geometry 非 NULL catch CRS 解析錯誤
- **`CUSTOM_VERIFIER_SRC` 走 env 而非 mount**：避免把 skill scripts dir 整個 mount 進容器，只傳該 DAG 需要的那一份原始碼，乾淨

## 互動風格

- 觸發前先 echo 一行「即將觸發 <DAG_ID>，預計 < N 分鐘…」
- Polling 期間每 30 秒一行 progress（不每 5 秒洗版）
- 失敗時把實際 STATE / 錯誤輸出給 user 看，不只說「failed」
- 最後 summary 一律用 Step 5 格式
