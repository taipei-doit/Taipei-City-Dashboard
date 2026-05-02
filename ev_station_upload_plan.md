# EV 充電站組件上傳計畫

> 目標：將 `ev_stations_with_district.geojson`（660 站，台北市 399 + 新北市 261）匯入資料庫，在 Mapbox 地圖上正確顯示兩個組件：`ev_station_distribution`（分布）與 `ev_station_realtime`（即時使用狀況）。

---

## 一、現有 SQL Script 的問題清單

### 問題 1：Markdown 超連結污染（嚴重）

原稿中所有 `EXCLUDED` 欄位被 Notion/Markdown 渲染為超連結，需全部修正：

| 位置                            | 錯誤寫法                                | 正確寫法                  |
| ------------------------------- | --------------------------------------- | ------------------------- |
| `components` ON CONFLICT        | `[EXCLUDED.name](http://...)`           | `EXCLUDED.name`           |
| `component_maps` ON CONFLICT    | `[EXCLUDED.property](http://...)`       | `EXCLUDED.property`       |
| `query_charts` ON CONFLICT (×4) | `[EXCLUDED.map](http://...)_config_ids` | `EXCLUDED.map_config_ids` |

---

### 問題 2：`query_type` 欄位值錯誤（嚴重）

4 筆 `query_charts` 的 `query_type` 均設為 `'static'`，Backend 只認識以下值：

| `query_type`        | Backend 處理函式          | SQL 輸出欄位                       |
| ------------------- | ------------------------- | ---------------------------------- |
| `two_d`             | `GetTwoDimensionalData`   | `x_axis`, `data`                   |
| `three_d`           | `GetThreeDimensionalData` | `x_axis`, `y_axis`, `data`         |
| `percent`           | `GetThreeDimensionalData` | 同上                               |
| `time`              | `GetTimeSeriesData`       | `x_axis`, `y_axis`, `data`（時間） |
| 其他（含 `static`） | `GetMapLegendData`        | 只回傳圖例，無圖表資料             |

修正：`ev_station_distribution` → `two_d`，`ev_station_realtime` → `three_d`

---

### 問題 3：欄位名稱與實際資料不符（嚴重）

依據實際上傳的 `ev_stations_with_district.csv` 與 `ev_stations_with_district.geojson`：

| 舊腳本假設                                                   | 實際欄位                                   | 說明                    |
| ------------------------------------------------------------ | ------------------------------------------ | ----------------------- |
| `operator_id` INTEGER                                        | `operator_name` VARCHAR                    | 業者名稱字串，非 ID     |
| `charging_points`                                            | `total_charging_points`                    | 欄位改名                |
| `charging_rate`                                              | `charge_rate`                              | 欄位改名                |
| `telephone`                                                  | `phone`                                    | 欄位改名                |
| `city = 'taipei'`                                            | `city = '台北市'`                          | 值為中文，非英文城市碼  |
| ❌                                                           | `operator_tel`, `operator_url`             | 新增                    |
| ❌                                                           | `unavailable`, `charged_kwh_total`         | 新增                    |
| ❌                                                           | `connector_types`, `payment`, `start_type` | 新增                    |
| `available`, `occupied`, `availability_pct` ❌（上一版移除） | ✅ 確實存在                                | realtime 組件可完整還原 |

---

### 問題 4：`query_chart` 為空 Mock（需填入實際 SQL）

詳見第三階段。

---

## 二、完整執行流程

### 階段 2-A：GeoJSON → 前端（地圖渲染用）

前端 mapStore 透過 `/mapData/{index}.geojson` 讀取靜態檔案，地圖渲染不經過 DB。
**GeoJSON properties 中不含 `lat`/`lon`（座標在 geometry.coordinates），無需處理。**

