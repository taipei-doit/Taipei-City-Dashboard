CREATE TABLE IF NOT EXISTS public.water_quality_realtime (
    data_time timestamp with time zone,
    station_id text,
    station_name text,
    lng double precision,
    lat double precision,
    turbidity_ntu double precision,
    residual_chlorine_mg_l double precision,
    ph double precision,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.water_quality_realtime_history (
    data_time timestamp with time zone,
    station_id text,
    station_name text,
    lng double precision,
    lat double precision,
    turbidity_ntu double precision,
    residual_chlorine_mg_l double precision,
    ph double precision,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS water_quality_realtime_wkb_geometry_idx
    ON public.water_quality_realtime USING gist (wkb_geometry);

CREATE INDEX IF NOT EXISTS water_quality_realtime_history_data_time_idx
    ON public.water_quality_realtime_history (data_time);

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

INSERT INTO public.components ("index", name)
VALUES ('water_quality_realtime', '即時水質監測')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'water_quality_realtime',
    ARRAY['#24B0DD', '#56B96D', '#F8CF58'],
    ARRAY['WaterQualityChart'],
    ''
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps WHERE "index" = 'water_quality_realtime';

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES (
    'water_quality_realtime',
    '水質監測站',
    'circle',
    'api',
    NULL,
    NULL,
    '{"circle-radius":["interpolate",["linear"],["zoom"],10,["interpolate",["linear"],["to-number",["get","turbidity_ntu"]],0,3,0.1,5,0.5,8,1,11],15,["interpolate",["linear"],["to-number",["get","turbidity_ntu"]],0,5,0.1,8,0.5,13,1,18]],"circle-color":["interpolate",["linear"],["to-number",["get","residual_chlorine_mg_l"]],0,"#ED6A45",0.2,"#F8CF58",0.5,"#56B96D",1,"#24B0DD"],"circle-opacity":0.86,"circle-stroke-color":"#ffffff","circle-stroke-width":1}',
    '[{"key":"station_name","name":"監測站"},{"key":"station_id","name":"站點代碼"},{"key":"data_time","name":"資料時間"},{"key":"turbidity_ntu","name":"濁度(NTU)"},{"key":"residual_chlorine_mg_l","name":"餘氯(mg/L)"},{"key":"ph","name":"pH值"}]'
);

DELETE FROM public.query_charts
WHERE "index" = 'water_quality_realtime' AND city = 'taipei';

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
    'water_quality_realtime',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'water_quality_realtime' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byLayer"}',
    'current',
    NULL,
    30,
    'minute',
    '臺北自來水事業處',
    '顯示臺北市即時水質監測站的 pH、濁度與餘氯資料。',
    '臺北自來水事業處即時水質資料包含各監測站位置、更新時間、濁度、餘氯及 pH 值，可用於掌握供水水質狀態與空間分布。',
    '可用於水質監測、民生供水狀態檢視與跨圖層疊合分析，協助判讀不同區域監測站的即時水質表現。',
    ARRAY['https://twd.water.gov.taipei/opendata/wqb/wqb.asmx/GetQualityData'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT x_axis, ROUND(AVG(data)::numeric, 2)::float AS data
FROM (
    SELECT ''濁度(NTU)'' AS x_axis, turbidity_ntu AS data FROM public.water_quality_realtime
    UNION ALL
    SELECT ''餘氯(mg/L)'' AS x_axis, residual_chlorine_mg_l AS data FROM public.water_quality_realtime
    UNION ALL
    SELECT ''pH值'' AS x_axis, ph AS data FROM public.water_quality_realtime
) d
GROUP BY x_axis
ORDER BY x_axis',
    'SELECT date_trunc(''%s'', data_time) AS x_axis, y_axis, ROUND(AVG(data)::numeric, 2)::float AS data
FROM (
    SELECT data_time, ''濁度(NTU)'' AS y_axis, turbidity_ntu AS data FROM public.water_quality_realtime_history
    UNION ALL
    SELECT data_time, ''餘氯(mg/L)'' AS y_axis, residual_chlorine_mg_l AS data FROM public.water_quality_realtime_history
    UNION ALL
    SELECT data_time, ''pH值'' AS y_axis, ph AS data FROM public.water_quality_realtime_history
) d
WHERE data_time BETWEEN ''%s'' AND ''%s''
GROUP BY x_axis, y_axis
ORDER BY x_axis, y_axis',
    'taipei'
);

INSERT INTO public.dashboards ("index", name, components, icon, created_at, updated_at)
VALUES (
    'water-quality-taipei',
    '水質監測',
    ARRAY[(SELECT id FROM public.components WHERE "index" = 'water_quality_realtime')],
    'water_drop',
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
WHERE d."index" = 'water-quality-taipei'
ON CONFLICT DO NOTHING;
