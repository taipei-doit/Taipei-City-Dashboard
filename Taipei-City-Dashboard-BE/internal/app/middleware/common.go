// Package middleware includes all middleware functions used by the APIs.
package middleware

import (
	"net/http"

	"TaipeiCityDashboardBE/internal/auth"

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

// 不確定想做什麼
// func LimitRequestTo(approved []int) gin.HandlerFunc {
// 	return func(c *gin.Context) {
// 		_, _, _, permissions := auth.GetUserInfoFromContext(c)

// 		for _, permission := range permissions {
// 			if slices.Contains(approved, role) {
// 				c.Next()
// 				return
// 			}
// 		}

// 		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
// 	}
// }

// IsAdmin checks if user is system admin.
func IsSysAdm() gin.HandlerFunc {
	return func(c *gin.Context) {
		_, _, isAdmin, _, _ := auth.GetUserInfoFromContext(c)
		if isAdmin {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}

// CheckPermission checks if the permissions contain a specific permission.
func LimitRequestTo(permission auth.Permission) gin.HandlerFunc {
	return func(c *gin.Context) {
		_, _, _, _, permissions := auth.GetUserInfoFromContext(c)
		for _, perm := range permissions {
			if perm.GroupID == permission.GroupID && perm.RoleID == permission.RoleID {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}
