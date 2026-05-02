# DE 實作規劃文件 §1～§11 章節骨架

每節該寫什麼、為什麼要寫、踩過的雷。寫規劃時逐節參照。

---

## §1 資料源確認

**用一張表格**列每個 dataset，欄位：

| 識別碼 | 名稱 | page_id (UUID) | 目前 rid | 格式 | 真實更新頻率 |
|---|---|---|---|---|---|

接著一句警告：rid 會輪替，必須用 `extract_stage.py:221` 的 `get_current_rid_from_page_id(page_id)`，不可硬寫 rid。

> 識別碼 = data.taipei dataset detail URL 上的 8 碼數字（如 `00001517`）。沒有這個就寫 N/A。
> page_id = 該 detail URL 上的 UUID。
> rid = 「目前」rid，會記錄抓樣本當下的值；上線後動態取。
> 真實更新頻率 = 從來源說明 + 樣本 `_importdate` 頻率推估，不是評估報告抄來的。

---

## §1.1 實際欄位（已抓樣本驗證 <today>）

**對每個 dataset 一張表**，列出來源中文鍵 vs 規劃用名 mapping：

| 來源中文鍵 | 樣本值 | 規劃用名 |
|---|---|---|

接著用「⚠️」與「✅」標出重要發現：
- ⚠️ 重大發現（如 `count=1` 公告 list 性質、欄位完全不存在等）
- ✅ regex / parse 已驗證（如「對 N 筆 facility_name 跑 regex 0 unmatched」）
- ⚠️ 命名一致性問題（如 alert station 含「站」字、elevator 不含 — 必須在 §5 處理）

**禁止寫評估報告假設的欄位**。每一項都要對得上樣本實況。

---

## §2 對「DAG 共用」的修正建議（若評估原文有提）

評估報告常給「DAG 共用 `*/5 * * * *`」這種一刀切排程，多半要修。理由：

- master data（如站點 GPS）每 5 分鐘抓沒意義
- 公告級（不定期更新）5 分鐘級異動率不高，徒耗 worker
- `common_pipeline.py:69-84` 把 minute gap ≤ 10 分鐘判為 realtime queue

**用一張表**列建議的拆分：

| DAG | 排程 | load_behavior | 理由 |
|---|---|---|---|

排程級距快速判斷：
- master data → daily（如 `0 4 * * *`）
- 即時狀態 → 每 15 分鐘（`*/15 * * * *`，避開 realtime queue）
- 真即時（公車 / 捷運運量） → `*/5 * * * *`（接受 realtime queue 開銷）

---

## §3 既有可用工具盤點（不需重造輪子）

**用一張表**列要用到的 utils 函式（`utils/extract_stage.py`、`utils/load_stage.py`、`utils/transform_*.py`）。每行：

| 需求 | 既有工具 | 位置（檔案:行號） |
|---|---|---|

掃 `dags/utils/*.py` 找該規劃會用到的：
- 抓資料源（`get_current_rid_from_page_id`、`get_data_taipei_api`、`get_tdx_data`、`get_shp_file`、`get_kml`、`download_file`）
- 取資料時間（`get_data_taipei_file_last_modified_time`）
- 時間 / 地理轉換（`convert_str_to_time_format`、`add_point_wkbgeometry_column_to_df`）
- Load（`save_dataframe_to_postgresql`、`save_geodataframe_to_postgresql`、`update_lasttime_in_data_to_dataset_info`）
- DAG 樣板（`CommonDag`）

**位置欄一定要寫具體行號**（grep 後確認），這是 skill 信譽的基礎。

---

## §3.1 骨架對照 DAG（已實證）

**用一張表**列 1～2 支既有 DAG 當骨架，明說為什麼最像：

| 新 DAG | 結構骨架 | 對照原因 |
|---|---|---|

對照原因要具體（「page_id + 純 DataFrame + current+history」），不可寫「參照 accessible_facilities/ 兩支檔案當骨架」這種模糊指引。

如果對照範例本身有缺陷（開發遺留 print、註解掉的 update_lasttime），要明確警告：「⚠️ env_srv_energy_subsidy.py 有開發遺留（line 45/47/79 的 `print()`、line 142-143 註解掉的 `update_lasttime_in_data_to_dataset_info`）— 上線前必須清掉，不要照抄。」

---

## §4 目錄與檔案結構

### 4.1 命名慣例對齊既有 codebase

