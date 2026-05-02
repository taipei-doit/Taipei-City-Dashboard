BEGIN;

INSERT INTO public.components (id, index, name)
VALUES (300, 'food_vendor_rating', '檢核評級業者')
ON CONFLICT (id) DO UPDATE SET
	index = EXCLUDED.index,
	name = EXCLUDED.name;

INSERT INTO public.component_charts (index, color, types, unit)
VALUES ('food_vendor_rating', ARRAY['#35B779', '#F8CF58'], ARRAY['MapLegend'], '家')
ON CONFLICT (index) DO UPDATE SET
	color = EXCLUDED.color,
	types = EXCLUDED.types,
	unit = EXCLUDED.unit;

INSERT INTO public.component_maps (
	id,
	index,
	title,
	type,
	source,
	size,
	icon,
	paint,
	property
)
VALUES (
	300,
	'food_vendor_rating',
	'檢核評級業者',
	'circle',
	'geojson',
	'big',
	NULL,
	'{
		"circle-color": ["match", ["get", "rating"], "優", "#35B779", "良", "#F8CF58", "#9CA3AF"],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 10, 0.4, 15, 1, 20, 1.5]
	}'::json,
	'[
		{"key": "name", "name": "店名"},
		{"key": "rating", "name": "評核等級"},
		{"key": "address", "name": "地址"},
		{"key": "phone", "name": "電話"},
		{"key": "registration_no", "name": "食品業者登錄字號"}
	]'::json
)
ON CONFLICT (id) DO UPDATE SET
	index = EXCLUDED.index,
	title = EXCLUDED.title,
	type = EXCLUDED.type,
	source = EXCLUDED.source,
	size = EXCLUDED.size,
	icon = EXCLUDED.icon,
	paint = EXCLUDED.paint,
	property = EXCLUDED.property;

INSERT INTO public.component_maps (
	id,
	index,
	title,
	type,
	source,
	size,
	icon,
	paint,
	property
)
VALUES (
	301,
	'food_vendor_rating_taipei',
	'檢核評級業者',
	'circle',
	'geojson',
	'big',
	NULL,
	'{
		"circle-color": ["match", ["get", "rating"], "優", "#35B779", "良", "#F8CF58", "#9CA3AF"],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 10, 0.4, 15, 1, 20, 1.5]
	}'::json,
	'[
		{"key": "name", "name": "店名"},
		{"key": "rating", "name": "評核等級"},
		{"key": "address", "name": "地址"},
		{"key": "phone", "name": "電話"},
		{"key": "registration_no", "name": "食品業者登錄字號"}
	]'::json
)
ON CONFLICT (id) DO UPDATE SET
	index = EXCLUDED.index,
	title = EXCLUDED.title,
	type = EXCLUDED.type,
	source = EXCLUDED.source,
	size = EXCLUDED.size,
	icon = EXCLUDED.icon,
	paint = EXCLUDED.paint,
	property = EXCLUDED.property;

DELETE FROM public.query_charts
WHERE index = 'food_vendor_rating'
	AND city IN ('metrotaipei', 'taipei');

INSERT INTO public.query_charts (
	index,
	history_config,
	map_config_ids,
	map_filter,
	time_from,
	time_to,
	update_freq,
	update_freq_unit,
	source,
	short_desc,
	long_desc,
	use_case,
	links,
	contributors,
	created_at,
	updated_at,
	query_type,
	query_chart,
	query_history,
	city
)
VALUES (
	'food_vendor_rating',
	NULL,
	ARRAY[300],
	NULL,
	'static',
	NULL,
	NULL,
	NULL,
	'CSV',
	'顯示臺北市與新北市檢核評級業者點位。',
	'此組件使用 CSV 內的店家地址與經緯度，在地圖上標示臺北市與新北市檢核評級業者位置，並可點擊查看店名、地址、電話、食品業者登錄字號與評核等級。',
	'可用於查看檢核評級業者的空間分布與附近店家資訊。',
	ARRAY[]::text[],
	ARRAY[]::text[],
	NOW(),
	NOW(),
	'map_legend',
	'SELECT unnest(ARRAY[''優'', ''良'']) AS name, ''circle'' AS type',
	NULL,
	'metrotaipei'
);

INSERT INTO public.query_charts (
	index,
	history_config,
	map_config_ids,
	map_filter,
	time_from,
	time_to,
	update_freq,
	update_freq_unit,
	source,
	short_desc,
	long_desc,
	use_case,
	links,
	contributors,
	created_at,
	updated_at,
	query_type,
	query_chart,
	query_history,
	city
)
VALUES (
	'food_vendor_rating',
	NULL,
	ARRAY[301],
	NULL,
	'static',
	NULL,
	NULL,
	NULL,
	'CSV',
	'顯示臺北市檢核評級業者點位。',
	'此組件使用 CSV 內的店家地址與經緯度，在地圖上標示臺北市檢核評級業者位置，並可點擊查看店名、地址、電話、食品業者登錄字號與評核等級。',
	'可用於查看臺北市檢核評級業者的空間分布與附近店家資訊。',
	ARRAY[]::text[],
	ARRAY[]::text[],
	NOW(),
	NOW(),
	'map_legend',
	'SELECT unnest(ARRAY[''優'', ''良'']) AS name, ''circle'' AS type',
	NULL,
	'taipei'
);

INSERT INTO public.dashboards (
	id,
	index,
	name,
	components,
	icon,
	updated_at,
	created_at
)
VALUES (
	400,
	'food_vendor_rating',
	'檢核評級業者',
	ARRAY[300],
	'restaurant',
	NOW(),
	NOW()
)
ON CONFLICT (id) DO UPDATE SET
	index = EXCLUDED.index,
	name = EXCLUDED.name,
	components = EXCLUDED.components,
	icon = EXCLUDED.icon,
	updated_at = NOW();

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
VALUES (400, 3)
ON CONFLICT DO NOTHING;

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
VALUES (400, 2)
ON CONFLICT DO NOTHING;

UPDATE public.dashboards
SET
	components = CASE
		WHEN components @> ARRAY[300]::integer[] THEN components
		ELSE components || ARRAY[300]::integer[]
	END,
	updated_at = NOW()
WHERE index = 'map-layers-metrotaipei';

UPDATE public.dashboards
SET
	components = CASE
		WHEN components @> ARRAY[300]::integer[] THEN components
		ELSE components || ARRAY[300]::integer[]
	END,
	updated_at = NOW()
WHERE index = 'map-layers-taipei';

SELECT setval('public.components_id_seq', GREATEST((SELECT MAX(id) FROM public.components), 1), true);
SELECT setval('public.component_maps_id_seq', GREATEST((SELECT MAX(id) FROM public.component_maps), 1), true);
SELECT setval('public.dashboards_id_seq', GREATEST((SELECT MAX(id) FROM public.dashboards), 1), true);

COMMIT;
