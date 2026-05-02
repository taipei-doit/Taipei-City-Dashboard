-- =====================================================
-- 環保餐廳 組件配置 SQL
-- 適用 postgres-manager (dashboardmanager)
-- 需先執行 green_restaurant_tables.sql 建表
-- =====================================================

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

-- ===== 1. 組件 =====

INSERT INTO public.components ("index", name)
VALUES ('green_restaurant', '環保餐廳')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

-- ===== 2. 圖表設定（DistrictChart + BarChart） =====

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'green_restaurant',
    ARRAY['#1b5e20','#4caf50','#81c784','#c8e6c9'],
    ARRAY['DistrictChart','BarChart'],
    '間'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- ===== 3. 地圖圖層 =====

DELETE FROM public.component_maps WHERE "index" IN ('green_restaurant_tpe', 'green_restaurant_ntpc');

INSERT INTO public.component_maps ("index", title, type, source, paint, property)
VALUES
(
    'green_restaurant_tpe',
    '台北環保餐廳',
    'circle',
    'geojson',
    '{"circle-color":"#4caf50","circle-radius":1.2,"circle-opacity":0.85,"circle-stroke-color":"#2e7d32","circle-stroke-width":0.3}',
    '[{"key":"name","name":"餐廳名稱"},{"key":"district","name":"行政區"},{"key":"category","name":"餐廳類別"},{"key":"tel","name":"電話"},{"key":"address","name":"地址"},{"key":"eco_actions","name":"額外環保作為"}]'
),
(
    'green_restaurant_ntpc',
    '新北環保餐廳',
    'circle',
    'geojson',
    '{"circle-color":"#66bb6a","circle-radius":1.2,"circle-opacity":0.85,"circle-stroke-color":"#388e3c","circle-stroke-width":0.3}',
    '[{"key":"name","name":"餐廳名稱"},{"key":"district","name":"行政區"},{"key":"category","name":"餐廳類別"},{"key":"tel","name":"電話"},{"key":"address","name":"地址"},{"key":"eco_actions","name":"額外環保作為"}]'
);

-- ===== 4. 查詢設定 =====

DELETE FROM public.query_charts WHERE "index" = 'green_restaurant';

INSERT INTO public.query_charts (
    "index", history_config,
    map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
)
VALUES
(
    'green_restaurant',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'green_restaurant_tpe' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"district"}}',
    'static', NULL, 1, 'month',
    '環保局',
    '顯示臺北市環保餐廳按行政區之分布數量。',
    '臺北市環保餐廳依行政區分布統計，資料來源為環保局環保餐廳名單，涵蓋餐廳名稱、行政區、餐廳類別、電話、地址與環保作為等資訊。點選長條圖或行政區圖可在地圖上篩選對應行政區之餐廳點位。',
    '可用於了解臺北市環保餐廳的行政區分布情形，協助市民查詢環保餐廳，並作為環保政策推廣成效之參考依據。',
    ARRAY[]::text[],
    ARRAY['doit'],
    NOW(), NOW(),
    'two_d',
    'SELECT district AS x_axis, COUNT(*) AS data FROM public.green_restaurant_tpe WHERE district IS NOT NULL GROUP BY district ORDER BY data DESC',
    NULL,
    'taipei'
),
(
    'green_restaurant',
    NULL,
    ARRAY[
        (SELECT id FROM public.component_maps WHERE "index" = 'green_restaurant_tpe' ORDER BY id DESC LIMIT 1),
        (SELECT id FROM public.component_maps WHERE "index" = 'green_restaurant_ntpc' ORDER BY id DESC LIMIT 1)
    ],
    '{"mode":"byParam","byParam":{"xParam":"district"}}',
    'static', NULL, 1, 'month',
    '環保局',
    '顯示雙北環保餐廳按行政區之分布數量。',
    '雙北環保餐廳依行政區分布統計，資料來源為環保局環保餐廳名單，涵蓋臺北市與新北市兩地資料，包含餐廳名稱、行政區、餐廳類別、電話、地址與環保作為等資訊。',
    '可用於比較雙北環保餐廳的行政區分布差異，協助市民查詢環保餐廳，並作為雙北環保政策推廣成效之參考依據。',
    ARRAY[]::text[],
    ARRAY['doit','ntpc'],
    NOW(), NOW(),
    'two_d',
    'SELECT x_axis, SUM(data) AS data FROM (SELECT district AS x_axis, COUNT(*) AS data FROM public.green_restaurant_tpe WHERE district IS NOT NULL GROUP BY district UNION ALL SELECT district AS x_axis, COUNT(*) AS data FROM public.green_restaurant_ntpc WHERE district IS NOT NULL GROUP BY district) d GROUP BY x_axis ORDER BY data DESC',
    NULL,
    'metrotaipei'
);

-- ===== 5. 加入儀表板 =====

UPDATE public.dashboards
SET components = array_append(components, (SELECT id FROM public.components WHERE "index" = 'green_restaurant')),
    updated_at = NOW()
WHERE "index" IN ('food_safety_health_tpe', 'food_safety_health_newtpe')
  AND NOT ((SELECT id FROM public.components WHERE "index" = 'green_restaurant') = ANY(components));

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
