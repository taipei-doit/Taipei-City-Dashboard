BEGIN;

DELETE FROM public.query_charts
WHERE index = 'restaurant_inspections';

DELETE FROM public.component_charts
WHERE index = 'restaurant_inspections';

DELETE FROM public.component_maps
WHERE id IN (905, 906)
   OR index IN ('restaurant_inspections_all', 'restaurant_inspections_failed');

DELETE FROM public.dashboard_groups
WHERE dashboard_id IN (
    SELECT id
    FROM public.dashboards
    WHERE index = 'restaurant_inspections_map'
);

DELETE FROM public.dashboards
WHERE index = 'restaurant_inspections_map';

DELETE FROM public.components
WHERE id = 903
   OR index = 'restaurant_inspections';

INSERT INTO public.components (id, index, name)
VALUES (903, 'restaurant_inspections', '餐廳抽驗結果');

INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'restaurant_inspections',
    ARRAY['#4FC3F7', '#EF5350'],
    ARRAY['MapLegend'],
    '家'
);

INSERT INTO public.component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES
(
    905,
    'restaurant_inspections_all',
    '全部',
    'circle',
    'geojson',
    'big',
    'static',
    '{
        "circle-color": [
            "match",
            ["get", "inspection_status"],
            "不合格", "#EF5350",
            "合格", "#4FC3F7",
            "#9E9E9E"
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 10, 0.4, 15, 1.1, 20, 1.8],
        "circle-opacity": 0.88
    }'::json,
    '[
        {"key":"restaurant_name","name":"餐廳名稱"},
        {"key":"inspection_status","name":"抽驗狀態"},
        {"key":"total_inspections","name":"抽驗筆數"},
        {"key":"failed_inspections","name":"不合格筆數"},
        {"key":"inspection_address","name":"抽驗地點"},
        {"key":"source_city","name":"來源縣市"},
        {"key":"source_years","name":"來源年份"},
        {"key":"sample_names","name":"檢體名稱"},
        {"key":"noncompliance_reasons","name":"不符合規定原因"}
    ]'::json
),
(
    906,
    'restaurant_inspections_failed',
    '不合格',
    'circle',
    'geojson',
    'big',
    NULL,
    '{
        "circle-color": "#EF5350",
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 10, 0.5, 15, 1.3, 20, 2],
        "circle-opacity": 0.92
    }'::json,
    '[
        {"key":"restaurant_name","name":"餐廳名稱"},
        {"key":"inspection_status","name":"抽驗狀態"},
        {"key":"total_inspections","name":"抽驗筆數"},
        {"key":"failed_inspections","name":"不合格筆數"},
        {"key":"inspection_address","name":"抽驗地點"},
        {"key":"source_city","name":"來源縣市"},
        {"key":"source_years","name":"來源年份"},
        {"key":"sample_names","name":"檢體名稱"},
        {"key":"noncompliance_reasons","name":"不符合規定原因"}
    ]'::json
);

INSERT INTO public.query_charts (
    index,
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
SELECT
    'restaurant_inspections',
    NULL::json,
    ARRAY[905, 906],
    '{"mode":"byLayer"}'::json,
    NULL,
    NULL,
    0,
    'static',
    'CSV 匯入',
    '餐廳抽驗結果點位',
    '依 CSV 匯入資料彙整餐廳抽驗結果，地圖可切換全部餐廳與不合格餐廳。',
    '掌握餐廳抽驗合格與不合格點位分布。',
    ARRAY[]::text[],
    ARRAY[]::text[],
    NOW(),
    NOW(),
    'map_legend',
    $query$
        SELECT '全部' AS name, 'circle' AS type, '' AS icon, COUNT(*)::float AS value
        FROM public.restaurant_inspection_locations
        UNION ALL
        SELECT '不合格' AS name, 'circle' AS type, '' AS icon, COUNT(*)::float AS value
        FROM public.restaurant_inspection_locations
        WHERE inspection_status = '不合格'
    $query$,
    NULL,
    city
FROM (VALUES ('taipei'), ('metrotaipei')) AS cities(city);

INSERT INTO public.dashboards (index, name, components, icon, created_at, updated_at)
VALUES (
    'restaurant_inspections_map',
    '餐廳抽驗結果',
    ARRAY[903],
    'restaurant',
    NOW(),
    NOW()
);

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
SELECT d.id, g.id
FROM public.dashboards d
CROSS JOIN public.groups g
WHERE d.index = 'restaurant_inspections_map'
  AND g.name IN ('taipei', 'metrotaipei');

SELECT setval('components_id_seq', (SELECT MAX(id) FROM public.components));
SELECT setval('component_maps_id_seq', (SELECT MAX(id) FROM public.component_maps));

COMMIT;
