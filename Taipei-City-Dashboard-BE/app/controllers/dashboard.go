// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"net/http"
	"strings"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

/*
GetAllDashboards retrieves all dashboards from the database
GET /api/v1/dashboard
Guest: Only public dashboards
User, Admin: Public and personal dashboards
*/
func GetAllDashboards(c *gin.Context) {
	// Get the user info from the context
	_, _, _, _, permissions := util.GetUserInfoFromContext(c)
	groups := util.GetPermissionAllGroupIDs(permissions)

	// Remove public group(id=1) from groups if exist
	var personalGroups []int
	for _, groupID := range groups {
		if groupID != 1 { // Assuming public group id is 1
			personalGroups = append(personalGroups, groupID)
		}
	}

	dashboards, err := models.GetAllDashboards(personalGroups)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboards})
}

/*
GetDashboardByIndex retrieves a dashboard and it's component configs from the database by index.
GET /api/v1/dashboard/:index
Guest: Only public dashboards
User, Admin: Public and personal dashboards
*/
func GetDashboardByIndex(c *gin.Context) {
	_, _, _, _, permissions := util.GetUserInfoFromContext(c)
	groups := util.GetPermissionAllGroupIDs(permissions)

	dashboardIndex := c.Param("index")

	components, err := models.GetDashboardByIndex(dashboardIndex, groups)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": components})
}

/*
CheckDashboardIndex checks if a dashboard index is available.
GET /api/v1/dashboard/check-index/:index
Guest, User: Forbidden
Admin: Allowed
*/
func CheckDashboardIndex(c *gin.Context) {
	dashboardIndex := c.Param("index")

	available, err := models.CheckDashboardIndex(dashboardIndex)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusAccepted, gin.H{"status": "success", "available": available})
}

/*
CreatePersonalDashboard creates a new dashboard in the database
POST /api/v1/dashboard
Guest: Forbidden
User, Admin: Allowed
*/
func CreatePersonalDashboard(c *gin.Context) {
	var dashboard models.Dashboard

	_, accountID, _, _, permissions := util.GetUserInfoFromContext(c)

	// Get Group ID
	groupID, err := models.GetUserPersonalGroup(accountID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// check has permission, role admin(id=1) editor(id=2)
	if !util.HasPermission(permissions, groupID, 1) && !util.HasPermission(permissions, groupID, 2) {
		c.JSON(http.StatusUnauthorized, gin.H{"message": "permission denied"})
		return
	}

	// Bind the JSON body to the dashboard struct
	err = c.ShouldBindJSON(&dashboard)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Check for invalid fields
	if dashboard.Name == "" || dashboard.Icon == "" || dashboard.Components == nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Missing required fields. Please provide a name, icon, and components array."})
		return
	}

	// Create the dashboard
	index := uuid.New().String()
	dashboard.Index = strings.Split(index, "-")[0] + strings.Split(index, "-")[1]
	dashboard, err = models.CreateDashboard(dashboard.Index, dashboard.Name, dashboard.Icon, dashboard.Components, groupID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
CreatePublicDashboard creates a new public dashboard in the database
POST /api/v1/dashboard/public
Guest, User: Forbidden
Admin: Allowed
*/
func CreatePublicDashboard(c *gin.Context) {
	var dashboard models.Dashboard

	_, _, _, _, permissions := util.GetUserInfoFromContext(c)

	// Get Group public(id=1)
	groupID := 1

	// check has permission, role admin(id=1) editor(id=2)
	if !util.HasPermission(permissions, groupID, 1) && !util.HasPermission(permissions, groupID, 2) {
		c.JSON(http.StatusUnauthorized, gin.H{"message": "permission denied"})
		return
	}

	// Bind the JSON body to the dashboard struct
	err := c.ShouldBindJSON(&dashboard)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Check for invalid fields
	if dashboard.Name == "" || dashboard.Icon == "" || dashboard.Index == "" || dashboard.Components == nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Missing required fields. Please provide an index, name, icon, and components array."})
		return
	}

	// Create the dashboard
	dashboard, err = models.CreateDashboard(dashboard.Index, dashboard.Name, dashboard.Icon, dashboard.Components, groupID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
UpdateDashboard updates a dashboard in the database
PATCH /api/v1/dashboard/:index
Guest: Forbidden
User: Only personal dashboards
Admin: Public and personal dashboards
*/
func UpdateDashboard(c *gin.Context) {
	var dashboard models.Dashboard

	_, _, _, _, permissions := util.GetUserInfoFromContext(c)
	adminGroups := util.GetPermissionGroupIDs(permissions, 1)  // role=admin
	editorGroups := util.GetPermissionGroupIDs(permissions, 2) // role=editor
	groups := util.MergeAndRemoveDuplicates(adminGroups, editorGroups)

	dashboardIndex := c.Param("index")

	err := c.ShouldBindJSON(&dashboard)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Update the dashboard
	dashboard, err = models.UpdateDashboard(dashboardIndex, dashboard.Name, dashboard.Icon, dashboard.Components, groups)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
DeleteDashboard deletes a dashboard from the database
DELETE /api/v1/dashboard/:index
Guest: Forbidden
User: Only personal dashboards
Admin: Public and personal dashboards
*/
func DeleteDashboard(c *gin.Context) {
	_, _, _, _, permissions := util.GetUserInfoFromContext(c)
	adminGroups := util.GetPermissionGroupIDs(permissions, 1)  // role=admin
	editorGroups := util.GetPermissionGroupIDs(permissions, 2) // role=editor
	groups := util.MergeAndRemoveDuplicates(adminGroups, editorGroups)

	dashboardIndex := c.Param("index")

	// Delete the dashboard
	err := models.DeleteDashboard(dashboardIndex, groups)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success"})
}
