package util

import (
	"time"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

// GetUserInfoFromContext retrieves the user info from the Gin context.
func GetUserInfoFromContext(c *gin.Context) (loginType string, accountID int, isAdmin bool, expiresAt time.Time, permissions []models.Permission) {
	// get context keys
	loginType = c.GetString("loginType")
	accountID = c.GetInt("accountID")
	isAdmin = c.GetBool("isAdmin")
	expiresAt = c.GetTime("expiresAt")
	// Retrieve permissions from the context
	if perms, exists := c.Get("permissions"); exists {
		// Check if the value exists
		if permsList, ok := perms.([]models.Permission); ok {
			permissions = permsList
		}
	}
	return
}
