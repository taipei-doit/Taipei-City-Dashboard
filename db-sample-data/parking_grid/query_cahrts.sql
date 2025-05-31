DELETE FROM query_charts WHERE index = 'parking_grid';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'parking_grid', 
	ARRAY[8],
	JSONB_BUILD_OBJECT(),
    'static', 
    '觀傳局', 
    '臺北停車格業者的基本營業資訊', 
    '臺北市停車格分佈資料是一個實用的住宿業基礎資訊資料集，收錄了臺北市各行政區內旅宿業者的核心營業資料。資料內容包含六個主要欄位：旅宿名稱、營業地址、聯絡電話、房間數量、最低住宿價格及最高住宿價格', 
    '這份資料集的特色在於其資訊的實用性與完整性。透過地址資訊可了解各旅宿的地理分佈狀況，房間數量反映了各業者的營運規模，而價格區間則提供了市場定位與消費水準的重要指標。消費者可以根據預算需求快速篩選合適的住宿選項，業者則能透過價格比較了解市場競爭態勢。
此資料集適合進行住宿市場分析、價格趨勢研究、區域發展評估等應用。研究者可以透過分析房間數分佈了解各區域的住宿供給能力，透過價格資料探討不同區域的住宿成本差異，並結合地址資訊進行空間分析，了解臺北市住宿業的整體發展格局與區域特色。', 
    ARRAY['https://data.taipei/dataset/detail?id=4d7d0b46-2e90-4ee7-b000-c0f2f3a37651'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'map_legend', 
	$$SELECT unnest(array['停車格']) as name, 'circle' as type$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'parking_grid', 
	ARRAY[8,9],
	JSONB_BUILD_OBJECT(),
    'static', 
    '觀傳局,新北市政府觀光旅遊局', 
    '雙北停車格業者的基本營業資訊', 
    '雙北停車格分佈資料是一個實用的住宿業基礎資訊資料集，收錄了臺北市與新北市各行政區內旅宿業者的核心營業資料。資料內容包含六個主要欄位：旅宿名稱、營業地址、聯絡電話、房間數量、最低住宿價格及最高住宿價格', 
    '這份資料集的特色在於其資訊的實用性與完整性。透過地址資訊可了解各旅宿的地理分佈狀況，房間數量反映了各業者的營運規模，而價格區間則提供了市場定位與消費水準的重要指標。消費者可以根據預算需求快速篩選合適的住宿選項，業者則能透過價格比較了解市場競爭態勢。
此資料集適合進行住宿市場分析、價格趨勢研究、區域發展評估等應用。研究者可以透過分析房間數分佈了解各區域的住宿供給能力，透過價格資料探討不同區域的住宿成本差異，並結合地址資訊進行空間分析，了解臺北市住宿業的整體發展格局與區域特色。', 
    ARRAY['https://data.taipei/dataset/detail?id=4d7d0b46-2e90-4ee7-b000-c0f2f3a37651','https://data.ntpc.gov.tw/datasets/8565597e-a174-4907-99c7-adb5ddee1326'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'map_legend', 
	$$SELECT unnest(array['停車格']) as name, 'circle' as type$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;