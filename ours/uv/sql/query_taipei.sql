UPDATE "public"."query_charts" SET "query_type" = 'two_d', "query_chart" = 'SELECT
	ALL_DISTRICTS.DISTRICT AS X_AXIS,
	COALESCE(uv.avg_uvindex, 0) AS DATA
FROM (
	SELECT UNNEST(ARRAY[
		''北投區'', ''士林區'', ''內湖區'', ''南港區'', ''松山區'', ''信義區'',
		''中山區'', ''大同區'', ''中正區'', ''萬華區'', ''大安區'', ''文山區''
	]) AS DISTRICT
) ALL_DISTRICTS
LEFT JOIN (
	SELECT
		DISTRICT,
		ROUND(AVG(uvindex)::numeric, 1) AS avg_uvindex
	FROM uv
	GROUP BY DISTRICT
) uv ON ALL_DISTRICTS.DISTRICT = uv.DISTRICT
ORDER BY ARRAY_POSITION(ARRAY[
	''北投區'', ''士林區'', ''內湖區'', ''南港區'', ''松山區'', ''信義區'',
	''中山區'', ''大同區'', ''中正區'', ''萬華區'', ''大安區'', ''文山區''
], ALL_DISTRICTS.DISTRICT);' WHERE "index" = 'uv' AND "city" = 'taipei';