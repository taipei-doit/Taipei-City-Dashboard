package controllers

import (
	"net/http"
	"time"

	"TaipeiCityDashboardBE/app/database"
	"TaipeiCityDashboardBE/app/database/models"

	"github.com/gin-gonic/gin"
)

/*
GetUserInfo returns the user information of the current user
GET /api/v1/user/me
*/
func GetUserInfo(c *gin.Context) {
	var user models.AuthUser

	userID := c.GetInt("accountID")
	err := database.DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
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

	err = database.DBManager.Table("auth_users").Where("id = ?", userID).Updates(&user).Error
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

	// Create a temporary database
	tempDB := database.DBManager.Table("auth_users")

	// Count the total amount of users
	tempDB.Count(&totalUsers)

	// Search the users
	if query.SearchByID != "" {
		tempDB = tempDB.Where("id = ?", query.SearchByID)
	}
	if query.SearchByName != "" {
		tempDB = tempDB.Where("name LIKE ?", "%"+query.SearchByName+"%")
	}

	tempDB.Count(&resultNum)

	// Sort the issues
	if query.Sort != "" {
		tempDB = tempDB.Order(query.Sort + " " + query.Order)
	}

	// Paginate the issues
	if query.PageSize > 0 {
		tempDB = tempDB.Limit(query.PageSize)
		if query.PageNum > 0 {
			tempDB = tempDB.Offset((query.PageNum - 1) * query.PageSize)
		}
	}

	err := tempDB.Find(&users).Error
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No user found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalUsers, "results": resultNum, "data": users})
}

/*
UpdateUserByID updates the user information by ID
GET /api/v1/user/:id
*/
func UpdateUserByID(c *gin.Context) {
	type UpdateUser struct {
		Name        string    `json:"name" gorm:"column:name;type:varchar"`
		IsAdmin     *bool     `json:"is_admin"   gorm:"column:is_admin;type:boolean;default:false"`       // 系統管理者
		IsActive    *bool     `json:"is_active" gorm:"column:is_active;type:boolean;default:true"`        // 啟用
		IsWhitelist *bool     `json:"is_whitelist" gorm:"column:is_whitelist;type:boolean;default:false"` // 白名單
		IsBlacked   *bool     `json:"is_blacked" gorm:"column:is_blacked;type:boolean;default:false"`     // 黑名單
		ExpiredAt   time.Time `json:"expired_at" gorm:"column:expired_at;type:timestamp with time zone;"` // 停用時間
	}
	var user UpdateUser
	userID := c.Param("id")

	// 1. Check if the user exists
	err := database.DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
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

	if !*user.IsActive {
		user.ExpiredAt = time.Now()
	} else {
		user.ExpiredAt = time.Time{}
	}

	// 3. Update the user
	err = database.DBManager.Table("auth_users").Where("id = ?", userID).Updates(&user).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "user": user})
}
