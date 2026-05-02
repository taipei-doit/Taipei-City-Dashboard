-- =====================================================
-- 登革熱確定病例統計 (dengue_confirmed_cases) - 資料表與組件配置
-- =====================================================

-- 資料表
CREATE TABLE IF NOT EXISTS public.dengue_confirmed_cases (
    onset_date text,
    diagnosis_date text,
    report_date text,
    gender text,
    age_group text,
    residence_city text,
    residence_district text,
    residence_village text,
    is_imported text,
    infection_country text,
    confirmed_cases integer,
    serotype text,
    lng double precision,
    lat double precision,
    wkb_geometry geometry(Point, 4326),
    data_time timestamp with time zone,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS dengue_confirmed_cases_wkb_geometry_idx
    ON public.dengue_confirmed_cases USING gist (wkb_geometry);

CREATE INDEX IF NOT EXISTS dengue_confirmed_cases_diagnosis_date_idx
    ON public.dengue_confirmed_cases (diagnosis_date);

-- =====================================================
-- 組件配置 (Manager DB)
-- =====================================================

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);

INSERT INTO public.components ("index", name)
VALUES ('dengue_confirmed_cases', '登革熱確定病例統計')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'dengue_confirmed_cases',
    ARRAY['#ED6A45', '#F8CF58', '#56B96D', '#24B0DD', '#E170A6', '#AF4137'],
    ARRAY['TimelineSeparateChart', 'BarChart'],
    '例'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.component_maps
WHERE "index" = 'dengue_confirmed_cases';

INSERT INTO public.component_maps ("index", title, type, source, size, icon, paint, property)
VALUES
(
    'dengue_confirmed_cases',
    '登革熱確定病例',
    'circle',
    'api',
    NULL,
    NULL,
    '{"circle-radius":["interpolate",["exponential",2],["zoom"],10,3.5,12,14,14,56,16,224],"circle-color":["match",["get","is_imported"],"是","#24B0DD","否","#ED6A45","#F8CF58"],"circle-opacity":0.4,"circle-stroke-color":"#ffffff","circle-stroke-width":1}',
    '[{"key":"diagnosis_date","name":"研判日期"},{"key":"onset_date","name":"發病日"},{"key":"residence_district","name":"居住區域"},{"key":"age_group","name":"年齡層"},{"key":"gender","name":"性別"},{"key":"is_imported","name":"境外移入"},{"key":"infection_country","name":"感染國家"},{"key":"serotype","name":"血清型"}]'
);

DELETE FROM public.query_charts
WHERE "index" = 'dengue_confirmed_cases' AND city = 'taipei';

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
    'dengue_confirmed_cases',
    NULL,
    ARRAY[(SELECT id FROM public.component_maps WHERE "index" = 'dengue_confirmed_cases' ORDER BY id DESC LIMIT 1)],
    '{"mode":"byParam","byParam":{"xParam":"is_imported"}}',
    'static',
    NULL,
    1,
    'day',
    '疾病管制署',
    '顯示臺北市登革熱確定病例分布與月份趨勢。',
    '登革熱確定病例統計資料來自疾病管制署開放資料，包含發病日、個案研判日、居住地區、年齡層、性別、是否境外移入、感染國家及血清型等資訊。透過地圖可檢視病例空間分布，圖表則呈現各月份確診案例數量趨勢，有助於掌握疫情時空變化。',
    '可用於疫情監測、公共衛生分析與防疫資源配置。透過病例分布與時間趨勢，可識別高風險區域與季節性模式，作為病媒蚊防治與衛教宣導之參考依據。',
    ARRAY['https://od.cdc.gov.tw/eic/Dengue_Daily.json'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'time',
    'SELECT
        DATE_TRUNC(''month'', TO_DATE(diagnosis_date, ''YYYY/MM/DD'')) AS x_axis,
        SUM(confirmed_cases)::float AS data
    FROM public.dengue_confirmed_cases
    WHERE diagnosis_date IS NOT NULL AND diagnosis_date != ''''
    GROUP BY DATE_TRUNC(''month'', TO_DATE(diagnosis_date, ''YYYY/MM/DD''))
    ORDER BY x_axis',
    NULL,
    'taipei'
);

-- 將組件加入儀表板 (假設有一個健康相關儀表板，這裡示範新增)
-- 如需加入現有儀表板，請依據實際需求調整

SELECT setval('public.component_maps_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.component_maps), true);
