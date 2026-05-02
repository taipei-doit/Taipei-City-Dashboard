# Taipei Dashboard Memory

This note is for future Codex sessions. Read this first before helping the user create dashboard components or GeoJSON files for the Taipei Dashboard project.

## Project Goal

The user is working on the Taipei Dashboard repo. The recurring workflow is:

1. User provides a Dataset, usually already loaded into PostgreSQL as a table.
2. Generate SQL INSERT/UPDATE statements that the user can manually run in pgAdmin.
3. These SQL statements create dashboard metadata so the FE automatically renders dashboard cards/charts.
4. Generate a GeoJSON file from the Dataset so Mapbox can show correct locations.

Do not assume Docker commands are needed. The user prefers to run SQL manually in pgAdmin.

## Repo Structure

Relevant folders:

- `Taipei-City-Dashboard-FE`
  - Vue frontend.
  - Mapbox rendering is handled in `src/store/mapStore.js`.
  - Dashboard cards are rendered by `src/dashboardComponent/DashboardComponent.vue`.
  - Local GeoJSON files live in `public/mapData`.

- `Taipei-City-Dashboard-BE`
  - Go backend.
  - Component config joins are in `app/models/componentConfig.go`.
  - Chart query execution and output parsing are in `app/models/componentData.go`.
  - Dashboard membership is in `app/models/dashboard.go`.

- `Taipei-City-Dashboard-DE`
  - Airflow/data engineering jobs. Useful for examples, but the user's current workflow is manual pgAdmin SQL plus GeoJSON generation.

- `db-sample-data`
  - Contains example metadata dumps such as `dashboardmanager-demo.sql`.

## Two Databases

There are conceptually two PostgreSQL databases:

1. `dashboard_manager`
   - Stores metadata/configuration.
   - Controls which dashboard cards exist, which chart type they use, what SQL they run, what map layer they connect to, and which dashboard they belong to.

2. `dashboard`
   - Stores actual dataset tables.
   - `query_charts.query_chart` SQL runs against this DB via BE `DBDashboard.Raw(...)`.

When I say "metadata", I mean rows in manager tables that describe how the frontend should display cards/charts/maps. It does not mean the raw Dataset rows.

## Core Metadata Tables

To create a working dashboard card, these manager tables are usually involved:

1. `components`
   - One row per logical dashboard card/component.
   - Key fields:
     - `id`: integer, referenced by `dashboards.components`.
     - `index`: unique string ID. Must match `component_charts.index` and `query_charts.index`.
     - `name`: card title shown on frontend.

2. `component_charts`
   - Chart display config for a component.
   - Key fields:
     - `index`: must equal `components.index`.
     - `color`: `varchar[]`, e.g. `ARRAY['#4CB495','#F5C860']`.
     - `types`: `varchar[]`, e.g. `ARRAY['BarChart','ColumnChart']`.
     - `unit`: unit label, e.g. `'家'`, `'%'`, `'件'`, or `NULL`.

3. `query_charts`
   - Per-city query and descriptive config.
   - Key fields:
     - `index`: must equal `components.index`.
     - `city`: usually `'taipei'` or `'metrotaipei'`.
     - `query_type`: determines parser. Valid practical values: `two_d`, `three_d`, `percent`, `time`, `map_legend`.
     - `query_chart`: SQL string executed against the `dashboard` DB.
     - `query_history`: optional SQL string for history data.
     - `history_config`: optional JSON, e.g. `{"range":["year"]}` if history is enabled.
     - `map_config_ids`: integer array referencing `component_maps.id`.
     - `map_filter`: JSON for chart-map interaction.
     - `time_from`: usually `static`, `current`, `demo`, or time-range keyword.
     - `time_to`, `update_freq`, `update_freq_unit`, `source`, `short_desc`, `long_desc`, `use_case`, `links`, `contributors`.

