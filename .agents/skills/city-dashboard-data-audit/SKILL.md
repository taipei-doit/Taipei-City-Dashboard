---
name: city-dashboard-data-audit
description: Audit 台北城市儀表板(Taipei City Dashboard)資料層 — 比對「資料源 API / CSV」「Airflow DAG ETL」「dashboard-stream DB」「後端 query_chart SQL」「前端圖表渲染」五層的一致性,找出資料筆數/欄位/顯示異常並提出修正。適用於 user 問「某個 component 數字不對」「某個 DAG 卡住」「為什麼 DB 跟資料源有落差」等情境。
---

# Taipei City Dashboard 資料層稽核

## 適用情境

- 使用者指出「儀表板上某元件的數字不對」
- 使用者說「某某 DAG 沒更新」或「資料不是最新的」
- 需要比對**資料源 → DB → 儀表板**三端數字是否一致
- 需要定位資料落差的根因(資料擁有單位變動、ETL 邏輯、BE query、FE 渲染)

## 五層資料流

```
資料擁有單位
   │
   ▼  (API / CSV / SHP / SOAP)
[1] data source
   │
   ▼  (Airflow DAG, 每日/每月排程)
[2] ETL (Airflow)
   │
   ▼  (GeoDataFrame → SQL write)
[3] DB: dashboard-stream (或 dashboardmanager)
   │
   ▼  (query_charts.query_chart SQL)
[4] BE query
   │
   ▼  (前端圖表組件渲染)
[5] 儀表板顯示
```

每一層都可能出問題。稽核的核心是**逐層核對筆數**。

## 可用 MCP / 工具

- `mcp__postgres__*` — dashboardmanager DB(後台設定:components / query_charts / dashboards / component_maps)
- `mcp__data-stream-prod-postgres__*` — dashboard-stream DB(ETL 產出表)
- `mcp__mcp-server-apache-airflow__*` — Airflow(DAG 狀態、trigger、log)— 若 MCP 無法用,改用 curl 打 `https://test-citydashboard.taipei/airflow-prod/api/v1/`
- 直接 `requests.get` 打資料源 URL

## 稽核流程

### Step 1: 確認使用者提到的元件對應的 DAG 與 DB 表

```sql
-- 在 dashboardmanager DB
SELECT c.id, c.index, c.name, qc.query_chart, qc.map_config_ids
FROM components c
LEFT JOIN query_charts qc ON c.index = qc.index
WHERE c.name LIKE '%XXX%' OR c.index = 'YYY';
```

從 query_chart SQL 讀出底層表名,再對應到 Airflow DAG(通常 DAG folder 名或 `ready_data_default_table` 跟 DB 表一致)。

### Step 2: 比對三個筆數

```python
# (a) 資料源 API
# data.taipei:  /api/v1/dataset/{rid}?scope=resourceAquire → .result.count
# data.taipei CSV: /api/frontstage/tpeod/dataset/resource.download?rid={rid}
# NTPC:  https://data.ntpc.gov.tw/api/datasets/{id}/json?page=0&size=1000
# MOENV: https://data.moenv.gov.tw/api/v2/{code}?api_key=...
# TDX:   OAuth → basic/v2/... endpoints
```

```sql
-- (b) DB 實際筆數
SELECT count(*), max(data_time), max(_mtime) FROM <ready_table>;

-- (c) BE query_chart 顯示筆數(跑完整 SQL 或 count(*) 包外層)
SELECT count(*) FROM (<query_chart SQL>) t;
```

### Step 3: 比對落差 → 定位出問題的層

| 落差 | 可能的層 |
|---|---|
| 資料源 > DB | [2] ETL 沒更新 / DAG failed / schedule 太疏 |
| 資料源 < DB | [2] ETL 累加重複 / JOIN one-to-many |
| DB = 資料源 但儀表板錯 | [4] query_chart SQL / [5] 前端渲染 |
| 全部一致但數字怪 | 資料擁有單位源頭問題 |

