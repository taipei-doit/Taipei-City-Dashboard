# EV 充電站組件 — 建置與上傳邏輯說明

## 一、整體架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        資料來源                                  │
│   ev_stations_with_district.csv    ev_stations_with_district.geojson │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│   dashboard DB           │   │  前端靜態檔案                      │
│   public.ev_stations     │   │  public/mapData/ev_stations.geojson │
│   (圖表查詢用)            │   │  (Mapbox 地圖渲染用)               │
└──────────────┬───────────┘   └──────────────┬───────────────────┘
               │                              │
               ▼                              │
┌──────────────────────────┐                  │
│  dashboardmanager DB     │                  │
│  components              │                  │
│  component_charts        │                  │
│  component_maps  ────────┼──────────────────┘
│  query_charts            │
│  (組件配置 & SQL 查詢)    │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│  GET /api/v1/component/:index                                │
│  → 合併 components + component_charts + query_charts         │
│  → 執行 query_chart SQL 取得圖表資料                          │
│  → 回傳 map_config (含 geojson 路徑) + chart data             │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                      Frontend                                │
│  ┌────────────────────┐    ┌──────────────────────────────┐  │
│  │  圖表面板            │    │  Mapbox 地圖                  │  │
│  │  DistrictChart      │    │  載入 /mapData/{index}.geojson │  │
│  │  PolarAreaChart     │    │  依 component_maps.paint 渲染  │  │
│  │  MapLegend          │    │  依 component_maps.property   │  │
│  │  (由 API 資料驅動)   │    │  顯示 popup 資訊              │  │
│  └────────────────────┘    └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 二、資料流詳細說明

### 2.1 圖表資料流（dashboard DB → API → 圖表）

```
[dashboard DB] public.ev_stations (704 筆原始資料)
        │
        │  query_charts.query_chart 中的 SQL 查詢
        │  SELECT district AS x_axis, SUM(total_charging_points) AS data
        │  FROM public.ev_stations
        │  GROUP BY district
        │  ORDER BY ...
        │
        ▼
[Backend] GetTwoDimensionalData (query_type = 'two_d')
        │
        │  Backend 將 SQL 結果轉換為 2D 格式：
        │  { "data": [{ "data": [{ "x": "北投區", "y": 140 }, ...] }] }
        │
        ▼
[Frontend] DistrictChart / PolarAreaChart / MapLegend
        │
        │  圖表元件讀取 data 陣列
        │  DistrictChart: 依行政區名著色深淺
        │  PolarAreaChart: 依數值大小顯示扇形面積
        │  MapLegend: 顯示圖例
        ▼
      使用者看到圖表
```

### 2.2 地圖資料流（GeoJSON → Mapbox）

```
[靜態檔案] public/mapData/ev_stations.geojson (660 個 Point features)
        │
        │  前端 mapStore 根據 component_maps.index 拼出路徑：
        │  /mapData/{index}.geojson → /mapData/ev_stations.geojson
        │
        ▼
[Mapbox GL JS] addSource('ev_stations', { type: 'geojson', data: ... })
        │
        │  依 component_maps.type = 'circle' 建立圖層
        │  依 component_maps.paint 設定樣式：
        │  {
        │    "circle-radius": 6,
        │    "circle-color": "#4CAF93",
        │    "circle-stroke-color": "#ffffff",
        │    "circle-stroke-width": 1.5,
        │    "circle-opacity": 0.85
        │  }
        │
        ▼
[Mapbox] 地圖上渲染 660 個綠色圓點
        │
        │  使用者點擊圓點 → 讀取 GeoJSON feature.properties
        │  依 component_maps.property 決定 popup 顯示內容：
        │  [
        │    {"key":"station_name","name":"充電站名稱"},
        │    {"key":"district","name":"行政區"},
        │    {"key":"operator_name","name":"營運業者"},
        │    ...
        │  ]
        │
        ▼
      使用者看到地圖站點 + 點擊 popup
```

### 2.3 地圖篩選（圖表 ↔ 地圖互動）

