// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/global"

	"github.com/gin-gonic/gin"
)

type componentAISummaryQuery struct {
	Index string `form:"index"`
	City  string `form:"city"`
	Type  string `form:"type"`
}

// GetComponentAISummary retrieves AI summary content by index, city, and type.
func GetComponentAISummary(c *gin.Context) {
	var query componentAISummaryQuery

	if err := c.ShouldBindQuery(&query); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": err.Error(),
		})
		return
	}

	// index 參數為必填
	if query.Index == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Index parameter is required",
		})
		return
	}

	// city 有帶才驗證
	if query.City != "" &&
		query.City != "taipei" &&
		query.City != "metrotaipei" {

		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Invalid City Name",
		})
		return
	}

	summary, err := models.GetComponentAISummary(
		query.Index,
		query.City,
		query.Type,
	)

	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"status":  "error",
			"message": "ai summary not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data":   summary,
	})
}

type triggerDAGReq struct {
	Index string `json:"index" binding:"required"`
	City  string `json:"city"`
	Type  string `json:"type"`
}

// TriggerComponentAISummaryDAG triggers the Airflow DAG for component AI summary generation.
func TriggerComponentAISummaryDAG(c *gin.Context) {
	var req triggerDAGReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Index parameter is required",
		})
		return
	}

	// 驗證 type 參數限制為 chart 或 map
	if req.Type != "" && req.Type != "chart" && req.Type != "map" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Type must be either 'chart' or 'map'",
		})
		return
	}

	conf := map[string]string{
		"index": req.Index,
	}
	if req.City != "" {
		conf["city"] = req.City
	}
	if req.Type != "" {
		conf["type"] = req.Type
	}

	payload := map[string]interface{}{
		"conf": conf,
	}

	jsonBytes, err := json.Marshal(payload)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to encode request payload",
		})
		return
	}

	baseURL := strings.TrimRight(global.Airflow.BaseURL, "/")
	targetURL := fmt.Sprintf("%s/api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns", baseURL)
	httpReq, err := http.NewRequestWithContext(c.Request.Context(), http.MethodPost, targetURL, bytes.NewBuffer(jsonBytes))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to create HTTP request",
		})
		return
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(global.Airflow.SvcUser, global.Airflow.SvcPass)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"status":  "error",
			"message": "Failed to connect to Airflow service: " + err.Error(),
		})
		return
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to read Airflow response",
		})
		return
	}

	var jsonResp map[string]interface{}
	if err := json.Unmarshal(respBody, &jsonResp); err != nil {
		c.JSON(resp.StatusCode, gin.H{
			"status": "error",
			"raw":    string(respBody),
		})
		return
	}

	c.JSON(resp.StatusCode, jsonResp)
}

// GetComponentAISummaryDAGStatus queries the status of a specific Airflow DAG run.
func GetComponentAISummaryDAGStatus(c *gin.Context) {
	dagRunID := c.Param("dag_run_id")
	if dagRunID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "dag_run_id parameter is required",
		})
		return
	}

	escapedID := url.PathEscape(dagRunID)
	baseURL := strings.TrimRight(global.Airflow.BaseURL, "/")
	targetURL := fmt.Sprintf("%s/api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns/%s", baseURL, escapedID)


	httpReq, err := http.NewRequestWithContext(c.Request.Context(), http.MethodGet, targetURL, nil)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to create HTTP request",
		})
		return
	}

	httpReq.SetBasicAuth(global.Airflow.SvcUser, global.Airflow.SvcPass)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"status":  "error",
			"message": "Failed to connect to Airflow service: " + err.Error(),
		})
		return
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "error",
			"message": "Failed to read Airflow response",
		})
		return
	}

	var jsonResp map[string]interface{}
	if err := json.Unmarshal(respBody, &jsonResp); err != nil {
		c.JSON(resp.StatusCode, gin.H{
			"status": "error",
			"raw":    string(respBody),
		})
		return
	}

	c.JSON(resp.StatusCode, jsonResp)
}

