-- =====================================================
-- 溯源餐廳 組件配置 SQL
-- 適用 postgres-manager (dashboardmanager)
-- =====================================================

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

-- ===== 1. 組件 =====

INSERT INTO public.components ("index", name)
VALUES ('traceable_restaurant', '溯源餐廳')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

-- ===== 2. 圖表設定（TreemapChart + BarChart） =====

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'traceable_restaurant',
    ARRAY['#ffcc80','#f57c00','#e65100','#fb8c00','#ff9800','#ffa726','#ffb74d','#ef6c00','#ffe0b2'],
    ARRAY['TreemapChart','BarChart'],
    '間'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- ===== 3. 地圖圖層 =====

DELETE FROM public.component_maps WHERE "index" IN ('traceable_restaurant_tpe', 'traceable_restaurant_ntpc');

INSERT INTO public.component_maps ("index", title, type, source, paint, property)
VALUES
(
    'traceable_restaurant_tpe',
    '台北溯源餐廳',
    'circle',
    'geojson',
    '{"circle-color":"#ef6c00","circle-radius":3,"circle-opacity":0.85,"circle-stroke-color":"#e65100","circle-stroke-width":0.5}',
    '[{"key":"name","name":"餐廳名稱"},{"key":"cuisine_type","name":"料理種類"},{"key":"star_rating","name":"星級數"},{"key":"address","name":"地址"},{"key":"tel","name":"電話"}]'
),
(
    'traceable_restaurant_ntpc',
    '新北溯源餐廳',
    'circle',
    'geojson',
    '{"circle-color":"#fb8c00","circle-radius":3,"circle-opacity":0.85,"circle-stroke-color":"#ef6c00","circle-stroke-width":0.5}',
    '[{"key":"name","name":"餐廳名稱"},{"key":"cuisine_type","name":"料理種類"},{"key":"star_rating","name":"星級數"},{"key":"address","name":"地址"},{"key":"tel","name":"電話"}]'
);

-- ===== 4. 查詢設定 =====

DELETE FROM public.query_charts WHERE "index" = 'traceable_restaurant';

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
    'traceable_restaurant',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'traceable_restaurant_tpe' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"cuisine_type","yParam":"star_rating"}}',
    'static', NULL, 1, 'month',
    '衛生局',
    '顯示台北市溯源餐廳按料理種類與星級之分布數量。',
    '台北市溯源餐廳依料理種類與星級分布統計，資料來源為衛生局溯源餐廳名單，涵蓋餐廳名稱、料理種類、星級數、地址、電話等資訊。點選橫向長條圖中的區段可在地圖上篩選對應料理種類與星級之餐廳點位。',
    '可用於評估台北市溯源餐廳的料理種類與星級分布情形，協助市民查詢具食材溯源認證之餐廳，並作為食品安全政策推廣成效之參考依據。',
    ARRAY[]::text[],
    ARRAY['doit'],
    NOW(), NOW(),
    'three_d',
    'SELECT x_axis, y_axis, data FROM (SELECT c.cuisine_type AS x_axis, s.star_rating AS y_axis, COALESCE(d.cnt, 0) AS data, SUM(COALESCE(d.cnt, 0)) OVER (PARTITION BY c.cuisine_type) AS total FROM (SELECT DISTINCT cuisine_type FROM traceable_restaurant_tpe WHERE cuisine_type IS NOT NULL) c CROSS JOIN (SELECT DISTINCT star_rating FROM traceable_restaurant_tpe) s LEFT JOIN (SELECT cuisine_type, star_rating, COUNT(*) AS cnt FROM traceable_restaurant_tpe WHERE cuisine_type IS NOT NULL GROUP BY cuisine_type, star_rating) d ON c.cuisine_type = d.cuisine_type AND s.star_rating = d.star_rating) sub ORDER BY total DESC, x_axis, y_axis',
    NULL,
    'taipei'
),
(
    'traceable_restaurant',
    NULL,
    ARRAY[
        (SELECT id FROM public.component_maps WHERE "index" = 'traceable_restaurant_tpe' ORDER BY id DESC LIMIT 1),
        (SELECT id FROM public.component_maps WHERE "index" = 'traceable_restaurant_ntpc' ORDER BY id DESC LIMIT 1)
    ],
    '{"mode":"byParam","byParam":{"xParam":"cuisine_type","yParam":"star_rating"}}',
    'static', NULL, 1, 'month',
    '衛生局',
    '顯示雙北溯源餐廳按料理種類與星級之分布數量。',
    '雙北溯源餐廳依料理種類與星級分布統計，資料來源為衛生局溯源餐廳名單，涵蓋台北市與新北市兩地資料，包含餐廳名稱、料理種類、星級數、地址、電話等資訊。點選橫向長條圖中的區段可在地圖上篩選對應料理種類與星級之餐廳點位。',
    '可用於比較雙北溯源餐廳的料理種類與星級分布差異，協助市民及遊客查詢具食材溯源認證之餐廳，並作為雙北食品安全政策整體推廣成效之參考依據。',
    ARRAY[]::text[],
    ARRAY['doit','ntpc'],
    NOW(), NOW(),
    'three_d',
    'SELECT x_axis, y_axis, data FROM (SELECT x_axis, y_axis, SUM(data) AS data, SUM(SUM(data)) OVER (PARTITION BY x_axis) AS total FROM (SELECT c.cuisine_type AS x_axis, s.star_rating AS y_axis, COALESCE(d.cnt, 0) AS data FROM (SELECT DISTINCT cuisine_type FROM traceable_restaurant_tpe WHERE cuisine_type IS NOT NULL UNION SELECT DISTINCT cuisine_type FROM traceable_restaurant_ntpc WHERE cuisine_type IS NOT NULL) c CROSS JOIN (SELECT DISTINCT star_rating FROM traceable_restaurant_tpe UNION SELECT DISTINCT star_rating FROM traceable_restaurant_ntpc) s LEFT JOIN (SELECT cuisine_type, star_rating, COUNT(*) AS cnt FROM traceable_restaurant_tpe WHERE cuisine_type IS NOT NULL GROUP BY cuisine_type, star_rating UNION ALL SELECT cuisine_type, star_rating, COUNT(*) AS cnt FROM traceable_restaurant_ntpc WHERE cuisine_type IS NOT NULL GROUP BY cuisine_type, star_rating) d ON c.cuisine_type = d.cuisine_type AND s.star_rating = d.star_rating) t GROUP BY x_axis, y_axis) sub ORDER BY total DESC, x_axis, y_axis',
    NULL,
    'metrotaipei'
);

-- ===== 5. 加入儀表板 =====

UPDATE public.dashboards
SET components = array_append(components, (SELECT id FROM public.components WHERE "index" = 'traceable_restaurant')),
    updated_at = NOW()
WHERE "index" IN ('food_safety_health_tpe', 'food_safety_health_newtpe')
  AND NOT ((SELECT id FROM public.components WHERE "index" = 'traceable_restaurant') = ANY(components));

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