```bash
# ev_stations_with_district.geojson 已同時含台北市與新北市（共 660 站）
# 兩個組件共用同一份地圖資料，複製為兩個 index 對應的檔名

cp ev_stations_with_district.geojson \
   Taipei-City-Dashboard-FE/public/mapData/ev_station_distribution.geojson

cp ev_stations_with_district.geojson \
   Taipei-City-Dashboard-FE/public/mapData/ev_station_realtime.geojson
```

---

### 階段 2-B：CSV → `dashboard` DB（圖表查詢用）

**在 dashboard 資料庫建立資料表：**

```sql
-- DB: dashboard
-- 注意：欄位名稱與順序完全對應 ev_stations_with_district.csv 的標頭
CREATE TABLE IF NOT EXISTS public.ev_stations (
    station_id          VARCHAR(50)  PRIMARY KEY,
    city                VARCHAR(50),            -- 中文值：'台北市' 或 '新北市'
    district            VARCHAR(50),            -- 中文行政區，如「大安區」
    station_name        VARCHAR(200),
    operator_name       VARCHAR(200),           -- 業者名稱（VARCHAR，非 INTEGER）
    operator_tel        VARCHAR(50),
    operator_url        VARCHAR(300),
    lat                 NUMERIC,
    lon                 NUMERIC,
    address             VARCHAR(200),
    description         TEXT,
    spaces              INTEGER,
    total_charging_points INTEGER,              -- 欄位名為 total_charging_points
    available           INTEGER,
    occupied            INTEGER,
    unavailable         INTEGER,
    availability_pct    INTEGER,
    charged_kwh_total   NUMERIC,
    connector_types     TEXT,                   -- 可能含多個規格，用 TEXT 避免長度問題
    charge_rate         TEXT,
    parking_rate        TEXT,
    payment             VARCHAR(200),
    start_type          VARCHAR(200),
    service_time        TEXT,                   -- 部分站點為多行文字，超過 VARCHAR(100)
    floors              VARCHAR(50),
    phone               VARCHAR(50)             -- 欄位名為 phone（非 telephone）
);
```

**CSV 欄位對應（依 CSV 標頭順序，共 26 欄）：**

| #   | CSV 欄位                | 型別    | 備註                                       |
| --- | ----------------------- | ------- | ------------------------------------------ |
| 1   | `station_id`            | VARCHAR | 主鍵                                       |
| 2   | `city`                  | VARCHAR | `台北市` 或 `新北市`                       |
| 3   | `district`              | VARCHAR | 中文值，供 map_filter byParam 對應 GeoJSON |
| 4   | `station_name`          | VARCHAR |                                            |
| 5   | `operator_name`         | VARCHAR | 部分為空（3 筆）                           |
| 6   | `operator_tel`          | VARCHAR | 部分為空（10 筆）                          |
| 7   | `operator_url`          | VARCHAR | 部分為空（10 筆）                          |
| 8   | `lat`                   | NUMERIC | 緯度                                       |
| 9   | `lon`                   | NUMERIC | 經度                                       |
| 10  | `address`               | VARCHAR | 部分為空（241 筆）                         |
| 11  | `description`           | VARCHAR | 部分為空（3 筆）                           |
| 12  | `spaces`                | INTEGER |                                            |
| 13  | `total_charging_points` | INTEGER |                                            |
| 14  | `available`             | INTEGER |                                            |
| 15  | `occupied`              | INTEGER |                                            |
| 16  | `unavailable`           | INTEGER |                                            |
| 17  | `availability_pct`      | INTEGER |                                            |
| 18  | `charged_kwh_total`     | NUMERIC |                                            |
| 19  | `connector_types`       | VARCHAR | 部分為空（62 筆）                          |
| 20  | `charge_rate`           | VARCHAR |                                            |
| 21  | `parking_rate`          | VARCHAR | 部分為空（15 筆）                          |
| 22  | `payment`               | VARCHAR | 部分為空（41 筆）                          |
| 23  | `start_type`            | VARCHAR | 多數為空（404 筆）                         |
| 24  | `service_time`          | VARCHAR |                                            |
| 25  | `floors`                | VARCHAR | 部分為空（2 筆）                           |
| 26  | `phone`                 | VARCHAR | 部分為空（21 筆）                          |

