// Package middleware includes all middleware functions used by the APIs.
package middleware

import (
	"net/http"
	"slices"

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

func LimitRequestTo(approved []int) gin.HandlerFunc {
	return func(c *gin.Context) {
		_, _, _, roles, _ := auth.GetUserInfoFromContext(c)

		for _, role := range roles {
			if slices.Contains(approved, role) {
				c.Next()
				return
			}
		}

		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"status": "error", "message": "Unauthorized"})
	}
}
