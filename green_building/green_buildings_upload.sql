-- ============================================================
-- 綠建築認可組件上傳 SQL Script
-- 組件名稱: green_buildings (綠建築認可建築分布)
-- 圖表類型: DistrictChart (行政區圖) + HorizontalBarChart (橫向長條圖) + MapLegend 圖例
-- 資料: valid==1 的建築數量 (two_d)
--       valid==1 且 rank==1~5 的等級分布 (two_d)
-- ============================================================

-- ************************************************************
-- 階段 1：dashboard DB — 建立 green_buildings 資料表
-- ************************************************************
-- 請在 dashboard 資料庫中執行以下 SQL

CREATE TABLE IF NOT EXISTS public.green_buildings (
    id                   SERIAL        PRIMARY KEY,
    building_no          INTEGER,
    building_name        VARCHAR(300),
    building_desc        TEXT,
    cert_version         VARCHAR(100),
    cert_level           VARCHAR(50),
    rank                 INTEGER,
    valid_until          VARCHAR(50),
    valid                VARCHAR(5),
    cert_type            VARCHAR(50),
    designer             VARCHAR(200),
    city                 VARCHAR(50),
    district             VARCHAR(50),
    lot_number           TEXT,
    building_use         VARCHAR(100),
    lon                  NUMERIC,
    lat                  NUMERIC
);

-- 建表後，請使用 pgAdmin 的 Import/Export 功能匯入 CSV：
--   右鍵 green_buildings → Import/Export Data
--   Format: CSV
--   Header: Yes
--   Encoding: UTF-8
--   欄位對應（CSV 原始欄位 → DB 欄位）：
--     # → building_no
--     建築物名稱 → building_name
--     建築物概要 → building_desc
--     認可版本 → cert_version
--     認可等級 → cert_level
--     rank → rank
--     有效期間 → valid_until
--     valid → valid
--     認可類別 → cert_type
--     設計人 → designer
--     行政區 → city         (如「臺北市」/「新北市」)
--     ditrict → district    (如「大安區」)
--     地號 → lot_number
--     建築物使用類別 → building_use
--     longtitude → lon
--     latitude → lat
--   共 1394 筆（valid==1 共 680 筆）

-- 匯入後驗證：
-- SELECT city, COUNT(*) FILTER (WHERE valid='1') AS valid_count
-- FROM public.green_buildings
-- GROUP BY city;
-- 預期：臺北市 356, 新北市 324（共 680）


-- ************************************************************
-- 階段 2：GeoJSON 檔案放置
-- ************************************************************
-- 請手動執行以下指令：
--
-- cp green_geocoded.geojson \
--    Taipei-City-Dashboard-FE/public/mapData/green_buildings.geojson
--
-- 注意：geojson 檔名必須與 component_maps.index 一致


-- ************************************************************
-- 階段 3：dashboardmanager DB — 新增組件設定
-- ************************************************************
-- 請在 dashboardmanager 資料庫中執行以下 SQL

-- ── 3-1. components ─────────────────────────────────────────
INSERT INTO public.components (index, name)
VALUES ('green_buildings', '綠建築認可建築分布')
ON CONFLICT (index) DO UPDATE
SET name = EXCLUDED.name;

-- ── 3-2. component_charts ───────────────────────────────────
-- DistrictChart 行政區圖 + HorizontalBarChart 橫向長條圖 + MapLegend 圖例
-- 顏色：鑽石(rank5)→黃金(4)→銀(3)→銅(2)→合格(1) 從深綠到淺綠
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'green_buildings',
    '{#1B5E20,#2E7D32,#388E3C,#43A047,#4CAF50,#66BB6A,#81C784,#A5D6A7,#C8E6C9,#E8F5E9}',
    '{DistrictChart,HorizontalBarChart,MapLegend}',
    '棟'
)
ON CONFLICT (index) DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit  = EXCLUDED.unit;

