# ETL 模組架構文件

> 記錄 `dags/ETL/` 資料夾下各程式的功能、設計模式與協作關係。

---

## 目錄結構

```
dags/ETL/
├── ETL.py                  # 主要 ETL 執行引擎
├── gen_config.py           # 設定檔產生工具
├── transform_utils.py      # 共用工具函式庫
├── etl_config.json         # 所有資料集的集中設定
└── transforms/
    ├── __init__.py
    ├── C1_藝文活動.py       # 藝文活動客製化轉換
    ├── C3_文化設施密度.py   # 文化設施密度客製化轉換
    └── C8_避難收容缺口.py  # 避難收容缺口客製化轉換
```

---

## 各檔案功能說明

### `ETL.py` — 主要執行引擎

**職責**：協調整個 Extract → Transform → Load 流程，獨立於 Airflow 運行。

| 函式 | 說明 |
|---|---|
| `extract(config)` | 依 `source_type` 派發至對應的擷取函式 |
| `_extract_data_taipei(rid)` | 從 data.taipei API 分頁擷取 |
| `_extract_open_api(api_url)` | 直接 GET 任意 Open API |
| `_extract_post_api(api_url, json_body)` | POST 方式擷取 API |
| `_extract_ntpc(ntpc_id)` | 從 data.ntpc.gov.tw 分頁擷取 |
| `_extract_merged(config)` | 遞迴擷取多個子來源並合併 |
| `extract_api()` | 提供給 transform 模組呼叫 API 的公開介面 |
| `transform(raw, data_time, config)` | 動態載入對應 transform 模組 |
| `load(df, output_dir, table_name)` | 輸出 CSV（含時間戳檔名） |
| `load_to_db(df, table_name, db_url)` | 寫入 PostgreSQL（SQLAlchemy） |
| `update_meta(df, output_path, config)` | 記錄執行 metadata 至 etl_meta.csv |
| `main(config)` | 主流程編排 |

**CLI 使用方式**：
```bash
python ETL.py --dag-id C1_藝文活動
```

---

### `gen_config.py` — 設定檔產生工具

**職責**：互動式精靈，透過關鍵字搜尋開放資料目錄，自動產生 `etl_config.json` 設定項目。

| 函式 | 說明 |
|---|---|
| `lookup_in_csv(keyword)` | 搜尋 Open Data / Open API / dataList 三份 CSV |
| `_parse_rid_from_url(access_url)` | 從 data.taipei 資源 URL 擷取 UUID |
| `_extract_open_api_endpoints(row)` | 從 CSV 欄位掃描 HTTP endpoint，推斷 method |
| `_choose_endpoint(endpoints)` | 互動選單（多 endpoint 時） |
| `fetch_columns(meta)` | 呼叫 API 取得實際欄位 schema |
| `save_to_json(dag_id, meta, cols)` | 將新設定寫入 etl_config.json |

**使用流程**：
```bash
python gen_config.py 文化資產
# → 搜尋符合關鍵字的資料集
# → 互動選擇 source 與欄位
# → 自動寫入 etl_config.json
```

---

### `transform_utils.py` — 共用工具函式庫

**職責**：提供所有 transform 模組共用的常數與通用資料清理邏輯，避免重複程式碼。

| 項目 | 說明 |
|---|---|
| `TAIPEI_TZ` | 台北時區常數（UTC+8） |
| `get_source_last_modified(page_id)` | 取得 data.taipei 資料集最後更新時間 |
| `transform_single(df, data_time, config)` | 通用清理：加 data_time、移除系統欄位、轉換座標、套用 keep_cols |

---

### `etl_config.json` — 集中設定檔

**職責**：所有資料集的 metadata 單一真相來源（Single Source of Truth）。

**設定項目結構**：
```json
"C1_藝文活動": {
    "dag_id": "C1_藝文活動",
    "output_table": "hackathon_component_1_event_map_ready",
    "source_dept": "文化部",
    "source_type": "open_api",
    "api_url": "https://cloud.culture.tw/...",
    "keep_cols": ["title", "location", ...]
}
```

**支援的 `source_type`**：

