UPDATE "public"."query_charts"
SET "query_type" = 'two_d',
    "query_chart" = 'SELECT
	ALL_DISTRICTS.DISTRICT AS X_AXIS,
	COALESCE(uv.avg_uvindex, 0) AS DATA
FROM (
	SELECT UNNEST(ARRAY[
        ''北投區'', ''士林區'', ''內湖區'', ''南港區'', ''松山區'', ''信義區'',
        ''中山區'', ''大同區'', ''中正區'', ''萬華區'', ''大安區'', ''文山區'',
        ''新莊區'', ''淡水區'', ''汐止區'', ''板橋區'', ''三重區'', ''樹林區'',
        ''土城區'', ''蘆洲區'', ''中和區'', ''永和區'', ''新店區'', ''鶯歌區'',
        ''三峽區'', ''瑞芳區'', ''五股區'', ''泰山區'', ''林口區'', ''深坑區'',
        ''石碇區'', ''坪林區'', ''三芝區'', ''石門區'', ''八里區'', ''平溪區'',
        ''雙溪區'', ''貢寮區'', ''金山區'', ''萬里區'', ''烏來區''
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
        ''中山區'', ''大同區'', ''中正區'', ''萬華區'', ''大安區'', ''文山區'',
        ''新莊區'', ''淡水區'', ''汐止區'', ''板橋區'', ''三重區'', ''樹林區'',
        ''土城區'', ''蘆洲區'', ''中和區'', ''永和區'', ''新店區'', ''鶯歌區'',
        ''三峽區'', ''瑞芳區'', ''五股區'', ''泰山區'', ''林口區'', ''深坑區'',
        ''石碇區'', ''坪林區'', ''三芝區'', ''石門區'', ''八里區'', ''平溪區'',
        ''雙溪區'', ''貢寮區'', ''金山區'', ''萬里區'', ''烏來區''
], ALL_DISTRICTS.DISTRICT);'
WHERE "index" = 'uv' AND "city" = 'metrotaipei';