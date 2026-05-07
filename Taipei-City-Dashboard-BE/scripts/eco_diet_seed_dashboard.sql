-- ──────────────────────────────────────────────────────────────────────
-- EcoDiet (綠色飲食行為流程儀表板) 整合進主庫 dashboard 系統的 seed
--
-- 將 fork 端原本獨立的 EcoDietView.vue（1906 行）拆解，把 7 個 component
-- 註冊進主庫的 query_charts / component_charts / component_maps / dashboards 表，
-- URL 走 /dashboard?index=eco_diet_metrotaipei&city=metrotaipei，與「長照關懷」
-- 等其他 dashboard 一致。
--
-- Schema (4 張 EcoDiet 資料表) 走 eco_diet_schema.sql + eco_diet_seed.sql；
-- 本檔負責 dashboardmanager 端的 component / dashboard 註冊。
--
-- 套用方式（dashboardmanager DB）：
--   docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
--     < eco_diet_seed_dashboard.sql
--
-- 套用 GeoJSON 點位：
--   FE 端 public/mapData/ 下已含 9 份對應 GeoJSON
--   (eco_restaurant_{tpe,new_tpe,metrotaipei}.geojson 等)，FE deploy 時自動帶上。
--
-- 注意：
--   1. 採用固定 component id 區段 600-606，避免與既有資料衝突；若有衝突請手動調整。
--   2. component_maps id 區段 200-208。
--   3. dashboards id 區段 700-702。
-- ──────────────────────────────────────────────────────────────────────

BEGIN;

-- ─── 0. 清掉 EcoDiet 既有 row（idempotent re-run 必要） ────────────
DELETE FROM dashboard_groups WHERE dashboard_id IN (SELECT id FROM dashboards WHERE index LIKE 'eco_diet_%');
DELETE FROM dashboards WHERE index LIKE 'eco_diet_%';
DELETE FROM query_charts WHERE index LIKE 'eco_diet_%';
DELETE FROM components WHERE index LIKE 'eco_diet_%';
DELETE FROM component_charts WHERE index LIKE 'eco_diet_%';
DELETE FROM component_maps WHERE index IN (
  'eco_restaurant_metrotaipei','eco_restaurant_tpe','eco_restaurant_new_tpe',
  'green_store_metrotaipei','green_store_tpe','green_store_new_tpe',
  'food_bank_metrotaipei','food_bank_tpe','food_bank_new_tpe'
);

-- ─── 1. component_charts (6 筆) ──────────────────────────────────────
-- chart_config（顏色 / chart 類型 / 單位），同 index 不分 city 共用一筆。

INSERT INTO component_charts (index, color, types, unit) VALUES
  ('eco_diet_restaurants_points',     ARRAY['#5fcf80','#5a9cf8'],                                      ARRAY['DonutChart','BarChart'], '家'),
  ('eco_diet_restaurants_density',    ARRAY['#5fcf80','#5a9cf8'],                                      ARRAY['DistrictChart','BarChart'], '家'),
  ('eco_diet_green_stores_points',    ARRAY['#ec7cb1','#67baca'],                                      ARRAY['DonutChart','BarChart'], '家'),
  ('eco_diet_food_banks_points',      ARRAY['#f6c344','#a37cf6'],                                      ARRAY['DonutChart','BarChart'], '處'),
  ('eco_diet_waste_yearly',           ARRAY['#ed5a5a','#f6c344','#5fcf80','#5a9cf8','#a37cf6','#ec7cb1','#888787','#67baca'], ARRAY['TimelineSeparateChart','BubbleChart'], '公噸'),
  ('eco_diet_waste_carbon_footprint_yearly', ARRAY['#5fcf80','#5a9cf8'],                              ARRAY['TimelineSeparateChart','ColumnChart'], '公噸 CO₂e');

-- ─── 2. components (6 筆) ────────────────────────────────────────────
-- 主庫的 component table 只有 id/index/name 三欄。