4. `component_maps`
   - Mapbox layer config. Only needed when a card should have a map layer.
   - Key fields:
     - `id`: referenced by `query_charts.map_config_ids`.
     - `index`: GeoJSON file basename if `source='geojson'`. This does not have to equal `components.index`.
     - `title`: map layer title.
     - `type`: Mapbox layer type, commonly `circle`, `line`, `fill`, `symbol`, `fill-extrusion`. Special app types include `arc`, `voronoi`, `isoline`, `symbol-3d`.
     - `source`: for local file use `'geojson'`.
     - `size`: optional style preset such as `small`, `big`, `wide`, `dash` depending on FE map config support.
     - `icon`: optional icon preset such as `youbike`, `bus`, `cctv`; often `NULL` for simple circle/fill/line.
     - `paint`: JSON Mapbox paint override.
     - `property`: JSON array for popup fields, e.g. `[{"key":"name","name":"名稱"}]`.

5. `dashboards`
   - Dashboard page/container.
   - Key fields:
     - `index`: dashboard URL/query index.
     - `name`: dashboard display name.
     - `components`: integer array of `components.id`, order matters.
     - `icon`: material icon / category key.

6. `dashboard_groups`
   - Associates dashboard with group/city.
   - In sample:
     - group `1` = public
     - group `2` = taipei
     - group `3` = metrotaipei

## Backend Data Flow

Important files:

- `Taipei-City-Dashboard-BE/app/models/componentConfig.go`
  - Defines `Component`, `QueryCharts`, `ComponentMap`, `ComponentChart`.
  - `createTempComponentDB()` joins:
    - `components`
    - `component_charts`
    - `query_charts`
    - `component_maps`
  - The join uses `query_charts.map_config_ids` with `component_maps.id`.

- `Taipei-City-Dashboard-BE/app/models/dashboard.go`
  - `GetDashboardByIndex(index, groups, city)`:
    - Reads `dashboards.components`.
    - Fetches those component IDs.
    - Preserves order using `ARRAY_POSITION`.
    - Filters by `query_charts.city` if city is provided.
    - Adds `city` into each map config object before returning to FE.

- `Taipei-City-Dashboard-BE/app/models/componentData.go`
  - `/component/:id/chart` obtains `query_charts.query_type` and `query_charts.query_chart`.
  - Runs SQL against actual dataset DB (`dashboard`).
  - Parses output based on `query_type`.

## Frontend Data Flow

Important files:

- `Taipei-City-Dashboard-FE/src/store/contentStore.js`
  - Fetches `/dashboard/` to list dashboards.
  - Fetches `/dashboard/:index` to get component configs.
  - Fetches `/component/:id/chart?city=...` for chart data.

- `Taipei-City-Dashboard-FE/src/dashboardComponent/DashboardComponent.vue`
  - Renders chart cards based on `config.chart_config.types`.
  - Supported chart component names include:
    - `DistrictChart`
    - `BarChart`
    - `MapLegend`
    - `MetroChart`
    - `TimelineSeparateChart`
    - `TimelineStackedChart`
    - `PolarAreaChart`
    - `IconPercentChart`
    - `ColumnChart`
    - `DonutChart`
    - `TreemapChart`
    - `BarPercentChart`
    - `GuageChart`
    - `RadarChart`
    - `HeatmapChart`
    - `ColumnLineChart`
    - `BarChartWithGoal`
    - `IndicatorChart`
    - `TextUnitChart`

- `Taipei-City-Dashboard-FE/src/store/mapStore.js`
  - `addToMapLayerList(map_config)` creates `layerId = {index}-{type}-{city}`.
  - If `map_config.source === 'geojson'`, calls `fetchLocalGeoJson(map_config)`.
  - `fetchLocalGeoJson` loads `/mapData/${map_config.index}.geojson`.
  - Therefore `component_maps.index` must exactly match the GeoJSON filename without `.geojson`.

Example:

```text
component_maps.index = 'hackathon_component_7_pharmacy_map_ready'
FE fetches /mapData/hackathon_component_7_pharmacy_map_ready.geojson
Local file path is Taipei-City-Dashboard-FE/public/mapData/hackathon_component_7_pharmacy_map_ready.geojson
```

## Chart SQL Output Requirements

The SQL in `query_charts.query_chart` must return exact column aliases expected by BE.

### `query_type = 'two_d'`

Use for simple x/y series such as bar/column chart.

Required columns:

```sql
SELECT
  some_label AS x_axis,
  numeric_value AS data
FROM ...
```

BE returns:

