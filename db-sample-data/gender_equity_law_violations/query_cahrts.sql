DELETE FROM query_charts WHERE index = 'gender_equity_law_violations';

INSERT INTO query_charts (index, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'gender_equity_law_violations', 
    'static', 
    '勞動局', 
    '顯示臺北歷年違反性平法的雇主數量', 
    '臺北市每一年分別有多少雇主違反性平法...', 
    '使用場景說明...', 
    ARRAY['https://data.taipei/dataset/detail?id=12f3421a-94f4-4a5e-8642-143dee2fa551'], 
    ARRAY['doit'], 
    '2025-05-07 07:35:00+00', 
    '2025-05-07 07:35:00+00', 
    'time', 
$$
SELECT
	TO_TIMESTAMP(x_axis::text, 'YYYY') AT TIME ZONE 'Asia/Taipei' AS x_axis, data
FROM (
	SELECT
		SUBSTRING(處分日期::text, 1, 3)::integer + 1911 AS x_axis,
		COUNT(*) AS data
	FROM 
		gender_equity_law_tpe
	WHERE 
    	處分日期 != '無' AND 處分日期 IS NOT NULL
	GROUP BY
        SUBSTRING(處分日期::text, 1, 3)::integer
) d
ORDER BY
    1;
$$,
    'taipei'
);

INSERT INTO query_charts (index, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'gender_equity_law_violations', 
    'static', 
    '勞動局', 
    '顯示雙北歷年違反性平法的雇主數量', 
    '雙北每一年分別有多少雇主違反性平法...', 
    '使用場景說明...', 
    ARRAY['https://data.taipei/dataset/detail?id=12f3421a-94f4-4a5e-8642-143dee2fa551', 'https://data.ntpc.gov.tw/datasets/d7b245c0-0ba7-4ee9-9021-5ca27ac52eb4'], 
    ARRAY['doit', 'ntpc'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'time', 
$$
SELECT
	TO_TIMESTAMP(x_axis::text, 'YYYY') AT TIME ZONE 'Asia/Taipei' AS x_axis,
    SUM(data) AS data
FROM (
    SELECT
        SUBSTRING(處分日期::text, 1, 3)::integer + 1911 AS x_axis,
        COUNT(*) AS data
    FROM
        gender_equity_law_tpe
    WHERE
        處分日期 != '無' AND 處分日期 IS NOT NULL
    GROUP BY
        SUBSTRING(處分日期::text, 1, 3)::integer
    
    UNION ALL
    
    SELECT
        SUBSTRING(dt::text, 1, 4)::integer AS x_axis,
        COUNT(*) AS data
    FROM
        gender_equity_law_new_tpe
    WHERE
        dt != '無' AND dt IS NOT NULL
    GROUP BY
        SUBSTRING(dt::text, 1, 4)::integer
) d
GROUP BY
    x_axis
ORDER BY
    1;
$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;