掃 `dags/proj_city_dashboard/` 看相同主題既有用什麼 prefix：
- 捷運：`mrtp_*`（R0047/R0087/R0088）
- 環保 / 能源：`env_srv_*`
- 衛生：`gynecology_*`、`flu_hospitals_*`
- 都市：`urbn_*`

新表 prefix 必須對齊既有。

### 4.2 兩支新 DAG 的目錄結構

```
dags/proj_city_dashboard/
├── <dag_id_a>/
│   ├── __init__.py
│   ├── job_config.json
│   └── <dag_id_a>.py
└── <dag_id_b>/
    ├── __init__.py
    ├── job_config.json
    └── <dag_id_b>.py
```

### 4.3 對應的 PostgreSQL 表

| DAG | 表名 |
|---|---|

---

## §5 / §6 DAG 規劃（每支 DAG 一節）

### 5.1 job_config.json

完整貼上 JSON。注意：
- `dag_id`、`schedule_interval`、`load_behavior`、`ready_data_default_table`、`ready_data_history_table` 都要對
- `description`、`etl_description` 要描述 transform 重點（如「station 去尾『站』字」）

### 5.2 <dag_id>.py 骨架

**必須是樣本驗證後的版本**，不是評估報告假設的：

```python
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
    from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from utils.transform_time import convert_str_to_time_format

    PAGE_ID = "<UUID>"

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    rid = get_current_rid_from_page_id(PAGE_ID)
    raw_list = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(raw_list)
    if raw_data.empty:
        ready_data = pd.DataFrame(columns=[...])  # 空表保護
    else:
        raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
        data = raw_data.rename(columns={
            # 樣本驗過的中文鍵 → 英文鍵
        })
        # ...transform 邏輯（依 §1.1 樣本決定）
        ready_data = data[[ ... ]]

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
    )
    if not ready_data.empty:
        update_lasttime_in_data_to_dataset_info(engine, dag_id, ready_data["data_time"].max())


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="<dag_id>")
dag.create_dag(etl_func=_transfer)
```

### 5.3 對應的 PostgreSQL 表 schema

```sql
CREATE TABLE IF NOT EXISTS <table_name> (
    -- 樣本驗過的欄位
);

-- current+history 加 history table
CREATE TABLE IF NOT EXISTS <table_name>_history (LIKE <table_name>);

-- 必要 indexes
CREATE INDEX IF NOT EXISTS ... ON <table_name> (...);
```

每個欄位要有 inline comment 說明來源。Indexes 要選 query 會用的欄位（如 status、line、data_time、wkb_geometry GIST）。

---

## §7 已知風險與緩解（至少 5 項）

**用一張表**：

| 風險 | 說明 | 緩解 |
|---|---|---|

必列項目：
1. 來源 API 偶爾回空（仿 childcare_etl 加 CSV fallback）
2. 來源欄位中文鍵不確定（已抓樣本，但仍可能變動）
3. 真實更新頻率不明（先設默認，上線後從 history 統計）
4. station / 主鍵命名一致性（若 join 兩表會用到）
5. history 表累積速度（若 schedule 很頻繁）
6. 開發遺留 print / 註解（對照範例可能有，照抄會帶進來）
7. 座標 CRS（geometry 必驗）

---

## §8 對 BE 的接口（API contract + chart query）

DE plan 的下游是 BE 實作（`be-api-impl` skill）。為了讓 BE 不必回頭重新設計 endpoint shape，這一節同時提供 **API contract** + **SQL** + **response 欄位語意**，三段一起寫。

### §8.1 API Contract（endpoint × method × response type × FE 渲染）

每個 component 一行：

| Component | Endpoint | Method | Response type | FE 渲染元件 |
|---|---|---|---|---|
| C1 異常統計卡 | `/api/v1/<domain>/<sub>/alert-count` | GET | `two_d` (`TwoDimensionalDataOutput`) | 數字卡片 / 單軸折線 |
| C2 各路線異常 | `/api/v1/<domain>/<sub>/alert-by-line` | GET | `three_d` (`ThreeDimensionalDataOutput` + `categories`) | 長條圖 |
| C3 異常類型分布 | `/api/v1/<domain>/<sub>/alert-by-type` | GET | `percent` (同 `three_d`，`data[i].data` 長度 1) | 圓餅圖 |
| C4 站點地圖 | `/api/v1/<domain>/<sub>/station-overview` | GET | `map_legend` (`MapLegendData`) | 地圖圖例 |

**規則**：