```json
[
  {
    "data": [
      {"x": "...", "y": 123}
    ]
  }
]
```

### `query_type = 'three_d'`

Use for grouped/stacked/multi-series charts.

Required columns:

```sql
SELECT
  category AS x_axis,
  series_name AS y_axis,
  numeric_value::int AS data
FROM ...
```

Optional:

```sql
SELECT category AS x_axis, icon, series_name AS y_axis, numeric_value::int AS data
```

If `icon` is not meaningful, return `NULL AS icon` or `'' AS icon`.

### `query_type = 'percent'`

Uses the same BE parser as `three_d`. Required aliases are the same:

```sql
SELECT x_axis, y_axis, data FROM ...
```

### `query_type = 'time'`

Use for timeline charts.

Required columns:

```sql
SELECT
  timestamp_value AS x_axis,
  series_name AS y_axis,
  numeric_value AS data
FROM ...
ORDER BY x_axis
```

`x_axis` should be timestamp/time.

### `query_type = 'map_legend'`

Use for MapLegend card/layer summaries.

Required columns:

```sql
SELECT
  name,
  type,
  icon,
  value
FROM ...
```

## Time Parameters in SQL

Some chart/history SQL can contain two `%s` placeholders for `time_from` and `time_to`. BE detects exactly two `%s` in chart SQL and uses `fmt.Sprintf(query, timeFrom, timeTo)`.

Example:

```sql
SELECT district AS x_axis, count(*) AS data
FROM public.my_table
WHERE data_time BETWEEN '%s' AND '%s'
GROUP BY district
```

For most user requests, prefer static queries unless user explicitly needs time filtering.

## Map Filter JSON

Map filters let chart clicks filter Mapbox layers.

Most useful format:

```json
{
  "mode": "byParam",
  "byParam": {
    "xParam": "district"
  }
}
```

This means when chart x-axis is clicked, FE filters map layer features where `feature.properties.district === clicked_x_value`.

For x/y filtering:

```json
{
  "mode": "byParam",
  "byParam": {
    "xParam": "district",
    "yParam": "type"
  }
}
```

By-layer filtering:

```json
{
  "mode": "byLayer"
}
```

Important: The property keys in `map_filter` must exist in GeoJSON feature `properties`.

## GeoJSON Requirements

Local GeoJSON files go here:

```text
Taipei-City-Dashboard-FE/public/mapData/{map_index}.geojson
```

Basic format:

```json
{
  "type": "FeatureCollection",
  "name": "my_component_map_ready",
  "crs": {
    "type": "name",
    "properties": {
      "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
    }
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [121.5173744, 25.0308592]
      },
      "properties": {
        "id": 1,
        "name": "Example",
        "district": "中正區",
        "value": 42
      }
    }
  ]
}
```

Rules:

- Coordinates must be WGS84 longitude/latitude.
- Order is `[longitude, latitude]`, never `[latitude, longitude]`.
- For point data, geometry type is `Point`.
- For roads/routes, use `LineString` or `MultiLineString`.
- For polygons/districts, use `Polygon` or `MultiPolygon`.
- Every field used by `component_maps.property`, `component_maps.paint`, and `query_charts.map_filter` must be present in `properties`.
- Avoid `NaN`, `Infinity`, invalid JSON, or trailing commas.
- The file must be valid JSON and should preferably be UTF-8.

## SQL To Generate GeoJSON From Table

If dataset table has longitude/latitude columns:

```sql
SELECT jsonb_pretty(
  jsonb_build_object(
    'type', 'FeatureCollection',
    'name', 'my_component_map_ready',
    'crs', jsonb_build_object(
      'type', 'name',
      'properties', jsonb_build_object(
        'name', 'urn:ogc:def:crs:OGC:1.3:CRS84'
      )
    ),
    'features', COALESCE(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', jsonb_build_object(
          'type', 'Point',
          'coordinates', jsonb_build_array(longitude, latitude)
        ),
        'properties', to_jsonb(t) - 'longitude' - 'latitude'
      )
    ), '[]'::jsonb)
  )
)
FROM public.my_dataset t
WHERE longitude IS NOT NULL
  AND latitude IS NOT NULL;
```

