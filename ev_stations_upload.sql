-- ============================================================
-- EV 充電站組件上傳 SQL Script
-- 組件名稱: ev_stations (電動車充電站分布)
-- 圖表類型: DistrictChart (行政區圖) + PolarAreaChart (極座標圖)
-- 資料: total_charging_points 加總 (two_d)
-- ============================================================

-- ************************************************************
-- 階段 1：dashboard DB — 建立 ev_stations 資料表
-- ************************************************************
-- 請在 dashboard 資料庫中執行以下 SQL

CREATE TABLE IF NOT EXISTS public.ev_stations (
    station_id            VARCHAR(50)   PRIMARY KEY,
    city                  VARCHAR(50),
    district              VARCHAR(50),
    station_name          VARCHAR(200),
    operator_name         VARCHAR(200),
    operator_tel          VARCHAR(50),
    operator_url          VARCHAR(300),
    lat                   NUMERIC,
    lon                   NUMERIC,
    address               VARCHAR(200),
    description           TEXT,
    spaces                INTEGER,
    total_charging_points INTEGER,
    available             INTEGER,
    occupied              INTEGER,
    unavailable           INTEGER,
    availability_pct      INTEGER,
    charged_kwh_total     NUMERIC,
    connector_types       TEXT,
    charge_rate           TEXT,
    parking_rate          TEXT,
    payment               VARCHAR(200),
    start_type            VARCHAR(200),
    service_time          TEXT,
    floors                VARCHAR(50),
    phone                 VARCHAR(50)
);

-- 建表後，請使用 pgAdmin 的 Import/Export 功能匯入 CSV：
--   右鍵 ev_stations → Import/Export Data
--   Format: CSV
--   Header: Yes
--   Encoding: UTF-8
--   檔案: ev_stations_with_district.csv (共 704 筆，台北市 399 + 新北市 261 + 無區域 44)

-- 匯入後驗證：
-- SELECT city, COUNT(*) AS station_count, SUM(total_charging_points) AS total_guns
-- FROM public.ev_stations
-- GROUP BY city;


-- ************************************************************
-- 階段 2：GeoJSON 檔案放置
-- ************************************************************
-- 請手動執行以下指令（或在檔案管理器中操作）：
--
-- cp ev_stations_with_district.geojson \
--    Taipei-City-Dashboard-FE/public/mapData/ev_stations.geojson


-- ************************************************************
-- 階段 3：dashboardmanager DB — 新增組件設定
-- ************************************************************
-- 請在 dashboardmanager 資料庫中執行以下 SQL

-- ── 3-1. components ─────────────────────────────────────────
INSERT INTO public.components (index, name)
VALUES ('ev_stations', '電動車充電站分布')
ON CONFLICT (index) DO UPDATE
SET name = EXCLUDED.name;

-- ── 3-2. component_charts ───────────────────────────────────
-- DistrictChart 行政區圖 + PolarAreaChart 極座標圖 + MapLegend 圖例
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'ev_stations',
    '{#4CAF93,#5BB8A0,#6DC1AC,#7ECAB8,#90D3C5,#A2DCD1,#B4E5DE,#C6EEEA,#D8F7F6,#EAF9F8,#C8E6C9,#A5D6A7}',
    '{DistrictChart,PolarAreaChart,MapLegend}',
    '支'
)
ON CONFLICT (index) DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit  = EXCLUDED.unit;

-- ── 3-3. component_maps ────────────────────────────────────
-- 地圖上以 circle 顯示每個充電站的點位
-- 顏色邏輯：available / total_charging_points
--   ≥ 50% → 綠色 #4CAF93
--   30~50% → 橘色 #FF9800
--   < 30% → 紅色 #E05C5C
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
    'ev_stations',
    '電動車充電站',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-radius": 6, "circle-color": ["case", [">=", ["/", ["get", "available"], ["max", ["get", "total_charging_points"], 1]], 0.5], "#4CAF93", [">=", ["/", ["get", "available"], ["max", ["get", "total_charging_points"], 1]], 0.3], "#FF9800", "#E05C5C"], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5, "circle-opacity": 0.85}',
    '[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"operator_name","name":"營運業者"},{"key":"total_charging_points","name":"充電槍數"},{"key":"available","name":"空閒槍數"},{"key":"connector_types","name":"充電規格"},{"key":"charge_rate","name":"充電費率"},{"key":"parking_rate","name":"停車費率"},{"key":"service_time","name":"服務時間"},{"key":"address","name":"地址"}]'
)
ON CONFLICT (index) DO UPDATE
SET title    = EXCLUDED.title,
    type     = EXCLUDED.type,
    source   = EXCLUDED.source,
    size     = EXCLUDED.size,
    icon     = EXCLUDED.icon,
    paint    = EXCLUDED.paint,
    property = EXCLUDED.property;

