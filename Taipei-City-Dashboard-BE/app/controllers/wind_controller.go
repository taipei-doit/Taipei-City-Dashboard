package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/global"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// GetRealTimeWindData 取得台北市即時觀測風速與風向
func GetRealTimeWindData(c *gin.Context) {
	// 這裡建議對接氣象署 (CWA) API 或台北市 Open Data
	// 目前先回傳一個 Mock 數據，你可以隨後更換為真正的爬蟲或 API 呼叫邏輯
	data := gin.H{
		"station":   "信義國中",
		"wind_dir":  45,    // 單位：度
		"wind_speed": 3.2,   // 單位：m/s
		"temp":       26.5,
		"timestamp":  global.GetLocalTime(), // 假設 global 有時間處理函式
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data":   data,
	})
}

// CreateWindSimulation 儲存前端運算後的熱力圖快照
func CreateWindSimulation(c *gin.Context) {
	var sim models.WindSimulation
	
	// 綁定 JSON，這包含你前端傳來的 WindComfortGrid 數值
	if err := c.ShouldBindJSON(&sim); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid simulation data: " + err.Error()})
		return
	}

	// 取得當前使用者 ID (從 JWT Middleware 傳入)
	userID, exists := c.Get("userID")
	if exists {
		sim.CreatedBy = userID.(uint)
	}

	// 呼叫 Model 儲存進資料庫 (建議使用 PostgreSQL JSONB 欄位儲存 Grid)
	if err := models.SaveSimulation(&sim); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save simulation"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "Simulation saved successfully",
		"id":      sim.ID,
	})
}

// GetAllWindSimulations 取得所有歷史模擬記錄
func GetAllWindSimulations(c *gin.Context) {
	simulations, err := models.GetSimulations()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch simulations"})
		return
	}

	c.JSON(http.StatusOK, simulations)
}

// GetWindSimulationByID 取得特定模擬細節
func GetWindSimulationByID(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	
	sim, err := models.GetSimulationByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Simulation not found"})
		return
	}

	c.JSON(http.StatusOK, sim)
}

// DeleteWindSimulation 刪除紀錄
func DeleteWindSimulation(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	
	if err := models.DeleteSimulation(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Delete failed"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Simulation deleted"})
}