pgAdmin 匯入注意事項：

- Format：CSV，Header：Yes
- Encoding：UTF-8（檔案含 BOM，pgAdmin 選 UTF-8 即可）
- 確認 CSV 末尾無空白行

---

### 階段 3：修正並執行 dashboardmanager SQL

```sql
-- ============================================================
-- EV Charging Station — DB Seed SQL (Fixed Version)
-- ============================================================

-- ── 1. components ────────────────────────────────────────────
INSERT INTO public.components (index, name)
VALUES
  ('ev_station_distribution', '電動車充電站分布'),
  ('ev_station_realtime',     '充電站即時使用狀況')
ON CONFLICT (index) DO UPDATE
SET name = EXCLUDED.name;

-- ── 2. component_charts ──────────────────────────────────────
INSERT INTO public.component_charts (index, color, types, unit)
VALUES
  (
    'ev_station_distribution',
    '{#4CAF93,#5BB8A0,#6DC1AC,#7ECAB8,#90D3C5,#A2DCD1,#B4E5DE,#C6EEEA,#D8F7F6,#EAF9F8,#C8E6C9,#A5D6A7}',
    '{MapLegend,EVStationChart}',
    '站'
  ),
  (
    'ev_station_realtime',
    '{#4CAF93,#E05C5C}',    -- 綠=空閒, 紅=使用中（兩個系列對應顏色）
    '{MapLegend,EVRealtimeChart}',
    '槍'
  )
ON CONFLICT (index) DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit  = EXCLUDED.unit;

-- ── 3. component_maps ────────────────────────────────────────
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES
  (
    'ev_station_distribution',
    '電動車充電站',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-radius": 6, "circle-color": "#4CAF93", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5, "circle-opacity": 0.85}',
    '[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"operator_name","name":"營運業者"},{"key":"total_charging_points","name":"充電槍數"},
  {"key":"available","name":"可用數"},{"key":"connector_types","name":"充電規格"},{"key":"charge_rate","name":"充電費率"},{"key":"parking_rate","name":"停車費率"},{"key":"service_time","name":"服務時間"},{"key":"address","name":"地址"}]'
  ),
  (
    'ev_station_realtime',
    '充電站即時狀態',
    'circle',
    'geojson',
    NULL,
    NULL,
    -- available 欄位存在，可使用條件著色：有空位=綠, 全滿=紅
    '{"circle-radius": 7, "circle-color": ["case",[">",["get","available"],0],"#4CAF93","#E05C5C"], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5}',
    '[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"available","name":"空閒槍數"},{"key":"occupied","name":"使用中槍數"},{"key":"unavailable","name":"故障槍數"},{"key":"availability_pct","name":"空閒率 (%)"},{"key":"charge_rate","name":"充電費率"},{"key":"service_time","name":"服務時間"}]'
  )
ON CONFLICT (index) DO UPDATE
SET title    = EXCLUDED.title,
    type     = EXCLUDED.type,
    source   = EXCLUDED.source,
    size     = EXCLUDED.size,
    icon     = EXCLUDED.icon,
    paint    = EXCLUDED.paint,
    property = EXCLUDED.property;

-- ── 4. query_charts ──────────────────────────────────────────

-- ev_station_distribution / taipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_distribution', 'taipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_distribution' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '臺北市各行政區電動車充電站數量分布',
  '呈現臺北市12個行政區的電動車充電站數量與充電槍總數。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。',
  '政府可透過本組件掌握充電基礎設施的空間分布，識別充電站不足的行政區，優先補充資源，推動低碳電動車普及。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  -- city 欄位值為中文「台北市」，非英文碼
  -- x_axis: district 中文值（如「大安區」），必須與 GeoJSON property 值完全一致
  'SELECT district AS x_axis, COUNT(*) AS data
   FROM public.ev_stations
   WHERE city = ''台北市''
   GROUP BY district
   ORDER BY data DESC',
  NULL
)
ON CONFLICT (index, city) DO UPDATE
SET map_config_ids = EXCLUDED.map_config_ids,
    map_filter     = EXCLUDED.map_filter,
    short_desc     = EXCLUDED.short_desc,
    long_desc      = EXCLUDED.long_desc,
    use_case       = EXCLUDED.use_case,
    query_type     = EXCLUDED.query_type,
    query_chart    = EXCLUDED.query_chart,
    updated_at     = NOW();

-- ev_station_distribution / metrotaipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_distribution', 'metrotaipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_distribution' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '雙北市各行政區電動車充電站數量分布',
  '呈現臺北市與新北市電動車充電站分布，共 660 站。',
  '比較雙北充電基礎設施密度，協助政策規劃。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  -- metrotaipei 不過濾 city，回傳台北市＋新北市全部行政區
  'SELECT district AS x_axis, COUNT(*) AS data
   FROM public.ev_stations
   GROUP BY district
   ORDER BY data DESC',
  NULL
)
ON CONFLICT (index, city) DO UPDATE
SET map_config_ids = EXCLUDED.map_config_ids,
    map_filter     = EXCLUDED.map_filter,
    short_desc     = EXCLUDED.short_desc,
    long_desc      = EXCLUDED.long_desc,
    use_case       = EXCLUDED.use_case,
    query_type     = EXCLUDED.query_type,
    query_chart    = EXCLUDED.query_chart,
    updated_at     = NOW();

-- ev_station_realtime / taipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_realtime', 'taipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_realtime' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 5, 'minute',
  '交通部 TDX 運輸資料流通服務',
  '臺北市充電站即時使用率',
  '以行政區彙整充電槍空閒與使用中數量。地圖綠色=有空位，紅色=全滿。',
  '市民即時查詢鄰近充電站使用情形，減少尋站時間，提升電動車便利性。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'three_d',
  -- x_axis: district，y_axis: 系列名稱，data: 整數
  -- subquery + GROUP BY 模式確保 GetThreeDimensionalData 的 categories 陣列對齊
  -- y_axis 順序對應 component_charts.color 陣列：#4CAF93=空閒槍數, #E05C5C=使用中槍數
  'SELECT x_axis, y_axis, SUM(data) AS data
   FROM (
     SELECT district AS x_axis, ''空閒槍數'' AS y_axis, available AS data
     FROM public.ev_stations
     WHERE city = ''台北市''
     UNION ALL
     SELECT district AS x_axis, ''使用中槍數'' AS y_axis, occupied AS data
     FROM public.ev_stations
     WHERE city = ''台北市''
   ) d
   GROUP BY x_axis, y_axis
   ORDER BY x_axis',
  NULL
)
ON CONFLICT (index, city) DO UPDATE
SET map_config_ids = EXCLUDED.map_config_ids,
    map_filter     = EXCLUDED.map_filter,
    short_desc     = EXCLUDED.short_desc,
    long_desc      = EXCLUDED.long_desc,
    use_case       = EXCLUDED.use_case,
    query_type     = EXCLUDED.query_type,
    query_chart    = EXCLUDED.query_chart,
    updated_at     = NOW();

-- ev_station_realtime / metrotaipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_realtime', 'metrotaipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_realtime' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 5, 'minute',
  '交通部 TDX 運輸資料流通服務',
  '雙北充電站即時使用率',
  '雙北 660 站充電槍空閒與使用中彙整。',
  '政府掌握雙北充電需求熱點，規劃充電基礎設施擴建優先區域。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'three_d',
  -- metrotaipei 不過濾 city，回傳台北市＋新北市全部行政區
  'SELECT x_axis, y_axis, SUM(data) AS data
   FROM (
     SELECT district AS x_axis, ''空閒槍數'' AS y_axis, available AS data
     FROM public.ev_stations
     UNION ALL
     SELECT district AS x_axis, ''使用中槍數'' AS y_axis, occupied AS data
     FROM public.ev_stations
   ) d
   GROUP BY x_axis, y_axis
   ORDER BY x_axis',
  NULL
)
ON CONFLICT (index, city) DO UPDATE
SET map_config_ids = EXCLUDED.map_config_ids,
    map_filter     = EXCLUDED.map_filter,
    short_desc     = EXCLUDED.short_desc,
    long_desc      = EXCLUDED.long_desc,
    use_case       = EXCLUDED.use_case,
    query_type     = EXCLUDED.query_type,
    query_chart    = EXCLUDED.query_chart,
    updated_at     = NOW();
```

