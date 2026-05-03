## 概述

本專案使用四個表來儲存儀表板組件的配置。當這些表連接 (join) 起來時，將能組成前端所需的完整[組件配置](/front-end/introduction-to-components)。

`components` 是主表。它儲存所有組件的index以及名稱，組件的內容存在`query_charts`，圖表和地圖配置除外。上述兩個配置分別另外儲存在 `component_charts` 和 `component_maps` 表中。`components` 和 `query_charts` 表透過 `components.index` 和 `query_charts.index` 欄連接`query_charts` 和 `component_charts` 表透過 `query_charts.index` 和 `component_charts.index` 欄連接。而 `query_charts` 和 `component_maps` 表則透過 `query_charts.map_config_ids` 和 `component_maps.id` 欄連接。

## components

`PK` `id`

```go
type Component struct {
	ID             int64           `json:"id"               gorm:"column:id;autoincrement;primaryKey"`
	Index          string          `json:"index"            gorm:"column:index;type:varchar;unique;not null"`
	Name           string          `json:"name"             gorm:"column:name;type:varchar;not null"`
}
```

**值得注意的欄位：**

`components` 表各欄位的詳細填寫方式（以確保前端相容性）可以在[這裡](/front-end/introduction-to-components)找到。

`v3.0.0`
因應多城市需求， 一個 Component (組件名稱) 可以有不同城市的 QueryCharts (組件資訊)，透過 index 做關聯



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

**值得注意的欄位：**

`map_config_ids` 僅用於連接 `query_charts` 和 `component_maps` 表；`query_chart` 和 `query_history` 分別儲存用來檢索圖表和歷史資料的 SQL 指令。SQL 指令的相關撰寫指南可以在 [組件資料 API 文章](/back-end/component-data-apis)中找到。

`v3.0.0`
City 為必填欄位，目前可填寫的值為 `taipei` (台北), `metrotaipei` (雙北)


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

`component_charts` 表各欄位的詳細填寫方式（以確保前端相容性）可以在[這裡](/front-end/supported-chart-types)找到。

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

`component_maps` 表各欄位的詳細填寫方式（以確保前端相容性）可以在[這裡](/front-end/supported-map-types)找到。