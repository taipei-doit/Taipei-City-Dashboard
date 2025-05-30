DELETE FROM query_charts WHERE index = 'garbage_can';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'garbage_can', 
	ARRAY[6],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', '行政區'
		)
	),
    'static', 
    '環保局', 
    '顯示臺北市行人專用清潔箱分佈', 
    '臺北市各行政區的行人專用清潔箱分佈多寡...', 
    '使用場景說明...', 
    ARRAY['https://data.taipei/dataset/detail?id=a835f3ba-7f50-4b0d-91a6-9df128632d1c'], 
    ARRAY['doit'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'two_d', 
	$$
	SELECT
		x_axis, data
	FROM
	(
		SELECT
			行政區 AS x_axis,
			COUNT(*)::numeric AS data
		FROM garbage_can_tpe
		GROUP BY
			行政區
	) AS d
ORDER BY 
	ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區'], d.x_axis);
	$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;