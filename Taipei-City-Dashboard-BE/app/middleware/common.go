// Package middleware includes all middleware functions used by the APIs.
package middleware

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"

	"github.com/gin-gonic/gin"
)

// AddCommonHeaders adds common headers that will be appended to all requests.
func AddCommonHeaders(c *gin.Context) {
	c.Header("Access-Control-Allow-Origin", "*")
	c.Header("Access-Control-Allow-Headers", "Content-Type,AccessToken,X-CSRF-Token, Authorization, Token")
	c.Header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, PATCH, DELETE")
	c.Header("Access-Control-Expose-Headers", "Content-Length, Access-Control-Allow-Origin, Access-Control-Allow-Headers, Content-Type")
	c.Header("Access-Control-Allow-Credentials", "true")

	if c.Request.Method == "OPTIONS" {
		c.AbortWithStatus(http.StatusNoContent)
	}

	c.Next()
}

// IsLoggedIn checks if user is logged in.
func IsLoggedIn() gin.HandlerFunc {
	return func(c *gin.Context) {
		loginType := c.GetString("loginType")
		if loginType != "no login" {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}

// IsSysAdm checks if user is system admin.
func IsSysAdm() gin.HandlerFunc {
	return func(c *gin.Context) {
		_, _, isAdmin, _, _ := util.GetUserInfoFromContext(c)
		if isAdmin {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}

// LimitRequestTo checks if the permissions contain a specific permission.
func LimitRequestTo(permission models.Permission) gin.HandlerFunc {
	return func(c *gin.Context) {
		_, _, _, _, permissions := util.GetUserInfoFromContext(c)
		for _, perm := range permissions {
			if perm.GroupID == permission.GroupID && perm.RoleID == permission.RoleID {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}
