// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

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
			"status": "error",
			"message": err.Error(),
		})
		return
	}

	// city 有帶才驗證
	if query.City != "" &&
		query.City != "taipei" &&
		query.City != "metrotaipei" {

		c.JSON(http.StatusBadRequest, gin.H{
			"status": "error",
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
			"status": "error",
			"message": "ai summary not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": summary,
	})
}
