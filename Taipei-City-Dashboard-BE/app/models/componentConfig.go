// Package models stores the models for the postgreSQL databases.
package models

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/lib/pq"
	"gorm.io/gorm"
)

/* ----- Models ----- */

// Component is the model for the components table.
type Component struct {
	ID             int64           `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Index          string          `json:"index" gorm:"column:index;type:varchar;unique;not null"     `
	Name           string          `json:"name" gorm:"column:name;type:varchar;not null"`
	HistoryConfig  json.RawMessage `json:"history_config" gorm:"column:history_config;type:json"`
	MapConfigIDs   pq.Int64Array   `json:"-" gorm:"column:map_config_ids;type:integer[]"`
	MapConfig      json.RawMessage `json:"map_config" gorm:"type:json"`
	ChartConfig    json.RawMessage `json:"chart_config" gorm:"type:json"`
	MapFilter      json.RawMessage `json:"map_filter" gorm:"column:map_filter;type:json"`
	TimeFrom       string          `json:"time_from" gorm:"column:time_from;type:varchar"`
	TimeTo         *string         `json:"time_to" gorm:"column:time_to;type:varchar"`
	UpdateFreq     *int64          `json:"update_freq" gorm:"column:update_freq;type:integer"`
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

// ComponentMap is the model for the component_maps table.
type ComponentMap struct {
	ID       int64            `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Index    string           `json:"index"      gorm:"column:index;type:varchar;not null"     `
	Title    string           `json:"title"      gorm:"column:title;type:varchar;not null"`
	Type     string           `json:"type"       gorm:"column:type;type:varchar;not null"`
	Source   string           `json:"source"     gorm:"column:source;type:varchar;not null"`
	Size     *string          `json:"size"       gorm:"column:size;type:varchar"`
	Icon     *string          `json:"icon"       gorm:"column:icon;type:varchar"`
	Paint    *json.RawMessage `json:"paint" gorm:"column:paint;type:json"`
	Property *json.RawMessage `json:"property" gorm:"column:property;type:json"`
}

// ComponentChart is the model for the component_charts table.
type ComponentChart struct {
	Index string         `json:"index"      gorm:"column:index;type:varchar;primaryKey"     `
	Color pq.StringArray `json:"color" gorm:"column:color;type:varchar[]"`
	Types pq.StringArray `json:"types" gorm:"column:types;type:varchar[]"`
	Unit  string         `json:"unit" gorm:"column:unit;type:varchar"`
}

/* ----- Handlers ----- */

// createTempComponentDB joins the components, component_maps, and component_charts tables and selects the columns to return.
func createTempComponentDB() *gorm.DB {
	// Columns to select from the components table
	selectColumns := []string{"id", "index", "name", "history_config", "map_filter", "time_from", "time_to", "update_freq", "update_freq_unit", "source", "short_desc", "long_desc", "use_case", "links", "contributors", "updated_at", "query_type"}
	selectString := ""
	for _, column := range selectColumns {
		selectString += "components." + column + ", "
	}

	return DBManager.
		Table("components").
		Select(fmt.Sprint(selectString, "json_agg(row_to_json(component_maps.*)) AS map_config, row_to_json(component_charts.*) AS chart_config")).
		Joins("LEFT JOIN unnest(components.map_config_ids) AS id_value ON true").
		Joins("LEFT JOIN component_maps ON id_value = component_maps.id").
		Joins("JOIN component_charts ON components.index = component_charts.index").
		Group("components.id, component_charts.*")
}

func GetAllComponents(pageSize int, pageNum int, sort string, order string, filterBy string, filterMode string, filterValue string, searchByIndex string, searchByName string) (components []Component, totalComponents int64, resultNum int64, err error) {
	tempDB := createTempComponentDB()

	// Count the total amount of components
	tempDB.Count(&totalComponents)

	// Search the components
	if searchByIndex != "" {
		tempDB = tempDB.Where("components.index LIKE ?", "%"+searchByIndex+"%")
	}
	if searchByName != "" {
		tempDB = tempDB.Where("components.name LIKE ?", "%"+searchByName+"%")
	}

	// Filter the components
	if filterBy != "" && filterValue != "" {
		switch filterMode {
		case "eq": // equals
			tempDB = tempDB.Where("components."+filterBy+" = ?", filterValue)
		case "ne": // not equals
			tempDB = tempDB.Where("components."+filterBy+" <> ?", filterValue)
		case "gt": // greater than
			tempDB = tempDB.Where("components."+filterBy+" > ?", filterValue)
		case "lt": // less than
			tempDB = tempDB.Where("components."+filterBy+" < ?", filterValue)
		case "in": // value in array
			tempDB = tempDB.Where("components."+filterBy+" IN ?", filterValue)
		default: // Default to eq
			tempDB = tempDB.Where("components."+filterBy+" = ?", filterValue)
		}
	}

	tempDB.Count(&resultNum)

	// Sort the components
	if sort != "" {
		tempDB = tempDB.Order("components." + sort + " " + order)
	}

	// Paginate the components
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	err = tempDB.Find(&components).Error
	if err != nil {
		return components, 0, 0, err
	}

	return components, totalComponents, resultNum, nil
}

