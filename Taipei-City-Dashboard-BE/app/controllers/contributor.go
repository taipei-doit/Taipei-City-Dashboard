package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

/*
GetContributorInfo returns the contributor information
GET /api/v1/contributor
*/
func GetContributorInfo(c *gin.Context) {
	type contributorQuery struct {
		PageSize       int    `form:"pagesize"`
		PageNum        int    `form:"pagenum"`
		FilterByStatus int    `form:"filterbystatus"`
		Sort           string `form:"sort"`
		Order          string `form:"order"`
	}

	// Get query parameters
	var query contributorQuery
	c.ShouldBindQuery(&query)

	contributors, totalContributors, resultNum, err := models.GetAllContributors(query.PageSize, query.PageNum, query.FilterByStatus, query.Sort, query.Order)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalContributors, "results": resultNum, "data": contributors})
}
