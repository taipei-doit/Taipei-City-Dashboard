## Overview

Three tables are used to store the configurations of dashboard components. When joined, the tables provide the complete [component config](/front-end/introduction-to-components) required by the front-end.

`components` is the main table. It stores all component configurations except for chart and map configurations which are stored in `component_charts` and `component_maps` respectively. The `components` and `component_charts` tables are joined via the `components.index` and `component_charts.index` columns. While the `components` and `component_maps` tables are joined via the `components.map_config_ids` and `component_maps.id` columns.

## components

`PK` `id`

```go
type Component struct {
	ID             int64           `json:"id"               gorm:"column:id;autoincrement;primaryKey"`
	Index          string          `json:"index"            gorm:"column:index;type:varchar;unique;not null"     `
	Name           string          `json:"name"             gorm:"column:name;type:varchar;not null"`
}
```

**Columns of Note:**
More information on front-end requirements for the `components` table can be found in the [here](/front-end/introduction-to-components).

`v3.0.0`
To support multiple cities, a single Component (component name) can have different QueryCharts (component information) for each city, with an index used for association.



## query_charts

`FK` `index` `map_config_ids`

```go
type QueryCharts struct {
	Index          string          `json:"index"            gorm:"column:index;type:varchar;unique;not null"     `
	HistoryConfig  json.RawMessage `json:"history_config"   gorm:"column:history_config;type:json"`
	MapConfigIDs   pq.Int64Array   `json:"-"                gorm:"column:map_config_ids;type:integer[]"`
	MapConfig      json.RawMessage `json:"map_config"       gorm:"type:json"`
	ChartConfig    json.RawMessage `json:"chart_config"     gorm:"type:json"`
	MapFilter      json.RawMessage `json:"map_filter"       gorm:"column:map_filter;type:json"`
	TimeFrom       string          `json:"time_from"        gorm:"column:time_from;type:varchar"`
	TimeTo         string          `json:"time_to"          gorm:"column:time_to;type:varchar"`
	UpdateFreq     int64           `json:"update_freq"      gorm:"column:update_freq;type:integer"`
	UpdateFreqUnit string          `json:"update_freq_unit" gorm:"column:update_freq_unit;type:varchar"`
	Source         string          `json:"source"           gorm:"column:source;type:varchar"`
	ShortDesc      string          `json:"short_desc"       gorm:"column:short_desc;type:text"`
	LongDesc       string          `json:"long_desc"        gorm:"column:long_desc;type:text"`
	UseCase        string          `json:"use_case"         gorm:"column:use_case;type:text"`
	Links          pq.StringArray  `json:"links"            gorm:"column:links;type:text[]"`
	Contributors   pq.StringArray  `json:"contributors"     gorm:"column:contributors;type:text[]"`
	CreatedAt      time.Time       `json:"-"                gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt      time.Time       `json:"updated_at"       gorm:"column:updated_at;type:timestamp with time zone;not null"`
	QueryType      string          `json:"query_type"       gorm:"column:query_type;type:varchar"`
	QueryChart     string          `json:"-"                gorm:"column:query_chart;type:text"`
	QueryHistory   string          `json:"-"                gorm:"column:query_history;type:text"`
	City           string          `json:"city"             gorm:"column:city;type:text"`
}
```

**Columns of Note:**

`map_config_ids` is used solely for the purpose of joining the `components` and `component_maps` tables; `query_chart` and `query_history` store the SQL queries used to retrieve data for the chart and history components respectively. More information on the queries will be disclosed in the [component data APIs article](/back-end/component-data-apis).

`v3.0.0`
The "City" field is required. The currently available values are `taipei` and `metrotaipei`.

## component_charts

`PK` `index`

```go
type ComponentChart struct {
	Index string         `json:"-"     gorm:"column:index;type:varchar;primaryKey"     `
	Color pq.StringArray `json:"color" gorm:"column:color;type:varchar[]"`
	Types pq.StringArray `json:"types" gorm:"column:types;type:varchar[]"`
	Unit  string         `json:"unit"  gorm:"column:unit;type:varchar"`
}
```

More information on front-end requirements for the `component_charts` table can be found in the [here](/front-end/supported-chart-types).

## component_maps

`PK` `id`

```go
type ComponentMap struct {
	ID       int64           `json:"id"       gorm:"column:id;autoincrement;primaryKey"`
	Index    string          `json:"index"    gorm:"column:index;type:varchar;not null"     `
	Title    string          `json:"title"    gorm:"column:title;type:varchar;not null"`
	Type     string          `json:"type"     gorm:"column:type;type:varchar;not null"`
	Source   string          `json:"source"   gorm:"column:source;type:varchar;not null"`
	Size     string          `json:"size"     gorm:"column:size;type:varchar"`
	Icon     string          `json:"icon"     gorm:"column:icon;type:varchar"`
	Paint    json.RawMessage `json:"paint"    gorm:"column:paint;type:json"`
	Property json.RawMessage `json:"property" gorm:"column:property;type:json"`
}
```

More information on front-end requirements for the `component_maps` table can be found in the [here](/front-end/supported-map-types).
