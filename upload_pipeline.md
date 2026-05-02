這是一份為你量身打造的 `upload_pipeline.md`。這份文件結合了系統規格書（Spec）的規範，以及我們剛剛在實戰中經歷的建表、資料清理、SQL 轉型與除錯經驗。

你可以直接將以下內容複製並存成 Markdown 檔案，作為未來新增任何組件的標準作業流程（SOP）。

---

# 臺北城市儀表板 - 新增組件與資料上傳標準流程 (Upload Pipeline)

本文件說明如何在系統中建立全新的資料組件（Component），涵蓋從原始資料匯入、關聯式資料庫建置，到圖表與地圖配置的完整流程。系統架構上分為 **實體資料庫 (`dashboard`)** 與 **設定檔資料庫 (`dashboardmanager`)**，操作時請務必確認當前連線環境。

---

## 階段一：準備資料與建置實體表 (Data Layer)

**操作環境**：`dashboard` 資料庫

### 1. 建立實體資料表

在匯入資料前，必須先在資料庫建立對應的 Schema。

- **字元規範**：若欄位名稱包含特殊符號（如 `[株]`、`/`）或全中文，必須使用**雙引號 `""`** 將欄位名稱包覆。
- **資料型態**：數值類統一設為 `NUMERIC`，帶有文字的時間或分類設為 `VARCHAR`。

```sql
CREATE TABLE public.your_dataset_name (
    "統計期" VARCHAR(20) PRIMARY KEY,
    "指標A[單位]" NUMERIC,
    "指標B[單位]" NUMERIC
);
```

### 2. 資料匯入 (CSV/Excel) 的避坑指南

透過 pgAdmin 的 Import/Export 功能匯入資料時，請注意以下兩點以避免 `psql: error: utility failed` 錯誤：

1.  **標題列 (Header)**：務必在匯入選項 (Options) 中將 `Header` 設為 `Yes`，讓資料庫略過第一行的中文字。
2.  **幽靈空白行**：CSV 檔案最末端絕對不能包含完全空白的換行符號（會導致 `missing data for column` 錯誤）。請用純文字編輯器刪除檔尾的空白行後再匯入。

---

## 階段二：組件註冊與配置 (Config Layer)

**操作環境**：`dashboardmanager` 資料庫

### 1. 註冊最高層級組件 (`components` 表)

在總表中註冊你的組件，賦予其唯一識別碼與介面顯示名稱。

- **index**: 組件的唯一英文識別碼（例如 `taipei_urban_greening`）[cite: 4]。
- **name**: 介面顯示的中文名稱（例如 `{臺北市市容綠美化}`）[cite: 4]。

### 2. 配置地圖屬性 (`component_maps` 表) _[空間資料適用]_

若資料包含 GeoJSON 或空間座標，需在此設定地圖渲染方式[cite: 4, 5]。若為純時間數列或統計資料，則**跳過此步**。

- **type**: 支援 `circle`, `fill`, `line`, `symbol` 等 Mapbox 內建類型[cite: 4, 5]。
- **paint**: 必須指定顏色屬性（如 `{"circle-color": "#FF0000"}`），否則預設為黑色[cite: 4, 5]。
- **property**: 設定要在地圖彈出式視窗 (Popup) 中顯示的 JSON 欄位對應[cite: 4, 5]。

### 3. 配置圖表屬性 (`component_charts` 表)

設定組件預設的視覺化圖表類型與色系[cite: 4, 5]。

- **types**: 填入 1-3 個圖表英文名稱（例如 `{TimelineSeparateChart,ColumnChart}`）[cite: 4, 5]。
- **color**: 填入 Hex 色碼陣列，為不同系列設定顏色[cite: 4, 5]。

---

## 階段三：資料查詢與前端綁定 (`query_charts` 表)

此步驟為核心，負責寫入 SQL 讓前端圖表知道如何去 `dashboard` 抓取資料[cite: 4, 5]。

### 1. 基礎設定

- **map_config_ids**: 填入階段二設定的地圖 ID，若無地圖則設為空陣列 `{}`[cite: 4, 5]。
- **query_type**: 二維資料設為 `two_d`，多維度/多系列資料設為 `three_d`[cite: 4, 5]。

### 2. SQL 撰寫標準 (Query Chart)

前端圖表套件對資料欄位有嚴格的命名要求。必須將查詢結果輸出為以下別名：

- **`x_axis`**：X 軸的分類或時間。
- **`data`**：Y 軸的實際數值。
- **`name`**：系列名稱（適用於 `three_d` 多線條/多系列的情境）[cite: 4, 5]。

#### 💡 進階轉換技巧一：解開多欄位 (Unpivot) 轉為 3D 結構

如果一張表有多個數值欄位（如行道樹、草花數），需使用 `UNION ALL` 轉為直向排列，並賦予 `name` 系列名稱，否則圖表數值會全部顯示為 0。

```sql
SELECT * FROM (
    SELECT "統計期" AS x_axis, '行道樹' AS name, "行道樹[株]" AS data FROM public.your_table
    UNION ALL
    SELECT "統計期" AS x_axis, '草花培育' AS name, "草花培育數[盆]" AS data FROM public.your_table
) d
```

#### 💡 進階轉換技巧二：時間軸格式轉換 (Time Series Parsing)

針對 `TimelineSeparateChart` 等折線圖，若 `x_axis` 傳入如 `"70年"` 的字串，前端時間軸會解析失敗導致所有資料點擠在最左側。必須在 SQL 中將其轉換為標準西元格式（`YYYY-MM-DD`）。

```sql
-- 將「70年」轉換為「1981-01-01」
CAST(CAST(REPLACE("統計期", '年', '') AS INTEGER) + 1911 AS VARCHAR) || '-01-01' AS x_axis
```

---

## 階段四：常見系統與介面除錯 (Troubleshooting)

1.  **API 回報 500 ERROR (relation does not exist)**
    - **原因**：後端連線的實體資料庫，與你建表的資料庫不同。
    - **解法**：確認建表 (CREATE TABLE) 的語法是執行在 `dashboard` (Data DB)，而不是 `dashboardmanager` (Config DB)。
2.  **pgAdmin 左側樹狀圖找不到剛建好的表**
    - **原因**：pgAdmin 介面快取未更新。
    - **解法**：對著左側 `Tables` 或 `Schemas` 點擊右鍵選擇 `Refresh...`。若無效，對 Database 點選 `Disconnect` 後再次連線即可強制重整。
3.  **折線圖 X 軸排序錯亂**
    - **原因**：字串排序陷阱（`"100年"` 會排在 `"70年"` 前面）。
    - **解法**：在 SQL 的 `ORDER BY` 中，將字串轉為純數字後再排序：`ORDER BY CAST(REPLACE(x_axis, '年', '') AS INTEGER) ASC`。
