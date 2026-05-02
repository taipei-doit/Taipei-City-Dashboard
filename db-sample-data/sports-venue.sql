CREATE TABLE IF NOT EXISTS public.sports_venue (
    data_time timestamp with time zone,
    venue_id text,
    name text,
    name_eng text,
    main_name text,
    main_name_eng text,
    district text,
    district_eng text,
    is_open boolean,
    is_sports_center boolean,
    organ text,
    people_capacity double precision,
    area_sqm double precision,
    rental_status text,
    locker_rent_status text,
    sports_center_rent_url text,
    photo_url text,
    detail_url text,
    lng double precision,
    lat double precision,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS sports_venue_wkb_geometry_idx
    ON public.sports_venue USING gist (wkb_geometry);

CREATE INDEX IF NOT EXISTS sports_venue_district_idx
    ON public.sports_venue (district);

INSERT INTO public.components ("index", name)
VALUES ('sports_venue', '運動場館')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'sports_venue',
    ARRAY['#24B0DD', '#56B96D', '#F8CF58', '#ED6A45', '#8F98A3'],
    ARRAY['BarChart', 'DonutChart'],
    '處'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps WHERE "index" = 'sports_venue';

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES (
    'sports_venue',
    '運動場館',
    'circle',
    'api',
    NULL,
    NULL,
    '{
        "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            10, 3,
            14, [
                "interpolate",
                ["linear"],
                ["to-number", ["get", "people_capacity"]],
                0, 4,
                100, 5,
                500, 8,
                3000, 12
            ],
            17, [
                "interpolate",
                ["linear"],
                ["to-number", ["get", "people_capacity"]],
                0, 6,
                100, 8,
                500, 12,
                3000, 18
            ]
        ],
        "circle-color": [
            "case",
            ["==", ["get", "is_open"], true], "#24B0DD",
            "#8F98A3"
        ],
        "circle-opacity": 0.84,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1
    }'::json,
    '[
        {"key":"photo_url","name":"照片","mode":"image"},
        {"key":"name","name":"場地名稱"},
        {"key":"main_name","name":"主場館"},
        {"key":"district","name":"行政區"},
        {"key":"people_capacity","name":"容納人數"},
        {"key":"area_sqm","name":"場地面積"},
        {"key":"is_open","name":"開放狀態"},
        {"key":"locker_rent_status","name":"置物櫃租借"},
        {"key":"detail_url","name":"詳細頁面"}
    ]'::json
);

DELETE FROM public.query_charts
WHERE "index" = 'sports_venue' AND city = 'taipei';

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
    'sports_venue',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'sports_venue' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byLayer"}',
    'current',
    NULL,
    1,
    'day',
    '臺北市政府體育局',
    '顯示臺北市運動場館位置、開放狀態、容納人數與場館照片。',
    '臺北市政府體育局場地租借系統提供運動場館與可租借場地資料。本資料擷取場館列表並解析各場館頁面中的地圖座標，地圖以點位呈現，點大小依容納人數，彈窗顯示場館照片與基本資訊。',
    '可用於運動設施盤點、行政區場館供給比較、民眾查找可租借運動場地，以及與人口、交通等圖層疊合分析。',
    ARRAY['https://vbs.sports.taipei/venues/'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT COALESCE(NULLIF(district, ''''), ''未分類'') AS x_axis, COUNT(*)::float AS data FROM public.sports_venue GROUP BY x_axis ORDER BY data DESC',
    NULL,
    'taipei'
);

INSERT INTO public.dashboards ("index", name, components, icon, created_at, updated_at)
VALUES (
    'sports-venue-taipei',
    '運動場館',
    ARRAY[(SELECT id FROM public.components WHERE "index" = 'sports_venue')],
    'sports_basketball',
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
WHERE d."index" = 'sports-venue-taipei'
ON CONFLICT DO NOTHING;

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
SELECT setval('public.component_maps_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.component_maps), true);