## 已知問題型態 / Playbook

### A. Hardcoded RID 凍結(data.taipei)

**症狀**:DAG 每月 success 但 DB 筆數從某個時間點起停止增加

**原因**:資料擁有單位重新發佈 → RID 換新 → 舊 RID 變 orphan snapshot

**修法**:
```python
# 改 ETL code
from utils.extract_stage import get_current_rid_from_page_id
PAGE_ID = "xxx"  # 原 RID 所屬的 dataset page id(從 source URL 的 ?id= 參數抓)
rid = get_current_rid_from_page_id(PAGE_ID)
# 若同 page 多資源,加 resource_name_contains='XXX' 精準篩選
```

helper 位置:`utils/extract_stage.py::get_current_rid_from_page_id`(已在這次 session 建立)

### B. 資料擁有單位改欄位名 / 值格式 → ETL KeyError

**症狀**:DAG 連續 failed,log 顯示 `KeyError: '某中文欄位' not in index`

**修法**:rename dict 兼容新舊欄位名(pandas rename 找不到會靜默跳過):
```python
data = data.rename(columns={
    "舊欄位名": "target",
    "新欄位名": "target",  # 新增一行,不刪舊的
})
```

值格式(例 `'V' → '1'`、`'◎' → '1'`):
```python
truthy = {'V', '1', 'Y', '◎', True, 1}
data['col'] = data['col'].apply(lambda x: x in truthy)
```

行政區代碼位數從 8 碼變 7 碼:
```python
district_map = {
    # 新舊都寫
    63000010: '松山區', 6300100: '松山區',
    63000020: '信義區', 6300200: '信義區',
    # ...
}
```

### C. API 回傳格式改版(dict → list)

**症狀**:TypeError `list indices must be integers or slices, not str`

**典型案例**:
- MOENV API v2: `{total, records:[]}` → 直接 list
- data.taipei: `{result:{count,results}}` → 偶爾回 list `[]`(資料集被下架 JSON 但保留 CSV)

**修法 helper 端**:
```python
body = response.json()
batch = body if isinstance(body, list) else body.get('records') or body.get('data') or body.get('result', {}).get('results') or []
# 分頁:抓到少於 limit 就停
```

**若 JSON 全空,改走 CSV fallback**:
```python
try:
    raw = get_data_taipei_api(rid)
except Exception:
    raw = None
if not raw:
    csv_url = f"https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid={rid}"
    resp = requests.get(csv_url, timeout=120, verify=False)
    for enc in ("utf-8-sig", "cp950", "big5", "utf-8"):
        try: csv_text = resp.content.decode(enc); break
        except: continue
    raw_df = pd.read_csv(io.StringIO(csv_text))
    raw_df = raw_df.loc[:, ~raw_df.columns.astype(str).str.startswith("Unnamed")]
```

### D. DB schema varchar(N) 太窄 → StringDataRightTruncation

**症狀**:`psycopg2.errors.StringDataRightTruncation: value too long for type character varying(N)`

**先找真正超長的欄位**:
```sql
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns WHERE table_name='<table>'
ORDER BY character_maximum_length NULLS LAST;
```

**修法 1 - 動 DB schema**(若表有 view 依賴,要先 DROP VIEW):
```sql
BEGIN;
DROP VIEW <view_name>;
ALTER TABLE <table> ALTER COLUMN <col> TYPE varchar(100);
CREATE VIEW <view_name> AS ...;
COMMIT;
```

**修法 2 - DAG 端截斷**(推薦,不碰 schema):
```python
df['col'] = df['col'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str[:50]
```

### E. CSV 編碼 BIG-5/cp950

**症狀**:`KeyError: '某英文欄位'` — 因為 pandas UTF-8 解碼把中文欄位名變亂碼,rename 後找不到

**修法**:
```python
csv_text = None
for enc in ('cp950', 'big5', 'utf-8-sig', 'utf-8'):
    try: csv_text = response.content.decode(enc); break
    except UnicodeDecodeError: continue
df = pd.read_csv(StringIO(csv_text))
```

