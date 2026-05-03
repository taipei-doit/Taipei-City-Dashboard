-- ===========================================================================
-- green_land / 02_dashboardmanager_components.sql → DB: dashboardmanager
--
-- 兩個組件：
--   932  green_land_vegetation  樹木植栽培育（逐年分組長條）  three_d  ColumnChart  株/盆（各期原值）
--   936  green_land_summary     綠美化關鍵指標（最新年份）    three_d  TextUnitChart
--          4 格數字看板：道路綠地累計面積（㎡）、路燈累計清洗汰換（盞）、
--                       後巷美化（累計條）、田園園圃面積（最新快照㎡）
--
-- 橫軸（932）：統計期（民國年，如 89年）
-- 先執行 00_alter_component_charts_stacked.sql（加 stacked 欄），再執行 01，最後本檔
-- ===========================================================================

-- 0. 冪等清除（含舊版單指標組件 931/933/934/935）
DELETE FROM public.query_charts
 WHERE index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');
DELETE FROM public.component_charts
 WHERE index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');
DELETE FROM public.components
 WHERE id IN (930,931,932,933,934,935,936)
    OR index IN ('green_land_area','green_land_vegetation',
                 'green_land_streetlight','green_land_alley','green_land_farm',
                 'green_land_summary','green_land_beautification');

-- ============================================================================
-- 1. components
-- ============================================================================
INSERT INTO public.components (id, index, name) VALUES
  (932, 'green_land_vegetation', '樹木植栽培育量'),
  (936, 'green_land_summary',    '綠美化關鍵指標');

-- ============================================================================
-- 2. component_charts
-- ============================================================================
INSERT INTO public.component_charts (index, color, types, unit, stacked) VALUES
  ('green_land_vegetation',
    ARRAY['#81C784','#43A047','#1B5E20','#AED581','#C5E1A5']::varchar[],
    ARRAY['ColumnChart']::varchar[], '株/盆', FALSE),
  -- TextUnitChart 使用 3 種顏色：color[0]=指標名稱, color[1]=數值, color[2]=單位
  ('green_land_summary',
    ARRAY['#A5D6A7','#F9A825','#66BB6A']::varchar[],
    ARRAY['TextUnitChart']::varchar[], '', FALSE);

-- ============================================================================
-- 3. query_charts
-- ============================================================================

-- 932 green_land_vegetation（樹木植栽培育, three_d, 5 系列, stacked=FALSE 分組長條）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter, time_from, time_to,
  update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
  links, contributors, created_at, updated_at, query_type, query_chart, query_history, city
) VALUES (
  'green_land_vegetation', NULL, '{}', NULL, 'static', NULL,
  1, 'year',
  '臺北市政府開放資料平台 / 市容綠美化統計',
  '臺北市行道樹、公園喬木、鄰里公園喬木、灌木、草花逐年培育量。',
  '各類植栽培育量以分組縱向長條圖呈現，單位：株（盆）。各期為當年度培育量原值，未做累計。',
  '城市植栽生態與綠化政策追蹤。',
  ARRAY[]::text[], ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT g.stat_label            AS x_axis,
       ''::text                AS icon,
       m.metric_label          AS y_axis,
       m.metric_value::integer AS data
  FROM public.green_land_beautification g
  CROSS JOIN LATERAL (VALUES
    (1, '行道樹[株]',          g.street_trees),
    (2, '公園內喬木數[株]',     g.park_trees),
    (3, '鄰里公園內喬木數[株]', g.neighborhood_park_trees),
    (4, '灌木培育數[株]',       g.shrub_count),
    (5, '草花培育數[盆]',       g.flower_pots)
  ) AS m(ord, metric_label, metric_value)
  ORDER BY g.roc_year, m.ord$$,
  NULL, 'taipei'
);

-- 936 green_land_summary（綠美化關鍵指標, three_d → TextUnitChart）
-- categories 只有一個空字串；每一列成為一個 series（name=指標, icon=單位, data=[數值]）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter, time_from, time_to,
  update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
  links, contributors, created_at, updated_at, query_type, query_chart, query_history, city
) VALUES (
  'green_land_summary', NULL, '{}', NULL, 'static', NULL,
  1, 'year',
  '臺北市政府開放資料平台 / 市容綠美化統計',
  '臺北市市容綠美化四項關鍵指標最新累計值。',
  '道路綠地累計面積、路燈累計清洗汰換、後巷美化累計巷數、田園城市示範園圃面積（最新年份快照）。',
  '城市市容綠美化政策成果一覽。',
  ARRAY[]::text[], ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT ''::text AS x_axis,
       m.unit  AS icon,
       m.label AS y_axis,
       m.val   AS data
  FROM (VALUES
    ('道路綠地累計面積', '平方公尺',
       (SELECT road_green_m2     FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('路燈累計清洗汰換', '盞',
       (SELECT streetlight_units FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('後巷美化累計巷數', '條',
       (SELECT alley_count       FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),
    ('田園城市示範園圃面積', '平方公尺',
       (SELECT demo_farm_m2      FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1))
  ) AS m(label, unit, val)$$,
  NULL, 'taipei'
);
