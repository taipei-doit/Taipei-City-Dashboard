CREATE TABLE IF NOT EXISTS public.drinking_fountain (
    data_time timestamp with time zone,
    source_id integer,
    fountain_id text,
    branch text,
    city text,
    place_type text,
    place_subtype text,
    owner_unit text,
    place_name text,
    address text,
    district text,
    maintenance_unit text,
    phone text,
    open_time text,
    install_location text,
    lng double precision,
    lat double precision,
    status text,
    status_updated_at timestamp with time zone,
    latest_sampled_at timestamp with time zone,
    e_coli_count text,
    quality_info_url text,
    photo_url text,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.drinking_fountain_history (
    data_time timestamp with time zone,
    source_id integer,
    fountain_id text,
    branch text,
    city text,
    place_type text,
    place_subtype text,
    owner_unit text,
    place_name text,
    address text,
    district text,
    maintenance_unit text,
    phone text,
    open_time text,
    install_location text,
    lng double precision,
    lat double precision,
    status text,
    status_updated_at timestamp with time zone,
    latest_sampled_at timestamp with time zone,
    e_coli_count text,
    quality_info_url text,
    photo_url text,
    wkb_geometry geometry(Point,4326),
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS drinking_fountain_wkb_geometry_idx
    ON public.drinking_fountain USING gist (wkb_geometry);

CREATE INDEX IF NOT EXISTS drinking_fountain_history_data_time_idx
    ON public.drinking_fountain_history (data_time);

CREATE OR REPLACE VIEW public.drinking_fountain_taipei AS
SELECT *
FROM public.drinking_fountain
WHERE city = '臺北市';

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

INSERT INTO public.components ("index", name)
VALUES ('drinking_fountain', '直飲臺')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'drinking_fountain',
    ARRAY['#56B96D', '#F8CF58', '#ED6A45', '#24B0DD'],
    ARRAY['BarChart', 'ColumnChart'],
    '座'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps WHERE "index" IN ('drinking_fountain', 'drinking_fountain_taipei');

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES
(
    'drinking_fountain_taipei',
    '直飲臺',
    'circle',
    'api',
    'big',
    NULL,
    '{"circle-color":["match",["get","status"],"正常","#56B96D","暫停","#ED6A45","暫停使用","#ED6A45","維修中","#F8CF58","#24B0DD"],"circle-opacity":0.82,"circle-stroke-color":"#ffffff","circle-stroke-width":1}',
    '[{"key":"place_name","name":"場所名稱"},{"key":"fountain_id","name":"直飲臺編號"},{"key":"status","name":"狀態"},{"key":"city","name":"市別"},{"key":"district","name":"行政區"},{"key":"place_type","name":"場所別"},{"key":"address","name":"地址"},{"key":"open_time","name":"開放時間"},{"key":"latest_sampled_at","name":"最近採樣時間"},{"key":"e_coli_count","name":"大腸桿菌數"},{"key":"quality_info_url","name":"水質及維護資訊"}]'
),
(
    'drinking_fountain',
    '直飲臺',
    'circle',
    'api',
    'big',
    NULL,
    '{"circle-color":["match",["get","status"],"正常","#56B96D","暫停","#ED6A45","暫停使用","#ED6A45","維修中","#F8CF58","#24B0DD"],"circle-opacity":0.82,"circle-stroke-color":"#ffffff","circle-stroke-width":1}',
    '[{"key":"place_name","name":"場所名稱"},{"key":"fountain_id","name":"直飲臺編號"},{"key":"status","name":"狀態"},{"key":"city","name":"市別"},{"key":"district","name":"行政區"},{"key":"place_type","name":"場所別"},{"key":"address","name":"地址"},{"key":"open_time","name":"開放時間"},{"key":"latest_sampled_at","name":"最近採樣時間"},{"key":"e_coli_count","name":"大腸桿菌數"},{"key":"quality_info_url","name":"水質及維護資訊"}]'
);

DELETE FROM public.query_charts
WHERE "index" = 'drinking_fountain' AND city IN ('taipei', 'metrotaipei');

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
    'drinking_fountain',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'drinking_fountain_taipei' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"status"}}',
    'current',
    NULL,
    1,
    'day',
    '臺北自來水事業處',
    '顯示臺北市直飲臺分布與目前使用狀態。',
    '直飲臺資料包含位置、場所類型、開放時間、維護狀態、最近採樣時間與水質維護連結，可用於掌握公共飲水設施分布與營運狀態。',
    '可用於公共服務設施盤點、場所類型分析與民眾飲水便利性檢視，也可與人口、交通、觀光或熱點圖層套疊評估服務覆蓋。',
    ARRAY['https://data.taipei/dataset/detail?id=181097e0-c171-4bcd-ad41-c7b55dbc616e'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT status AS x_axis, COUNT(*)::float AS data
FROM public.drinking_fountain
WHERE city = ''臺北市''
GROUP BY status
ORDER BY data DESC',
    NULL,
    'taipei'
),
(
    'drinking_fountain',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'drinking_fountain' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"status"}}',
    'current',
    NULL,
    1,
    'day',
    '臺北自來水事業處',
    '顯示臺北市與新北市直飲臺分布與目前使用狀態。',
    '直飲臺資料包含位置、場所類型、開放時間、維護狀態、最近採樣時間與水質維護連結，可用於掌握公共飲水設施分布與營運狀態。',
    '可用於公共服務設施盤點、場所類型分析與民眾飲水便利性檢視，也可與人口、交通、觀光或熱點圖層套疊評估服務覆蓋。',
    ARRAY['https://data.taipei/dataset/detail?id=181097e0-c171-4bcd-ad41-c7b55dbc616e'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT status AS x_axis, COUNT(*)::float AS data
FROM public.drinking_fountain
GROUP BY status
ORDER BY data DESC',
    NULL,
    'metrotaipei'
);

UPDATE public.dashboards
SET components = ARRAY[
        (SELECT id FROM public.components WHERE "index" = 'water_quality_realtime'),
        (SELECT id FROM public.components WHERE "index" = 'drinking_fountain')
    ],
    updated_at = NOW()
WHERE "index" = 'water-quality-taipei';
