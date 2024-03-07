package models

import (
	"github.com/dgrijalva/jwt-go"
)

// Role represents a user role in the system.
type Role struct {
	Id            int    `json:"role_id"         gorm:"column:id;autoincrement;primaryKey"`
	Name          string `json:"role_name"       gorm:"column:name;type:varchar"`
	AccessControl bool   `json:"access_control"  gorm:"column:access_control;type:boolean;default:false"`
	Modify        bool   `json:"modify"          gorm:"column:modify;type:boolean;default:false"`
	Read          bool   `json:"read"            gorm:"column:read;type:boolean;default:false"`
}

// Groups ....
type Group struct {
	Id         int      `json:"group_id"    gorm:"column:id;autoincrement;primaryKey"`
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

type Claims struct {
	LoginType   string       `json:"login_type"`
	AccountID   int          `json:"account_id"`
	IsAdmin     bool         `json:"is_admin"`
	Permissions []Permission `json:"permissions"`
	jwt.StandardClaims
}
