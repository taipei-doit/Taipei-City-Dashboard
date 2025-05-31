DELETE FROM component_maps WHERE index = 'tourist_spot_tpe';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	30,
	'tourist_spot_tpe',
	'商圈景點遊客',
	'circle',
	'geojson',
	'big',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#abcd00'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'scenicspot', 'name', '景點名稱'),
		JSONB_BUILD_OBJECT('key', 'visits', 'name', '訪客人次'),
		JSONB_BUILD_OBJECT('key', '行政區', 'name', '行政區'),
		JSONB_BUILD_OBJECT('key', '地址', 'name', '地址')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;



DELETE FROM component_maps WHERE index = 'tourist_spot_metrotaipei';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	31,
	'tourist_spot_metrotaipei',
	'商圈景點遊客',
	'circle',
	'geojson',
	'big',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#abcd00'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'scenicspot', 'name', '景點名稱'),
		JSONB_BUILD_OBJECT('key', 'visits', 'name', '訪客人次'),
		JSONB_BUILD_OBJECT('key', '行政區', 'name', '行政區'),
		JSONB_BUILD_OBJECT('key', '地址', 'name', '地址')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;