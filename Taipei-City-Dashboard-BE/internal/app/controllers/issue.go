package controllers

import (
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"

	"github.com/gin-gonic/gin"
)

/*
GetAllIssues retrieves all issues from the database.
GET /api/v1/issue

| Param          | Description                                     | Value         | Default |
| -------------- | ----------------------------------------------- | ------------- | ------- |
| pagesize       | Number of issues per page.                      | `int`         | -       |
| pagenum        | Page number. Only works if pagesize is defined. | `int`         | 1       |
| filterbystatus | Text strings to filter status by                | `string[]`    | -       |
| sort           | The column to sort by.                          | `string`      | -       |
| order          | Ascending or descending.                        | `asc`, `desc` | `asc`   |
*/

type issueQuery struct {
	PageSize       int    `form:"pagesize"`
	PageNum        int    `form:"pagenum"`
	FilterByStatus string `form:"filterbystatus"`
	Sort           string `form:"sort"`
	Order          string `form:"order"`
}

func GetAllIssues(c *gin.Context) {
	var issues []models.Issue
	var totalIssues int64
	var resultNum int64

	// Get query parameters
	var query issueQuery
	c.ShouldBindQuery(&query)

	// Create Temp DB
	tempDB := postgres.DBManager.Table("issues")

	// Count the total amount of issues
	tempDB.Count(&totalIssues)

	// Filter by status
	if query.FilterByStatus != "" {
		statuses := strings.Split(query.FilterByStatus, ",")
		tempDB = tempDB.Where("issues.status IN (?)", statuses)
	}

	tempDB.Count(&resultNum)

	// Sort the issues
	if query.Sort != "" {
		tempDB = tempDB.Order("issues." + query.Sort + " " + query.Order)
	}

	// Paginate the issues
	if query.PageSize > 0 {
		tempDB = tempDB.Limit(query.PageSize)
		if query.PageNum > 0 {
			tempDB = tempDB.Offset((query.PageNum - 1) * query.PageSize)
		}
	}

	// Get the issues
	err := tempDB.Find(&issues).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalIssues, "results": resultNum, "data": issues})
}

/*
CreateIssue creates a new issue.
POST /api/v1/issue
*/

func CreateIssue(c *gin.Context) {
	var issue models.Issue

	// Bind the issue data
	if err := c.ShouldBindJSON(&issue); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	issue.CreatedAt = time.Now()
	issue.UpdatedAt = time.Now()
	issue.Status = "待處理"

	if issue.Title == "" || issue.Description == "" || issue.UserName == "" || issue.UserID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "title, description, user info is required"})
		return
	}

	// Create the issue
	err := postgres.DBManager.Create(&issue).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": issue})
}

/*
UpdateIssueByID modifies an issue by its ID.
PATCH /api/v1/issue/:id
*/
func UpdateIssueByID(c *gin.Context) {
	var issue models.UpdateIssue

	issueID := c.Param("id")

	// Bind the issue data
	if err := c.ShouldBindJSON(&issue); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	issue.UpdatedAt = time.Now()

	if issue.UpdatedBy == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "updated_by is required"})
		return
	}

	// Update the issue
	err := postgres.DBManager.Table("issues").Where("id = ?", issueID).Updates(issue).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": issue})
}
