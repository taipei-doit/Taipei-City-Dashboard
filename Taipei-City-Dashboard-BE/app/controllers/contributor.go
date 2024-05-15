package controllers

import (
	"net/http"
	"strconv"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

/*
GetAllContributors returns the contributor information
GET /api/v1/contributor
*/
func GetAllContributors(c *gin.Context) {
	type contributorQuery struct {
		PageSize int    `form:"pagesize"`
		PageNum  int    `form:"pagenum"`
		Sort     string `form:"sort"`
		Order    string `form:"order"`
	}

	// Get query parameters
	var query contributorQuery
	c.ShouldBindQuery(&query)

	contributors, totalContributors, err := models.GetAllContributors(query.PageSize, query.PageNum, query.Sort, query.Order)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalContributors, "data": contributors})
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

	if contributor.UserID == "" || contributor.UserName == "" || contributor.Image == "" || contributor.Link == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "user_id, user_name, image and link info is required"})
		return
	}

	contributor, err := models.CreateContributor(contributor.UserID, contributor.UserName, contributor.Image, contributor.Link, contributor.Identity, contributor.Description, contributor.Include)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": contributor})
}

/*
UpdateContributor updates the contributor information
PATCH /api/v1/contributor/:id
*/
func UpdateContributor(c *gin.Context) {
	ID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid contributor ID"})
		return
	}

	// 1. Check if the contributor exists
	contributor, err := models.GetContributorByID(ID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No contributor found"})
		return
	}

	// 2. Bind the JSON body to the contributor struct
	err = c.ShouldBindJSON(&contributor)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 3. Update the contributor
	contributor, err = models.UpdateContributor(ID, contributor.UserID, contributor.UserName, contributor.Image, contributor.Link, contributor.Identity, contributor.Description, contributor.Include)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update contributor"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": contributor})
}

/*
DeleteContributor deletes a contributor from the database.
DELETE /api/v1/contributor/:id
*/
func DeleteContributor(c *gin.Context) {
	// 1. Get the contributor ID from the context
	ID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid contributor ID"})
		return
	}

	// 2. Delete the contributor
	contributorStatus, err := models.DeleteContributorByID(ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "contributor_deleted": contributorStatus})
}
