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

/*
CreateContributor creates a new contributor
POST /api/v1/contributor
*/

func CreateContributor(c *gin.Context) {
	var contributor models.Contributor

	// Bind the contributor data
	if err := c.ShouldBindJSON(&contributor); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if contributor.UserID == "" ||  contributor.UserName == ""|| contributor.Image == "" || contributor.Link == ""{
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "user_id, user_name, image link info is required"})
		return
	}

	contributor, err := models.CreateContributor(contributor.UserID, contributor.UserName, contributor.Image, contributor.Link)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": contributor})
}
