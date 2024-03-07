package models

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"TaipeiCityDashboardBE/logs"

	"github.com/google/uuid"
	"github.com/lib/pq"
)

/* ----- Models ----- */

type AuthUser struct {
	ID            int        `json:"user_id" gorm:"column:id;autoincrement;primaryKey"`
	Name          string     `json:"name" gorm:"column:name;type:varchar"`
	Email         *string    `json:"account" gorm:"column:email;type:varchar;unique;check:(email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')"`
	Password      *string    `json:"-" gorm:"column:password;type:varchar"`
	IDNo          *string    `json:"-" gorm:"column:idno;type:varchar;unique;"`
	TpUuID        *string    `json:"-" gorm:"column:uuid;type:varchar;unique;"`
	TpAccount     *string    `json:"TpAccount" gorm:"column:tp_account;type:varchar"`
	TpMemberType  *string    `json:"-" gorm:"column:member_type;type:varchar"`                           // 會員類別
	TpVerifyLevel *string    `json:"-" gorm:"column:verify_level;type:varchar"`                          // 會員驗證等級
	IsAdmin       *bool      `json:"is_admin"   gorm:"column:is_admin;type:boolean;default:false"`       // 系統管理者
	IsActive      *bool      `json:"is_active" gorm:"column:is_active;type:boolean;default:true"`        // 啟用
	IsWhitelist   *bool      `json:"is_whitelist" gorm:"column:is_whitelist;type:boolean;default:false"` // 白名單
	IsBlacked     *bool      `json:"is_blacked" gorm:"column:is_blacked;type:boolean;default:false"`     // 黑名單
	ExpiredAt     *time.Time `json:"expired_at" gorm:"column:expired_at;type:timestamp with time zone;"` // 停用時間
	CreatedAt     time.Time  `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;"`
	LoginAt       time.Time  `json:"login_at" gorm:"column:login_at;type:timestamp with time zone;"`
	// Roles       []Role       `json:"roles" gorm:"many2many:email_user_roles;"`
	// Groups      []Group      `json:"groups" gorm:"many2many:email_user_groups;"`
}

/* ----- Handlers ----- */

func GetAllUsers(pageSize int, pageNum int, sort string, order string, searchByID string, searchByName string) (users []AuthUser, totalUsers int64, resultNum int64, err error) {
	// Create a temporary database
	tempDB := DBManager.Table("auth_users")

	// Count the total amount of users
	err = tempDB.Count(&totalUsers).Error
	if err != nil {
		return users, 0, 0, err
	}

	// Search the users
	if searchByID != "" {
		tempDB = tempDB.Where("id = ?", searchByID)
	}
	if searchByName != "" {
		tempDB = tempDB.Where("name LIKE ?", "%"+searchByName+"%")
	}

	err = tempDB.Count(&resultNum).Error
	if err != nil {
		return users, 0, 0, err
	}

	// Sort the issues
	if sort != "" {
		tempDB = tempDB.Order(sort + " " + order)
	}

	// Paginate the issues
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	err = tempDB.Find(&users).Error
	if err != nil {
		return users, 0, 0, err
	}

	// Return the users, total number of users, number of results, and nil error.
	return users, totalUsers, resultNum, nil
}

func GetUserByID(userID int) (user AuthUser, err error) {
	err = DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
	if err != nil {
		return user, err
	}
	return user, nil
}

// CreateUser creates a new AuthUser and stores it in the database
func CreateUser(name string, email, password *string, isAdmin, isActive, isWhitelist, isBlacked *bool, expiredAt *time.Time) (userID int, err error) {
	// Initialize a new AuthUser instance and set its properties.
	user := AuthUser{
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

	// Attempt to save the user to the
	if err := DBManager.Create(&user).Error; err != nil {
		// If an error occurs during creation, return the error and userID as 0.
		return 0, err
	}
	logs.FInfo("create user %d success", user.ID)

	// create personal group
	groupID, err := CreateGroup("user: "+strconv.Itoa(user.ID)+"'s personal group", true, user.ID)
	if err != nil {
		return 0, fmt.Errorf("create user personal group failed %v", err)
	}

	// set user own group permission
	if err := CreateUserGroupRole(user.ID, groupID, 1); err != nil {
		logs.FError("Failed to set admin permission:%s", err)
	}

	// create favorite dashboard
	tmpIndex := uuid.New().String()
	dashboardIndex := strings.Split(tmpIndex, "-")[0] + strings.Split(tmpIndex, "-")[1]
	dashboardName := "收藏組件"
	var dashboardComponents pq.Int64Array
	_, err = CreateDashboard(dashboardIndex, dashboardName, "favorite", dashboardComponents, groupID)
	if err != nil {
		return 0, fmt.Errorf("create user favorite dashboard failed %v", err)
	}

	// Return the ID of the new user and nil error.
	return user.ID, nil
}

// UpdateUser updates an existing AuthUser in the database
func UpdateUser(userID int, name string, isAdmin, isActive, isWhitelist, isBlacked *bool) (user AuthUser, err error) {
	user.Name = name
	user.IsAdmin = isAdmin
	user.IsActive = isActive
	user.IsWhitelist = isWhitelist
	user.IsBlacked = isBlacked

	timeNow := time.Now()

	if !*user.IsActive {
		user.ExpiredAt = &timeNow
	} else {
		user.ExpiredAt = nil
	}

	err = DBManager.Table("auth_users").Where("id = ?", userID).Updates(&user).Error
	if err != nil {
		return user, err
	}

	if *isAdmin {
		DeleteUserGroupRole(userID, 1, 3)
		CreateUserGroupRole(userID, 1, 1)
	} else if !*isAdmin {
		DeleteUserGroupRole(userID, 1, 1)
		CreateUserGroupRole(userID, 1, 3)
	}

	err = DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
	if err != nil {
		return user, err
	}
	return user, nil
}

func UpdateSelf(userID int, name string) (user AuthUser, err error) {
	user.Name = name

	err = DBManager.Table("auth_users").Where("id = ?", userID).Updates(&user).Error
	if err != nil {
		return user, err
	}

	err = DBManager.Table("auth_users").Where("id = ?", userID).First(&user).Error
	if err != nil {
		return user, err
	}
	return user, nil
}

// DeleteUser deletes an AuthUser from the database based on the provided userID.
func DeleteUser(userID int) error {
	// Start a transaction to ensure data integrity.
	tx := DBManager.Begin()

	// Find the provided userID.
	var user AuthUser
	result := tx.Where("id = ?", userID).First(&user)
	if result.Error != nil {
		// If the user is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete entries from AuthUserGroupRole table associated with the user.
	if err := tx.Where("user_id = ?", userID).Delete(&AuthUserGroupRole{}).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Delete the user
	if err := tx.Delete(&user).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}