---

## 三、執行順序總覽

```
[階段 2-A] ev_stations_with_district.geojson 複製兩份，放入 public/mapData/
             → ev_station_distribution.geojson
             → ev_station_realtime.geojson
    ↓
[階段 2-B] 在 dashboard DB 建立 public.ev_stations 表（26 個欄位，對應 CSV 標頭）
    ↓
[階段 2-B] pgAdmin Import CSV（UTF-8，Header=Yes）→ ev_stations（704 筆資料）
    ↓
[階段 3]  在 dashboardmanager DB 執行修正後的 SQL
    ↓
[驗證]    pgAdmin 確認 4 筆 query_charts 寫入正確，map_config_ids 非空陣列
    ↓
[驗證]    重啟 BE 後呼叫 API，確認圖表資料格式正確
    ↓
[驗證]    開啟前端地圖，確認圓點出現（realtime 應有綠/紅兩色）
```

---

## 四、驗證查詢

在 **dashboard** 執行：

```sql
-- 確認資料筆數與城市分布
SELECT city, COUNT(*) AS station_count, SUM(total_charging_points) AS total_guns
FROM public.ev_stations
GROUP BY city;
-- 預期：台北市 399, 新北市 261

-- 確認 district 與 available/occupied 欄位正確
SELECT district, SUM(available) AS avail, SUM(occupied) AS occ, COUNT(*) AS stations
FROM public.ev_stations
WHERE city = '台北市'
GROUP BY district
ORDER BY stations DESC;
```