INSERT INTO components (id, index, name) VALUES
  (600, 'eco_diet_restaurants_points',           '環保餐廳數量'),
  (601, 'eco_diet_restaurants_density',          '各行政區環保餐廳數量'),
  (603, 'eco_diet_green_stores_points',          '綠色商店數量'),
  (604, 'eco_diet_food_banks_points',            '實物銀行數量'),
  (605, 'eco_diet_waste_yearly',                 '雙北廢棄物產量趨勢(年)'),
  (606, 'eco_diet_waste_carbon_footprint_yearly','雙北廢棄物碳足跡趨勢(年)');

-- ─── 3. component_maps (9 筆) ────────────────────────────────────────
-- C1a / C4 / C7a 各 3 個 city（metrotaipei / tpe / new_tpe）對應 9 份 GeoJSON。
-- index 對應 FE public/mapData/<index>.geojson 檔名。

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property) VALUES
  -- 環保餐廳
  (200, 'eco_restaurant_metrotaipei', '環保餐廳點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":["match",["get","city"],"臺北市","#5fcf80","新北市","#5a9cf8","#888888"],"circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"city","name":"城市"},{"key":"tel","name":"電話"},{"key":"env_actions","name":"環保作為"}]'::json),
  (201, 'eco_restaurant_tpe',         '臺北環保餐廳點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#5fcf80","circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"},{"key":"env_actions","name":"環保作為"}]'::json),
  (202, 'eco_restaurant_new_tpe',     '新北環保餐廳點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#5a9cf8","circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"}]'::json),
  -- 綠色商店
  (203, 'green_store_metrotaipei',    '綠色商店點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":["match",["get","city"],"臺北市","#ec7cb1","新北市","#67baca","#888888"],"circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"city","name":"城市"},{"key":"tel","name":"電話"},{"key":"store_type","name":"店家類型"}]'::json),
  (204, 'green_store_tpe',            '臺北綠色商店點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#ec7cb1","circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"},{"key":"store_type","name":"店家類型"}]'::json),
  (205, 'green_store_new_tpe',        '新北綠色商店點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#67baca","circle-radius":4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"店名"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"},{"key":"store_type","name":"店家類型"}]'::json),
  -- 實物銀行
  (206, 'food_bank_metrotaipei',      '實物銀行點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":["match",["get","city"],"臺北市","#f6c344","新北市","#a37cf6","#888888"],"circle-radius":5,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"機構名稱"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"city","name":"城市"},{"key":"tel","name":"電話"},{"key":"org_type","name":"機構類型"}]'::json),
  (207, 'food_bank_tpe',              '臺北實物銀行點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#f6c344","circle-radius":5,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"機構名稱"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"},{"key":"org_type","name":"機構類型"}]'::json),
  (208, 'food_bank_new_tpe',          '新北實物銀行點位', 'circle', 'geojson', NULL, NULL,
    '{"circle-color":"#a37cf6","circle-radius":5,"circle-stroke-color":"#ffffff","circle-stroke-width":1}'::json,
    '[{"key":"name","name":"機構名稱"},{"key":"address","name":"地址"},{"key":"district","name":"行政區"},{"key":"tel","name":"電話"},{"key":"org_type","name":"機構類型"}]'::json);

-- ─── 4. query_charts (19 筆) ────────────────────────────────────────
-- 注意：query_chart SQL 直接打 dashboard DB（postgres-data，含 EcoDiet 4 張表）。
-- (index, city) 對應一筆 row；FE /component/<id>/chart?city=xxx 會撈對應 row 的 SQL 跑。