`cp950` 通常優先於 `big5`(前者是微軟擴充版,包含一些特殊字)。

### F. 地址擷取行政區 — 避免 str.slice

**症狀**:`area` 欄位全部為 None 或抓到「臺北市」

**原因**:str.slice(3,6) 遇到帶郵遞區號的地址(`108臺北市萬華區...`)會抓到「臺北市」不是「萬華區」

**修法**:
```python
data['area'] = data['address'].str.extract(r"([^市縣\s]{1,3}區)", expand=False)
```

### G. LEFT JOIN 跨行政區同名街道 / 實體

**症狀**:DB 比資料源多幾筆

**原因**:JOIN key 只用街道名稱,多個行政區內的同名街道被複製

**修法**:JOIN key 改用 `(行政區, 街道名)` 複合鍵

### H. DAG 被 paused / 從未跑過

**症狀**:DB 筆數跟 source 落差很大,且 `max(_mtime)` 時間很老

**診斷**:
```bash
curl .../api/v1/dags/<dag_id>  # 看 is_paused
curl .../api/v1/dags/<dag_id>/dagRuns  # 看 total_entries(= 0 表從未跑過)
```

**修法**:
```bash
curl -X PATCH .../dags/<dag_id> -d '{"is_paused": false}'
curl -X POST  .../dags/<dag_id>/dagRuns -d '{"dag_run_id":"manual_..."}'
```

### I. load_behavior=replace + 時間序列元件不符

**症狀**:儀表板時間序列圖只畫當月一根柱

**原因**:DAG 設定 `load_behavior=replace` 每次覆蓋,無 history_table,但 query_chart 想畫月度 time-series

**修法**:改為 `current+history` 並設定 `history_table`,query_chart 改讀 history_table

### J. query_chart SQL 統計漏掉 filter 條件

**症狀**:儀表板顯示的值是真實值的倍數(×2、×3 等)

**典型**:`city_age_distribution_taipei` 每個區/每年有 `統計類型 IN ('男','女','計')` 三筆,且 `計 = 男+女`。漏 filter 就會 2 倍。

**修法**:在 query_charts 加 `AND 統計類型='計'`(或對應的 filter)

### K. 前端圖表組件渲染 bug(UNION ALL 多系列誤解)

**症狀**:DB 資料正確、query_chart SQL 回傳正確,但儀表板顯示年份重複、或只畫前 N 筆

**非 ETL 問題**:前端 `TimelineSeparateChart` 等組件處理多系列時間資料邏輯缺陷。

**處理**:回報 FE team,或改寫 query_chart 為 pivot 格式(需先驗 BE `query_type=time` 處理器相容性)

## 實用 SQL / Python snippets

### 全域統計:119 支 DAG 的 DB vs API 比對

```python
# 讀取 .agent/db_vs_api.csv 或重新執行
# 批次 UNION ALL 查所有 ready_table 的 count(*),對照 dag_row_counts.json
```

### 列出所有 hardcoded RID 的 DAG

```bash
grep -rE 'RID\s*=\s*"[0-9a-f-]{36}"|rid\s*=\s*"[0-9a-f-]{36}"' \
     Taipei-City-Dashboard-DE/dags/proj_*/ | grep -v '^\s*#'
```

### 查 DAG 最近 run 失敗原因

```python
import subprocess, json
AUTH='tuic:XXX'
BASE='https://test-citydashboard.taipei/airflow-prod/api/v1'

# 1) 最近 runs
r=subprocess.run(['curl','-sk','-u',AUTH,f'{BASE}/dags/{dag_id}/dagRuns?order_by=-execution_date&limit=5'],capture_output=True,text=True)

# 2) 抓某 run 的 log
r=subprocess.run(['curl','-sk','-u',AUTH,f'{BASE}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/etl/logs/{try_num}?full_content=true'],capture_output=True,text=True)
# 掃 traceback、KeyError、TypeError、psycopg2
```

