// Package middleware includes all middleware functions used by the APIs.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package middleware

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"errors"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

func GetTime(c *gin.Context) (string, string, error) {
	timefrom := c.Query("timefrom")
	timeto := c.Query("timeto")
 
	layout := "2006-01-02T15:04:05+08:00" // 定義時間格式
 
	// timeFrom defaults to 1990-01-01 (essentially, all data)
	if timefrom == "" {
		timefrom = time.Date(1990, 1, 1, 0, 0, 0, 0, time.FixedZone("UTC+8", 8*60*60)).Format(layout)
	} else {
		// 檢查 timefrom 格式
		if _, err := time.Parse(layout, timefrom); err != nil {
			return "", "", errors.New("timefrom 格式無效")
		}
	}
	// timeTo defaults to current time
	if timeto == "" {
		timeto = time.Now().Format(layout)
	} else {
		// 檢查 timeto 格式
		if _, err := time.Parse(layout, timeto); err != nil {
			return "", "", errors.New("timeto 格式無效")
		}
	}
 
	return timefrom, timeto, nil
}



// AddCommonHeaders adds common headers that will be appended to all requests.
func AddCommonHeaders(c *gin.Context) {
	// c.Header("Access-Control-Allow-Origin", "*")
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
