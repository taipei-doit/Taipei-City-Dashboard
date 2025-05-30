DELETE FROM component_maps WHERE index = 'garbage_can_tpe';

INSERT INTO component_maps (id, index, title, type, source, icon, paint, property)
VALUES(
	6,
	'garbage_can_tpe',
	'行人專用垃圾桶',
	'symbol',
	'geojson',
	'triangle_white',
	JSONB_BUILD_OBJECT(
		'icon-color', '#8fe25f'
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', '行政區', 'name', '行政區'),
		JSONB_BUILD_OBJECT('key', '地址', 'name', '地址'),
		JSONB_BUILD_OBJECT('key', '備註', 'name', '罰則')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;