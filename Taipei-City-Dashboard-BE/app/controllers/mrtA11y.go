package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

// GetMrtAlertCount returns active alert count as two_d card data.
// GET /api/v1/mrt/a11y/alert-count
func GetMrtAlertCount(c *gin.Context) {
	data, err := models.GetMrtAlertCount()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// GetMrtAlertByLine returns per-line abnormal station counts as three_d bar data.
// GET /api/v1/mrt/a11y/alert-by-line
func GetMrtAlertByLine(c *gin.Context) {
	data, categories, err := models.GetMrtAlertByLine()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})
}

// GetMrtAlertByType returns per-equipment-type counts as percent pie data.
// GET /api/v1/mrt/a11y/alert-by-type
func GetMrtAlertByType(c *gin.Context) {
	data, categories, err := models.GetMrtAlertByType()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})
}

// GetMrtStationOverview returns normal/alert station counts as map_legend data.
// GET /api/v1/mrt/a11y/station-overview
func GetMrtStationOverview(c *gin.Context) {
	data, err := models.GetMrtStationOverview()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}
