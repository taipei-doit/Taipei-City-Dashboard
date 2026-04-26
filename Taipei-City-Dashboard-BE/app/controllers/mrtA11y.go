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

// GetMrtAlertByType returns active-alert distinct station counts grouped by facility type.
// GET /api/v1/mrt/a11y/alert-by-type
func GetMrtAlertByType(c *gin.Context) {
	data, categories, err := models.GetMrtAlertByType()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})
}

// GetMrtAlertTrend30d returns per-line alert count over the past 30 days as three_d bar data.
// GET /api/v1/mrt/a11y/alert-trend-30d
func GetMrtAlertTrend30d(c *gin.Context) {
	data, categories, err := models.GetMrtAlertTrend30d()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})
}

// GetMrtStations returns every elevator/ramp exit point with its latest active alert (if any).
// GET /api/v1/mrt/a11y/stations
func GetMrtStations(c *gin.Context) {
	data, err := models.GetMrtStations()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// GetMrtStationOverview returns a 2-row alert / normal summary of distinct stations.
// GET /api/v1/mrt/a11y/station-overview
func GetMrtStationOverview(c *gin.Context) {
	data, err := models.GetMrtStationOverview()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}
