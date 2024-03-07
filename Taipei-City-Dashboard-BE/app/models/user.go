package models

import "time"

type AuthUser struct {
	Id            int        `json:"user_id" gorm:"column:id;autoincrement;primaryKey"`
	Name          string     `json:"name" gorm:"column:name;type:varchar"`
	Email         *string    `json:"account" gorm:"column:email;type:varchar;unique;check:(email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')"`
	Password      *string    `json:"-" gorm:"column:password;type:varchar"`
	IdNo          *string    `json:"-" gorm:"column:idno;type:varchar;unique;"`
	TpUuid        *string    `json:"-" gorm:"column:uuid;type:varchar;unique;"`
	TpAccount     *string    `json:"TpAccount" gorm:"column:tp_account;type:varchar"`
	TpMemberType  *string    `json:"-" gorm:"column:member_type;type:varchar"`                           // 會員類別
	TpVerifyLevel *string    `json:"-" gorm:"column:verify_level;type:varchar"`                          // 會員驗證等級
	IsAdmin       bool       `json:"is_admin"   gorm:"column:is_admin;type:boolean;default:false"`       // 系統管理者
	IsActive      bool       `json:"is_active" gorm:"column:is_active;type:boolean;default:true"`        // 啟用
	IsWhitelist   bool       `json:"is_whitelist" gorm:"column:is_whitelist;type:boolean;default:false"` // 白名單
	IsBlacked     bool       `json:"is_blacked" gorm:"column:is_blacked;type:boolean;default:false"`     // 黑名單
	ExpiredAt     *time.Time `json:"expired_at" gorm:"column:expired_at;type:timestamp with time zone;"` // 停用時間
	CreatedAt     time.Time  `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;"`
	LoginAt       time.Time  `json:"login_at" gorm:"column:login_at;type:timestamp with time zone;"`
	// Roles       []Role       `json:"roles" gorm:"many2many:email_user_roles;"`
	// Groups      []Group      `json:"groups" gorm:"many2many:email_user_groups;"`
}