-- ── 3-3. component_maps（共 2 個圖層）────────────────────────
-- Layer 1：綠色圓點（所有 valid=="1"）
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
    'green_buildings',
    '綠建築認可建築',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-color": "#4CAF50", "circle-radius": 5, "circle-opacity": 0.8, "circle-stroke-color": "#ffffff", "circle-stroke-width": 1, "filter": ["==", ["get", "valid"], "1"]}',
    '[{"key":"建築物名稱","name":"建築物名稱"},{"key":"認可等級","name":"認可等級"},{"key":"rank","name":"等級分數"},{"key":"建築物概要","name":"建築物概要"},{"key":"認可版本","name":"認可版本"},{"key":"認可類別","name":"認可類別"},{"key":"有效期間","name":"有效期間"},{"key":"建築物使用類別","name":"建築物使用類別"},{"key":"設計人","name":"設計人"},{"key":"ditrict","name":"行政區"}]'
)
ON CONFLICT (index) DO UPDATE
SET title    = EXCLUDED.title,
    type     = EXCLUDED.type,
    source   = EXCLUDED.source,
    size     = EXCLUDED.size,
    icon     = EXCLUDED.icon,
    paint    = EXCLUDED.paint,
    property = EXCLUDED.property;

-- Layer 2：鑽石級標記（valid=="1" AND rank==5）使用 symbol + leaf-icon
-- 注意：使用前端需在 mapStore 初始化 map.on('load', ...) 中注入 SVG icon：
--
-- const svg = `<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#78A75A">
--   <path d="M216-176q-45-45-70.5-104T120-402q0-63 24-124.5T222-642q35-35 86.5-60t122-39.5Q501-756 591.5-759t202.5 7q8 106 5 195t-16.5 160.5q-13.5 71.5-38 125T684-182q-53 53-112.5 77.5T450-80q-65 0-127-25.5T216-176Zm112-16q29 17 59.5 24.5T450-160q46 0 91-18.5t86-59.5q18-18 36.5-50.5t32-85Q709-426 716-500.5t2-177.5q-49-2-110.5-1.5T485-670q-61 9-116 29t-90 55q-45 45-62 89t-17 85q0 59 22.5 103.5T262-246q42-80 111-153.5T534-520q-72 63-125.5 142.5T328-192Zm0 0Zm0 0Z"/>
-- </svg>`;
-- const blob = new Blob([svg], { type: 'image/svg+xml' });
-- const url = URL.createObjectURL(blob);
-- const img = new Image(24, 24);
-- img.onload = () => { map.addImage('leaf-icon', img); URL.revokeObjectURL(url); };
-- img.src = url;
--
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
    'green_buildings',
    '鑽石級綠建築',
    'symbol',
    'geojson',
    NULL,
    'leaf-icon',
    '{"filter": ["all", ["==", ["get", "valid"], "1"], ["==", ["get", "rank"], 5]], "layout": {"icon-image": "leaf-icon", "icon-size": 1.2, "icon-allow-overlap": true}}',
    '[{"key":"建築物名稱","name":"建築物名稱"},{"key":"認可等級","name":"認可等級"},{"key":"rank","name":"等級分數"},{"key":"建築物概要","name":"建築物概要"},{"key":"有效期間","name":"有效期間"},{"key":"ditrict","name":"行政區"}]'
)
ON CONFLICT DO NOTHING;