If coordinates are named `lng`/`lat`, adjust accordingly. If geometry is stored as PostGIS geometry, use `ST_AsGeoJSON` / `ST_Transform(geom, 4326)` if PostGIS is available.

## Component Creation SQL Template

Use this as the baseline for one component with one GeoJSON map layer.

Replace:

- `my_component_index`
- `我的新組件`
- `my_component_map_ready`
- `public.my_dataset`
- chart SQL
- descriptions
- dashboard index

```sql
BEGIN;

WITH new_component AS (
  INSERT INTO public.components (index, name)
  VALUES ('my_component_index', '我的新組件')
  RETURNING id, index
),
new_map AS (
  INSERT INTO public.component_maps
    (index, title, type, source, size, icon, paint, property)
  VALUES (
    'my_component_map_ready',
    '我的地圖圖層',
    'circle',
    'geojson',
    'big',
    NULL,
    '{
      "circle-color": [
        "interpolate", ["linear"], ["get", "value"],
        0, "#d9f0a3",
        50, "#78c679",
        100, "#238443"
      ],
      "circle-opacity": 0.85
    }'::json,
    '[
      {"key":"name","name":"名稱"},
      {"key":"district","name":"行政區"},
      {"key":"address","name":"地址"},
      {"key":"value","name":"數值"}
    ]'::json
  )
  RETURNING id
),
new_chart AS (
  INSERT INTO public.component_charts (index, color, types, unit)
  SELECT
    index,
    ARRAY['#4CB495', '#F5C860'],
    ARRAY['BarChart', 'ColumnChart'],
    '筆'
  FROM new_component
  RETURNING index
),
new_query AS (
  INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case, links, contributors,
    created_at, updated_at, query_type, query_chart, query_history, city
  )
  SELECT
    c.index,
    NULL,
    ARRAY[m.id],
    '{"mode":"byParam","byParam":{"xParam":"district"}}'::json,
    'static',
    NULL,
    0,
    NULL,
    '自建資料集',
    '短描述',
    '長描述',
    '使用情境',
    ARRAY[]::text[],
    ARRAY[]::text[],
    now(),
    now(),
    'two_d',
    $$
      SELECT district AS x_axis, round(avg(value)::numeric, 2) AS data
      FROM public.my_dataset
      GROUP BY district
      ORDER BY data DESC
    $$,
    NULL,
    'taipei'
  FROM new_component c, new_map m
  RETURNING index
)
SELECT
  c.id AS component_id,
  c.index AS component_index,
  m.id AS map_config_id
FROM new_component c, new_map m;

COMMIT;
```

Then add the component to an existing dashboard:

```sql
UPDATE public.dashboards
SET components = array_append(
    COALESCE(components, ARRAY[]::integer[]),
    (SELECT id FROM public.components WHERE index = 'my_component_index')
  ),
  updated_at = now()
WHERE index = 'target_dashboard_index';
```

If adding five components, prefer one transaction and create all five rows, then update dashboard with all IDs in desired order.

Example:

```sql
UPDATE public.dashboards
SET components = COALESCE(components, ARRAY[]::integer[])
  || ARRAY[
    (SELECT id FROM public.components WHERE index = 'component_1'),
    (SELECT id FROM public.components WHERE index = 'component_2'),
    (SELECT id FROM public.components WHERE index = 'component_3'),
    (SELECT id FROM public.components WHERE index = 'component_4'),
    (SELECT id FROM public.components WHERE index = 'component_5')
  ],
  updated_at = now()
WHERE index = 'target_dashboard_index';
```

## Create New Dashboard Template

If the dashboard itself does not exist:

```sql
WITH d AS (
  INSERT INTO public.dashboards (index, name, components, icon, updated_at, created_at)
  VALUES (
    'my_dashboard_index',
    '我的 Dashboard',
    ARRAY[
      (SELECT id FROM public.components WHERE index = 'component_1'),
      (SELECT id FROM public.components WHERE index = 'component_2')
    ],
    'public',
    now(),
    now()
  )
  RETURNING id
)
INSERT INTO public.dashboard_groups (dashboard_id, group_id)
SELECT id, 2 FROM d; -- 2=taipei, 3=metrotaipei
```

## Recommended Tomorrow Workflow

When user gives a Dataset/table:

