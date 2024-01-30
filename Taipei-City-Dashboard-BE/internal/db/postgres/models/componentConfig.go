// Package models stores the models for the postgreSQL databases.
package models

import (
	"encoding/json"
	"time"

	"github.com/lib/pq"
)

// Component is the model for the components table.
type Component struct {
	ID             int64           `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Index          string          `json:"index"      gorm:"column:index;type:varchar;unique;not null"     `
	Name           string          `json:"name"       gorm:"column:name;type:varchar;not null"`
	HistoryConfig  json.RawMessage `json:"history_config" gorm:"column:history_config;type:json"`
	MapConfigIDs   pq.Int64Array   `json:"-" gorm:"column:map_config_ids;type:integer[]"`
	MapConfig      json.RawMessage `json:"map_config" gorm:"type:json"`
	ChartConfig    json.RawMessage `json:"chart_config" gorm:"type:json"`
	MapFilter      json.RawMessage `json:"map_filter" gorm:"column:map_filter;type:json"`
	TimeFrom       string          `json:"time_from" gorm:"column:time_from;type:varchar"`
	TimeTo         string          `json:"time_to" gorm:"column:time_to;type:varchar"`
	UpdateFreq     int64           `json:"update_freq" gorm:"column:update_freq;type:integer"`
	UpdateFreqUnit string          `json:"update_freq_unit" gorm:"column:update_freq_unit;type:varchar"`
	Source         string          `json:"source" gorm:"column:source;type:varchar"`
	ShortDesc      string          `json:"short_desc" gorm:"column:short_desc;type:text"`
	LongDesc       string          `json:"long_desc" gorm:"column:long_desc;type:text"`
	UseCase        string          `json:"use_case" gorm:"column:use_case;type:text"`
	Links          pq.StringArray  `json:"links" gorm:"column:links;type:text[]"`
	Contributors   pq.StringArray  `json:"contributors" gorm:"column:contributors;type:text[]"`
	CreatedAt      time.Time       `json:"-" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt      time.Time       `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
	QueryType      string          `json:"query_type" gorm:"column:query_type;type:varchar"`
	QueryChart     string          `json:"-" gorm:"column:query_chart;type:text"`
	QueryHistory   string          `json:"-" gorm:"column:query_history;type:text"`
}

type UpdateComponent struct {
	Index          string          `json:"index"      `
	Name           string          `json:"name"       `
	HistoryConfig  json.RawMessage `json:"history_config" gorm:"json"`
	MapConfigIds   pq.Int64Array   `json:"map_config_ids" gorm:"type:integer[]"`
	MapFilter      json.RawMessage `json:"map_filter" gorm:"json"`
	UpdateFreq     *int64          `json:"update_freq" gorm:"type:integer"`
	UpdateFreqUnit string          `json:"update_freq_unit" `
	Source         string          `json:"source" `
	ShortDesc      string          `json:"short_desc" `
	LongDesc       string          `json:"long_desc" `
	UseCase        string          `json:"use_case" `
	Links          pq.StringArray  `json:"links" gorm:"type:text[]"`
	Contributors   pq.StringArray  `json:"contributors" gorm:"type:text[]"`
	QueryType      string          `json:"query_type" `
	UpdatedAt      time.Time       `json:"updated_at" gorm:"autoUpdateTime"`
}

// ComponentMap is the model for the component_maps table.
type ComponentMap struct {
	ID       int64           `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Index    string          `json:"index"      gorm:"column:index;type:varchar;not null"     `
	Title    string          `json:"title"      gorm:"column:title;type:varchar;not null"`
	Type     string          `json:"type"       gorm:"column:type;type:varchar;not null"`
	Source   string          `json:"source"     gorm:"column:source;type:varchar;not null"`
	Size     string          `json:"size"       gorm:"column:size;type:varchar"`
	Icon     string          `json:"icon"       gorm:"column:icon;type:varchar"`
	Paint    json.RawMessage `json:"paint" gorm:"column:paint;type:json"`
	Property json.RawMessage `json:"property" gorm:"column:property;type:json"`
}

// UpdateMapConfig is the model for the component_maps table.
type UpdateMapConfig struct {
	Index    string          `json:"index"      `
	Title    string          `json:"title"      `
	Type     string          `json:"type"       `
	Source   string          `json:"source"     `
	Size     string          `json:"size"`
	Icon     string          `json:"icon"`
	Paint    json.RawMessage `json:"paint" gorm:"json"`
	Property json.RawMessage `json:"property" gorm:"json"`
}

// ComponentChart is the model for the component_charts table.
type ComponentChart struct {
	Index      string         `json:"index"      gorm:"column:index;type:varchar;primaryKey"     `
	Color      pq.StringArray `json:"color" gorm:"column:color;type:varchar[]"`
	Types      pq.StringArray `json:"types" gorm:"column:types;type:varchar[]"`
	Categories pq.StringArray `json:"categories" gorm:"column:categories;type:varchar[]"`
	Unit       string         `json:"unit" gorm:"column:unit;type:varchar"`
}

// UpdateChartConfig is the model for the component_charts table.
type UpdateChartConfig struct {
	Color      pq.StringArray `json:"color" gorm:"type:text[]"`
	Types      pq.StringArray `json:"types" gorm:"type:text[]"`
	Categories pq.StringArray `json:"categories" gorm:"type:text[]"`
	Unit       string         `json:"unit"`
}