func GetComponentByID(id int) (component Component, err error) {
	tempDB := createTempComponentDB()

	err = tempDB.Where("components.id = ?", id).First(&component).Error
	if err != nil {
		return component, err
	}
	return component, nil
}

func CreateComponent(name string, historyConfig json.RawMessage, mapFilter json.RawMessage, timeFrom string, timeTo *string, updateFreq *int64, updateFreqUnit string, source string, shortDesc string, longDesc string, useCase string, links pq.StringArray, contributors pq.StringArray) (component Component, err error) {
    component = Component{
        Name:            name,
        HistoryConfig:   historyConfig,
        MapFilter:       mapFilter,
        TimeFrom:        timeFrom,
        TimeTo:          timeTo,
        UpdateFreq:      updateFreq,
        UpdateFreqUnit:  updateFreqUnit,
        Source:          source,
        ShortDesc:       shortDesc,
        LongDesc:        longDesc,
        UseCase:         useCase,
        Links:           links,
        Contributors:    contributors,
        CreatedAt:       time.Now(),
        UpdatedAt:       time.Now(),
    }

    err = DBManager.Table("components").Create(&component).Error
    if err != nil {
        return component, err
    }
    return component, nil
}

func UpdateComponent(id int, name string, historyConfig json.RawMessage, mapFilter json.RawMessage, timeFrom string, timeTo *string, updateFreq *int64, updateFreqUnit string, source string, shortDesc string, longDesc string, useCase string, links pq.StringArray, contributors pq.StringArray) (component Component, err error) {
	component = Component{Name: name, HistoryConfig: historyConfig, MapFilter: mapFilter, TimeFrom: timeFrom, TimeTo: timeTo, UpdateFreq: updateFreq, UpdateFreqUnit: updateFreqUnit, Source: source, ShortDesc: shortDesc, LongDesc: longDesc, UseCase: useCase, Links: links, Contributors: contributors, UpdatedAt: time.Now()}

	err = DBManager.Table("components").Where("id = ?", id).Updates(&component).Error
	if err != nil {
		return component, err
	}

	err = DBManager.Where("id = ?", id).First(&component).Error
	if err != nil {
		return component, err
	}
	return component, nil
}

func UpdateComponentChartConfig(index string, color pq.StringArray, types pq.StringArray, unit string) (chartConfig ComponentChart, err error) {
	chartConfig = ComponentChart{Color: color, Types: types, Unit: unit}

	err = DBManager.Table("component_charts").Where("index = ?", index).Updates(&chartConfig).Error
	if err != nil {
		return chartConfig, err
	}

	err = DBManager.Where("index = ?", index).First(&chartConfig).Error
	if err != nil {
		return chartConfig, err
	}
	return chartConfig, nil
}

func UpdateComponentMapConfig(id int, index string, title string, mapType string, source string, size *string, icon *string, paint *json.RawMessage, property *json.RawMessage) (mapConfig ComponentMap, err error) {
	mapConfig = ComponentMap{Index: index, Title: title, Type: mapType, Source: source, Size: size, Icon: icon, Paint: paint, Property: property}

	err = DBManager.Table("component_maps").Where("id = ?", id).Updates(&mapConfig).Error
	if err != nil {
		return mapConfig, err
	}

	err = DBManager.Where("id = ?", id).First(&mapConfig).Error
	if err != nil {
		return mapConfig, err
	}
	return mapConfig, nil
}

func DeleteComponent(id int, index string, mapConfigIDs pq.Int64Array) (deleteChartStatus bool, deleteMapStatus bool, err error) {
	// 1. Delete component config
	err = DBManager.Table("components").Where("id = ?", id).Delete(Component{}).Error
	if err != nil {
		return false, false, err
	}

	// 2. Delete the chart config
	err = DBManager.Table("component_charts").Where("index = ?", index).Delete(ComponentChart{}).Error
	if err != nil {
		return false, false, err
	}

	// 3. Loop through mapconfigIds if it exists and delete the map config if no other components are using it
	if len(mapConfigIDs) > 0 {
		for _, mapConfigID := range mapConfigIDs {
			var mapConfigCount int64
			DBManager.Table("components").Where("map_config_ids @> ARRAY[?]::integer[]", mapConfigID).Count(&mapConfigCount)
			if mapConfigCount == 0 {
				err = DBManager.Table("component_maps").Where("id = ?", mapConfigID).Delete(ComponentMap{}).Error
			}
		}
	}
	if err != nil {
		return true, false, err
	}

	return true, true, nil
}
