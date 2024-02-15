// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/internal/auth"
	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/lib/pq"
)

/*
GetAllDashboards retrieves all dashboards from the database.
GET /api/v1/dashboard
Guest: Only public dashboards
User, Admin: Public and personal dashboards
*/
func GetAllDashboards(c *gin.Context) {
	type allDashboards struct {
		Public   []models.Dashboard `json:"public"`
		Personal []models.Dashboard `json:"personal"`
	}
	var dashboards allDashboards

	// 1. Get the user info from the context
	_, _, _, _, permissions := auth.GetUserInfoFromContext(c)

	groups := auth.GetPermissionAllGroupIDs(permissions)
	// 3. Get all the personal dashboards
	err := postgres.DBManager.
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", groups).
		Order("dashboards.id").
		Find(&dashboards.Personal).
		Error
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
	tempDB := createTempComponentDB()
	type componentArray struct {
		Components pq.Int64Array `gorm:"type:int[]"`
	}
	var componentIds componentArray
	var components []models.Component

	_, _, _, _, permissions := auth.GetUserInfoFromContext(c) // accountType, accountID, isAdmin, expiresAt, permissions
	groups := auth.GetPermissionAllGroupIDs(permissions)

	// 1. Get the dashboard index from the context
	dashboardIndex := c.Param("index")

	// 2. Find the dashboard and component ids
	err := postgres.DBManager.Table("dashboards").Select("components").Where("index = ?", dashboardIndex).First(&componentIds).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": err.Error()})
		return
	}
	err = postgres.DBManager.
		Table("dashboards").Select("components").
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", dashboardIndex).
		Order("dashboards.id").
		First(&componentIds).
		Error
	if err != nil {
		c.JSON(http.StatusForbidden, gin.H{"status": "error", "message": "You do not have permission to view this dashboard."})
		return
	}

	// 3. Format component ids into slice and string
	var componentIdsSlice []int64
	for _, v := range componentIds.Components {
		componentIdsSlice = append(componentIdsSlice, int64(v))
	}

	if len(componentIdsSlice) == 0 {
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": components})
		return
	}

	var componentIdsString string
	for i, v := range componentIdsSlice {
		if i > 0 {
			componentIdsString += ","
		}
		componentIdsString += fmt.Sprintf("%d", v)
	}

	// 4. Get components by ids
	err = tempDB.
		Where(componentIdsSlice).
		Order(fmt.Sprintf("ARRAY_POSITION(ARRAY[%s], components.id)", componentIdsString)).
		Find(&components).Error

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
	var dashboard models.Dashboard

	// 1. Get the dashboard index from the context
	dashboardIndex := c.Param("index")

	// 2. If no dashboards exist with the index, return true
	err := postgres.DBManager.Table("dashboards").Where("index = ?", dashboardIndex).First(&dashboard).Error
	if err != nil {
		if (err.Error() == "record not found") || strings.Contains(err.Error(), "no rows in result set") {
			c.JSON(http.StatusOK, gin.H{"status": "success", "available": true})
			return
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
			return
		}
	}

	// 3. If a dashboard exists with the index, return false
	c.JSON(http.StatusAccepted, gin.H{"status": "success", "available": false})
}

// func IsAdmin(userID int) bool {
// 	// Here you would typically query the database to check if the user with the given userID is an admin.
// 	// For instance, you might have a query like this:
// 	var user models.AuthUser
// 	if err := postgres.DBManager.Where("id = ? AND is_admin = ?", userID, true).First(&user).Error; err != nil {
// 		// Handle the error, such as log it or return false if the user is not found or there's an error during the query.
// 		return false
// 	}

// 	// If the user is found and is an admin, return true.
// 	return user.IsAdmin
// }

