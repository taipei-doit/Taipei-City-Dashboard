package models

import (
	"fmt"

	"github.com/dgrijalva/jwt-go"
)

/* ----- Models ----- */

type Role struct {
	ID            int    `json:"role_id"         gorm:"column:id;autoincrement;primaryKey"`
	Name          string `json:"role_name"       gorm:"column:name;type:varchar"`
	AccessControl bool   `json:"access_control"  gorm:"column:access_control;type:boolean;default:false"`
	Modify        bool   `json:"modify"          gorm:"column:modify;type:boolean;default:false"`
	Read          bool   `json:"read"            gorm:"column:read;type:boolean;default:false"`
}

type Group struct {
	ID         int      `json:"group_id"    gorm:"column:id;autoincrement;primaryKey"`
	Name       string   `json:"group_name"  gorm:"column:name;type:varchar"`
	IsPersonal bool     `json:"is_personal" gorm:"column:is_personal;type:boolean;default:false"`
	CreateBy   int      `json:"create_by"   gorm:"column:create_by;"`
	AuthUser   AuthUser `gorm:"foreignKey:create_by"`
}

type AuthUserGroupRole struct {
	AuthUserID int      `json:"user_id"     gorm:"column:auth_user_id;primaryKey"`
	GroupID    int      `json:"group_id"    gorm:"column:group_id;primaryKey;"`
	RoleID     int      `json:"role_id"     gorm:"column:role_id;primaryKey"`
	AuthUser   AuthUser `gorm:"foreignKey:AuthUserID"`
	Group      Group    `gorm:"foreignKey:GroupID"`
	Role       Role     `gorm:"foreignKey:RoleID"`
}

type Permission struct {
	GroupID int `json:"group_id"`
	RoleID  int `json:"role_id"`
}

type GroupUser struct {
	UserID int `json:"user_id"`
	RoleID int `json:"role_id"`
}

type Claims struct {
	LoginType   string       `json:"login_type"`
	AccountID   int          `json:"account_id"`
	IsAdmin     bool         `json:"is_admin"`
	Permissions []Permission `json:"permissions"`
	jwt.StandardClaims
}

/* ----- Handlers ----- */

/* --- Role --- */

// GetRoleIDByName queries and returns the role ID based on the role name.
func GetRoleIDByName(roleName string) (int, error) {
	var role Role

	// Find the role in the database with the given role name.
	if err := DBManager.Where("name = ?", roleName).First(&role).Error; err != nil {
		// Return an error if any error occurs during the lookup.
		return 0, err
	}

	// Return the role ID if the role is found.
	return role.ID, nil
}

// CreateRole creates a new role and stores it in the database
func CreateRole(roleName string, accessControl, modify, read bool) (roleID int, err error) {
	// Initialize a new Role instance and set its properties.
	role := Role{
		Name:          roleName,
		AccessControl: accessControl,
		Modify:        modify,
		Read:          read,
	}

	// Attempt to save the role to the models.
	if err := DBManager.Create(&role).Error; err != nil {
		// If an error occurs during creation, return the error and roleID as 0.
		return 0, err
	}

	// Return the ID of the new role and nil error.
	return role.ID, nil
}

// UpdateRole updates an existing role in the database
func UpdateRole(roleID int, updatedRole Role) error {
	// Check if the roleID is one of the default roles that cannot be updated.
	if roleID <= 3 {
		return fmt.Errorf("cannot delete default group")
	}

	// Find the role with the provided roleID.
	var role Role
	result := DBManager.Where("role_id = ?", roleID).First(&role)
	if result.Error != nil {
		// If the role is not found, return the error.
		return result.Error
	}

	// Update the role's properties with the provided updatedRole.
	role.Name = updatedRole.Name
	role.AccessControl = updatedRole.AccessControl
	role.Modify = updatedRole.Modify
	role.Read = updatedRole.Read

	// Save the updated role to the models.
	if err := DBManager.Save(&role).Error; err != nil {
		// If an error occurs during update, return the error.
		return err
	}

	// Return nil to indicate successful update.
	return nil
}

