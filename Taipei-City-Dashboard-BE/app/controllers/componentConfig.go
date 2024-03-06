// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"fmt"
	"net/http"
	"time"

	"TaipeiCityDashboardBE/app/database"
	"TaipeiCityDashboardBE/app/database/models"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// createTempComponentDB creates a temporary database for components that can be used throughout the file.
func createTempComponentDB() *gorm.DB {
	// Columns to select from the components table
	selectColumns := []string{"id", "index", "name", "history_config", "map_filter", "time_from", "time_to", "update_freq", "update_freq_unit", "source", "short_desc", "long_desc", "use_case", "links", "contributors", "updated_at", "query_type"}
	selectString := ""
	for _, column := range selectColumns {
		selectString += "components." + column + ", "
	}

	return database.DBManager.
		Table("components").
		Select(fmt.Sprint(selectString, "json_agg(row_to_json(component_maps.*)) AS map_config, row_to_json(component_charts.*) AS chart_config")).
		Joins("LEFT JOIN unnest(components.map_config_ids) AS id_value ON true").
		Joins("LEFT JOIN component_maps ON id_value = component_maps.id").
		Joins("JOIN component_charts ON components.index = component_charts.index").
		Group("components.id, component_charts.*")
}

/*
GetAllComponents retrieves all public components from the database.
GET /api/v1/component

| Param         | Description                                         | Value                        | Default |
| ------------- | --------------------------------------------------- | ---------------------------- | ------- |
| pagesize      | Number of components per page.                      | `int`                        | -       |
| pagenum       | Page number. Only works if pagesize is defined.     | `int`                        | 1       |
| searchbyname  | Text string to search name by.                      | `string`                     | -       |
| searchbyindex | Text string to search index by.                     | `string`                     | -       |
| filterby      | Column to filter by. `filtervalue` must be defined. | `string`                     | -       |
| filtermode    | How the data should be filtered.                    | `eq`, `ne`, `gt`, `lt`, `in` | `eq`    |
| filtervalue   | The value to filter by.                             | `int`, `string`              | -       |
| sort          | The column to sort by.                              | `string`                     | -       |
| order         | Ascending or descending.                            | `asc`, `desc`                | `asc`   |
*/

type componentQuery struct {
	PageSize      int    `form:"pagesize"`
	PageNum       int    `form:"pagenum"`
	Sort          string `form:"sort"`
	Order         string `form:"order"`
	FilterBy      string `form:"filterby"`
	FilterMode    string `form:"filtermode"`
	FilterValue   string `form:"filtervalue"`
	SearchByIndex string `form:"searchbyindex"`
	SearchByName  string `form:"searchbyname"`
}

func GetAllComponents(c *gin.Context) {
	tempDB := createTempComponentDB()
	var components []models.Component // Create a slice of components
	var totalComponents int64         // Create a variable to store the total amount of components
	var resultNum int64               // Create a variable to store the amount of components returned

	// Get all query parameters from context
	var query componentQuery
	c.ShouldBindQuery(&query)

	// Count the total amount of components
	tempDB.Count(&totalComponents)

	// Search the components
	if query.SearchByIndex != "" {
		tempDB = tempDB.Where("components.index LIKE ?", "%"+query.SearchByIndex+"%")
	}
	if query.SearchByName != "" {
		tempDB = tempDB.Where("components.name LIKE ?", "%"+query.SearchByName+"%")
	}

	// Filter the components
	if query.FilterBy != "" && query.FilterValue != "" {
		switch query.FilterMode {
		case "eq": // equals
			tempDB = tempDB.Where("components."+query.FilterBy+" = ?", query.FilterValue)
		case "ne": // not equals
			tempDB = tempDB.Where("components."+query.FilterBy+" <> ?", query.FilterValue)
		case "gt": // greater than
			tempDB = tempDB.Where("components."+query.FilterBy+" > ?", query.FilterValue)
		case "lt": // less than
			tempDB = tempDB.Where("components."+query.FilterBy+" < ?", query.FilterValue)
		case "in": // value in array
			tempDB = tempDB.Where("components."+query.FilterBy+" IN ?", query.FilterValue)
		default: // Default to eq
			tempDB = tempDB.Where("components."+query.FilterBy+" = ?", query.FilterValue)
		}
	}

	tempDB.Count(&resultNum)

	// Sort the components
	if query.Sort != "" {
		tempDB = tempDB.Order("components." + query.Sort + " " + query.Order)
	}

	// Paginate the components
	if query.PageSize > 0 {
		tempDB = tempDB.Limit(query.PageSize)
		if query.PageNum > 0 {
			tempDB = tempDB.Offset((query.PageNum - 1) * query.PageSize)
		}
	}

	err := tempDB.Find(&components).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Return the components
	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalComponents, "results": resultNum, "data": components})
}