在 **dashboardmanager** 執行：

```sql
SELECT index, city, query_type, array_length(map_config_ids, 1) AS map_count
FROM public.query_charts
WHERE index IN ('ev_station_distribution', 'ev_station_realtime')
ORDER BY index, city;
-- 預期：
-- ev_station_distribution | metrotaipei | two_d   | 1
-- ev_station_distribution | taipei      | two_d   | 1
-- ev_station_realtime     | metrotaipei | three_d | 1
-- ev_station_realtime     | taipei      | three_d | 1
```

---

## 五、已知限制與注意事項

1. **`city` 值為中文**：DB 中 `city` 欄位存的是 `台北市`/`新北市`，與 `query_charts.city` 的 `taipei`/`metrotaipei` 是不同層次的概念（前者是原始資料欄位，後者是儀表板城市碼）。SQL 的 WHERE 條件務必使用中文值。

2. **兩個組件共用同一 GeoJSON**：台北和雙北版本共用同一筆 `component_maps`（LIMIT 1），地圖永遠顯示全部 660 站。若需分城市顯示，需為 metrotaipei 另建 `component_maps` 記錄。

3. **realtime 為靜態資料**：`available`/`occupied` 目前是快照值，非真正即時。若要每 5 分鐘更新，需建立 TDX API 串接排程，定期更新 `ev_stations` 表並重新產生 `ev_station_realtime.geojson`。

4. **Mapbox 渲染與 Vue 圖表組件獨立**：地圖顯示由 `component_maps` 的 paint/property 控制。`EVStationChart`/`EVRealtimeChart` 僅影響圖表面板，不影響地圖渲染。

5. **`address` 欄位 241 筆為空**：Popup 顯示地址時部分站點會是空白，屬原始資料問題。
