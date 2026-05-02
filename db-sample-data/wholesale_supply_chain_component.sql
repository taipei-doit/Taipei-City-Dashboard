-- =====================================================
-- 批發市場供應鏈推演 組件配置 SQL
-- 涵蓋 taipei / metrotaipei 雙版本
-- 圖層：零售狀態(circle) + 批發點位(symbol) + 4類弧線(arc)
-- =====================================================

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

INSERT INTO public.components ("index", name)
VALUES ('wholesale_supply_chain', '市場供應鏈')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'wholesale_supply_chain',
    ARRAY['#2ECC71','#E67E22','#27AE60','#2980B9','#C0392B','#8E44AD','#2ECC71'],
    ARRAY['MapLegend','BarChart','ColumnChart'],
    '公斤'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- Map layers
DELETE FROM public.component_maps
WHERE "index" IN (
    'supply_chain_tpe', 'supply_chain_new_tpe', 'supply_chain_wholesale',
    'supply_chain_arcs',
    'supply_chain_arc_vf', 'supply_chain_arc_fish',
    'supply_chain_arc_pork', 'supply_chain_arc_poultry'
);

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES
-- 零售市場狀態 (circle)
(
    'supply_chain_tpe',
    '供應鏈狀態（臺北）',
    'circle', 'geojson', NULL, NULL,
    '{"circle-color":["case",["get","supply_active"],"#2ECC71","#E74C3C"],"circle-radius":["interpolate",["linear"],["get","trust_score"],0,4,50,7,90,11],"circle-opacity":0.85,"circle-stroke-color":"#ffffff","circle-stroke-width":1.5}'::json,
    '[{"key":"name","name":"市場名稱"},{"key":"district","name":"行政區"},{"key":"supply_active","name":"今日供貨"},{"key":"supply_categories","name":"供貨���別"},{"key":"total_items","name":"供應品項數"},{"key":"trust_score","name":"信任分數"},{"key":"status_text","name":"供應狀態"},{"key":"top_items_display","name":"主要供應品項"}]'::json
),
(
    'supply_chain_new_tpe',
    '��應鏈狀態（��北）',
    'circle', 'geojson', NULL, NULL,
    '{"circle-color":["case",["get","supply_active"],"#2ECC71","#E74C3C"],"circle-radius":["interpolate",["linear"],["get","trust_score"],0,4,50,7,90,11],"circle-opacity":0.85,"circle-stroke-color":"#ffffff","circle-stroke-width":1.5}'::json,
    '[{"key":"name","name":"市場��稱"},{"key":"district","name":"行政區"},{"key":"supply_active","name":"今日供貨"},{"key":"supply_categories","name":"供貨類別"},{"key":"total_items","name":"供應品項數"},{"key":"trust_score","name":"信任分數"},{"key":"status_text","name":"供應狀態"}]'::json
),
-- 批發市場點位 (symbol)
(
    'supply_chain_wholesale',
    '���發市場',
    'symbol', 'geojson', NULL, 'triangle_green',
    '{}'::json,
    '[{"key":"name","name":"市場名稱"},{"key":"type","name":"類型"},{"key":"district","name":"行政區"},{"key":"categories","name":"供貨類別"}]'::json
),
-- 四類供應路線 (arc) — 各自獨立圖層，可個別 toggle
(
    'supply_chain_arc_vf',
    '蔬果供應路線',
    'arc', 'geojson', NULL, NULL,
    '{"arc-color":["#27AE60","#2ECC71"],"arc-width":2,"arc-opacity":0.5,"arc-animate":true}'::json,
    '[{"key":"wholesale_name","name":"批發市場"},{"key":"retail_name","name":"零售市場"},{"key":"category","name":"供貨類別"}]'::json
),
(
    'supply_chain_arc_fish',
    '漁產供應路��',
    'arc', 'geojson', NULL, NULL,
    '{"arc-color":["#2980B9","#3498DB"],"arc-width":2,"arc-opacity":0.5,"arc-animate":true}'::json,
    '[{"key":"wholesale_name","name":"批發市場"},{"key":"retail_name","name":"零售市場"},{"key":"category","name":"供貨類別"}]'::json
),
(
    'supply_chain_arc_pork',
    '肉類供應路線',
    'arc', 'geojson', NULL, NULL,
    '{"arc-color":["#C0392B","#E74C3C"],"arc-width":2,"arc-opacity":0.5,"arc-animate":true}'::json,
    '[{"key":"wholesale_name","name":"批發市場"},{"key":"retail_name","name":"零售市場"},{"key":"category","name":"供���類別"}]'::json
),
(
    'supply_chain_arc_poultry',
    '家禽供應路線',
    'arc', 'geojson', NULL, NULL,
    '{"arc-color":["#8E44AD","#9B59B6"],"arc-width":2,"arc-opacity":0.5,"arc-animate":true}'::json,
    '[{"key":"wholesale_name","name":"批發市場"},{"key":"retail_name","name":"零售市��"},{"key":"category","name":"供貨類別"}]'::json
);

