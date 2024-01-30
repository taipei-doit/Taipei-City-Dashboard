package auth

import (
	"net/http"

	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

/*
	CreateGroup is a utility function that creates a new group and registers the user to the group.

return: created group name and id

! Remember to only call this function in controllers that block guests. !
*/
func CreateGroup(c *gin.Context) (int, string) {
	var group models.Group
	var EmailUserGroup models.EmailUserGroup
	var IssoUserGroup models.IssoUserGroup

	// 1. Get User Details
	accountType, accountID, _, _, _ := GetUserInfoFromContext(c)

	// 2. Create a new group
	groupName := uuid.New().String()
	group.Name = groupName
	err := postgres.DBManager.Table("groups").Create(&group).Error
	if err != nil {
		c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
		return 0, ""
	}

	// 3. Register the user to the group
	if accountType == "Email" {
		EmailUserGroup.UserID = accountID
		EmailUserGroup.GroupID = group.Id
		err = postgres.DBManager.Table("email_user_groups").Create(&EmailUserGroup).Error
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
			return 0, ""
		}
	} else {
		IssoUserGroup.UserID = accountID
		IssoUserGroup.GroupID = group.Id
		err = postgres.DBManager.Table("isso_user_groups").Create(&IssoUserGroup).Error
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
			return 0, ""
		}
	}

	return group.Id, groupName
}

/*
DeleteGroup is a utility function that deletes a group and removes the user from the group.

return: deleted group name and id

! Currently only 1 person will be in each group. This function should be modified in the future if multiple users are allowed in a group. !
*/
func DeleteGroup(c *gin.Context, groupID int) bool {
	var group models.Group
	var EmailUserGroup models.EmailUserGroup
	var IssoUserGroup models.IssoUserGroup

	var accountType string
	var accountID int
	// 1. Get User Details
	accountType, accountID, _, _, _ = GetUserInfoFromContext(c)

	// 2. Delete the user from the group
	if accountType == "Email" {
		err := postgres.DBManager.Table("email_user_groups").Where("email_user_id = ? AND group_id = ?", accountID, groupID).Delete(&EmailUserGroup)
		if err.Error != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
			return false
		}
	} else {
		err := postgres.DBManager.Table("isso_user_groups").Where("isso_user_id = ? AND group_id = ?", accountID, groupID).Delete(&IssoUserGroup)
		if err.Error != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
			return false
		}
	}

	// 3. Delete the group
	// postgres.DBManager.Table("groups").Where("id = ?", groupID).Find(&group)
	err := postgres.DBManager.Table("groups").Where("id = ?", groupID).Delete(&group)
	if err.Error != nil {
		c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error})
		return false
	}

	return true
}
