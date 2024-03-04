package controllers

import (
	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"net/http"

	"github.com/gin-gonic/gin"
)

func GetUserInfo(c *gin.Context) {
	var user models.AuthUser

	userID := c.GetInt("accountID")
	err := postgres.DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No user found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "user": user})
}

func EditUserInfo(c *gin.Context) {
	type UpdateUser struct {
		Name string `json:"name"`
	}
	var user UpdateUser
	userID := c.GetInt("accountID")

	err := c.ShouldBindJSON(&user)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	err = postgres.DBManager.Table("auth_users").Where("id = ?", userID).Updates(&user).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": user})
}