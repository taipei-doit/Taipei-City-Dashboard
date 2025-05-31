DO $$
DECLARE
    target_index text := 'uv';
BEGIN
    DELETE FROM public.query_charts
  	WHERE index LIKE '%' || target_index || '%';

	DELETE FROM public.component_maps
  	WHERE index LIKE '%' || target_index || '%';

    DELETE FROM public.component_charts
  	WHERE index LIKE '%' || target_index || '%';

    DELETE FROM public.components
  	WHERE index LIKE '%' || target_index || '%';
END $$;

-- Root: components
INSERT INTO
    public.components (id, index, name)
VALUES (2487, 'uv', '紫外線');

-- component_charts
INSERT INTO public.component_charts (index, color, types, unit) 
VALUES ('uv',ARRAY['#24B0DD','#56B96D','#F8CF58','#F5AD4A','#E170A6','#ED6A45','#AF4137','#10294A']::text[],'{ColumnChart,DistrictChart,PolarAreaChart}', '指數');

-- component_maps
-- no map
INSERT INTO
    public.component_maps (
		id,
        index,
        title,
        type,
        source,
        size,
        icon,
        paint,
        property
    )
VALUES (
		-- AUTO INCREMENT IDENTIFIED
		nextval('component_maps_id_seq'),
        'uv_taipei',
        '紫外線',
        'circle',
        'geojson',
        'big',
        'heatmap',
        '{"circle-color":"#4CAF50","circle-radius":6,"circle-opacity":0.8,"circle-stroke-width":1,"circle-stroke-color":"#ffffff"}',
		'{}'
	),
    (
		nextval('component_maps_id_seq') + 1,
        'uv_metrotaipei',
        '紫外線',
        'circle',
        'geojson',
        'big',
        'heatmap',
        '{"circle-color":"#4CAF50","circle-radius":6,"circle-opacity":0.8,"circle-stroke-width":1,"circle-stroke-color":"#ffffff"}',
        '{}'
    );

-- query_charts
INSERT INTO
    public.query_charts (
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
VALUES (
        'uv',
        'null',
        '{}',
        '{}',
        'static',
        NULL,
        NULL,
        NULL,
        '中央氣象局',
		'紫外線分佈',
        '顯示臺北市各區的紫外線指數分布情況。',
        '適用於了解臺北市各區的紫外線指數分布情況。',
        '{https://opendata.cwb.gov.tw/}',
        '{doit}',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP,
        'three_d',
        'WITH districts AS (     SELECT unnest(ARRAY[         ''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',         ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區''     ]) AS 行政區 ), types AS (     SELECT unnest(ARRAY[''低量級'', ''中量級'', ''高量級'']) AS 類型 ), combinations AS (     SELECT d.行政區, t.類型     FROM districts d CROSS JOIN types t ), counts AS (     SELECT 行政區, 類型, COUNT(*) AS data     FROM public.uv_data     WHERE 市 IN (''臺北市'')     GROUP BY 行政區, 類型 ) SELECT      c.行政區 AS x_axis,     c.類型 AS y_axis,     COALESCE(cnt.data, 0) AS data FROM combinations c LEFT JOIN counts cnt     ON c.行政區 = cnt.行政區 AND c.類型 = cnt.類型 ORDER BY array_position(ARRAY[     ''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',     ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區'' ], c.行政區), c.類型;',
        NULL,
        'taipei'
    ),
    (
        'uv',
        'null',
        '{}',
        '{}',
        'static',
        NULL,
        NULL,
        NULL,
        '中央氣象局',
		'紫外線分佈',
        '顯示雙北市各區的紫外線指數分布情況。',
        '適用於了解雙北市各區的紫外線指數分布情況。',
		'{https://opendata.cwb.gov.tw/}',
        '{doit,ntpc}',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP,
        'three_d',
        'WITH districts AS (     SELECT unnest(ARRAY[         ''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',         ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區'',         ''新莊區'',''淡水區'',''汐止區'',''板橋區'',''三重區'',''樹林區'',         ''土城區'',''蘆洲區'',''中和區'',''永和區'',''新店區'',''鶯歌區'',         ''三峽區'',''瑞芳區'',''五股區'',''泰山區'',''林口區'',''深坑區'',         ''石碇區'',''坪林區'',''三芝區'',''石門區'',''八里區'',''平溪區'',         ''雙溪區'',''貢寮區'',''金山區'',''萬里區'',''烏來區''     ]) AS 行政區 ), types AS (     SELECT unnest(ARRAY[''低量級'', ''中量級'', ''高量級'']) AS 類型 ), combinations AS (     SELECT d.行政區, t.類型     FROM districts d CROSS JOIN types t ), counts AS (     SELECT 行政區, 類型, COUNT(*) AS data     FROM public.uv_data     WHERE 市 IN (''臺北市'', ''新北市'')     GROUP BY 行政區, 類型 ) SELECT      c.行政區 AS x_axis,     c.類型 AS y_axis,     COALESCE(cnt.data, 0) AS data FROM combinations c LEFT JOIN counts cnt     ON c.行政區 = cnt.行政區 AND c.類型 = cnt.類型 ORDER BY array_position(ARRAY[     ''北投區'',''士林區'',''內湖區'',''南港區'',''松山區'',''信義區'',     ''中山區'',''大同區'',''中正區'',''萬華區'',''大安區'',''文山區'',     ''新莊區'',''淡水區'',''汐止區'',''板橋區'',''三重區'',''樹林區'',     ''土城區'',''蘆洲區'',''中和區'',''永和區'',''新店區'',''鶯歌區'',     ''三峽區'',''瑞芳區'',''五股區'',''泰山區'',''林口區'',''深坑區'',     ''石碇區'',''坪林區'',''三芝區'',''石門區'',''八里區'',''平溪區'',     ''雙溪區'',''貢寮區'',''金山區'',''萬里區'',''烏來區'' ], c.行政區), c.類型;',
        NULL,
        'metrotaipei'
    );