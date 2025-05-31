DELETE FROM query_charts WHERE index = 'business_district_directory';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'business_district_directory', 
	ARRAY[40],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', '分區'
		)
	),
    'static', 
    '台北市產業局商業處', 
    '臺北市商圈通訊錄', 
    '商圈通訊錄資料，提供分區、商圈名稱、組織或里辦公處、組織代表、職稱、聯絡電話、傳真、商圈通訊地址、經緯度等資訊', 
    '可用於商圈開發、維護之聯繫用', 
    ARRAY['https://data.taipei/dataset/detail?id=89f53365-ea7b-4132-b702-27b26a575b3b'], 
    ARRAY[''], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'two_d', 
	$$
SELECT
    分區 AS x_axis,
    COUNT(DISTINCT "組織或里辦公處")::numeric AS data
FROM business_district_directory_tpe
GROUP BY 分區
ORDER BY     ARRAY_POSITION(
        ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區'],
        分區
    );	
	$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;




INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'business_district_directory', 
	ARRAY[41],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', '分區'
		)
	),
    'static', 
    '台北市產業局商業處、新北市政府經濟發展局', 
    '雙北商圈通訊錄', 
    '商圈通訊錄資料，提供分區、商圈名稱、組織或里辦公處、組織代表、職稱、聯絡電話、傳真、商圈通訊地址、經緯度等資訊', 
    '可用於商圈開發、維護之聯繫用', 
    ARRAY['https://data.ntpc.gov.tw/datasets/f54ded71-eb04-466d-bb6d-dd948c8d8502'], 
    ARRAY[''], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'two_d', 
	$$
SELECT
    分區 AS x_axis,
    COUNT(DISTINCT "組織或里辦公處")::numeric AS data
FROM business_district_directory_metrotaipei
GROUP BY 分區
ORDER BY ARRAY_POSITION(
        ARRAY[ '北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區', '新莊區', '淡水區', '汐止區', '板橋區', '三重區', '樹林區', '土城區', '蘆洲區', '中和區', '永和區', '新店區', '鶯歌區', '三峽區', '瑞芳區', '五股區', '泰山區', '林口區', '深坑區', '石碇區', '坪林區', '三芝區', '石門區', '八里區', '平溪區', '雙溪區', '貢寮區', '金山區', '萬里區', '烏來區'],
        分區
    );
	$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;