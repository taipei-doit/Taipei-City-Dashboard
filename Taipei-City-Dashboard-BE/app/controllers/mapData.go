package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

func GetMapGeoJSON(c *gin.Context) {
	geojson, err := models.GetMapGeoJSON(c.Param("index"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.Data(http.StatusOK, "application/geo+json; charset=utf-8", geojson)
}
