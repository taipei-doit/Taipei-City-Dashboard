// Package controllers stores all the controllers for the Gin router.//yy
package controllers

import (
	"net/http"
	"strconv"
	"time"
	"fmt"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"github.com/lib/pq"
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
GET /api/v1/
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

/*
CompareRank checks if the current component ranking has changed compared to the previous one
GET /api/v1/compareRank
This API fetches components from the dashboardmanager database,
sorts them by the 'times' field in descending order, and 
compares with the previously stored SortedComponentIndices.

If rankings are different, it also updates the "熱門儀表板" dashboard's components field.

Response:
- status = "render" if rankings are different
- status = "success" if rankings are the same
- status = "error" if an error occurs
*/
func CompareRank(c *gin.Context) {
	logs.FInfo("CompareRank API 被呼叫 - 開始檢查排名變化")
	
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
		logs.FError("從資料庫獲取組件資料失敗: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
		})
		return
	}

	logs.FInfo("從資料庫成功獲取 %d 個組件", len(components))
	
	// 創建一個新的排序索引陣列
	newSortedIndices := make([]string, 0, len(components))
	for _, comp := range components {
		newSortedIndices = append(newSortedIndices, comp.Index)
	}

	// 檢查是否需要更新
	needsUpdate := false
	updateReason := ""
	
	// 檢查全域變數是否已初始化
	if SortedComponentIndices == nil {
		needsUpdate = true
		updateReason = "全域排序變數尚未初始化"
		logs.FInfo("需要更新原因: %s", updateReason)
	} else if len(newSortedIndices) != len(SortedComponentIndices) {
		needsUpdate = true
		updateReason = fmt.Sprintf("排序長度不同 (原有: %d, 新的: %d)", 
			len(SortedComponentIndices), len(newSortedIndices))
		logs.FInfo("需要更新原因: %s", updateReason)
	} else {
		// 逐一比較每個元素
		for i := 0; i < len(newSortedIndices); i++ {
			if newSortedIndices[i] != SortedComponentIndices[i] {
				needsUpdate = true
				updateReason = fmt.Sprintf("排序第 %d 位不同 (原有: %s, 新的: %s)",
					i+1, SortedComponentIndices[i], newSortedIndices[i])
				logs.FInfo("需要更新原因: %s", updateReason)
				break
			}
		}
	}

	// 如果需要更新
	if needsUpdate {
		logs.FInfo("排名已變化，需要更新熱門儀表板. 原因: %s", updateReason)
		
		// 更新全域變數
		SortedComponentIndices = newSortedIndices
		
		// 收集前 10 個最熱門組件的 ID (或所有組件，如果少於 10 個)
		limit := 10
		if len(components) < limit {
			limit = len(components)
		}
		
		// 創建一個整數陣列來存儲排序後的組件 ID
		topComponentIDs := make([]int, limit)
		componentDetails := make([]string, limit)
		for i := 0; i < limit; i++ {
			topComponentIDs[i] = int(components[i].ID)
			componentDetails[i] = fmt.Sprintf("ID:%d, 名稱:%s, 次數:%d", 
				components[i].ID, components[i].Name, components[i].Times)
		}
		
		logs.FInfo("前 %d 名組件詳情:", limit)
		for i, detail := range componentDetails {
			logs.FInfo("  第 %d 名: %s", i+1, detail)
		}
		
		// 更新 dashboards 表中名為 "熱門儀表板" 的 components 欄位
		logs.FInfo("開始更新熱門儀表板組件列表: %v", topComponentIDs)
		
		result := models.DBManager.Exec(`
			UPDATE dashboards 
			SET components = ?, updated_at = ? 
			WHERE name = ?`, 
			pq.Array(topComponentIDs), 
			time.Now(),
			"熱門儀表板")
			
		if result.Error != nil {
			logs.FError("更新熱門儀表板失敗: %v", result.Error)
		} else {
			rowsAffected := result.RowsAffected
			logs.FInfo("更新熱門儀表板成功! 影響的記錄數: %d", rowsAffected)
			if rowsAffected == 0 {
				logs.FWarn("沒有找到名為「熱門儀表板」的記錄，請確認記錄存在")
			}
		}
		
		c.JSON(http.StatusOK, gin.H{
			"status": "render",
		})
		return
	}

	logs.FInfo("組件排名沒有變化，不需要更新熱門儀表板")
	
	// 若所有元素都相同，回傳成功
	c.JSON(http.StatusOK, gin.H{
		"status": "success",
	})
}

/*
PlusOne increments the 'times' counter for a component by one
POST /api/v1/plusOne
Request body: {"index": "component_index"}
This API increments the 'times' field for the component with the specified index.

Response:
- status = "success" with updated component info if successful
- status = "error" if an error occurs
*/
func PlusOne(c *gin.Context) {
	logs.FInfo("PlusOne API 被呼叫 - 開始增加組件訪問次數")
	
	// 解析請求體參數
	type RequestBody struct {
		Index string `json:"index" binding:"required"`
	}
	
	var reqBody RequestBody
	if err := c.ShouldBindJSON(&reqBody); err != nil {
		logs.FError("解析請求參數失敗: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "無效的請求參數: " + err.Error(),
		})
		return
	}
	
	// 檢查 index 參數
	if reqBody.Index == "" {
		logs.FError("Index 參數不能為空")
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Index 參數不能為空",
		})
		return
	}
	
	logs.FInfo("嘗試增加組件 [%s] 的訪問次數", reqBody.Index)
	
	// 更新 components 表中指定 index 的 times 欄位 (+1)
	result := models.DBManager.Exec(`
		UPDATE components 
		SET times = times + 1 
		WHERE index = ?`, 
		reqBody.Index)
		
	if result.Error != nil {
		logs.FError("更新組件訪問次數失敗: %v", result.Error)
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "更新組件訪問次數失敗: " + result.Error.Error(),
		})
		return
	}
	
	// 檢查是否有更新任何記錄
	if result.RowsAffected == 0 {
		logs.FWarn("沒有找到 index 為 [%s] 的組件", reqBody.Index)
		c.JSON(http.StatusNotFound, gin.H{
			"status":  "error",
			"message": "找不到指定的組件",
		})
		return
	}
	
	// 查詢更新後的組件資料
	type Component struct {
		ID    int64  `json:"id" gorm:"column:id"`
		Index string `json:"index" gorm:"column:index"`
		Name  string `json:"name" gorm:"column:name"`
		Times int    `json:"times" gorm:"column:times"`
	}
	
	var component Component
	err := models.DBManager.Table("components").
		Where("index = ?", reqBody.Index).
		First(&component).Error
		
	if err != nil {
		logs.FError("獲取更新後的組件資料失敗: %v", err)
		// 即使無法獲取更新後的資料，我們仍返回成功，因為更新操作已經成功
		c.JSON(http.StatusOK, gin.H{
			"status":  "success",
			"message": "組件訪問次數已增加，但無法獲取更新後的資料",
		})
		return
	}
	
	logs.FInfo("成功增加組件 [%s] 的訪問次數，當前次數: %d", component.Index, component.Times)
	
	// 返回成功和更新後的組件資料
	c.JSON(http.StatusOK, gin.H{
		"status":    "success",
		"component": component,
	})
}

// CheckRank API is a RESTful endpoint that retrieves component data from the dashboardmanager database
// It supports pagination, sorting, filtering by city, and searching by component name or index
// The endpoint is accessible at /api/v1/checkRank and returns data in JSON format
