CREATE TABLE IF NOT EXISTS public.sports_center (
    data_time timestamp with time zone,
    name text,
    postal_code text,
    address text,
    phone text,
    website text,
    location_id text,
    realtime_name text,
    sw_people_num double precision,
    sw_max_people_num double precision,
    sw_usage_rate double precision,
    gym_people_num double precision,
    gym_max_people_num double precision,
    gym_usage_rate double precision,
    lng double precision,
    lat double precision,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS sports_center_wkb_geometry_idx
    ON public.sports_center USING gist (wkb_geometry);

CREATE INDEX IF NOT EXISTS sports_center_name_idx
    ON public.sports_center (name);

INSERT INTO public.components ("index", name)
VALUES ('sports_center', '運動中心')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'sports_center',
    ARRAY['#24B0DD', '#ED6A45', '#56B96D', '#F8CF58', '#8F98A3'],
    ARRAY['BarChart', 'DonutChart'],
    '人'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps WHERE "index" = 'sports_center';

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES (
    'sports_center',
    '運動中心',
    'circle',
    'api',
    NULL,
    NULL,
    '{
        "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            10, 5,
            14, 9,
            17, 14
        ],
        "circle-color": [
            "case",
            [">=", ["coalesce", ["to-number", ["get", "gym_usage_rate"]], 0], 0.8], "#ED6A45",
            [">=", ["coalesce", ["to-number", ["get", "sw_usage_rate"]], 0], 0.8], "#F8CF58",
            "#24B0DD"
        ],
        "circle-opacity": 0.86,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1.2
    }'::json,
    '[
        {"key":"name","name":"名稱"},
        {"key":"address","name":"地址"},
        {"key":"phone","name":"電話"},
        {"key":"website","name":"網址"},
        {"key":"sw_people_num","name":"泳池目前人數"},
        {"key":"sw_max_people_num","name":"泳池容留人數"},
        {"key":"gym_people_num","name":"健身房目前人數"},
        {"key":"gym_max_people_num","name":"健身房容留人數"},
        {"key":"data_time","name":"資料時間"}
    ]'::json
);

DELETE FROM public.query_charts
WHERE "index" = 'sports_center' AND city = 'taipei';

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
VALUES (
    'sports_center',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'sports_center' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"name"}}',
    'current',
    NULL,
    10,
    'minute',
    '臺北市政府體育局、臺北市運動中心場地預約系統',
    '顯示臺北市運動中心位置，以及游泳池與健身房即時人流。',
    '本資料整合臺北市資料大平臺運動中心基本資料與運動中心場地預約系統即時人流，地圖以點位呈現運動中心位置，並依泳池或健身房高使用率標示顏色。',
    '可用於掌握各運動中心目前泳池與健身房使用狀況，輔助民眾避開尖峰時段，並支援公共運動設施營運監測。',
    ARRAY[
        'https://data.taipei/dataset/detail?id=80be7612-593f-4795-9935-a10ce0f7b75b',
        'https://booking-tpsc.sporetrofit.com/Home/LocationPeopleNum'
    ],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT name AS x_axis, (COALESCE(sw_people_num, 0) + COALESCE(gym_people_num, 0))::float AS data FROM public.sports_center ORDER BY name',
    NULL,
    'taipei'
);

INSERT INTO public.dashboards ("index", name, components, icon, created_at, updated_at)
VALUES (
    'sports-center-taipei',
    '運動中心',
    ARRAY[(SELECT id FROM public.components WHERE "index" = 'sports_center')],
    'fitness_center',
    NOW(),
    NOW()
)
ON CONFLICT ("index") DO UPDATE
SET name = EXCLUDED.name,
    components = EXCLUDED.components,
    icon = EXCLUDED.icon,
    updated_at = NOW();

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
SELECT d.id, 2
FROM public.dashboards d
WHERE d."index" = 'sports-center-taipei'
ON CONFLICT DO NOTHING;

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
SELECT setval('public.component_maps_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.component_maps), true);
