// Package auth stores the authentication functions for the application. This includes controllers, middlewares, and utility functions.
package auth

import (
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

type Permission struct {
	GroupID int `json:"group_id"`
	RoleID  int `json:"role_id"`
}

type GroupUser struct {
	UserID int `json:"user_id"`
	RoleID int `json:"role_id"`
}

const (
	emailRegex = "^\\w+((-\\w+)|(\\.\\w+))*\\@[A-Za-z0-9]+((\\.|-)[A-Za-z0-9]+)*\\.[A-Za-z]+$"
)

func Login(c *gin.Context) {
	var user models.AuthUser

	const authPrefix = "Basic "

	credentials, err := getAuthFromRequest(c, authPrefix)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	email, password, err := decodedCredentials(credentials)
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
	passwordSHA := HashString(password)
	if err := postgres.DBManager.
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
	if !user.IsActive {
		c.JSON(http.StatusForbidden, gin.H{"error": "User not activated"})
		return
	}

	permissions, err := GetUserPermission(user.Id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	// generate JWT token
	user.LoginAt = time.Now()
	token, err := GenerateJWT(user.LoginAt.Add(global.TokenExpirationDuration), "Email", user.Id, user.IsAdmin, permissions)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	// update last login time
	if err := postgres.DBManager.Save(&user).Error; err != nil {
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

// CreateUser creates a new AuthUser and stores it in the database.
func CreateUser(name string, email, password *string, isAdmin, isActive, isWhitelist, isBlacked bool, expiredAt *time.Time) (userID int, err error) {
	// Initialize a new AuthUser instance and set its properties.
	user := models.AuthUser{
		Name:        name,
		Email:       email,
		Password:    password,
		IsAdmin:     isAdmin,
		IsActive:    isActive,
		IsWhitelist: isWhitelist,
		IsBlacked:   isBlacked,
		ExpiredAt:   expiredAt,
		CreatedAt:   time.Now(),
		LoginAt:     time.Now(),
	}

	// Attempt to save the user to the database.
	if err := postgres.DBManager.Create(&user).Error; err != nil {
		// If an error occurs during creation, return the error and userID as 0.
		return 0, err
	}
	logs.FInfo("create user %d success", user.Id)

	// create personal group
	groupId, err := CreateGroup("user: "+strconv.Itoa(user.Id)+"'s personal group", true, user.Id)
	if err != nil {
		return 0, fmt.Errorf("create user personal group failed %v", err)
	}

	// set user own group permission
	if err := CreateUserGroupRole(user.Id, groupId, 1); err != nil {
		logs.FError("Failed to set admin permission:%s", err)
	}

	// create favorite dashboard
	tmpIndex := uuid.New().String()
	dashboardIndex := strings.Split(tmpIndex, "-")[0] + strings.Split(tmpIndex, "-")[1]
	dashboardName := "user " + strconv.Itoa(user.Id) + "'s favorite"
	_, err = CreateDashboard(dashboardIndex, dashboardName, "favorite", groupId)
	if err != nil {
		return 0, fmt.Errorf("create user favorite dashboard failed %v", err)
	}

	// Return the ID of the new user and nil error.
	return user.Id, nil
}

// DeleteUser deletes an AuthUser from the database based on the provided userID.
func DeleteUser(userID int) error {
	// Start a transaction to ensure data integrity.
	tx := postgres.DBManager.Begin()

	// Find the provided userID.
	var user models.AuthUser
	result := tx.Where("id = ?", userID).First(&user)
	if result.Error != nil {
		// If the user is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from AuthUserGroupRole table associated with the user.
	if err := tx.Where("user_id = ?", userID).Delete(&models.AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the user from the database.
	if err := tx.Delete(&user).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}

// UpdateUser updates an existing AuthUser in the database.
func UpdateUser(userID int, updatedUser models.AuthUser) error {
	// Find the user with the provided userID.
	var user models.AuthUser
	result := postgres.DBManager.Where("user_id = ?", userID).First(&user)
	if result.Error != nil {
		// If the user is not found, return the error.
		return result.Error
	}

	// Update the user's properties with the provided updatedUser.
	user.Name = updatedUser.Name
	user.Email = updatedUser.Email
	user.Password = updatedUser.Password
	user.IdNo = updatedUser.IdNo
	user.TpUuid = updatedUser.TpUuid
	user.TpAccount = updatedUser.TpAccount
	user.TpMemberType = updatedUser.TpMemberType
	user.TpVerifyLevel = updatedUser.TpVerifyLevel
	user.IsActive = updatedUser.IsActive
	user.IsWhitelist = updatedUser.IsWhitelist
	user.IsBlacked = updatedUser.IsBlacked
	user.ExpiredAt = updatedUser.ExpiredAt
	user.CreatedAt = updatedUser.CreatedAt
	user.LoginAt = updatedUser.LoginAt

	// Save the updated user to the database.
	if err := postgres.DBManager.Save(&user).Error; err != nil {
		// If an error occurs during update, return the error.
		return err
	}

	// Return nil to indicate successful update.
	return nil
}

// CreateGroup optimizes the creation of a group in the database.
// It takes the group name, a boolean flag indicating if it's personal,
// and the ID of the creator as input parameters.
// It returns the ID of the created group.
func CreateGroup(groupName string, isPersonal bool, createBy int) (groupID int, err error) {
	// Initialize a new Group instance with provided parameters.
	group := models.Group{
		Name:       groupName,
		IsPersonal: isPersonal,
		CreateBy:   createBy,
	}
	// Attempt to create the group in the database.
	if err := postgres.DBManager.Create(&group).Error; err != nil {
		// If an error occurs during creation, return 0 indicating failure.
		return 0, err
	}

	// Return the ID of the created group.
	return group.Id, nil
}

// GetGroupIDByName queries and returns the group ID based on the group name.
func GetGroupIDByName(groupName string) (int, error) {
	var group models.Group

	// Find the group in the database with the given group name.
	if err := postgres.DBManager.Where("name = ?", groupName).First(&group).Error; err != nil {
		// Return an error if any error occurs during the lookup.
		return 0, err
	}

	// Return the group ID if the group is found.
	return group.Id, nil
}

// DeleteGroup deletes a group from the database based on its ID.
func DeleteGroup(groupID int) error {
	// Start a transaction to ensure data integrity.
	tx := postgres.DBManager.Begin()

	// Find the group with the provided ID.
	var group models.Group
	result := tx.Where("group_id = ?", groupID).First(&group)
	if result.Error != nil {
		// If the group is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from userGroupRoles table associated with the group.
	if err := tx.Where("group_id = ?", groupID).Delete(&models.AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the group from the database.
	if err := tx.Delete(&group).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}

// createRole creates a new role and stores it in the database.
func CreateRole(roleName string, accessControl, modify, read bool) (roleID int, err error) {
	// Initialize a new Role instance and set its properties.
	role := models.Role{
		Name:          roleName,
		AccessControl: accessControl,
		Modify:        modify,
		Read:          read,
	}

	// Attempt to save the role to the database.
	if err := postgres.DBManager.Create(&role).Error; err != nil {
		// If an error occurs during creation, return the error and roleID as 0.
		return 0, err
	}

	// Return the ID of the new role and nil error.
	return role.Id, nil
}

// GetRoleIDByName queries and returns the role ID based on the role name.
func GetRoleIDByName(roleName string) (int, error) {
	var role models.Role

	// Find the role in the database with the given role name.
	if err := postgres.DBManager.Where("name = ?", roleName).First(&role).Error; err != nil {
		// Return an error if any error occurs during the lookup.
		return 0, err
	}

	// Return the role ID if the role is found.
	return role.Id, nil
}

// DeleteRole deletes a role from the database based on the provided roleID.
func DeleteRole(roleID int) error {
	// Check if the roleID is one of the default roles that cannot be deleted.
	if roleID <= 3 {
		return fmt.Errorf("cannot delete default group")
	}

	// Start a transaction to ensure data integrity.
	tx := postgres.DBManager.Begin()

	// Find the provided roleID.
	var role models.Role
	result := tx.Where("id = ?", roleID).First(&role)
	if result.Error != nil {
		// If the role is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from AuthUserGroupRole table associated with the role.
	if err := tx.Where("role_id = ?", roleID).Delete(&models.AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the role from the database.
	if err := tx.Delete(&role).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}

// UpdateRole updates an existing role in the database.
func UpdateRole(roleID int, updatedRole models.Role) error {
	// Check if the roleID is one of the default roles that cannot be updated.
	if roleID <= 3 {
		return fmt.Errorf("cannot delete default group")
	}

	// Find the role with the provided roleID.
	var role models.Role
	result := postgres.DBManager.Where("role_id = ?", roleID).First(&role)
	if result.Error != nil {
		// If the role is not found, return the error.
		return result.Error
	}

	// Update the role's properties with the provided updatedRole.
	role.Name = updatedRole.Name
	role.AccessControl = updatedRole.AccessControl
	role.Modify = updatedRole.Modify
	role.Read = updatedRole.Read

	// Save the updated role to the database.
	if err := postgres.DBManager.Save(&role).Error; err != nil {
		// If an error occurs during update, return the error.
		return err
	}

	// Return nil to indicate successful update.
	return nil
}

// CreateUserGroupRole creates a new association between an AuthUser, Group, and Role in the database.
func CreateUserGroupRole(authUserID, groupID, roleID int) error {
	// Initialize a new AuthUserGroupRole instance with the provided IDs.
	authUserGroupRole := models.AuthUserGroupRole{
		AuthUserID: authUserID,
		GroupID:    groupID,
		RoleID:     roleID,
	}

	// Attempt to create the association in the database.
	if err := postgres.DBManager.Create(&authUserGroupRole).Error; err != nil {
		// If an error occurs during creation, return the error.
		return err
	}

	// Return nil to indicate successful association creation.
	return nil
}

// DeleteUserGroupRole deletes an association between an AuthUser, Group, and Role from the database.
func DeleteUserGroupRole(authUserID, groupID, roleID int) error {
	// Find the association with the provided IDs.
	var authUserGroupRole models.AuthUserGroupRole
	result := postgres.DBManager.Where("auth_user_id = ? AND group_id = ? AND role_id = ?", authUserID, groupID, roleID).First(&authUserGroupRole)
	if result.Error != nil {
		// If the association is not found, return the error.
		return result.Error
	}

	// Delete the association from the database.
	if err := postgres.DBManager.Delete(&authUserGroupRole).Error; err != nil {
		// If an error occurs during deletion, return the error.
		return err
	}

	// Return nil to indicate successful association deletion.
	return nil
}

// GetUserPermission retrieves permissions associated with a specific user from the database.
func GetUserPermission(authUserID int) (permissions []Permission, err error) {
	// Query the database to find permissions associated with the provided authUserID.
	result := postgres.DBManager.
		Model(&models.AuthUserGroupRole{}).
		Select("group_id, role_id").
		Where("auth_user_id = ?", authUserID).
		Scan(&permissions)

	if result.Error != nil {
		// If an error occurs during the query, return nil slice and the error.
		return nil, result.Error
	}

	// Check if the permissions include public group.
	hasPublicGroup := false
	for _, perm := range permissions {
		if perm.GroupID == 1 { // Assuming 1 is the ID of the public group
			hasPublicGroup = true
			break
		}
	}

	// If public group is not found in permissions, add it.
	if !hasPublicGroup {
		permissions = append(permissions, Permission{GroupID: 1, RoleID: 3})
	}

	// Return the found permissions and nil error.
	return permissions, nil
}

// GetGroupUsers retrieves user IDs and their corresponding role IDs associated with a specific group from the database.
func GetGroupUsers(groupID int) (groupUsers []GroupUser, err error) {
	// Query the database to find all users and their role IDs associated with the provided groupID.
	result := postgres.DBManager.
		Model(&models.AuthUserGroupRole{}).
		Select("auth_user_id as user_id, role_id").
		Where("group_id = ?", groupID).
		Scan(&groupUsers)

	if result.Error != nil {
		// If an error occurs during the query, return nil slice and the error.
		return nil, result.Error
	}

	// Return the found group users and nil error.
	return groupUsers, nil
}

// GetUserPersonalGroup retrieves the ID of the personal group associated with the given userID.
func GetUserPersonalGroup(userID int) (groupID int, err error) {
	var group models.Group
	// Find the personal group associated with the user.
	if err := postgres.DBManager.Where("create_by = ? AND is_personal = ?", userID, true).First(&group).Error; err != nil {
		// If an error occurs or the group is not found, return an error.
		return 0, err
	}
	// Return the ID of the personal group.
	return group.Id, nil
}

// HasPermission checks if the permissions contain a specific groupid and roleid.
func HasPermission(permissions []Permission, targetGroupID, targetRoleID int) bool {
	for _, perm := range permissions {
		if perm.GroupID == targetGroupID && perm.RoleID == targetRoleID {
			return true
		}
	}
	return false
}

func IsAdmin(userID int) bool {
	// Here you would typically query the database to check if the user with the given userID is an admin.
	// For instance, you might have a query like this:
	var user models.AuthUser
	if err := postgres.DBManager.Where("id = ? AND is_admin = ?", userID, true).First(&user).Error; err != nil {
		// Handle the error, such as log it or return false if the user is not found or there's an error during the query.
		return false
	}

	// If the user is found and is an admin, return true.
	return user.IsAdmin
}

// ConvertPermissionsToGroupIDs extracts unique group IDs from a list of permissions.
func GetPermissionAllGroupIDs(permissions []Permission) []int {
	uniqueGroupIDs := make(map[int]struct{})

	// Extract unique group IDs from permissions
	for _, perm := range permissions {
		uniqueGroupIDs[perm.GroupID] = struct{}{}
	}

	// Convert unique group IDs to a slice
	groupIDs := make([]int, 0, len(uniqueGroupIDs))
	for groupID := range uniqueGroupIDs {
		groupIDs = append(groupIDs, groupID)
	}

	return groupIDs
}

// GetPermissionGroupIDs extracts unique group IDs from permissions based on a specific role.
func GetPermissionGroupIDs(permissions []Permission, role int) []int {
	uniqueGroupIDs := make(map[int]struct{})

	// Extract unique group IDs from permissions for the specified role
	for _, perm := range permissions {
		if perm.RoleID == role {
			uniqueGroupIDs[perm.GroupID] = struct{}{}
		}
	}

	// Convert unique group IDs to a slice
	groupIDs := make([]int, 0, len(uniqueGroupIDs))
	for groupID := range uniqueGroupIDs {
		groupIDs = append(groupIDs, groupID)
	}

	return groupIDs
}
