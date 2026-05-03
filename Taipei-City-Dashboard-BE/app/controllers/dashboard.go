// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"context"
	"errors"
	"net/http"
	"strings"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

/*
GetAllDashboards retrieves all dashboards from the database
GET /api/v1/dashboard
Guest: Only public dashboards
User, Admin: Public and personal dashboards
*/
func GetAllDashboards(c *gin.Context) {
	// Get the user info from the context
	_, accountID, _, _, permissions := util.GetUserInfoFromContext(c)
	groups := util.GetPermissionAllGroupIDs(permissions)
	// _, _, _, _, permissions := util.GetUserInfoFromContext(c)
	// groups := util.GetPermissionAllGroupIDs(permissions)

	// Remove public group(id=1) from groups if exist
	// var personalGroups []int
	// for _, groupID := range groups {
	// 	if groupID != 1 { // Assuming public group id is 1
	// 		personalGroups = append(personalGroups, groupID)
	// 	}
	// }
	
	dashboards, err := models.GetAllDashboards(accountID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if lang, ok := c.Get("lang"); ok && global.GlobalTranslator != nil {
		targetLang := lang.(string)
		ctx := c.Request.Context()
		translateDashboardNames(ctx, dashboards.Public, targetLang)
		translateDashboardNames(ctx, dashboards.Taipei, targetLang)
		translateDashboardNames(ctx, dashboards.MetroTaipei, targetLang)
		translateDashboardNames(ctx, dashboards.Personal, targetLang)
	}

	// Optional: also return current dashboard components (translated) in the same response
	includeIndex := c.Query("includeIndex")
	includeCity := c.Query("city")
	if includeIndex != "" {
		components, err := models.GetDashboardByIndex(includeIndex, groups, includeCity)
		if err == nil {
			if lang, ok := c.Get("lang"); ok && global.GlobalTranslator != nil {
				targetLang := lang.(string)
				ctx := c.Request.Context()
				for i := range components {
					components[i].Name = global.GlobalTranslator.Translate(ctx, components[i].Name, targetLang, "component_name")
					components[i].ShortDesc = global.GlobalTranslator.Translate(ctx, components[i].ShortDesc, targetLang, "short_desc")
					components[i].Source = global.GlobalTranslator.Translate(ctx, components[i].Source, targetLang, "source")
					components[i].LongDesc = global.GlobalTranslator.Translate(ctx, components[i].LongDesc, targetLang, "long_desc")
					components[i].UseCase = global.GlobalTranslator.Translate(ctx, components[i].UseCase, targetLang, "use_case")
				}
			}
			c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboards, "included_components": components})
			return
		}
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": dashboards})
}

func translateDashboardNames(ctx context.Context, list []models.Dashboard, targetLang string) {
	if global.GlobalTranslator == nil {
		return
	}
	for i := range list {
		list[i].Name = global.GlobalTranslator.Translate(ctx, list[i].Name, targetLang, "dashboard_name")
	}
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
	city := c.Query("city")

	components, err := models.GetDashboardByIndex(dashboardIndex, groups, city)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound){
			c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": err.Error()})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Translation: header strings plus long_desc / use_case for component-info UI; omit chart payloads.
	if lang, ok := c.Get("lang"); ok && global.GlobalTranslator != nil {
		targetLang := lang.(string)
		ctx := c.Request.Context()
		for i := range components {
			components[i].Name = global.GlobalTranslator.Translate(ctx, components[i].Name, targetLang, "component_name")
			components[i].ShortDesc = global.GlobalTranslator.Translate(ctx, components[i].ShortDesc, targetLang, "short_desc")
			components[i].Source = global.GlobalTranslator.Translate(ctx, components[i].Source, targetLang, "source")
			components[i].LongDesc = global.GlobalTranslator.Translate(ctx, components[i].LongDesc, targetLang, "long_desc")
			components[i].UseCase = global.GlobalTranslator.Translate(ctx, components[i].UseCase, targetLang, "use_case")
		}
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
		// c.JSON(http.StatusUnauthorized, gin.H{"message": "permission denied"})
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "permission denied"})
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

	var query componentQuery
	c.ShouldBindQuery(&query)
	if !(query.City == "taipei" || query.City == "metrotaipei" || query.City == ""){
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid City Name"})
		return
	}

	if query.City == ""{
		query.City = "taipei"
	}

	_, _, _, _, permissions := util.GetUserInfoFromContext(c)


	var groupID int
	if query.City == ""{
		// Get Group public(id=1)
		groupID = 1
	}else{
		var errr error
		groupID, errr = models.GetGroupIDByName(query.City)
		if errr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": errr.Error()})
			return
		}
	}


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

	// Trigger Qdrant rebuild in the background
    go services.RebuildQdrantPublicCollection()

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
