package controllers

import (
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

const (
	emailRegex = "^\\w+((-\\w+)|(\\.\\w+))*\\@[A-Za-z0-9]+((\\.|-)[A-Za-z0-9]+)*\\.[A-Za-z]+$"
)

func Login(c *gin.Context) {
	var user models.AuthUser

	const authPrefix = "Basic "

	credentials, err := util.GetAuthFromRequest(c, authPrefix)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	email, password, err := util.DecodeCredentials(credentials)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	// check parameters
	emailRegexp, err := regexp.MatchString(emailRegex, email)
	if err != nil || !emailRegexp {
		c.JSON(http.StatusUnauthorized, gin.H{"error": fmt.Errorf("invalid email format: %v", err)})
		return
	}

	if password == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "password is required"})
		return
	}

	// search DB to validate user password
	passwordSHA := util.HashString(password)
	if err := models.DBManager.
		Where("LOWER(email) = LOWER(?)", email).
		Where("password = ?", passwordSHA).
		First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Incorrect username or password"})
			return
		} else {
			logs.FError("Login failed: unexpected database error: %v", err)
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
			return
		}
	}

	// check user is active
	if !*user.IsActive {
		c.JSON(http.StatusForbidden, gin.H{"error": "User not activated"})
		return
	}

	permissions, err := models.GetUserPermission(user.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	// generate JWT token
	user.LoginAt = time.Now()
	token, err := util.GenerateJWT(user.LoginAt.Add(global.TokenExpirationDuration), "Email", user.ID, *user.IsAdmin, permissions)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	// update last login time
	if err := models.DBManager.Save(&user).Error; err != nil {
		logs.FError("Failed to update login time: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "unexpected database error"})
		return
	}

	// return JWT token
	c.JSON(http.StatusOK, gin.H{
		"user":       user,
		"permission": permissions,
		"token":      token,
	})
}