```
[使用者] 在 DistrictChart 上點擊「大安區」
        │
        │  selectedIndex = "大安區"
        │
        ▼
[mapStore] addByParamFilter({
             xParam: "district",    ← 來自 query_charts.map_filter.byParam.xParam
             value: "大安區"         ← 來自使用者點擊
           })
        │
        │  Mapbox filter: ["==", ["get", "district"], "大安區"]
        │
        ▼
[Mapbox] 只顯示 district === "大安區" 的站點（其餘隱藏）
        │
        │  再次點擊同區域 → clearByParamFilter → 恢復顯示全部
        ▼
      地圖篩選完成
```

## 三、資料庫表格關聯

### dashboardmanager DB

```
┌─────────────────────┐
│     components       │
│─────────────────────│
│ index (PK): 組件 ID  │ ← "ev_stations"
│ name: 組件中文名      │ ← "電動車充電站分布"
└──────────┬──────────┘
           │ index = index
           ▼
┌──────────────────────────────────────────────────────┐
│                   component_charts                    │
│──────────────────────────────────────────────────────│
│ index (PK): 組件 ID                                   │
│ color: hex 色碼陣列      ← '{#4CAF93, #5BB8A0, ...}' │
│ types: 圖表類型陣列      ← '{DistrictChart, PolarAreaChart, MapLegend}' │
│ unit: 資料單位           ← '支'                       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                   component_maps                      │
│──────────────────────────────────────────────────────│
│ id (PK): 自動產生的 serial ID                         │
│ index: 組件 ID + 地圖檔案名      ← "ev_stations"      │
│ title: 地圖圖層名稱              ← "電動車充電站"      │
│ type: Mapbox 地圖類型            ← "circle"           │
│ source: 資料來源                 ← "geojson"          │
│ size: 預設大小變化               ← NULL               │
│ icon: 預設圖示變化               ← NULL               │
│ paint: Mapbox Paint JSON         ← circle 樣式        │
│ property: popup 顯示欄位 JSON    ← 9 個欄位           │
└──────────┬───────────────────────────────────────────┘
           │ id → query_charts.map_config_ids
           ▼
┌──────────────────────────────────────────────────────┐
│                    query_charts                       │
│──────────────────────────────────────────────────────│
│ index + city (複合 PK)                                │
│   ├─ "ev_stations" + "taipei"                        │
│   └─ "ev_stations" + "metrotaipei"                   │
│                                                      │
│ map_config_ids: INTEGER[]  ← {component_maps.id}     │
│ map_filter: JSON           ← byParam + xParam=district │
│ query_type: 'two_d'        ← Backend 用此決定解析函式  │
│ query_chart: SQL 查詢文字   ← 對 dashboard DB 執行     │
│ source / short_desc / long_desc / use_case: 組件資訊  │
│ time_from: 'static'        ← 表示非時間序列            │
│ update_freq + unit: 更新頻率                          │
└──────────────────────────────────────────────────────┘
```

### dashboard DB

```
┌──────────────────────────────────────────────────────┐
│                   ev_stations                         │
│──────────────────────────────────────────────────────│
│ station_id (PK): VARCHAR(50)   ← "TPE0201U03"       │
│ city: VARCHAR(50)              ← "台北市" / "新北市"  │
│ district: VARCHAR(50)          ← "大安區"            │
│ station_name: VARCHAR(200)     ← 充電站名稱          │
│ operator_name: VARCHAR(200)    ← 營運業者            │
│ lat / lon: NUMERIC             ← 座標（CSV 專用）    │
│ total_charging_points: INTEGER ← 充電槍數            │
│ available / occupied / unavailable: INTEGER          │
│ connector_types / charge_rate / parking_rate: TEXT    │
│ ... 共 26 個欄位                                     │
└──────────────────────────────────────────────────────┘
```

## 四、query_type 與 Backend 處理函式對應