-- ── 3-4. query_charts (taipei) ──────────────────────────────
-- DistrictChart：統計臺北市各行政區 valid==1 的建築棟數 (two_d)
-- HorizontalBarChart：統計全體 valid==1 且 rank 1~5 的棟數，依 rank 分組 (two_d)
--   x_axis 標籤：rank 1=合格級, 2=銅級, 3=銀級, 4=黃金級, 5=鑽石級
--   長條圖最左邊為最低 rank（rank1 合格級在最上方/左方）
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'green_buildings', 'taipei',
  NULL,
  (ARRAY[
    (SELECT id FROM public.component_maps WHERE index = 'green_buildings' AND type = 'circle' LIMIT 1),
    (SELECT id FROM public.component_maps WHERE index = 'green_buildings' AND type = 'symbol' LIMIT 1)
  ]),
  '{"mode":"byParam","byParam":{"xParam":"ditrict"}}',
  'static', NULL, 1, 'day',
  '內政部建築研究所 綠建築標章',
  '臺北市各行政區綠建築認可建築分布',
  '呈現臺北市12個行政區獲得有效綠建築認可（valid=1）的建築棟數，並依鑽石、黃金、銀、銅、合格五個等級統計分布。資料來源為內政部建築研究所。',
  '政府可透過本組件掌握綠建築認可建築的空間與等級分布，識別尚待強化的行政區，優先推廣綠建築政策。',
  '{https://www.abri.gov.tw/}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  -- DistrictChart 查詢：臺北市 12 區 valid==1 棟數
  'SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data
   FROM (VALUES
     (''北投區''),(''士林區''),(''內湖區''),(''南港區''),(''松山區''),(''信義區''),
     (''中山區''),(''大同區''),(''中正區''),(''萬華區''),(''大安區''),(''文山區'')
   ) AS d(district)
   LEFT JOIN public.green_buildings g
     ON g.district = d.district
     AND g.valid = ''1''
     AND g.city = ''臺北市''
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
-- 雙北 41 個行政區 valid==1 棟數 (DistrictChart) + rank 等級分布 (HorizontalBarChart)
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'green_buildings', 'metrotaipei',
  NULL,
  (ARRAY[
    (SELECT id FROM public.component_maps WHERE index = 'green_buildings' AND type = 'circle' LIMIT 1),
    (SELECT id FROM public.component_maps WHERE index = 'green_buildings' AND type = 'symbol' LIMIT 1)
  ]),
  '{"mode":"byParam","byParam":{"xParam":"ditrict"}}',
  'static', NULL, 1, 'day',
  '內政部建築研究所 綠建築標章',
  '雙北各行政區綠建築認可建築分布',
  '呈現雙北41個行政區獲得有效綠建築認可（valid=1）的建築棟數（共680棟），並依鑽石、黃金、銀、銅、合格五個等級統計分布。資料來源為內政部建築研究所。',
  '比較雙北綠建築密度，協助政策規劃與推廣優先區域選定，促進低碳永續都市發展。',
  '{https://www.abri.gov.tw/}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  -- DistrictChart 查詢：雙北 41 區 valid==1 棟數
  'SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data
   FROM (VALUES
     (''北投區''),(''士林區''),(''內湖區''),(''南港區''),(''松山區''),(''信義區''),
     (''中山區''),(''大同區''),(''中正區''),(''萬華區''),(''大安區''),(''文山區''),
     (''新莊區''),(''淡水區''),(''汐止區''),(''板橋區''),(''三重區''),(''樹林區''),
     (''土城區''),(''蘆洲區''),(''中和區''),(''永和區''),(''新店區''),(''鶯歌區''),
     (''三峽區''),(''瑞芳區''),(''五股區''),(''泰山區''),(''林口區''),(''深坑區''),
     (''石碇區''),(''坪林區''),(''三芝區''),(''石門區''),(''八里區''),(''平溪區''),
     (''雙溪區''),(''貢寮區''),(''金山區''),(''萬里區''),(''烏來區'')
   ) AS d(district)
   LEFT JOIN public.green_buildings g
     ON g.district = d.district
     AND g.valid = ''1''
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


