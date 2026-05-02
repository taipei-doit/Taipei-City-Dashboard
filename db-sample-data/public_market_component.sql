-- =====================================================
-- 公有市場組件 (public_market) - 組件配置 SQL
-- 涵蓋 taipei / metrotaipei 雙版本
-- =====================================================

INSERT INTO public.components ("index", name)
VALUES ('public_market', '公有市場')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'public_market',
    ARRAY['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#F0B27A','#85C1E9','#82E0AA','#F1948A','#BB8FCE','#73C6B6'],
    ARRAY['BarChart','DonutChart'],
    '間'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps
WHERE "index" IN ('public_market_tpe', 'public_market_new_tpe');

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES
(
    'public_market_tpe',
    '公有市場',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-color": "#FF6B6B", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1}'::json,
    '[{"key":"name","name":"市場名稱"},{"key":"district","name":"行政區"},{"key":"total_stalls","name":"攤位總數"},{"key":"food_drink","name":"飲食攤位"},{"key":"meat","name":"獸肉攤位"},{"key":"vegetable","name":"蔬菜攤位"}]'::json
),
(
    'public_market_new_tpe',
    '公有市場',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-color": "#4ECDC4", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1}'::json,
    '[{"key":"name","name":"市場名稱"},{"key":"district","name":"行政區"},{"key":"phone","name":"電話"},{"key":"market_type","name":"營業類型"}]'::json
);

DELETE FROM public.query_charts
WHERE "index" = 'public_market' AND city IN ('taipei', 'metrotaipei');

INSERT INTO public.query_charts (
    "index",
    history_config,
    map_config_ids,
    map_filter,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES
(
    'public_market',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'public_market_tpe' ORDER BY id DESC LIMIT 1)],
    '{}',
    'static',
    NULL,
    0,
    NULL,
    '市場處',
    '顯示臺北市各行政區公有市場數量分布。',
    '此圖表呈現臺北市公有零售市場在各行政區的分布情形，包含各市場的攤位數量統計與分類（蔬菜、青果、獸肉、漁產、家禽、糧食、花卉、雜貨、百貨、飲食等）。透過此資料可掌握臺北市公有市場的空間配置與業種結構，作為商業規劃、民生服務與市場管理之參考依據。',
    '適用於城市商業規劃、市場管理與民生消費分析。政府可藉此評估各區市場供需平衡，規劃市場改建或新設地點。市民可查詢住家附近的公有市場位置與營業資訊。',
    ARRAY[]::text[],
    ARRAY['doit'],
    '2025-05-01 00:00:00+00',
    '2025-05-01 00:00:00+00',
    'two_d',
    'SELECT district AS x_axis, COUNT(*)::float AS data FROM public_market_tpe GROUP BY district ORDER BY data DESC',
    NULL,
    'taipei'
),
(
    'public_market',
    NULL,
    ARRAY[
        (SELECT id FROM public.component_maps WHERE "index" = 'public_market_tpe' ORDER BY id DESC LIMIT 1),
        (SELECT id FROM public.component_maps WHERE "index" = 'public_market_new_tpe' ORDER BY id DESC LIMIT 1)
    ],
    '{}',
    'static',
    NULL,
    0,
    NULL,
    '市場處',
    '顯示雙北各行政區公有市場數量分布。',
    '此圖表呈現臺北市與新北市公有零售市場在各行政區的分布情形。臺北市部分包含各市場的攤位數量統計與分類，新北市部分包含市場基本資訊與營業類型。透過此資料可掌握雙北地區公有市場的空間配置，作為跨域商業規劃、民生服務與市場管理之參考依據。',
    '適用於跨域商業規劃與民生消費分析，涵蓋臺北市與新北市。政府可藉此評估雙北各區市場分布密度，作為市場新設或改建之決策參考。',
    ARRAY[]::text[],
    ARRAY['doit','ntpc'],
    '2025-05-01 00:00:00+00',
    '2025-05-01 00:00:00+00',
    'two_d',
    'SELECT x_axis, SUM(data)::float AS data FROM (SELECT district AS x_axis, COUNT(*)::float AS data FROM public_market_tpe GROUP BY district UNION ALL SELECT district AS x_axis, COUNT(*)::float AS data FROM public_market_new_tpe GROUP BY district) d GROUP BY x_axis ORDER BY data DESC',
    NULL,
    'metrotaipei'
);

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
SELECT setval('public.component_maps_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.component_maps), true);