-- ── 3-4. query_charts (taipei) ──────────────────────────────
-- 台北模式：只查台北市 12 個行政區，WHERE city = '台北市'
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_stations', 'taipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_stations' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '臺北市各行政區電動車充電站充電槍數分布',
  '呈現臺北市12個行政區的電動車充電站充電槍總數（total_charging_points）。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。',
  '政府可透過本組件掌握充電基礎設施的空間分布，識別充電槍不足的行政區，優先補充資源，推動低碳電動車普及。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  'SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data
   FROM (VALUES
     (''北投區''),(''士林區''),(''內湖區''),(''南港區''),(''松山區''),(''信義區''),
     (''中山區''),(''大同區''),(''中正區''),(''萬華區''),(''大安區''),(''文山區'')
   ) AS d(district)
   LEFT JOIN public.ev_stations e ON e.district = d.district AND e.city = ''台北市''
   GROUP BY d.district
   ORDER BY ARRAY_POSITION(
     ARRAY[''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',
           ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區''],
     d.district
   )',
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

-- ── 3-5. query_charts (metrotaipei) ─────────────────────────
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_stations', 'metrotaipei',
  NULL,
  (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_stations' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '雙北各行政區電動車充電站充電槍數分布',
  '呈現雙北41個行政區的電動車充電站充電槍總數（total_charging_points），共660站。資料來源為交通部TDX平台。',
  '比較雙北充電基礎設施密度，協助政策規劃與充電站擴建優先區域選定。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  'SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data
   FROM (VALUES
     (''北投區''),(''士林區''),(''內湖區''),(''南港區''),(''松山區''),(''信義區''),
     (''中山區''),(''大同區''),(''中正區''),(''萬華區''),(''大安區''),(''文山區''),
     (''新莊區''),(''淡水區''),(''汐止區''),(''板橋區''),(''三重區''),(''樹林區''),
     (''土城區''),(''蘆洲區''),(''中和區''),(''永和區''),(''新店區''),(''鶯歌區''),
     (''三峽區''),(''瑞芳區''),(''五股區''),(''泰山區''),(''林口區''),(''深坑區''),
     (''石碇區''),(''坪林區''),(''三芝區''),(''石門區''),(''八里區''),(''平溪區''),
     (''雙溪區''),(''貢寮區''),(''金山區''),(''萬里區''),(''烏來區'')
   ) AS d(district)
   LEFT JOIN public.ev_stations e ON e.district = d.district
   GROUP BY d.district
   ORDER BY ARRAY_POSITION(
     ARRAY[''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',
           ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區'',
           ''新莊區'',''淡水區'',''汐止區'',''板橋區'',''三重區'',''樹林區'',
           ''土城區'',''蘆洲區'',''中和區'',''永和區'',''新店區'',''鶯歌區'',
           ''三峽區'',''瑞芳區'',''五股區'',''泰山區'',''林口區'',''深坑區'',
           ''石碇區'',''坪林區'',''三芝區'',''石門區'',''八里區'',''平溪區'',
           ''雙溪區'',''貢寮區'',''金山區'',''萬里區'',''烏來區''],
     d.district
   )',
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


-- ************************************************************
-- 階段 4：驗證查詢
-- ************************************************************

-- [dashboard DB] 確認資料筆數
-- SELECT city, COUNT(*) AS station_count, SUM(total_charging_points) AS total_guns
-- FROM public.ev_stations
-- GROUP BY city;
-- 預期：台北市 399, 新北市 261

-- [dashboardmanager DB] 確認 query_charts 寫入
-- SELECT index, city, query_type, array_length(map_config_ids, 1) AS map_count
-- FROM public.query_charts
-- WHERE index = 'ev_stations'
-- ORDER BY city;
-- 預期：
-- ev_stations | metrotaipei | two_d | 1
-- ev_stations | taipei      | two_d | 1

-- [dashboardmanager DB] 確認 component_maps 寫入
-- SELECT id, index, title, type, source FROM public.component_maps WHERE index = 'ev_stations';