DELETE FROM public.query_charts
WHERE "index" = 'wholesale_supply_chain' AND city IN ('taipei', 'metrotaipei');

INSERT INTO public.query_charts (
    "index", history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
)
VALUES
(
    'wholesale_supply_chain',
    NULL,
    ARRAY[
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_tpe'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_wholesale'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_vf'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_fish'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_pork'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_poultry')
    ],
    '{"mode":"byLayerToggle"}',
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    '即時推演臺北市公有市場的批發供貨狀態與食安信任分數。',
    '透過農產品批發市場交易行情(蔬果/豬肉/漁產/家禽)API，結合供應鏈對應表與產銷履歷/CAS驗證資料，即時推演雙北79間公有市場的供貨狀態。綠色圓點表示今日已有新鮮物資由批發端流入，圓圈大小反映信任分數(0~100)。三角形為批發市場，弧線為推演的供應路線（基於地理鄰近性，非實際物流紀錄）。',
    '適用於食安監控、市場管理與民生供應鏈透明化。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'three_d',
    'SELECT CASE category WHEN ''vegetable_fruit'' THEN ''��果'' WHEN ''fishery'' THEN ''漁產'' WHEN ''pork'' THEN ''肉類'' WHEN ''poultry'' THEN ''家禽'' END AS x_axis, market_name AS y_axis, COALESCE(total_quantity, 0)::integer AS data FROM wholesale_daily_summary ORDER BY total_quantity DESC',
    NULL,
    'taipei'
),
(
    'wholesale_supply_chain',
    NULL,
    ARRAY[
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_tpe'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_new_tpe'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_wholesale'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_vf'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_fish'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_pork'),
        (SELECT id FROM public.component_maps WHERE "index" = 'supply_chain_arc_poultry')
    ],
    '{"mode":"byLayerToggle"}',
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    '即時推演雙北公有市場的���發供貨狀態與食安信任分數。',
    '透過農產��批發市場交易行情(蔬果/豬肉/漁產/��禽)API，結合供應鏈對應表與���銷履歷/CAS驗證資料，即時推演雙北79間公有市場的供貨狀態。',
    '適用於跨域食安監控與市場管理。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'three_d',
    'SELECT CASE category WHEN ''vegetable_fruit'' THEN ''蔬果'' WHEN ''fishery'' THEN ''漁產'' WHEN ''pork'' THEN ''肉類'' WHEN ''poultry'' THEN ''家禽'' END AS x_axis, market_name AS y_axis, COALESCE(total_quantity, 0)::integer AS data FROM wholesale_daily_summary ORDER BY total_quantity DESC',
    NULL,
    'metrotaipei'
);

-- 加入「食安健康」儀表板 (冪等)
UPDATE public.dashboards
SET components = array_append(components, (SELECT id FROM public.components WHERE "index" = 'wholesale_supply_chain')),
    updated_at = NOW()
WHERE "index" = 'food_safety_health_tpe'
  AND NOT ((SELECT id FROM public.components WHERE "index" = 'wholesale_supply_chain') = ANY(components));

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
SELECT setval('public.component_maps_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.component_maps), true);
