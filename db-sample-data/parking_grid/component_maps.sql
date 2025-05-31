DELETE FROM component_maps WHERE index = 'parking_grid_tpe';
DELETE FROM component_maps WHERE index = 'parking_grid_new_tpe';

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	6,
	'parking_grid_tpe',
	'停車格',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', 
			JSONB_BUILD_ARRAY(
				'match',
				JSONB_BUILD_ARRAY('get', 'pktype'),
				'大型車停車位', '#090974',
				'汽車身心障礙專用', '#033E6B',
				'機車停車位', '#0C60A4',
				'時段性禁停停車位', '#4F2981',
				'汽車停車位', '#7373D8',
				'裝卸貨專用停車位', '#66A2D2',
				'#1D7370'
			)
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'pktype', 'name', '類型'),
		JSONB_BUILD_OBJECT('key', 'district', 'name', '行政區')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;

INSERT INTO component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES(
	7,
	'parking_grid_new_tpe',
	'停車格',
	'circle',
	'geojson',
	'small',
	'heatmap',
	JSONB_BUILD_OBJECT(
		'circle-color', 
			JSONB_BUILD_ARRAY(
				'match',
				JSONB_BUILD_ARRAY('get', 'pktype'),
				'大型車停車位', '#090974',
				'汽車身心障礙專用', '#033E6B',
				'機車停車位', '#0C60A4',
				'時段性禁停停車位', '#4F2981',
				'汽車停車位', '#7373D8',
				'裝卸貨專用停車位', '#66A2D2',
				'#1D7370'
			)
	),
	JSONB_BUILD_ARRAY(
		JSONB_BUILD_OBJECT('key', 'pktype', 'name', '類型'),
		JSONB_BUILD_OBJECT('key', 'district', 'name', '行政區')
	)
);

SELECT * FROM component_maps ORDER BY id ASC;