-- ── 3-6. query_charts — HorizontalBarChart (rank 等級分布) ──
-- 獨立查詢：雙北 valid==1 且 rank 1~5 的棟數，以等級名稱為 x_axis
-- rank 由低到高排列（rank1 合格級在最左/最上方）
-- 供 HorizontalBarChart 使用的獨立 query_charts 條目（city='metrotaipei_rank'）
-- 若框架支援同一組件多個 query，可改用 query_history 或另設 index
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'green_buildings', 'rank_dist',
  NULL,
  (ARRAY[
    (SELECT id FROM public.component_maps WHERE index = 'green_buildings' AND type = 'circle' LIMIT 1)
  ]),
  NULL,
  'static', NULL, 1, 'day',
  '內政部建築研究所 綠建築標章',
  '雙北綠建築認可等級分布（合格→鑽石）',
  '統計雙北地區 valid==1 且 rank 1~5 的綠建築棟數，依合格、銅、銀、黃金、鑽石五個等級呈現水平長條圖，rank 1（合格級）在最左方，rank 5（鑽石級）在最右方。',
  '掌握雙北綠建築認可等級結構，了解高等級建築（黃金、鑽石）分布情況，推動更多建築達到高標準認可。',
  '{https://www.abri.gov.tw/}',
  '{hackathon_team}',
  NOW(), NOW(),
  'two_d',
  -- HorizontalBarChart 查詢：rank 1~5 依序排列
  -- x_axis = 等級名稱（合格→銅→銀→黃金→鑽石），data = 棟數
  'SELECT r.rank_name AS x_axis, COALESCE(COUNT(g.id), 0) AS data
   FROM (VALUES
     (1, ''合格級''),
     (2, ''銅級''),
     (3, ''銀級''),
     (4, ''黃金級''),
     (5, ''鑽石級'')
   ) AS r(rank_val, rank_name)
   LEFT JOIN public.green_buildings g
     ON g.rank = r.rank_val
     AND g.valid = ''1''
   GROUP BY r.rank_val, r.rank_name
   ORDER BY r.rank_val ASC',
  NULL
)
ON CONFLICT (index, city) DO UPDATE
SET short_desc  = EXCLUDED.short_desc,
    long_desc   = EXCLUDED.long_desc,
    query_type  = EXCLUDED.query_type,
    query_chart = EXCLUDED.query_chart,
    updated_at  = NOW();


-- ************************************************************
-- 階段 4：驗證查詢
-- ************************************************************

-- [dashboard DB] 確認資料筆數
-- SELECT city, COUNT(*) AS total, COUNT(*) FILTER (WHERE valid='1') AS valid_count
-- FROM public.green_buildings
-- GROUP BY city;
-- 預期：臺北市 total~, valid=356; 新北市 total~, valid=324

-- [dashboard DB] 確認 rank 分布
-- SELECT rank, COUNT(*) FROM public.green_buildings WHERE valid='1' GROUP BY rank ORDER BY rank;
-- 預期：1→130, 2→61, 3→312, 4→127, 5→47

-- [dashboardmanager DB] 確認 component_maps 建立（應有 2 筆：circle + symbol）
-- SELECT id, index, title, type FROM public.component_maps WHERE index = 'green_buildings';

-- [dashboardmanager DB] 確認 query_charts 寫入
-- SELECT index, city, query_type, array_length(map_config_ids, 1) AS map_count
-- FROM public.query_charts
-- WHERE index = 'green_buildings'
-- ORDER BY city;
-- 預期：
-- green_buildings | metrotaipei | two_d | 2
-- green_buildings | taipei      | two_d | 2
-- green_buildings | rank_dist   | two_d | 1


-- ************************************************************
-- 附錄：前端 mapStore 注入 leaf-icon 參考程式碼
-- ************************************************************
-- 在 mapStore 初始化的 map.on('load', () => { ... }) 內加入：
--
-- const svg = `<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#78A75A">
--   <path d="M216-176q-45-45-70.5-104T120-402q0-63 24-124.5T222-642q35-35 86.5-60t122-39.5Q501-756 591.5-759t202.5 7q8 106 5 195t-16.5 160.5q-13.5 71.5-38 125T684-182q-53 53-112.5 77.5T450-80q-65 0-127-25.5T216-176Zm112-16q29 17 59.5 24.5T450-160q46 0 91-18.5t86-59.5q18-18 36.5-50.5t32-85Q709-426 716-500.5t2-177.5q-49-2-110.5-1.5T485-670q-61 9-116 29t-90 55q-45 45-62 89t-17 85q0 59 22.5 103.5T262-246q42-80 111-153.5T534-520q-72 63-125.5 142.5T328-192Zm0 0Zm0 0Z"/>
-- </svg>`;
-- const blob = new Blob([svg], { type: 'image/svg+xml' });
-- const url = URL.createObjectURL(blob);
-- const img = new Image(24, 24);
-- img.onload = () => {
--   map.addImage('leaf-icon', img);
--   URL.revokeObjectURL(url);
-- };
-- img.src = url;
