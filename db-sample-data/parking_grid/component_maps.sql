DELETE FROM component_maps WHERE index = 'parking_grid_tpe';
DELETE FROM component_maps WHERE index = 'parking_grid_new_tpe';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	8,
	'parking_grid_tpe',
	'停車格',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#ff3f66'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'name', 'name', '名稱'),
		JSONB_BUILD_OBJECT('key', 'address', 'name', '地址'),
		JSONB_BUILD_OBJECT('key', 'tel', 'name', '電話'),
		JSONB_BUILD_OBJECT('key', 'room_count', 'name', '房間數'),
		JSONB_BUILD_OBJECT('key', 'price_min', 'name', '最低價'),
		JSONB_BUILD_OBJECT('key', 'price_max', 'name', '最高價')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	9,
	'parking_grid_new_tpe',
	'停車格',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#ff3f66'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'name', 'name', '名稱'),
		JSONB_BUILD_OBJECT('key', 'address', 'name', '地址'),
		JSONB_BUILD_OBJECT('key', 'tel', 'name', '電話'),
		JSONB_BUILD_OBJECT('key', 'room_count', 'name', '房間數'),
		JSONB_BUILD_OBJECT('key', 'price_min', 'name', '最低價'),
		JSONB_BUILD_OBJECT('key', 'price_max', 'name', '最高價')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;