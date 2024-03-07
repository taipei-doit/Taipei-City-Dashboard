package controllers

import (
	"net/http"
	"strconv"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

/*
GetUserInfo returns the user information of the current user
GET /api/v1/user/me
*/
func GetUserInfo(c *gin.Context) {
	userID := c.GetInt("accountID")
	user, err := models.GetUserByID(userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No user found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "user": user})
}

/*
EditUserInfo updates the user information of the current user
PATCH /api/v1/user/me
*/
func EditUserInfo(c *gin.Context) {
	var user models.AuthUser
	userID := c.GetInt("accountID")

	err := c.ShouldBindJSON(&user)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err = models.UpdateSelf(userID, user.Name)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": user})
}

type userQuery struct {
	PageSize     int    `form:"pagesize"`
	PageNum      int    `form:"pagenum"`
	Sort         string `form:"sort"`
	Order        string `form:"order"`
	SearchByID   string `form:"searchbyid"`
	SearchByName string `form:"searchbyname"`
}

/*
GetAllUsers returns all users
GET /api/v1/user
*/
func GetAllUsers(c *gin.Context) {
	var users []models.AuthUser // Create a slice of components
	var totalUsers int64        // Create a variable to store the total amount of components
	var resultNum int64         // Create a variable to store the amount of components returned

	// Get all query parameters from context
	var query userQuery
	c.ShouldBindQuery(&query)

	// Get all users
	users, totalUsers, resultNum, err := models.GetAllUsers(query.PageSize, query.PageNum, query.Sort, query.Order, query.SearchByID, query.SearchByName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get users"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalUsers, "results": resultNum, "data": users})
}

/*
UpdateUserByID updates the user information by ID
GET /api/v1/user/:id
*/
func UpdateUserByID(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid user ID"})
		return
	}

	// 1. Check if the user exists
	user, err := models.GetUserByID(userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No user found"})
		return
	}

	// 2. Bind the JSON body to the user struct
	err = c.ShouldBindJSON(&user)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 3. Update the user
	user, err = models.UpdateUser(userID, user.Name, user.IsAdmin, user.IsActive, user.IsWhitelist, user.IsBlacked)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "user": user})
}