// DeleteRole deletes a role from the database based on the provided roleID.
func DeleteRole(roleID int) error {
	// Check if the roleID is one of the default roles that cannot be deleted.
	if roleID <= 3 {
		return fmt.Errorf("cannot delete default group")
	}

	// Start a transaction to ensure data integrity.
	tx := DBManager.Begin()

	// Find the provided roleID.
	var role Role
	result := tx.Where("id = ?", roleID).First(&role)
	if result.Error != nil {
		// If the role is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from AuthUserGroupRole table associated with the role.
	if err := tx.Where("role_id = ?", roleID).Delete(&AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the role from the models.
	if err := tx.Delete(&role).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}

/* --- Group --- */

// GetGroupIDByName queries and returns the group ID based on the group name.
func GetGroupIDByName(groupName string) (int, error) {
	var group Group

	// Find the group in the database with the given group name.
	if err := DBManager.Where("name = ?", groupName).First(&group).Error; err != nil {
		// Return an error if any error occurs during the lookup.
		return 0, err
	}

	// Return the group ID if the group is found.
	return group.ID, nil
}

// CreateGroup optimizes the creation of a group in the database
// It takes the group name, a boolean flag indicating if it's personal,
// and the ID of the creator as input parameters.
// It returns the ID of the created group.
func CreateGroup(groupName string, isPersonal bool, createBy int) (groupID int, err error) {
	// Initialize a new Group instance with provided parameters.
	group := Group{
		Name:       groupName,
		IsPersonal: isPersonal,
		CreateBy:   createBy,
	}
	// Attempt to create the group in the models.
	if err := DBManager.Create(&group).Error; err != nil {
		// If an error occurs during creation, return 0 indicating failure.
		return 0, err
	}

	// Return the ID of the created group.
	return group.ID, nil
}

// DeleteGroup deletes a group from the database based on its ID.
func DeleteGroup(groupID int) error {
	// Start a transaction to ensure data integrity.
	tx := DBManager.Begin()

	// Find the group with the provided ID.
	var group Group
	result := tx.Where("group_id = ?", groupID).First(&group)
	if result.Error != nil {
		// If the group is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from userGroupRoles table associated with the group.
	if err := tx.Where("group_id = ?", groupID).Delete(&AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the group from the models.
	if err := tx.Delete(&group).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}

/* --- AuthUserGroupRole --- */

// GetUserPermission retrieves permissions associated with a specific user from the database
func GetUserPermission(authUserID int) (permissions []Permission, err error) {
	// Query the database to find permissions associated with the provided authUserID.
	result := DBManager.
		Model(&AuthUserGroupRole{}).
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

// GetGroupUsers retrieves user IDs and their corresponding role IDs associated with a specific group from the database
func GetGroupUsers(groupID int) (groupUsers []GroupUser, err error) {
	// Query the database to find all users and their role IDs associated with the provided groupID.
	result := DBManager.
		Model(&AuthUserGroupRole{}).
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
	var group Group
	// Find the personal group associated with the user.
	if err := DBManager.Where("create_by = ? AND is_personal = ?", userID, true).First(&group).Error; err != nil {
		// If an error occurs or the group is not found, return an error.
		return 0, err
	}
	// Return the ID of the personal group.
	return group.ID, nil
}

// CreateUserGroupRole creates a new association between an AuthUser, Group, and Role in the database
func CreateUserGroupRole(authUserID, groupID, roleID int) error {
	// Initialize a new AuthUserGroupRole instance with the provided IDs.
	authUserGroupRole := AuthUserGroupRole{
		AuthUserID: authUserID,
		GroupID:    groupID,
		RoleID:     roleID,
	}

	// Attempt to create the association in the models.
	if err := DBManager.Create(&authUserGroupRole).Error; err != nil {
		// If an error occurs during creation, return the error.
		return err
	}

	// Return nil to indicate successful association creation.
	return nil
}

// DeleteUserGroupRole deletes an association between an AuthUser, Group, and Role from the database
func DeleteUserGroupRole(authUserID, groupID, roleID int) error {
	// Find the association with the provided IDs.
	var authUserGroupRole AuthUserGroupRole
	result := DBManager.Where("auth_user_id = ? AND group_id = ? AND role_id = ?", authUserID, groupID, roleID).First(&authUserGroupRole)
	if result.Error != nil {
		// If the association is not found, return the error.
		return result.Error
	}

	// Delete the association from the models.
	if err := DBManager.Delete(&authUserGroupRole).Error; err != nil {
		// If an error occurs during deletion, return the error.
		return err
	}

	// Return nil to indicate successful association deletion.
	return nil
}

func IsAdmin(userID int) bool {
	// Here you would typically query the database to check if the user with the given userID is an admin.
	// For instance, you might have a query like this:
	var user AuthUser
	if err := DBManager.Where("id = ? AND is_admin = ?", userID, true).First(&user).Error; err != nil {
		// Handle the error, such as log it or return false if the user is not found or there's an error during the query.
		return false
	}

	// If the user is found and is an admin, return true.
	return *user.IsAdmin
}
