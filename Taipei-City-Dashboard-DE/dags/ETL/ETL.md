# `ETL.py` 說明文件

> 不依賴 Airflow 的獨立 ETL 腳本，流程對應 `template_dag.py`，輸出 CSV 供前端或隊友直接使用。

---

## 快速開始

```bash
# 安裝相依套件
pip install requests pandas

# 執行（使用頂部手動 CONFIG）
python ETL.py
```

---

## 三種執行方式

### 方式 A：手動指定（預設）

直接修改 `ETL.py` 頂部的 `CONFIG` 字典，填入 `RID` 與 `PAGE_ID` 後執行：

```bash
python ETL.py
```

### 方式 B：互動式從 CSV 選擇資料集

```bash
python ETL.py --from-csv
```

執行後依序提示：
1. 選擇 CSV 來源（Open Data / Open API / dataList）
2. 顯示前 30 筆資料集列表
3. 輸入列號或名稱關鍵字 → 自動填入 PAGE_ID / RID

### 方式 C：直接指定資料集名稱（最快）

```bash
python ETL.py --dataset "臺北市醫院清冊"
```

支援關鍵字模糊比對，不需打完整名稱。

### 列出 CSV 內容（查找資料集用）

```bash
python ETL.py --list open_data    # 查 Open Data.csv
python ETL.py --list open_api     # 查 Open API.csv
python ETL.py --list data_list    # 查 dataList.csv
```

---

## CSV 來源說明

| CSV 檔案 | 資料來源 | PAGE_ID / RID | 支援程度 |
|---|---|---|---|
| `Open Data.csv` | data.taipei 靜態檔案 | 自動解析 | 全自動 |
| `Open API.csv` | 即時 API（各局處） | 無（直接呼叫 URL） | extract 自動，transform 需調整 |
| `dataList.csv` | 新北市等其他平台 | 不適用 | 僅取得網址，extract 需自行補寫 |

---

## 流程對應關係

| DAG 步驟 | 本腳本對應函式 | 說明 |
|---|---|---|
| `get_job_config` | `CONFIG` 字典 | 集中管理所有設定 |
| ETL – Extract | `extract()` | 依 source_type 自動選擇取資料策略 |
| ETL – Transform | `transform()` | 清洗、欄位標準化、時區處理 |
| ETL – Load | `load()` | 輸出 CSV（原本寫 PostgreSQL） |
| `update_lasttime_in_data` | `update_meta()` | 記錄 ETL 執行資訊至 `etl_meta.csv` |

---

## 各函式詳解

### `CONFIG`

集中管理所有可調整的參數，手動模式時只需改這一處。

```python
CONFIG = {
    "dag_id":       "heal_hospital",   # 識別用名稱
    "output_dir":   "./data",          # CSV 輸出目錄
    "output_table": "heal_hospital",   # 輸出檔名前綴
    "RID":          "04a3d195-...",    # data.taipei 資源 ID
    "PAGE_ID":      "ffdd5753-...",    # data.taipei 頁面 ID（取更新時間）
}
```

---

### `load_config_from_csv(dataset_name)` — 從 CSV 自動建立 CONFIG

依名稱關鍵字搜尋三個 CSV，自動解析並回傳 config dict。

- **Open Data.csv**：`資料集id` → `PAGE_ID`；`資料存取網址` 路徑中第二段 UUID → `RID`
- **Open API.csv**：直接取 `資料存取網址` 作為 `api_url`
- **dataList.csv**：取 `資料集網址`，標記為 `other` 來源

---

### `extract(config)` — 取原始資料

依 `_csv_type` 自動選擇策略：

| source_type | 行為 |
|---|---|
| `open_data` | `GET https://data.taipei/api/v1/dataset/{RID}/preview` 分頁取回 |
| `open_api` | 直接 GET `api_url`，自動解析 list / result / data / records |
| `data_list` | 印出警告，回傳空 DataFrame（需自行實作） |

---

### `get_source_last_modified(page_id)` — 取資料更新時間

- 有 PAGE_ID：呼叫 `https://data.taipei/api/v1/dataset/{page_id}` 取 `modified` 欄位
- 無 PAGE_ID（Open API / 其他來源）：fallback 為當下時間

---

### `transform(raw_df, data_time)` — 清洗

執行步驟：

1. **欄位名稱轉小寫** — 避免大小寫不一致
2. **重命名欄位** — 中文 → 英文小寫（依實際資料集調整 `rename_map`）
3. **時間標準化** — 加上台北時區 `UTC+8`，輸出 ISO 格式
4. **數值轉換** — `lng`、`lat` 轉 float，無效值填 NaN
5. **移除平台內部欄位** — `_id`、`objectid`
6. **篩選輸出欄位** — 只保留 `keep_cols` 列表內的欄位
7. **去除空值列** — 刪除 `name` 為空的資料

> **換資料集時**，主要調整 `rename_map` 和 `keep_cols` 兩處。

---

### `load(df, output_dir, table_name)` — 輸出 CSV

- 自動建立輸出目錄
- 檔名格式：`{table_name}_{YYYYMMDD_HHMMSS}.csv`
- 編碼使用 `utf-8-sig`（含 BOM，Excel 直接開啟不亂碼）

---

### `update_meta(df, output_path, config)` — 記錄執行資訊

對應 DAG 的 `update_lasttime_in_data_to_dataset_info`，追加至 `etl_meta.csv`：

| 欄位 | 說明 |
|---|---|
| `dag_id` | 資料集識別碼 |
| `output_file` | 本次輸出的 CSV 檔名 |
| `rows` | 輸出筆數 |
| `lasttime_in_data` | 資料中最新的 `data_time` |
| `run_at` | 本次執行時間 |

---

## 換其他資料集的步驟

### 使用 CSV 自動模式（推薦）

```bash
# 1. 查詢可用資料集
python ETL.py --list open_data

# 2. 執行（關鍵字即可）
python ETL.py --dataset "資料集名稱關鍵字"

# 3. 如果欄位名稱不同，調整 ETL.py 內 transform() 的 rename_map
```

### 手動模式

1. 至 [data.taipei](https://data.taipei) 找到目標資料集，取得 **PAGE_ID**（網址列 `id=` 後方）與 **RID**（資料存取網址路徑中第二段 UUID）
2. 修改 `CONFIG` 中的 `RID`、`PAGE_ID`、`dag_id`、`output_table`
3. 根據實際欄位調整 `transform()` 內的 `rename_map` 和 `keep_cols`
4. 執行 `python ETL.py`

---

## 輸出檔案結構

```
data/
├── heal_hospital_20260418_093012.csv   ← 主資料
├── heal_hospital_20260418_150045.csv   ← 下次執行
└── etl_meta.csv                        ← 每次執行紀錄（累加）
```

### 主資料欄位（預設）

| 欄位 | 型別 | 說明 |
|---|---|---|
| `data_time` | string (ISO) | 資料時間（含時區） |
| `name` | string | 機構名稱 |
| `addr` | string | 地址 |
| `lng` | float | 經度 |
| `lat` | float | 緯度 |

---

## 相依套件

```
requests>=2.28
pandas>=2.0
```
