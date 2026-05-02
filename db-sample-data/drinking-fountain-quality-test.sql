CREATE TABLE IF NOT EXISTS public.drinking_fountain_quality_test (
    data_time timestamp with time zone,
    sample_name text,
    fountain_id text,
    sampled_at timestamp with time zone,
    sample_date text,
    sample_time text,
    e_coli_result text,
    e_coli_numeric double precision,
    e_coli_unit text,
    standard_mpn_per_100ml integer,
    quality_status text,
    source_page integer,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.drinking_fountain_quality_test_history (
    data_time timestamp with time zone,
    sample_name text,
    fountain_id text,
    sampled_at timestamp with time zone,
    sample_date text,
    sample_time text,
    e_coli_result text,
    e_coli_numeric double precision,
    e_coli_unit text,
    standard_mpn_per_100ml integer,
    quality_status text,
    source_page integer,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS drinking_fountain_quality_test_fountain_id_idx
    ON public.drinking_fountain_quality_test (lower(fountain_id));

CREATE INDEX IF NOT EXISTS drinking_fountain_quality_test_history_fountain_id_sampled_at_idx
    ON public.drinking_fountain_quality_test_history (lower(fountain_id), sampled_at);

CREATE OR REPLACE VIEW public.drinking_fountain_with_quality AS
SELECT
    df.*,
    qt.sample_name AS quality_sample_name,
    qt.sampled_at AS latest_quality_sampled_at,
    qt.e_coli_result AS latest_e_coli_result,
    qt.e_coli_numeric AS latest_e_coli_numeric,
    qt.e_coli_unit AS latest_e_coli_unit,
    qt.standard_mpn_per_100ml,
    COALESCE(qt.quality_status, '未檢驗') AS quality_status,
    qt.source_page AS quality_source_page
FROM public.drinking_fountain df
LEFT JOIN public.drinking_fountain_quality_test qt
    ON lower(df.fountain_id) = lower(qt.fountain_id);

CREATE OR REPLACE VIEW public.drinking_fountain_with_quality_taipei AS
SELECT *
FROM public.drinking_fountain_with_quality
WHERE city = '臺北市';

UPDATE public.component_maps
SET "index" = 'drinking_fountain_with_quality_taipei',
    paint = '{"circle-color":["match",["get","quality_status"],"合格","#56B96D","不合格","#ED6A45","未檢驗","#888787","#24B0DD"],"circle-opacity":0.84,"circle-stroke-color":["match",["get","status"],"正常","#ffffff","#ED6A45"],"circle-stroke-width":["match",["get","status"],"正常",1,2]}'::json,
    property = '[{"key":"place_name","name":"場所名稱"},{"key":"fountain_id","name":"直飲臺編號"},{"key":"quality_status","name":"水質檢驗"},{"key":"latest_quality_sampled_at","name":"最近檢驗時間"},{"key":"latest_e_coli_result","name":"大腸桿菌群(MPN/100mL)"},{"key":"status","name":"設施狀態"},{"key":"city","name":"市別"},{"key":"district","name":"行政區"},{"key":"place_type","name":"場所別"},{"key":"address","name":"地址"},{"key":"open_time","name":"開放時間"},{"key":"quality_info_url","name":"水質及維護資訊"}]'::json
WHERE "index" = 'drinking_fountain_taipei';

UPDATE public.component_maps
SET "index" = 'drinking_fountain_with_quality',
    paint = '{"circle-color":["match",["get","quality_status"],"合格","#56B96D","不合格","#ED6A45","未檢驗","#888787","#24B0DD"],"circle-opacity":0.84,"circle-stroke-color":["match",["get","status"],"正常","#ffffff","#ED6A45"],"circle-stroke-width":["match",["get","status"],"正常",1,2]}'::json,
    property = '[{"key":"place_name","name":"場所名稱"},{"key":"fountain_id","name":"直飲臺編號"},{"key":"quality_status","name":"水質檢驗"},{"key":"latest_quality_sampled_at","name":"最近檢驗時間"},{"key":"latest_e_coli_result","name":"大腸桿菌群(MPN/100mL)"},{"key":"status","name":"設施狀態"},{"key":"city","name":"市別"},{"key":"district","name":"行政區"},{"key":"place_type","name":"場所別"},{"key":"address","name":"地址"},{"key":"open_time","name":"開放時間"},{"key":"quality_info_url","name":"水質及維護資訊"}]'::json
WHERE "index" = 'drinking_fountain';

UPDATE public.query_charts
SET query_chart = 'SELECT quality_status AS x_axis, COUNT(*)::float AS data
FROM public.drinking_fountain_with_quality
WHERE city = ''臺北市''
GROUP BY quality_status
ORDER BY data DESC'
WHERE "index" = 'drinking_fountain' AND city = 'taipei';

UPDATE public.query_charts
SET query_chart = 'SELECT quality_status AS x_axis, COUNT(*)::float AS data
FROM public.drinking_fountain_with_quality
GROUP BY quality_status
ORDER BY data DESC'
WHERE "index" = 'drinking_fountain' AND city = 'metrotaipei';