- Response type 四選一，對齊 `Taipei-City-Dashboard-BE/app/models/componentData.go` 的既有型別。**禁止自訂新 struct**，除非樣本資料形狀真的塞不進四種標準（這時要在後面用 blockquote 說明為何）。
- Endpoint 走 `/api/v1/<domain>/<subdomain>/<metric>` pattern；`<domain>` / `<subdomain>` 對齊既有 router group（如 `/api/v1/mrt/a11y/...`）。掃 `Taipei-City-Dashboard-BE/app/routes/router.go` 確認命名慣例。
- Method 一律 GET，無必填參數，無 request body（與 dashboard 既有 component endpoint 一致）。

對應的 response 結構（給 BE / FE 對齊）：

```json
// two_d
{ "status": "success", "data": [{ "data": [{ "x": "...", "y": 0 }] }] }

// three_d / percent
{ "status": "success", "data": [{ "name": "...", "icon": "", "data": [3, 2] }], "categories": ["...", "..."] }

// map_legend
{ "status": "success", "data": [{ "name": "...", "type": "...", "icon": "...", "value": 4 }] }
```

### §8.2 各 endpoint 對應的 SQL

每個 endpoint 一條 SQL，用 §1.1 樣本驗過的欄位寫。**禁止用評估報告假設的欄位**（會踩到 §11 的修正紀錄）。

如果 SQL 有特殊處理（`LATERAL JOIN`、`DISTINCT ON` 去重、CTE 多步聚合），在 SQL 後面用 markdown blockquote 解釋為什麼。

```sql
-- C1: /api/v1/<domain>/<sub>/alert-count → two_d
SELECT TO_CHAR(data_time, 'YYYY-MM-DD') AS x, COUNT(*) AS y
FROM <table>
WHERE ...
GROUP BY 1 ORDER BY 1;
```

> 為什麼用 `TO_CHAR` 而不是 `data_time::date`：FE 的 `x` 期望字串，避免 driver 把 date 序列化成 timezone-aware timestamp。

### §8.3 Response 欄位語意

每個 endpoint 列出回應內每個欄位的意思、允許值、單位、注意事項。讓 BE 實作 / FE 對接不用回頭翻 schema 就知道怎麼用。

| Endpoint | 欄位 | 型別 | 語意 / 允許值 |
|---|---|---|---|
| `/.../alert-count` | `data[0].data[i].x` | string | 日期，格式 `YYYY-MM-DD` |
| `/.../alert-count` | `data[0].data[i].y` | int | 該日異常筆數 |
| `/.../alert-by-type` | `categories[i]` | string | 異常類型中文（`電梯` / `坡道` / `其他`） |
| `/.../station-overview` | `data[i].type` | string | `active` / `closed`（決定地圖 marker 顏色） |
| `/.../station-overview` | `data[i].value` | int | 該站當前 active 異常數 |

**寫到「允許值」要列舉完整**（特別是 `type` / `status` 這類 FE 會切顏色的欄位），讓 FE 不用猜可能值。

---

## §9 實作順序（建議 1 個工作日完成）

**用一張表**：

| 步驟 | 動作 | 預估 |
|---|---|---|

實作步驟通常包含：
1. cp -r <對照 DAG folder> 到新 dag folder
2. 改 job_config.json，**清掉照抄來的 print() 與被註解的 update_lasttime**
3. 按 §5 寫 transform 邏輯
4. Airflow webserver 觸發手動 run，看 PostgreSQL 表內容
5. 重複給第二支 DAG（若有）
6. 寫 BE chart query 並插入 query_charts

每步預估時間（min/hour），合計 ~4–8 小時。

---

## §10 關鍵決策請確認後再動工

至少 2 個由 user 拍板的決策。每個用：

```
1. **<決策標題>**？（推薦：<選項>，理由 ...）；如果偏好 <另一個選項>，需要 ...
```

常見決策類型：
- 是否拆成多支 DAG（vs 單一 DAG 串多 transform）
- 是否保留 history（current+history vs replace）
- status / 分類規則（keyword regex 還是 ML）
- 對照表是否獨立（如 mrt_line_station）

---

## §11 修正紀錄（<today> 抓樣本後）

**用一張表**：

| 章節 | 原規劃（依頁面描述合理推測） | 修正後（依實際樣本） |
|---|---|---|

每一項代表「如果不抓樣本就會犯的錯」。透明列出：
- §X rename：A 欄位 → B 欄位（原 A 不存在）
- §Y schema：移除 X 欄、加 Y 欄
- §Z BE query：原用 X 欄，改用 Y 欄

讀者看到 §11 就知道哪些地方被「依樣本」修過、為什麼這樣決定。