/*
CreatePersonalDashboard creates a new dashboard in the database.
POST /api/v1/dashboard
Guest: Forbidden
User, Admin: Allowed
*/
func CreatePersonalDashboard(c *gin.Context) {
	var dashboard models.Dashboard

	_, accountID, _, _, permissions := auth.GetUserInfoFromContext(c)

	// Get Group ID
	// groupId := c.GetInt("group_id")
	groupId, err := auth.GetUserPersonalGroup(accountID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// check has permission, role admin(id=1) editor(id=2)
	if !auth.HasPermission(permissions, groupId, 1) && !auth.HasPermission(permissions, groupId, 2) {
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
	dashboard, err = auth.CreateDashboard(dashboard.Index, dashboard.Name, dashboard.Icon, groupId)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
CreatePublicDashboard creates a new public dashboard in the database.
POST /api/v1/dashboard/public
Guest, User: Forbidden
Admin: Allowed
*/
func CreatePublicDashboard(c *gin.Context) {
	var dashboard models.Dashboard

	_, _, _, _, permissions := auth.GetUserInfoFromContext(c)

	// Get Group public(id=1)
	groupId := 1

	// check has permission, role admin(id=1) editor(id=2)
	if !auth.HasPermission(permissions, groupId, 1) && !auth.HasPermission(permissions, groupId, 2) {
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
	dashboard, err = auth.CreateDashboard(dashboard.Index, dashboard.Name, dashboard.Icon, groupId)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
UpdateDashboard updates a dashboard in the database.
PATCH /api/v1/dashboard/:index
Guest: Forbidden
User: Only personal dashboards
Admin: Public and personal dashboards
*/
func UpdateDashboard(c *gin.Context) {
	var dashboard models.UpdateDashboard

	_, _, _, _, permissions := auth.GetUserInfoFromContext(c)
	adminGroups := auth.GetPermissionGroupIDs(permissions, 1)  // role=admin
	editorGroups := auth.GetPermissionGroupIDs(permissions, 2) // role=editor
	// Merge and remove duplicates from the two groups
	groups := auth.MergeAndRemoveDuplicates(adminGroups, editorGroups)
	// // if roles contains admin (id=1)
	// if slices.Contains(roles, 1) {
	// 	groups = append(groups, 1)
	// }

	// // check has permission, role admin(id=1) editor(id=2)
	// if !auth.HasPermission(permissions, groupId, 1) && !auth.HasPermission(permissions, groupId, 2) {
	// 	c.JSON(http.StatusUnauthorized, gin.H{"message": "permission denied"})
	// 	return
	// }

	// 1. Get the dashboard index from the context
	dashboardIndex := c.Param("index")

	// 2. Find the dashboard
	err := postgres.DBManager.Table("dashboards").Where("index = ?", dashboardIndex).First(&dashboard).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": err.Error()})
		return
	}
	err = postgres.DBManager.
		Table("dashboards").
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", dashboardIndex).
		First(&dashboard).
		Error
	if err != nil {
		c.JSON(http.StatusForbidden, gin.H{"status": "error", "message": "You do not have permission to edit this dashboard."})
		return
	}

	// 3. Bind the JSON body to the dashboard struct
	err = c.ShouldBindJSON(&dashboard)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}
	dashboard.UpdatedAt = time.Now()
	dashboard.Index = dashboardIndex

	// 4. Update the dashboard
	err = postgres.DBManager.Table("dashboards").Where("index = ?", dashboardIndex).Updates(&dashboard).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboard})
}

/*
DeleteDashboard deletes a dashboard from the database.
DELETE /api/v1/dashboard/:index
Guest: Forbidden
User: Only personal dashboards
Admin: Public and personal dashboards
*/
func DeleteDashboard(c *gin.Context) {
	var dashboard models.Dashboard
	var dashboardGroup models.DashboardGroup
	var deletedGroup models.DashboardGroup

	// GetUserInfoFromContext
	_, _, _, _, permissions := auth.GetUserInfoFromContext(c)
	adminGroups := auth.GetPermissionGroupIDs(permissions, 1)  // role=admin
	editorGroups := auth.GetPermissionGroupIDs(permissions, 2) // role=editor
	// Merge and remove duplicates from the two groups
	groups := auth.MergeAndRemoveDuplicates(adminGroups, editorGroups)

	// // if user role contains admin add group public
	// if slices.Contains(roles, 1) {
	// 	groups = append(groups, 1)
	// }

	// 1. Get the dashboard index from the context
	dashboardIndex := c.Param("index")

	// 2. Check if the dashboard exists
	err := postgres.DBManager.Table("dashboards").Where("index = ?", dashboardIndex).First(&dashboard).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": err.Error()})
		return
	}
	err = postgres.DBManager.
		Select("dashboard_groups.group_id").
		Joins("JOIN dashboards ON dashboard_groups.dashboard_id = dashboards.id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", dashboardIndex).
		First(&deletedGroup).
		Error
	if err != nil {
		c.JSON(http.StatusForbidden, gin.H{"status": "error", "message": "You do not have permission to delete this dashboard."})
		return
	}

	// 3. Delete the dashboard group
	err = postgres.DBManager.Table("dashboard_groups").Where("dashboard_id = ?", dashboard.ID).Delete(&dashboardGroup).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if deletedGroup.GroupID != 1 {
		err := auth.DeleteGroup(deletedGroup.GroupID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Dashboard is deleted but Failed to delete auth group."})
			return
		}
	}

	// 4. Delete the dashboard
	err = postgres.DBManager.Table("dashboards").Where("index = ?", dashboardIndex).Delete(&dashboard).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// The cause group id is auto-incremented and thus will not repeat.
	// Additionally, after the JWT token expires, it will be regenerated.

	c.JSON(http.StatusOK, gin.H{"status": "success"})
}