1. Ask or infer:
   - Dataset table name in `dashboard` DB.
   - Column names and types.
   - Which five components/cards they want.
   - Which dashboard index should receive them.
   - Which columns are longitude/latitude or geometry.

2. Inspect or request table schema/sample rows if needed:
   - Need enough info to write correct chart SQL.
   - For charts, make sure aliases match `query_type`.
   - For maps, make sure GeoJSON properties match popup/filter/style keys.

3. Produce pgAdmin SQL:
   - Use `BEGIN; ... COMMIT;`.
   - Insert `components`.
   - Insert `component_charts`.
   - Insert `component_maps` for map layers.
   - Insert `query_charts`.
   - Update or insert `dashboards`.
   - Optionally update `dashboard_groups`.
   - Include a verification `SELECT` at the end.

4. Produce GeoJSON:
   - Either create local file directly if dataset is available/exported in workspace.
   - Or provide SQL query to generate GeoJSON from DB for user to export.
   - Filename must match `component_maps.index`.

5. Validate mentally:
   - `components.index == component_charts.index == query_charts.index`.
   - `query_charts.map_config_ids` references real `component_maps.id`.
   - `component_maps.index` matches GeoJSON basename.
   - Chart SQL returns exact aliases.
   - GeoJSON property names match `property`, `paint`, `map_filter`.
   - Dashboard `components` array includes the component IDs.

## Common Pitfalls

- Only inserting `components` is not enough. Frontend needs joined config from `component_charts` and `query_charts`.
- `component_maps.index` is the GeoJSON filename basename. If it is wrong, Mapbox fetches a missing file.
- `component_maps.index` can differ from `components.index`; this is normal.
- Chart SQL runs against actual dataset DB, not manager DB.
- Metadata INSERTs run against manager DB.
- `query_type` must match SQL output aliases.
- Longitude/latitude order in GeoJSON must be `[lng, lat]`.
- `map_filter` keys must exist in GeoJSON properties.
- `paint` JSON must be valid Mapbox paint syntax.
- For `circle-color` or other expressions using `["get","value"]`, `value` must exist and be numeric in GeoJSON properties.
- If a dashboard is city-filtered, `query_charts.city` must match the FE city query such as `taipei`.
- If using `metrotaipei`, there may need to be separate `query_charts` rows for `taipei` and `metrotaipei` depending on how the dashboard should behave.

## Pharmacy Hackathon Example Notes

Current active GeoJSON:

```text
Taipei-City-Dashboard-FE/public/mapData/hackathon_component_7_pharmacy_map_ready.geojson
```

It is a `FeatureCollection` of `Point` features with properties similar to:

- `id`
- `nhi`
- `city`
- `name`
- `address`
- `district`
- `data_time`
- `telephone`
- `pharmacy_per_10k`

If a map config uses this file, set:

```sql
component_maps.index = 'hackathon_component_7_pharmacy_map_ready'
component_maps.source = 'geojson'
component_maps.type = 'circle' -- likely appropriate for points
```

Possible popup property JSON:

```json
[
  {"key":"name","name":"藥局名稱"},
  {"key":"district","name":"行政區"},
  {"key":"address","name":"地址"},
  {"key":"telephone","name":"電話"},
  {"key":"pharmacy_per_10k","name":"每萬人藥局數"}
]
```

Possible paint JSON:

```json
{
  "circle-color": [
    "interpolate", ["linear"], ["get", "pharmacy_per_10k"],
    0, "#f7fbff",
    2, "#6baed6",
    5, "#08306b"
  ],
  "circle-opacity": 0.85,
  "circle-stroke-color": "#ffffff",
  "circle-stroke-width": 0.5
}
```

Possible filter JSON if chart x-axis is district:

```json
{
  "mode": "byParam",
  "byParam": {
    "xParam": "district"
  }
}
```

## Final Reminder

The frontend is data-driven. To show a Dashboard:

```text
Dataset table in dashboard DB
  -> query_charts.query_chart reads it
  -> BE parses into chart_data
  -> components/component_charts/query_charts describe card
  -> dashboards.components includes component IDs
  -> component_maps + GeoJSON describe map layer
  -> FE renders dashboard card and Mapbox layer automatically
```