| query_type | Backend 函式 | SQL 回傳欄位 | 適用圖表 |
|---|---|---|---|
| `two_d` | `GetTwoDimensionalData` | `x_axis`, `data` | DistrictChart, PolarAreaChart, BarChart, ColumnChart, DonutChart, TreemapChart, RadarChart |
| `three_d` | `GetThreeDimensionalData` | `x_axis`, `y_axis`, `data` | BarPercentChart, ColumnChart (多系列), HeatmapChart, TextUnitChart |
| `percent` | `GetThreeDimensionalData` | `x_axis`, `y_axis`, `data` | GuageChart, IconPercentChart |
| `time` | `GetTimeSeriesData` | `x_axis`, `y_axis`, `data` (時間) | TimelineSeparateChart, TimelineStackedChart |
| 其他 | `GetMapLegendData` | 只回傳圖例 | MapLegend (無圖表) |

本組件使用 `two_d`，SQL 回傳 `x_axis`（行政區名）+ `data`（充電槍數加總），Backend 自動轉換為 `{ "x": "...", "y": N }` 格式。

## 五、GeoJSON 與 CSV 的分工

| 面向 | CSV (→ dashboard DB) | GeoJSON (→ 前端靜態檔案) |
|---|---|---|
| 用途 | 圖表查詢 (SQL GROUP BY) | 地圖渲染 (Mapbox) |
| 資料筆數 | 704 筆 | 660 筆 (僅含有行政區的站點) |
| 座標處理 | lat/lon 存在 DB 欄位中（圖表不使用） | geometry.coordinates 供 Mapbox 定位 |
| 經過 Backend | 是 (Backend 執行 SQL 查詢) | 否 (前端直接載入靜態檔案) |
| 檔案命名規則 | 匯入後不需要特定檔名 | 必須是 `{component_maps.index}.geojson` |

## 六、完整執行步驟

### Step 1：dashboard DB — 建表 & 匯入

```sql
-- 在 dashboard DB 執行
CREATE TABLE IF NOT EXISTS public.ev_stations ( ... );
-- 然後用 pgAdmin Import CSV (UTF-8, Header=Yes)
```

### Step 2：GeoJSON 放置前端

```bash
cp ev_stations_with_district.geojson \
   Taipei-City-Dashboard-FE/public/mapData/ev_stations.geojson
# 檔名必須與 component_maps.index 一致
```

### Step 3：dashboardmanager DB — 執行 SQL

依序 INSERT 四張表（順序重要，因為 query_charts 需要引用 component_maps.id）：

1. `components` — 建立組件基本資料
2. `component_charts` — 設定圖表類型與顏色
3. `component_maps` — 設定地圖圖層樣式（此步產生 `id`）
4. `query_charts` — 設定查詢 SQL 並引用 `component_maps.id`

### Step 4：重啟 Backend & 驗證

```
重啟 Backend → API 重新讀取 dashboardmanager 設定
前端載入 → 呼叫 API 取得組件資料 + 載入 geojson
圖表顯示 DistrictChart / PolarAreaChart
地圖顯示 660 個圓點
點擊圖表行政區 → 地圖篩選對應站點
```

## 七、常見問題排查

| 症狀 | 原因 | 解決方式 |
|---|---|---|
| 地圖沒有圓點 | geojson 檔名與 component_maps.index 不一致 | 確認 `public/mapData/{index}.geojson` 存在 |
| 圖表無資料 | query_type 設錯（如設為 static） | 確認 query_type = 'two_d' |
| 行政區圖缺少區域 | SQL 沒有包含全部 41 個行政區 | 使用 LEFT JOIN + VALUES 確保 41 區全出現 |
| 點擊圖表地圖不篩選 | map_filter 未設定或 xParam 不匹配 | 確認 map_filter.byParam.xParam 與 geojson property key 一致 |
| map_config_ids 為空 | component_maps 未先 INSERT 就執行 query_charts | 確保執行順序：component_maps → query_charts |
| popup 欄位顯示不出 | property JSON 中 key 與 geojson properties 名稱不符 | 比對 geojson feature.properties 的實際 key |