### 模擬 DAG transform 驗證(不寫 DB)

```python
import requests, urllib3, io, pandas as pd
urllib3.disable_warnings()
r = requests.get(csv_url, timeout=60, verify=False)
df = pd.read_csv(io.StringIO(r.content.decode('cp950')))
# 套用 DAG 的 rename/filter/transform 邏輯 → 比對筆數
```

## 修正後的部署流程

```bash
# 1. feature branch 做修改
git checkout feature/mapping_data
# ... 編輯 code ...

# 2. 驗證 syntax
python3 -c "import ast; ast.parse(open('file.py').read())"

# 3. commit + push feature
git add ...; git commit -m "...";  git push origin feature/mapping_data

# 4. merge 進 develop(Airflow 從 develop 拉)
git checkout develop && git pull && git merge feature/mapping_data --no-edit
git push origin develop

# 5. 等 Airflow git sync(1~3 分鐘)+ re-parse

# 6. 驗證 code 已部署
curl .../api/v1/dags/<dag_id>/details → file_token
curl .../api/v1/dagSources/<file_token>  ← 確認新 code 內容

# 7. 手動 trigger 驗證
curl -X POST .../dagRuns -d '{"dag_run_id":"verify_<ts>"}'

# 8. 查 DB count 是否對齊預期
```

## 產出檔案(累積在 `.agent/`)

| CSV | 內容 |
|---|---|
| `dag_row_counts.csv` | 所有 active DAG 從資料源抓的最新筆數 |
| `db_vs_api.csv` | DAG × (DB 筆數 / API 筆數 / diff / component / dashboard / chart_row_counts / chart_sum_data) |
| `geocoding_dags_with_counts.csv` | 走 TPGOS 地址→座標的 DAG 清單 + 對應元件 |
| `issues_summary.csv` | 所有發現的問題彙整(對外可看的中性語言) |

## 行文規範(對外溝通)

給資料擁有單位 / 其他部門看的問題報告,**避免**以下 ETL/開發視角用詞:

| ❌ 避免 | ✅ 改用 |
|---|---|
| 凍結 X 天 | DB X 筆 vs 資料源 Y 筆 |
| 連續 N 次 failed | 資料無法更新 |
| hardcoded / 寫死 | ETL 原本引用 |
| helper crash / 炸 | API 回傳格式改版導致相容性問題 |
| bug / 錯誤 | 調整 / 相容性問題 / 落差 |

多數問題可歸因到「資料擁有單位改格式」而非 ETL 本身,如實描述即可。

## 元件 ID 範圍快速記憶

- 5~178: 早期 dashboard 元件(circular、metro、traffic、planning、disaster、childcare 等類別)
- 200~211: 節能補助、青創貸款類(台北)
- 212~219: 雙北通用 + 人口結構 KPI
- 244~261: 商圈活化、健康守護
- 286~291: 新增類別(觀光直播、YouBike E、涼適點、永續校園)

## 五層對比決策樹

```
user 說數字不對
├─ 查 dashboardmanager.query_charts 對應 SQL
├─ 跑 SQL 看 BE 層回傳幾筆  ← 跟儀表板顯示比對
│   ├─ 若 BE 回傳 ≠ 儀表板 → FE 渲染問題
│   └─ 若 BE 回傳 = 儀表板 → 繼續往下
├─ SELECT count(*) FROM <ready_table>  ← DB 層
│   └─ 對照 query_chart 有沒有用到某 WHERE filter(可能造成差異)
├─ 打資料源 API/CSV 數筆數
│   ├─ 若 DB < 資料源 → ETL 沒跟上(DAG failed / paused / schedule 太疏)
│   ├─ 若 DB > 資料源 → ETL 重複(JOIN 問題 / 累加)
│   └─ 若 DB = 資料源 → 檢查 BE SQL filter
└─ 若連資料源都不對 → 資料擁有單位的源頭問題
```