-- ─── C1a 環保餐廳數量（map_legend，3 city） ─────────────────────────
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_restaurants_points', NULL, ARRAY[200]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '雙北環保局', '雙北環保餐廳全量點位（依城市配色）',
    '整合臺北市與新北市環保餐廳名錄，所有列管餐廳依經緯度落圖，臺北市以綠色、新北市以藍色標示，協助使用者直觀掌握雙北環保飲食店家的空間分布。',
    '市民查詢居家附近的環保餐廳、店家規劃新分店時參考既有環保認證店家分布、政府評估環保餐廳推廣的地理覆蓋率。',
    ARRAY['https://data.taipei/dataset/detail?id=51d6b46c-37b2-4c9b-b5bf-ab21f8b3f58e','https://data.ntpc.gov.tw/datasets/E90D14F8-5995-4EBB-AF19-8F8FD7D396C8'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT city AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE lng IS NOT NULL AND lat IS NOT NULL GROUP BY city ORDER BY city',
    NULL, 'metrotaipei'),
  ('eco_diet_restaurants_points', NULL, ARRAY[201]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '臺北市環保局', '臺北環保餐廳全量點位',
    '臺北市環保餐廳名錄，所有列管餐廳依經緯度落圖。',
    '市民查詢居家附近的環保餐廳、店家規劃新分店時參考既有環保認證店家分布。',
    ARRAY['https://data.taipei/dataset/detail?id=51d6b46c-37b2-4c9b-b5bf-ab21f8b3f58e'],
    ARRAY['doit'],
    NOW(), NOW(), 'two_d',
    'SELECT ''臺北市'' AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''臺北市''',
    NULL, 'taipei'),
  ('eco_diet_restaurants_points', NULL, ARRAY[202]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '新北市環保局', '新北環保餐廳全量點位',
    '新北市環保餐廳名錄，所有列管餐廳依經緯度落圖。',
    '市民查詢居家附近的環保餐廳、店家規劃新分店時參考既有環保認證店家分布。',
    ARRAY['https://data.ntpc.gov.tw/datasets/E90D14F8-5995-4EBB-AF19-8F8FD7D396C8'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT ''新北市'' AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''新北市''',
    NULL, 'newtaipei');

-- ─── C1b 各行政區環保餐廳密度（two_d，3 city） ──────────────────────
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_restaurants_density', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '雙北環保局', '雙北各行政區環保餐廳家數', '依行政區聚合雙北環保餐廳家數，呈現分布密度。', '市民查詢居住地附近環保餐廳供給度。',
    ARRAY['https://data.taipei/dataset/detail?id=51d6b46c-37b2-4c9b-b5bf-ab21f8b3f58e','https://data.ntpc.gov.tw/datasets/E90D14F8-5995-4EBB-AF19-8F8FD7D396C8'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT district AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE district IS NOT NULL GROUP BY district ORDER BY data DESC, district',
    NULL, 'metrotaipei'),
  ('eco_diet_restaurants_density', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '臺北市環保局', '臺北各行政區環保餐廳家數', '依行政區聚合臺北環保餐廳家數，呈現分布密度。', '市民查詢居住地附近環保餐廳供給度。',
    ARRAY['https://data.taipei/dataset/detail?id=51d6b46c-37b2-4c9b-b5bf-ab21f8b3f58e'],
    ARRAY['doit'],
    NOW(), NOW(), 'two_d',
    'SELECT district AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE district IS NOT NULL AND city=''臺北市'' GROUP BY district ORDER BY data DESC, district',
    NULL, 'taipei'),
  ('eco_diet_restaurants_density', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '新北市環保局', '新北各行政區環保餐廳家數', '依行政區聚合新北環保餐廳家數，呈現分布密度。', '市民查詢居住地附近環保餐廳供給度。',
    ARRAY['https://data.ntpc.gov.tw/datasets/E90D14F8-5995-4EBB-AF19-8F8FD7D396C8'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT district AS x_axis, COUNT(*)::float AS data FROM eco_restaurant WHERE district IS NOT NULL AND city=''新北市'' GROUP BY district ORDER BY data DESC, district',
    NULL, 'newtaipei');

-- ─── C2 雙北環保餐廳數量（two_d，僅 metrotaipei） ───────────────────
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_restaurants_count_by_city', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '雙北環保局', '雙北環保餐廳家數比較', '比較臺北市與新北市環保餐廳總數。', '看雙城環保飲食店家供給差異。',
    ARRAY['https://data.taipei/dataset/detail?id=51d6b46c-37b2-4c9b-b5bf-ab21f8b3f58e','https://data.ntpc.gov.tw/datasets/E90D14F8-5995-4EBB-AF19-8F8FD7D396C8'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT city AS x_axis, COUNT(*)::float AS data FROM eco_restaurant GROUP BY city ORDER BY x_axis',
    NULL, 'metrotaipei');

-- ─── C4 綠色商店數量（two_d，3 city） ───────────────────────────────
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_green_stores_points', NULL, ARRAY[203]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '雙北環保局', '雙北綠色商店全量點位', '整合雙北環保署認證的綠色商店資料並依城市配色（臺北粉／新北青）。', '綠色消費研究、消費者尋找最近綠色商店。',
    ARRAY['https://data.taipei/dataset/detail?id=2bcfa37e-9f59-4c2e-b53a-cc1d7a9e6a0c','https://data.ntpc.gov.tw/datasets/6CCD0274-0C09-43B0-98FC-4D5222A71E8B'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT city AS x_axis, COUNT(*)::float AS data FROM green_store WHERE lng IS NOT NULL AND lat IS NOT NULL GROUP BY city ORDER BY city',
    NULL, 'metrotaipei'),
  ('eco_diet_green_stores_points', NULL, ARRAY[204]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '臺北市環保局', '臺北綠色商店全量點位', '臺北綠色商店全量點位。', '綠色消費研究、消費者尋找最近綠色商店。',
    ARRAY['https://data.taipei/dataset/detail?id=2bcfa37e-9f59-4c2e-b53a-cc1d7a9e6a0c'],
    ARRAY['doit'],
    NOW(), NOW(), 'two_d',
    'SELECT ''臺北市'' AS x_axis, COUNT(*)::float AS data FROM green_store WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''臺北市''',
    NULL, 'taipei'),
  ('eco_diet_green_stores_points', NULL, ARRAY[205]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '新北市環保局', '新北綠色商店全量點位', '新北綠色商店全量點位。', '綠色消費研究、消費者尋找最近綠色商店。',
    ARRAY['https://data.ntpc.gov.tw/datasets/6CCD0274-0C09-43B0-98FC-4D5222A71E8B'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT ''新北市'' AS x_axis, COUNT(*)::float AS data FROM green_store WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''新北市''',
    NULL, 'newtaipei');

-- ─── C7a 實物銀行數量（two_d，3 city） ──────────────────────────────
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_food_banks_points', NULL, ARRAY[206]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '雙北社會局', '雙北實物銀行（社福資源）全量點位', '整合臺北市社福機構名冊與新北市轄區社會福利服務中心資料，篩選出實物銀行（含食物銀行）類別據點。', '社福政策研究、食物剩餘再分配研究、民眾尋找最近實物銀行。',
    ARRAY['https://data.taipei/dataset/detail?id=3fbc79e5-0138-4c89-8c47-39feddbd6d3f','https://data.ntpc.gov.tw/datasets/1C1D0066-A4E7-4753-B8BC-D7728D5F3E04'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT city AS x_axis, COUNT(*)::float AS data FROM food_bank WHERE lng IS NOT NULL AND lat IS NOT NULL GROUP BY city ORDER BY city',
    NULL, 'metrotaipei'),
  ('eco_diet_food_banks_points', NULL, ARRAY[207]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '臺北市社會局', '臺北實物銀行全量點位', '臺北實物銀行（含食物銀行）類別據點。', '社福政策研究、民眾尋找最近實物銀行。',
    ARRAY['https://data.taipei/dataset/detail?id=3fbc79e5-0138-4c89-8c47-39feddbd6d3f'],
    ARRAY['doit'],
    NOW(), NOW(), 'two_d',
    'SELECT ''臺北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''臺北市''',
    NULL, 'taipei'),
  ('eco_diet_food_banks_points', NULL, ARRAY[208]::integer[], '{}'::json, 'static', NULL, NULL, NULL,
    '新北市社會局', '新北實物銀行全量點位', '新北實物銀行（含食物銀行）類別據點。', '社福政策研究、民眾尋找最近實物銀行。',
    ARRAY['https://data.ntpc.gov.tw/datasets/1C1D0066-A4E7-4753-B8BC-D7728D5F3E04'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'two_d',
    'SELECT ''新北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank WHERE lng IS NOT NULL AND lat IS NOT NULL AND city=''新北市''',
    NULL, 'newtaipei');

-- ─── C5 雙北廢棄物產量趨勢（three_d，3 city） ────────────────────────
-- y_axis = '<縣市>-<metric>'，雙北 8 條（雙北 × 4 metric），單城 4 條
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_waste_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部', '雙北逐年廚餘量／一般垃圾／資源垃圾／總產生量', '整合行政院環保署一般廢棄物統計年報資料，呈現臺北市與新北市自 2018 年起的四項廢棄物年度趨勢。',
    '雙北減量政策成效評估、廚餘減量趨勢分析。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'three_d',
    $sql$WITH yearly AS (SELECT data_year, county, food_wastes_recycled, garbage_clearance, garbage_recycled, garbage_generated FROM gov_open_waste_yearly WHERE county IN ('臺北市','新北市'))
SELECT data_year::text AS x_axis, '' AS icon, county || '-廚餘量' AS y_axis, ROUND(food_wastes_recycled)::int AS data FROM yearly
UNION ALL SELECT data_year::text, '', county || '-一般垃圾', ROUND(garbage_clearance)::int FROM yearly
UNION ALL SELECT data_year::text, '', county || '-資源垃圾', ROUND(garbage_recycled)::int FROM yearly
UNION ALL SELECT data_year::text, '', county || '-總產生量', ROUND(garbage_generated)::int FROM yearly
ORDER BY 1, 3$sql$,
    NULL, 'metrotaipei'),
  ('eco_diet_waste_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部', '臺北逐年廚餘量／一般垃圾／資源垃圾／總產生量', '臺北自 2018 年起的四項廢棄物年度趨勢。', '臺北減量政策成效評估。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['doit'],
    NOW(), NOW(), 'three_d',
    $sql$WITH yearly AS (SELECT data_year, food_wastes_recycled, garbage_clearance, garbage_recycled, garbage_generated FROM gov_open_waste_yearly WHERE county = '臺北市')
SELECT data_year::text AS x_axis, '' AS icon, '廚餘量' AS y_axis, ROUND(food_wastes_recycled)::int AS data FROM yearly
UNION ALL SELECT data_year::text, '', '一般垃圾', ROUND(garbage_clearance)::int FROM yearly
UNION ALL SELECT data_year::text, '', '資源垃圾', ROUND(garbage_recycled)::int FROM yearly
UNION ALL SELECT data_year::text, '', '總產生量', ROUND(garbage_generated)::int FROM yearly
ORDER BY 1, 3$sql$,
    NULL, 'taipei'),
  ('eco_diet_waste_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部', '新北逐年廚餘量／一般垃圾／資源垃圾／總產生量', '新北自 2018 年起的四項廢棄物年度趨勢。', '新北減量政策成效評估。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'three_d',
    $sql$WITH yearly AS (SELECT data_year, food_wastes_recycled, garbage_clearance, garbage_recycled, garbage_generated FROM gov_open_waste_yearly WHERE county = '新北市')
SELECT data_year::text AS x_axis, '' AS icon, '廚餘量' AS y_axis, ROUND(food_wastes_recycled)::int AS data FROM yearly
UNION ALL SELECT data_year::text, '', '一般垃圾', ROUND(garbage_clearance)::int FROM yearly
UNION ALL SELECT data_year::text, '', '資源垃圾', ROUND(garbage_recycled)::int FROM yearly
UNION ALL SELECT data_year::text, '', '總產生量', ROUND(garbage_generated)::int FROM yearly
ORDER BY 1, 3$sql$,
    NULL, 'newtaipei');

-- ─── C5b 雙北廢棄物碳足跡趨勢（three_d，3 city） ────────────────────
-- 公式：food_wastes_recycled × 0.0483 + garbage_clearance × 0.34 + garbage_recycled × 0.369
-- 係數來源：repo 根目錄 coal_emission.csv 三類加權平均（單位：公噸 CO₂e/公噸 廢棄物）
INSERT INTO query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) VALUES
  ('eco_diet_waste_carbon_footprint_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部 × 行政院環保署 產品碳足跡公開資料',
    '雙北逐年廢棄物碳足跡（單位：公噸 CO₂e/年）',
    '計算公式：碳足跡(公噸 CO₂e/年) = 廚餘量(公噸) × 0.0483 + 一般垃圾量(公噸) × 0.340 + 資源垃圾量(公噸) × 0.369。三個轉換係數均萃取自 coal_emission.csv 平均值。',
    '雙北減碳政策推進評估、不同廢棄物類別對碳排貢獻拆解。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['doit','ntpc'],
    NOW(), NOW(), 'three_d',
    $sql$SELECT data_year::text AS x_axis, '' AS icon, county || '-碳足跡' AS y_axis,
ROUND(food_wastes_recycled * 0.0483 + garbage_clearance * 0.340 + garbage_recycled * 0.369)::int AS data
FROM gov_open_waste_yearly WHERE county IN ('臺北市','新北市') ORDER BY 1, 3$sql$,
    NULL, 'metrotaipei'),
  ('eco_diet_waste_carbon_footprint_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部 × 行政院環保署 產品碳足跡公開資料',
    '臺北逐年廢棄物碳足跡（單位：公噸 CO₂e/年）', '臺北逐年廢棄物碳足跡。', '臺北減碳政策推進評估。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['doit'],
    NOW(), NOW(), 'three_d',
    $sql$SELECT data_year::text AS x_axis, '' AS icon, '碳足跡' AS y_axis,
ROUND(food_wastes_recycled * 0.0483 + garbage_clearance * 0.340 + garbage_recycled * 0.369)::int AS data
FROM gov_open_waste_yearly WHERE county = '臺北市' ORDER BY 1$sql$,
    NULL, 'taipei'),
  ('eco_diet_waste_carbon_footprint_yearly', NULL, NULL, NULL, 'static', NULL, NULL, NULL,
    '環境部 × 行政院環保署 產品碳足跡公開資料',
    '新北逐年廢棄物碳足跡（單位：公噸 CO₂e/年）', '新北逐年廢棄物碳足跡。', '新北減碳政策推進評估。',
    ARRAY['https://data.gov.tw/dataset/9112'],
    ARRAY['ntpc'],
    NOW(), NOW(), 'three_d',
    $sql$SELECT data_year::text AS x_axis, '' AS icon, '碳足跡' AS y_axis,
ROUND(food_wastes_recycled * 0.0483 + garbage_clearance * 0.340 + garbage_recycled * 0.369)::int AS data
FROM gov_open_waste_yearly WHERE county = '新北市' ORDER BY 1$sql$,
    NULL, 'newtaipei');

-- ─── 5. dashboards (1 筆) ────────────────────────────────────────────
-- 綠色飲食只掛在雙北儀表板，不在臺北或新北各自設定 dashboard。
-- components 對應 EcoDietView 原本的 6 個 component（C1a/C1b/C4/C5/C5b/C7a）。

INSERT INTO dashboards (id, index, name, components, icon, updated_at, created_at) VALUES
  (700, 'eco_diet_metrotaipei', '綠色飲食行為流程',
   ARRAY[600, 601, 603, 604, 605, 606]::int[], 'eco', NOW(), NOW())
ON CONFLICT (index) DO UPDATE SET
  id   = EXCLUDED.id,
  name = EXCLUDED.name,
  components = EXCLUDED.components,
  icon = EXCLUDED.icon,
  updated_at = NOW();

-- ─── 6. dashboard_groups (1 筆) ──────────────────────────────────────
-- eco_diet_metrotaipei → metrotaipei (group 3)

INSERT INTO dashboard_groups (dashboard_id, group_id)
SELECT 700, id FROM groups WHERE name = 'metrotaipei'
ON CONFLICT (dashboard_id, group_id) DO NOTHING;

COMMIT;
