DELETE FROM query_charts WHERE index = 'ecofriendly_restaurant';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'ecofriendly_restaurant', 
	ARRAY[10],
	JSONB_BUILD_OBJECT(),
    'static', 
    '環保局', 
    '具環保理念的臺北餐廳基本資訊', 
    '環保餐廳資料是一個專門蒐集具有環保意識餐飲業者的基礎資訊資料集(包含餐廳名稱、營業地址及聯絡電話)。這些餐廳通常具備減塑、使用在地食材、節能減碳、廢棄物減量等環境友善特色，代表了餐飲業朝向永續經營發展的重要趨勢。', 
    '資料內容包含三個核心欄位：餐廳名稱、營業地址及聯絡電話。透過餐廳名稱可識別各環保餐廳的品牌特色，地址資訊有助於了解環保餐廳的地理分佈情況，而聯絡電話則提供消費者直接聯繫的管道。', 
    ARRAY['https://data.taipei/dataset/detail?id=845818d9-c432-44b4-85dd-03d71bd867b2'], 
    ARRAY['doit'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'map_legend', 
	$$SELECT unnest(array['環保餐廳']) as name, 'circle' as type$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'ecofriendly_restaurant', 
	ARRAY[10,11],
	JSONB_BUILD_OBJECT(),
    'static', 
    '環保局,新北市政府環境保護局', 
    '具環保理念的雙北餐廳基本資訊', 
    '環保餐廳資料是一個專門蒐集具有環保意識餐飲業者的基礎資訊資料集(包含餐廳名稱、營業地址及聯絡電話)。這些餐廳通常具備減塑、使用在地食材、節能減碳、廢棄物減量等環境友善特色，代表了餐飲業朝向永續經營發展的重要趨勢。', 
    '資料內容包含三個核心欄位：餐廳名稱、營業地址及聯絡電話。透過餐廳名稱可識別各環保餐廳的品牌特色，地址資訊有助於了解環保餐廳的地理分佈情況，而聯絡電話則提供消費者直接聯繫的管道。', 
    ARRAY['https://data.taipei/dataset/detail?id=845818d9-c432-44b4-85dd-03d71bd867b2','https://data.ntpc.gov.tw/datasets/e90d14f8-5995-4ebb-af19-8f8fd7d396c8'], 
    ARRAY['doit','ntpc'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'map_legend', 
	$$SELECT unnest(array['環保餐廳']) as name, 'circle' as type$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;