/*
GetComponentByID retrieves a public component from the database by ID.
GET /api/v1/component/:id
*/
func GetComponentByID(c *gin.Context) {
	tempDB := createTempComponentDB()
	var component models.Component

	// Get the component ID from the context
	componentID := c.Param("id")

	// Find the component
	err := tempDB.Where("components.id = ?", componentID).First(&component).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "component not found"})
		return
	}

	// Return the component
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": component})
}

/*
UpdateComponent updates a component's config in the database.
PATCH /api/v1/component/:id
*/
func UpdateComponent(c *gin.Context) {
	var component models.UpdateComponent

	// 1. Get the component ID from the context
	componentID := c.Param("id")

	// 2. Find the component
	err := database.DBManager.Table("components").Where("id = ?", componentID).First(&component).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "component not found"})
		return
	}
	componentIndex := component.Index

	// 3. Bind the request body to the component and make sure it's valid
	err = c.ShouldBindJSON(&component)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}
	component.UpdatedAt = time.Now()

	// 3.1 不能改變 index
	component.Index = componentIndex

	// 4. Update the component
	err = database.DBManager.Table("components").Where("id = ?", componentID).Updates(&component).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 5. Return the component
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": component})
}

/*
UpdateComponentChartConfig updates a component's chart config in the database.
PATCH /api/v1/component/:id/chart
*/
func UpdateComponentChartConfig(c *gin.Context) {
	var chartConfig models.UpdateChartConfig
	var component models.UpdateComponent

	// 1. Get the component ID from the context
	componentID := c.Param("id")

	// 2. Find the component and chart config
	err := database.DBManager.Table("components").Where("id = ?", componentID).First(&component).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "component not found"})
		return
	}
	err = database.DBManager.Table("component_charts").Where("index = ?", component.Index).First(&chartConfig).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "chart config not found"})
		return
	}

	// 3. Bind the request body to the component and make sure it's valid
	err = c.ShouldBindJSON(&chartConfig)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}
	component.UpdatedAt = time.Now()

	// 4. Update the chart config. Then update the update_time in components table.
	err = database.DBManager.Table("component_charts").Where("index = ?", component.Index).Updates(&chartConfig).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	err = database.DBManager.Table("components").Where("id = ?", componentID).Updates(&component).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 5. Return the component
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartConfig})
}

/*
UpdateComponentMapConfig updates a component's map config in the database.
PATCH /api/v1/component/:id/map
*/
func UpdateComponentMapConfig(c *gin.Context) {
	var mapConfig models.UpdateMapConfig

	// 1. Get the map config index from the context
	mapConfigID := c.Param("id")

	// 2. Find the map config
	err := database.DBManager.Table("component_maps").Where("id = ?", mapConfigID).First(&mapConfig).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "map config not found"})
		return
	}

	// 3. Bind the request body to the component and make sure it's valid
	err = c.ShouldBindJSON(&mapConfig)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 4. Update the map config
	err = database.DBManager.Table("component_maps").Where("id = ?", mapConfigID).Updates(&mapConfig).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 5. Return the map config
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": mapConfig})
}

/*
DeleteComponent deletes a component from the database.
DELETE /api/v1/component/:id

Note: Associated chart config will also be deleted. Associated map config will only be deleted if no other components are using it.
*/
func DeleteComponent(c *gin.Context) {
	var component models.UpdateComponent
	var chartConfig models.UpdateChartConfig
	var mapConfig models.UpdateMapConfig

	// 1. Get the component ID from the context
	componentID := c.Param("id")

	// 2. Find the component
	err := database.DBManager.Table("components").Where("id = ?", componentID).First(&component).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "component not found"})
		return
	}

	// 3. Delete the component
	err = database.DBManager.Table("components").Where("id = ?", componentID).Delete(&component).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 4. Delete the chart config
	deleteChartStatus := true
	err = database.DBManager.Table("component_charts").Where("index = ?", component.Index).Delete(&chartConfig).Error
	if err != nil {
		deleteChartStatus = false
	}

	// 5. Loop through mapconfigIds if it exists and delete the map config if no other components are using it
	deleteMapStatus := true
	if len(component.MapConfigIds) > 0 {
		for _, mapConfigID := range component.MapConfigIds {
			var mapConfigCount int64
			database.DBManager.Table("components").Where("map_config_ids @> ARRAY[?]::integer[]", mapConfigID).Count(&mapConfigCount)
			if mapConfigCount == 0 {
				err = database.DBManager.Table("component_maps").Where("id = ?", mapConfigID).Delete(&mapConfig).Error
				if err != nil {
					deleteMapStatus = false
				}
			}
		}
	}

	// 6. Return success
	c.JSON(http.StatusOK, gin.H{"status": "success", "chart_deleted": deleteChartStatus, "map_deleted": deleteMapStatus})
}
