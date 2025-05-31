DELETE FROM query_charts WHERE index = 'parking_grid';

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'parking_grid', 
	ARRAY[6],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', 'district',
			'yParam', 'pktype'
		)
	),
    'static', 
    '交通局停管處', 
    '臺北市各行政區停車格', 
    '臺北市停車格分佈資料涵蓋停車格類型、行政區等欄位，停車格類型包含機車停車位、汽車停車位、時段性禁停停車位、身心障礙專用停車位等多元類別，反映了都市交通管理的複雜需求與精細化程度。透過精確的經緯度座標資訊，每個停車格都能在地圖上準確定位，便於進行空間分析與視覺化呈現。', 
    '以信義區為例，假設該區域因為新開幕的大型購物中心而帶動龐大人潮。週末時分，大量民眾開車前往購物，但對於停車資訊一無所知。此時，停車格分佈資料就發揮了關鍵作用。商場管理業者可以利用這份資料，在官網上建置「購物停車指南」，清楚標示周邊500公尺內有多少個汽車停車格、機車停車格的分佈位置。民眾出發前就能透過地圖篩選功能，預先了解目的地附近的停車選擇，避免在商圈內繞圈找車位的困擾。同時，當地區公所也能運用統計分析功能，發現信義區因為商圈發達，停車需求遠超過現有供給。透過比較信義區與其他行政區的停車格密度差異，可以向市政府提出增設停車格或建置立體停車場的政策建議，有效紓解商圈停車壓力，提升民眾購物體驗，進而促進商圈持續發展。', 
    ARRAY['https://data.taipei/dataset/detail?id=5a911ea5-1694-4301-808e-e1780d971611'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'three_d', 
	$$
	SELECT
		x_axis, y_axis, data
	FROM
	(
		SELECT
			district AS x_axis,
			pktype AS y_axis,
			COUNT(*)::numeric AS data
		FROM parking_grid_tpe
		GROUP BY
			district, pktype
	) AS d
	ORDER BY 
	ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區'], d.x_axis);
	$$,
    'taipei'
);

SELECT * FROM query_charts ORDER BY index ASC;

INSERT INTO query_charts (index, map_config_ids, map_filter, time_from, source, short_desc, long_desc, use_case, links, created_at, updated_at, query_type, query_chart, city)
VALUES (
    'parking_grid', 
	ARRAY[6,7],
	JSONB_BUILD_OBJECT(
		'mode', 'byParam',
		'byParam', JSONB_BUILD_OBJECT(
			'xParam', 'district',
			'yParam', 'pktype'
		)
	),
    'static', 
    '交通局停管處,新北市政府交通局', 
    '雙北各行政區停車格', 
    '雙北停車格分佈資料涵蓋停車格類型、行政區等欄位，停車格類型包含機車停車位、汽車停車位、時段性禁停停車位、身心障礙專用停車位等多元類別，反映了都市交通管理的複雜需求與精細化程度。透過精確的經緯度座標資訊，每個停車格都能在地圖上準確定位，便於進行空間分析與視覺化呈現。', 
    '以信義區為例，假設該區域因為新開幕的大型購物中心而帶動龐大人潮。週末時分，大量民眾開車前往購物，但對於停車資訊一無所知。此時，停車格分佈資料就發揮了關鍵作用。商場管理業者可以利用這份資料，在官網上建置「購物停車指南」，清楚標示周邊500公尺內有多少個汽車停車格、機車停車格的分佈位置。民眾出發前就能透過地圖篩選功能，預先了解目的地附近的停車選擇，避免在商圈內繞圈找車位的困擾。同時，當地區公所也能運用統計分析功能，發現信義區因為商圈發達，停車需求遠超過現有供給。透過比較信義區與其他行政區的停車格密度差異，可以向市政府提出增設停車格或建置立體停車場的政策建議，有效紓解商圈停車壓力，提升民眾購物體驗，進而促進商圈持續發展。', 
    ARRAY['https://data.taipei/dataset/detail?id=5a911ea5-1694-4301-808e-e1780d971611','https://data.ntpc.gov.tw/datasets/54a507c4-c038-41b5-bf60-bbecb9d052c6'], 
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP, 
    'three_d', 
	$$
	SELECT
		x_axis, y_axis, data
	FROM
	(
		SELECT
			district AS x_axis,
			pktype AS y_axis,
			COUNT(*)::numeric AS data
		FROM parking_grid_tpe
		GROUP BY
			district, pktype
		UNION
		SELECT
			district AS x_axis,
			pktype AS y_axis,
			COUNT(*)::numeric AS data
		FROM parking_grid_new_tpe
		GROUP BY
			district, pktype
	) AS d
	ORDER BY 
	ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區', '新莊區', '淡水區', '汐止區', '板橋區', '三重區', '樹林區', '土城區', '蘆洲區', '中和區', '永和區', '新店區', '鶯歌區', '三峽區', '瑞芳區', '五股區', '泰山區', '林口區', '深坑區', '石碇區', '坪林區', '三芝區', '石門區', '八里區', '平溪區', '雙溪區', '貢寮區', '金山區', '萬里區', '烏來區'], d.x_axis);
	$$,
    'metrotaipei'
);

SELECT * FROM query_charts ORDER BY index ASC;