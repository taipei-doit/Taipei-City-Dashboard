package controllers

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

func GetIncident(c *gin.Context) {
	type incidentQuery struct {
		PageSize       int    `form:"pagesize"`
		PageNum        int    `form:"pagenum"`
		FilterByStatus string `form:"filterbystatus"`
		Sort           string `form:"sort"`
		Order          string `form:"order"`
	}

	// Get query parameters
	var query incidentQuery
	c.ShouldBindQuery(&query)
	
	incidents, totalIncidents, resultNum, err := models.GetAllIncident(query.PageSize, query.PageNum, query.FilterByStatus, query.Sort, query.Order)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalIncidents, "results": resultNum, "data": incidents})
}

func CreateIncident(c *gin.Context) {
	var incident models.Incident
	// var buf bytes.Buffer
	// _, err := io.Copy(&buf, c.Request.Body)
	// if err != nil {
	// 		// Handle error
	// 		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read request body"})
	// 		return
	// }
	
	// Convert buffer to string
	// requestBody := buf.String()
	// fmt.Println(requestBody)

	// Bind the issue data
	if err := c.ShouldBindJSON(&incident); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if incident.Type == "" || incident.Description == "" || incident.Distance == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "title, description, distance info is required"})
		return
	}

	tmpIncident, err := models.CreateIncident(incident.Type, incident.Description, incident.Distance, incident.Latitude, incident.Longitude, incident.Status)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"status": "success", "data": tmpIncident})
}

func UpdateIncidentByID(c *gin.Context) {
	var incident models.Incident

	incidentID := c.Param("id")

	// Bind the incident data
	if err := c.ShouldBindJSON(&incident); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	incident, err := models.UpdateIncidentByID(incidentID, incident.Status)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": incident})
}

func DeleteIncident(c *gin.Context) {
	var incident models.Incident

	// Bind the issue data
	if err := c.ShouldBindJSON(&incident); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// if incident.Type == "" || incident.Description == "" || incident.Distance == 0 {
	// 	c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "title, description, distance info is required"})
	// 	return
	// }

	tmpIncident, err := models.DeleteIncident(incident.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": tmpIncident})
}
