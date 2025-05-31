DELETE FROM component_maps WHERE index = 'ecofriendly_restaurant_tpe';
DELETE FROM component_maps WHERE index = 'ecofriendly_restaurant_new_tpe';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	10,
	'ecofriendly_restaurant_tpe',
	'環保餐廳',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#75373b'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'name', 'name', '名稱'),
		JSONB_BUILD_OBJECT('key', 'address', 'name', '地址'),
		JSONB_BUILD_OBJECT('key', 'tel', 'name', '電話')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	11,
	'ecofriendly_restaurant_new_tpe',
	'環保餐廳',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', '#181a80'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'name', 'name', '名稱'),
		JSONB_BUILD_OBJECT('key', 'address', 'name', '地址'),
		JSONB_BUILD_OBJECT('key', 'tel', 'name', '電話')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;