| 類型 | 說明 |
|---|---|
| `data.taipei API` | data.taipei 分頁 API（用 RID） |
| `data.ntpc API` | data.ntpc.gov.tw 分頁 API |
| `open_api` | 任意 GET API |
| `open_api_post` | POST 方式 API（附 api_body） |
| `merged` | 多子來源合併（遞迴擷取） |

**已設定資料集**（13 個）：

| dag_id | 說明 |
|---|---|
| 臺北市文化資產 | 台北文化資產 |
| 新北市文化資產 | 新北文化資產 |
| 雙北文化資產 | 雙北合併 |
| C1_藝文活動 | 藝文活動地圖 |
| C3_文化設施密度 | 各區文化設施密度 |
| C4_AED急救 | AED 位置 |
| C5_急診壅塞 | 急診壅塞（POST API） |
| C8_避難收容缺口 | 避難所容量缺口（4 來源合併） |
| C8_台北收容 | 台北避難所 |
| C8_新北收容 | 新北避難所 |
| C8_台北人口 | 台北人口（分區年齡） |
| C8_新北人口 | 新北人口（分區年齡） |
| C9_淹水監測 | 淹水監測 |

---

### `transforms/C1_藝文活動.py`

**職責**：轉換文化部 API 的藝文活動資料，處理巢狀 `showInfo` 陣列。

**輸入**：含 `showInfo`（JSON 字串陣列）的 API 回應

**處理步驟**：
1. 解析 `showInfo` JSON 字串
2. `explode` 展開（一活動 → 多場次）
3. 從 show 物件擷取場次地點、經緯度、時間
4. 過濾無效座標（dropna）
5. 轉換 `onSales` 為布林值
6. 加入 `data_time`、`source_trace`、`data_mode`

**輸出表**：`hackathon_component_1_event_map_ready`

---

### `transforms/C3_文化設施密度.py`

**職責**：整合台北、新北文化設施資料，進行區域層級聚合分析。

**輸入**：
- 台北：`個案名稱`, `資產類別`, `資產種類`, `所在地理區域`
- 新北：`name`, `affection`, `category`, `address`

**處理步驟**：
1. 統一欄位名稱（雙城欄位名稱不同）
2. 從新北地址以 regex 擷取行政區
3. 去除城市前綴，正規化區名
4. 合併雙城資料
5. 依 `city_scope` + `district` 聚合：
   - 計算設施數量
   - 蒐集設施類型清單

**輸出表**：`hackathon_component_3_cultural_density_ready`

---

### `transforms/C8_避難收容缺口.py`

**職責**：複雜多來源計算，分析各行政區對 65 歲以上脆弱族群的避難所容量缺口。

**輸入**：4 個子來源（台北/新北各自的避難所 + 人口資料）

**處理步驟**：
1. 分別解析 4 個來源（`_parse_*` 函式）
2. 台北人口：篩選 `性別=計`，加總 65 歲以上各欄位
3. 新北人口：解析 `field1` 格式（`{年}年 {區}0 {性別}`），取 `percent28` 欄位
4. 以行政區合併避難所 + 人口資料
5. 計算缺口指標：
   - `capacity_gap_abs` = 人口 − 容量
   - `capacity_gap_ratio` = 缺口 / 人口
   - `support_status`：`surplus` / `tight` / `gap` / `critical_gap`
6. 合併雙城結果

**輸出表**：`hackathon_component_8_shelter_gap_ready`

---

## 設計模式

### 1. Plugin 架構（動態 Transform 載入）

`ETL.py` 透過 `importlib.import_module()` 動態載入 `transforms/{dag_id}.py`，若不存在則退而使用 `transform_single()`。

```
所有 transform 模組必須實作相同介面：
transform(raw, data_time, config, dataset_configs) → DataFrame
```

新增資料集的 transform 只需在 `transforms/` 下建立同名 `.py` 檔，無需修改核心 `ETL.py`。

### 2. Strategy 模式（Extract 派發）

`extract()` 函式依 `source_type` 值派發至對應的擷取策略：

