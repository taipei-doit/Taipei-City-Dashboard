package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

/*
GetAllIssues retrieves all issues from the database
GET /api/v1/issue

| Param          | Description                                     | Value         | Default |
| -------------- | ----------------------------------------------- | ------------- | ------- |
| pagesize       | Number of issues per page.                      | `int`         | -       |
| pagenum        | Page number. Only works if pagesize is defined. | `int`         | 1       |
| filterbystatus | Text strings to filter status by                | `string[]`    | -       |
| sort           | The column to sort by.                          | `string`      | -       |
| order          | Ascending or descending.                        | `asc`, `desc` | `asc`   |
*/

func GetAllIssues(c *gin.Context) {
	type issueQuery struct {
		PageSize       int    `form:"pagesize"`
		PageNum        int    `form:"pagenum"`
		FilterByStatus string `form:"filterbystatus"`
		Sort           string `form:"sort"`
		Order          string `form:"order"`
	}

	// Get query parameters
	var query issueQuery
	c.ShouldBindQuery(&query)

	issues, totalIssues, resultNum, err := models.GetAllIssues(query.PageSize, query.PageNum, query.FilterByStatus, query.Sort, query.Order)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalIssues, "results": resultNum, "data": issues})
}

/*
CreateIssue creates a new issue
POST /api/v1/issue
*/

func CreateIssue(c *gin.Context) {
	var issue models.Issue

	// Bind the issue data
	if err := c.ShouldBindJSON(&issue); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if issue.Title == "" || issue.Description == "" || issue.UserName == "" || issue.UserID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "title, description, user info is required"})
		return
	}

	issue, err := models.CreateIssue(issue.Title, issue.UserName, issue.UserID, issue.Context, issue.Description)
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
	var issue models.Issue

	issueID := c.Param("id")

	// Bind the issue data
	if err := c.ShouldBindJSON(&issue); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if issue.UpdatedBy == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "updated_by is required"})
		return
	}

	issue, err := models.UpdateIssueByID(issueID, issue.Status, issue.DecisionDesc, issue.UpdatedBy)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": issue})
}
