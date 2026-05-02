-- =====================================================
-- 產銷履歷抽驗結果 + CAS 認證產品 組件配置 SQL
-- 需先執行 traceability_cas_tables.sql 建表
-- =====================================================

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

-- ===== 1. 產銷履歷抽驗結果 =====

INSERT INTO public.components ("index", name)
VALUES ('traceability_inspection', '產銷履歷抽驗結果')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'traceability_inspection',
    ARRAY['#2ECC71','#E74C3C'],
    ARRAY['DonutChart','BarChart'],
    '件'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.query_charts
WHERE "index" = 'traceability_inspection';

INSERT INTO public.query_charts (
    "index", history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
)
VALUES
(
    'traceability_inspection',
    NULL, NULL, NULL,
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    '產銷履歷農產品抽驗合格率。',
    '透過農業部產銷履歷農產品抽驗結果 API，即時呈現各抽樣地點的檢驗合格與不合格統計，綠色為合格、紅色為不合格。',
    '適用於食安監控與農產品品質追蹤。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'two_d',
    'SELECT inspect_result AS x_axis, COUNT(*)::integer AS data FROM traceability_inspection WHERE inspect_result IS NOT NULL GROUP BY inspect_result ORDER BY inspect_result DESC',
    NULL,
    'taipei'
),
(
    'traceability_inspection',
    NULL, NULL, NULL,
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    '產銷履歷農產品抽驗合格率。',
    '透過農業部產銷履歷農產品抽驗結果 API，即時呈現各抽樣地點的檢驗合格與不合格統計，綠色為合格、紅色為不合格。',
    '適用於食安監控與農產品品質追蹤。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'two_d',
    'SELECT inspect_result AS x_axis, COUNT(*)::integer AS data FROM traceability_inspection WHERE inspect_result IS NOT NULL GROUP BY inspect_result ORDER BY inspect_result DESC',
    NULL,
    'metrotaipei'
);

-- ===== 2. CAS 認證產品分佈 =====

INSERT INTO public.components ("index", name)
VALUES ('cas_product', 'CAS 認證產品分佈')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'cas_product',
    ARRAY['#3498DB','#E67E22','#2ECC71','#9B59B6','#E74C3C','#1ABC9C','#F39C12','#34495E'],
    ARRAY['TreemapChart','BarChart'],
    '項'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.query_charts
WHERE "index" = 'cas_product';

INSERT INTO public.query_charts (
    "index", history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
)
VALUES
(
    'cas_product',
    NULL, NULL, NULL,
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    'CAS 優良農產品認證產品類別分佈。',
    '透過農業部 CAS 產品查詢 API，以樹狀圖呈現各材料類別（肉品、蛋品、水產等）通過 CAS 認證的產品數量，面積越大代表該類認證產品越多。',
    '適用於食安監控與優良農產品推廣。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'two_d',
    'SELECT material_name AS x_axis, COUNT(*)::integer AS data FROM cas_product WHERE material_name IS NOT NULL GROUP BY material_name ORDER BY data DESC',
    NULL,
    'taipei'
),
(
    'cas_product',
    NULL, NULL, NULL,
    'current', NULL, 1, 'hour',
    '農業部農業開放資料平臺',
    'CAS 優良農產品認證產品類別分佈。',
    '透過農業部 CAS 產品查詢 API，以樹狀圖呈現各材料類別（肉品、蛋品、水產等）通過 CAS 認證的產品數量，面積越大代表該類認證產品越多。',
    '適用於食安監控與優良農產品推廣。',
    ARRAY['https://data.moa.gov.tw/api.aspx'],
    ARRAY['doit'],
    NOW(), NOW(),
    'two_d',
    'SELECT material_name AS x_axis, COUNT(*)::integer AS data FROM cas_product WHERE material_name IS NOT NULL GROUP BY material_name ORDER BY data DESC',
    NULL,
    'metrotaipei'
);

-- ===== 加入「食安健康」儀表板（tpe + newtpe） =====

UPDATE public.dashboards
SET components = array_append(components, (SELECT id FROM public.components WHERE "index" = 'traceability_inspection')),
    updated_at = NOW()
WHERE "index" IN ('food_safety_health_tpe', 'food_safety_health_newtpe')
  AND NOT ((SELECT id FROM public.components WHERE "index" = 'traceability_inspection') = ANY(components));

UPDATE public.dashboards
SET components = array_append(components, (SELECT id FROM public.components WHERE "index" = 'cas_product')),
    updated_at = NOW()
WHERE "index" IN ('food_safety_health_tpe', 'food_safety_health_newtpe')
  AND NOT ((SELECT id FROM public.components WHERE "index" = 'cas_product') = ANY(components));

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
