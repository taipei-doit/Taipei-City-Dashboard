DELETE FROM component_maps WHERE index = 'business_district_directory_tpe';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	40,
	'business_district_directory_tpe',
	'商圈理事長聯絡網絡',
	'circle',
	'geojson',
	'big',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#e08e14'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', '商圈名稱', 'name', '商圈名稱'),
		JSONB_BUILD_OBJECT('key', '分區', 'name', '行政區'),
		JSONB_BUILD_OBJECT('key', '組織或里辦公處', 'name', '組織或里辦公處'),
		JSONB_BUILD_OBJECT('key', '組織代表', 'name', '組織代表'),
		JSONB_BUILD_OBJECT('key', '職稱', 'name', '職稱'),
		JSONB_BUILD_OBJECT('key', '聯絡電話', 'name', '聯絡電話'),
		JSONB_BUILD_OBJECT('key', '商圈通訊地址', 'name', '通訊地址')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;



DELETE FROM component_maps WHERE index = 'business_district_directory_metrotaipei';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	41,
	'business_district_directory_metrotaipei',
	'商圈理事長聯絡網絡',
	'circle',
	'geojson',
	'big',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#e08e14'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', '商圈名稱', 'name', '商圈名稱'),
		JSONB_BUILD_OBJECT('key', '分區', 'name', '行政區'),
		JSONB_BUILD_OBJECT('key', '組織或里辦公處', 'name', '組織或里辦公處'),
		JSONB_BUILD_OBJECT('key', '組織代表', 'name', '組織代表'),
		JSONB_BUILD_OBJECT('key', '職稱', 'name', '職稱'),
		JSONB_BUILD_OBJECT('key', '聯絡電話', 'name', '聯絡電話'),
		JSONB_BUILD_OBJECT('key', '商圈通訊地址', 'name', '通訊地址')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;