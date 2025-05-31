// Package controllers stores all the controllers for the Gin router.//yy
package controllers

import (
	"net/http"
	"strconv"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"

	"github.com/gin-gonic/gin"
)

/*
GetComponentChartData retrieves the chart data for a component.
/api/v1/components/:id/chart

header: time_from, time_to (optional)
*/
func GetComponentChartData(c *gin.Context) {
	// 1. Get the component id from the URL
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid component ID"})
		return
	}

	// 1.1 Get the city name from the URL
	var query componentQuery
	c.ShouldBindQuery(&query)
	if !(query.City == "taipei" || query.City == "metrotaipei" || query.City == ""){
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid City Name"})
		return
	}

	if query.City == ""{
		query.City = "taipei"
	}

	// 2. Get the chart data query and chart data type from the database
	queryType, queryString, err := models.GetComponentChartDataQuery(id, query.City)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	if (queryString == "") || (queryType == "") {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "No chart data available"})
		return
	}

	timeFrom, timeTo, err:= util.GetTime(c)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 3. Get and parse the chart data based on chart data type
	if queryType == "two_d" {
		chartData, err := models.GetTwoDimensionalData(&queryString, timeFrom, timeTo)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData})
	} else if queryType == "three_d" || queryType == "percent" {
		chartData, categories, err := models.GetThreeDimensionalData(&queryString, timeFrom, timeTo)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData, "categories": categories})
	} else if queryType == "time" {
		chartData, err := models.GetTimeSeriesData(&queryString, timeFrom, timeTo)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData})
	} else if queryType == "map_legend" {
		chartData, err := models.GetMapLegendData(&queryString, timeFrom, timeTo)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData})
	}
}

/*
GetComponentHistoryData retrieves the history data for a component.
/api/v1/components/:id/history

header: time_from, time_to (mandatory)
timesteps are automatically determined based on the time range:
  - Within 24hrs: hour
  - Within 1 month: day
  - Within 3 months: week
  - Within 2 years: month
  - More than 2 years: year
*/
func GetComponentHistoryData(c *gin.Context) {
	// 1. Get the component id from the URL
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid component ID"})
		return
	}

	// 1.1 Get the city name from the URL
	var query componentQuery
	c.ShouldBindQuery(&query)
	if !(query.City == "taipei" || query.City == "metrotaipei" || query.City == ""){
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid City Name"})
		return
	}

	if query.City == ""{
		query.City = "taipei"
	}

	timeFrom, timeTo, err := util.GetTime(c)
		if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
			return
	}
	// 2. Get the history data query from the database
	queryHistory, err := models.GetComponentHistoryDataQuery(id, query.City, timeFrom, timeTo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	if queryHistory == "" {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "No history data available"})
		return
	}

	// 3. Get and parse the history data
	chartData, err := models.GetTimeSeriesData(&queryHistory, timeFrom, timeTo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData})
}

// SortedComponentIndices 存儲按照訪問次數(times)從高到低排序的組件索引
// 這個變數可以在其他函數中使用，例如推薦系統或數據分析
var SortedComponentIndices []string

// ComponentsRankMap 存儲組件索引到排名的映射
var ComponentsRankMap map[string]int

/*
CheckRank retrieves component information from the database
GET /api/v1/checkRank
This API fetches components from the dashboardmanager database, 
sorts them by the 'times' field in descending order, and 
stores the sorted indices in a global variable for later use.

Response includes:
- All components sorted by times (descending)
- A list of component indices ranked by popularity
*/
func CheckRank(c *gin.Context) {
	// 定義 Component 結構來匹配資料庫結構
	type ComponentWithTimes struct {
		ID    int64  `json:"id" gorm:"column:id"`
		Index string `json:"index" gorm:"column:index"`
		Name  string `json:"name" gorm:"column:name"`
		Times int    `json:"times" gorm:"column:times"`
	}

	// 查詢 components 表格並按 times 欄位降序排序
	var components []ComponentWithTimes
	err := models.DBManager.Table("components").
		Order("times DESC").
		Find(&components).Error

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to retrieve components: " + err.Error(),
		})
		return
	}

	// 清空並重新填充全局暫存的排序索引陣列
	SortedComponentIndices = make([]string, 0, len(components))
	ComponentsRankMap = make(map[string]int, len(components))
	
	for i, comp := range components {
		SortedComponentIndices = append(SortedComponentIndices, comp.Index)
		ComponentsRankMap[comp.Index] = i + 1 // 排名從1開始
	}

	// 構建回應
	response := gin.H{
		"status":     "success",
		"timestamp":  time.Now().Format(time.RFC3339),
		"total":      len(components),
		"components": components,
		"ranks":      SortedComponentIndices,
		"rankMap":    ComponentsRankMap,
	}

	c.JSON(http.StatusOK, response)
}

// CheckRank API is a RESTful endpoint that retrieves component data from the dashboardmanager database
// It supports pagination, sorting, filtering by city, and searching by component name or index
// The endpoint is accessible at /api/v1/checkRank and returns data in JSON format