```
source_type
├── "data.taipei API"  → _extract_data_taipei()
├── "data.ntpc API"    → _extract_ntpc()
├── "open_api"         → _extract_open_api()
├── "open_api_post"    → _extract_post_api()
└── "merged"           → _extract_merged()  [遞迴]
```

### 3. 設定驅動設計

`etl_config.json` 是唯一的設定來源，`gen_config.py` 精靈自動生成設定，ETL.py 消費設定。新增資料集不需修改任何 Python 程式碼，僅需新增設定項目（加上可選的 transform 模組）。

### 4. 共用工具函式庫

`transform_utils.py` 提供所有 transform 共用的清理邏輯與常數，防止重複實作。

---

## 協作關係圖

```
gen_config.py
    │  產生設定
    ▼
etl_config.json ◄─────────────────────────────┐
    │  提供設定                                  │
    ▼                                           │
ETL.py                                         │
    ├── extract()                               │
    │     └── 依 source_type 派發              │
    ├── transform()                             │
    │     ├── importlib 動態載入               │
    │     │   ├── transforms/C1_藝文活動.py    │
    │     │   ├── transforms/C3_文化設施密度.py│
    │     │   └── transforms/C8_避難收容缺口.py│
    │     └── fallback: transform_utils.transform_single()
    └── load()
          ├── CSV 輸出
          └── PostgreSQL 寫入

transform_utils.py ──► 被 C1 / C3 / C8 import（TAIPEI_TZ、transform_single）
```

**依賴方向**（無循環依賴）：
- `ETL.py` → `transform_utils`（直接 import）
- `ETL.py` → `transforms/*`（動態 import，執行期）
- `transforms/*` → `transform_utils`（直接 import）
- `transforms/*` ✗ `ETL.py`（不反向 import，避免循環）

---

## 資料流範例

### 單來源標準流程（C1_藝文活動）

```
Open API (cloud.culture.tw)
    ↓ _extract_open_api()
    ↓ C1_藝文活動.transform()
      ├── 解析 showInfo JSON
      ├── explode 展開場次
      ├── 擷取 lat/lon/address
      └── 過濾無效座標
    ↓ load() → CSV + DB
```

### 多來源合併流程（C3_文化設施密度）

```
extract() [merged]
├── 臺北市文化資產 → data.taipei API → DataFrame
└── 新北市文化資產 → data.ntpc API  → DataFrame
    ↓ C3_文化設施密度.transform()
      ├── 套用 column_map 統一欄位名
      ├── concat 雙城資料
      ├── regex 擷取新北行政區
      └── 聚合：設施數 + 類型清單
    ↓ load() → CSV + DB
```

### 複雜計算流程（C8_避難收容缺口）

```
extract() [merged, 4 子來源]
├── C8_台北收容 → 避難所資料
├── C8_新北收容 → 避難所資料
├── C8_台北人口 → 65+ 人口
└── C8_新北人口 → 65+ 人口
    ↓ C8_避難收容缺口.transform()
      ├── _parse_taipei_shelter()
      ├── _parse_ntpc_shelter()
      ├── _parse_taipei_population()  [加總 65~100 歲各欄]
      ├── _parse_ntpc_population()    [解析 field1 格式]
      ├── merge 避難所 + 人口（by 行政區）
      └── _calc_gap()：計算缺口 + 分類
    ↓ load() → CSV + DB
```

---

## 資料庫連線優先序

`load_to_db()` 依以下順序決定連線：

1. 傳入的 `db_url` 參數
2. 環境變數 `HACKATHON_DB_URL`
3. 環境變數 `DB_DASHBOARD_*`（user/password/host/port/dbname）
4. 預設 localhost postgres（開發用）

若 DB 寫入失敗，資料仍會儲存至 CSV（graceful degradation）。

---

## 新增資料集 SOP

1. **產生設定**：`python gen_config.py {關鍵字}` → 互動選擇 → 自動寫入 `etl_config.json`
2. **撰寫 transform**（可選）：在 `transforms/{dag_id}.py` 實作 `transform(raw, data_time, config, dataset_configs) → DataFrame`
3. **執行**：`python ETL.py --dag-id {dag_id}`

若無需客製化清理邏輯，步驟 2 可跳過，系統自動使用 `transform_single()` 通用清理。
