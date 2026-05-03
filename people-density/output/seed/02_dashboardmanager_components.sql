-- ===========================================================================
-- people-density / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
--
-- 註冊「村里人口密度」基本圖層（雙北通用）：
--   * components.id = 941
--   * index         = 'metrotaipei_village_population_density'
--   * 圖層類型      = fill（透明，僅供地圖交叉比對時點擊村里查看 popup）
--   * 圖表類型      = MapLegend（基本圖層僅顯示圖例，不繪資料圖）
--
-- GeoJSON 檔案位置：
--   Taipei-City-Dashboard-FE/public/mapData/
--     metrotaipei_village_population_density.geojson
--
-- ⚠️ 將此組件實際掛入「基本圖層」儀表板（map-layers-taipei / map-layers-metrotaipei）
--    請執行 03_map_layers_dashboard.sql。
-- ===========================================================================

-- 0. 冪等：清舊紀錄（同 index 與同 id 都清，避免殘留）
DELETE FROM public.query_charts
 WHERE index = 'metrotaipei_village_population_density';
DELETE FROM public.component_charts
 WHERE index = 'metrotaipei_village_population_density';
DELETE FROM public.component_maps
 WHERE index = 'metrotaipei_village_population_density';
DELETE FROM public.components
 WHERE index = 'metrotaipei_village_population_density'
    OR id = 941;

-- ============================================================================
-- 1. components
-- ============================================================================
INSERT INTO public.components (id, index, name) VALUES
  (941, 'metrotaipei_village_population_density', '村里人口密度');

-- ============================================================================
-- 2. component_charts
--    基本圖層慣例：使用 MapLegend 圖表，僅顯示圖例與單位。
-- ============================================================================
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('metrotaipei_village_population_density',
    ARRAY['#000000'],
    ARRAY['MapLegend'],
    '人/km²');

-- ============================================================================
-- 3. component_maps
--    透明 fill 圖層；點擊村里會在 popup 顯示完整 7 個欄位（含單位）。
--    fill-opacity = 0：圖層在地圖上不可見，但 queryRenderedFeatures 仍可取
--    到 feature，因此 popup 互動正常。
-- ============================================================================
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'metrotaipei_village_population_density',
  '村里人口密度',
  'fill',
  'geojson',
  NULL, NULL,
  '{"fill-color": "#000000", "fill-opacity": 0}'::json,
  '[
    {"key":"county",          "name":"縣市"},
    {"key":"town",            "name":"鄉鎮市區"},
    {"key":"village",         "name":"村里"},
    {"key":"population",      "name":"人口數（人）"},
    {"key":"households",      "name":"戶數"},
    {"key":"area_km2",        "name":"面積（km²）"},
    {"key":"density_per_km2", "name":"人口密度（人/km²）"}
  ]'::json
);

-- ============================================================================
-- 4. query_charts
--    基本圖層採 MapLegend 慣例（query_type = 'map_legend'）：
--    SQL 回傳 (name, type) 兩欄，給左側圖層列表顯示圖例。
--    - taipei      → 同一個 fill 圖層
--    - metrotaipei → 同一個 fill 圖層（資料本身已含雙北全部村里）
-- ============================================================================

-- 4-1 taipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'metrotaipei_village_population_density', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'metrotaipei_village_population_density'),
  '{}'::json,
  'static', NULL, 1, 'month',
  '內政部戶政司 / 村里界圖',
  '臺北市村里級人口密度（人/km²）',
  '以村里為單位呈現臺北市人口密度資訊。圖層本身為透明 fill，僅在地圖交叉比對時供使用者點擊村里檢視該里之縣市、鄉鎮市區、村里、人口數、戶數、面積、人口密度等資訊，方便與其他主題圖資（如自行車道、公車捷運站、人行道等）交叉判讀。',
  '作為基本圖層疊加於各主題圖資之上，協助規劃單位評估高人口密度區域的設施需求、可及性、服務不足缺口等議題。',
  ARRAY['https://data.gov.tw/']::text[],
  ARRAY['hackathon_team']::text[],
  NOW(), NOW(),
  'map_legend',
  $$SELECT unnest(ARRAY['村里人口密度']) AS name, 'fill' AS type$$,
  NULL,
  'taipei'
);

-- 4-2 metrotaipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'metrotaipei_village_population_density', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'metrotaipei_village_population_density'),
  '{}'::json,
  'static', NULL, 1, 'month',
  '內政部戶政司 / 村里界圖',
  '雙北村里級人口密度（人/km²）',
  '以村里為單位呈現雙北（臺北市 + 新北市）人口密度資訊。圖層本身為透明 fill，僅在地圖交叉比對時供使用者點擊村里檢視該里之縣市、鄉鎮市區、村里、人口數、戶數、面積、人口密度等資訊，方便與其他主題圖資（如自行車道、公車捷運站、人行道等）交叉判讀。',
  '作為雙北通用的基本圖層，協助跨市、跨主題比較人口密度與都市機能、交通建設、公共服務之關聯。',
  ARRAY['https://data.gov.tw/']::text[],
  ARRAY['hackathon_team']::text[],
  NOW(), NOW(),
  'map_legend',
  $$SELECT unnest(ARRAY['村里人口密度']) AS name, 'fill' AS type$$,
  NULL,
  'metrotaipei'
);
