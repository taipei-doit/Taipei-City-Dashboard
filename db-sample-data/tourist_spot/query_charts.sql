DELETE FROM query_charts WHERE index = 'tourist_spot';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'tourist_spot', 
	ARRAY[30],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', '行政區'
		)
	),
    'static', 
    '主計處', 
    '臺北市觀光遊憩統計資料', 
    '呈現臺北市觀光最新一年度遊憩資料，原始資料包括統計期、國立故宮博物院遊客人次、市立美術館遊客人次、國民革命忠烈祠遊客人次、國立歷史博物館遊客人次、國立臺灣科學教育館遊客人次、國立臺灣藝術教育館遊客人次、市立動物園遊客人次、市立兒童新樂園遊客人次、市立天文科學教育館遊客人次、兒童交通博物館遊客人次、客家文化主題公園遊客人次、小巨蛋遊客人次、青年局場館遊客人次、國立國父紀念館遊客人次、士林官邸公園遊客人次、林安泰古厝民俗文物館遊客人次、順益臺灣原住民博物館遊客人次、陽明公園[陽明山]遊客人次、二二八紀念館遊客人次、國立中正紀念堂遊客人次、臺北自來水園區遊客人次、龍山寺遊客人次、關渡自然公園遊客人次、台北當代藝術館遊客人次、北投溫泉博物館遊客人次、林語堂故居遊客人次、圓山別莊遊客人次、台北探索館遊客人次、凱達格蘭文化館遊客人次、台北101遊客人次、美麗華百樂園摩天輪遊客人次、臺北市孔廟遊客人次、梅庭遊客人次、大龍峒保安宮遊客人次、台北霞海城隍廟遊客人次、臺北流行音樂中心遊客人次、臺北表演藝術中心遊客人次、西門紅樓遊客人次、草山行館遊客人次、寶藏巖遊客人次、芝山文化生態綠園遊客人次、西門町商圈遊客人次、松山文創園區遊客人次、華山1914文化創意產業園區遊客人次、台北植物園遊客人次', 
    '可用於評估觀光熱點，以利政府官員調整觀光資源分配和基礎設施建置；另外也方便民眾根據本圖資訊發掘觀光熱點安排旅遊景點', 
    ARRAY['https://data.taipei/dataset/detail?id=1ddeff62-8872-441c-aaf2-10fd0515ddb1'], 
    ARRAY[''], 
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
		SUM(visits)::numeric AS data
	FROM tourist_spot_tpe
	GROUP BY
		行政區
) AS d
ORDER BY 
	ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區'], d.x_axis);
	$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;




INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'tourist_spot', 
	ARRAY[30, 31],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', '行政區'
		)
	),
    'static', 
    '主計處、新北市政府觀光旅遊局', 
    '雙北觀光遊憩統計資料', 
    '呈現雙北觀光最新一年度遊憩資料，原始資料包含景點和時間序列資料', 
    '可用於評估觀光熱點，以利政府調整觀光資源分配和基礎設施建置；另外也方便民眾根據本圖資訊發掘觀光熱點安排旅遊景點', 
    ARRAY['https://data.taipei/dataset/detail?id=a835f3ba-7f50-4b0d-91a6-9df128632d1c'], 
    ARRAY[''], 
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
			SUM(visits)::numeric AS data
		FROM tourist_spot_metrotaipei
		GROUP BY
			行政區
	) AS d
ORDER BY 
	ARRAY_POSITION(ARRAY[ '北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區', '新莊區', '淡水區', '汐止區', '板橋區', '三重區', '樹林區', '土城區', '蘆洲區', '中和區', '永和區', '新店區', '鶯歌區', '三峽區', '瑞芳區', '五股區', '泰山區', '林口區', '深坑區', '石碇區', '坪林區', '三芝區', '石門區', '八里區', '平溪區', '雙溪區', '貢寮區', '金山區', '萬里區', '烏來區'], d.x_axis);
	$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;