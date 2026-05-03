## Overview

The `auth_users`, `roles`, and `groups` tables are used to manage user access to the application. `auth_users` contains user information; `roles` contains three predefined roles (admin, editor, and viewer) and their permissions; and `groups` contains the permission groups that users can be assigned to.

The `auth_user_group_roles` table is used to manage the relationship between users, groups, and roles. Users can be assigned to multiple groups, and each group can have multiple roles.

## auth_users

`PK` `id`

```go
type AuthUser struct {
	Id            int        `json:"user_id"      gorm:"column:id;autoincrement;primaryKey"`
	Name          string     `json:"name"         gorm:"column:name;type:varchar"`
	Email         *string    `json:"account"      gorm:"column:email;type:varchar;unique;check:(email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')"`
	Password      *string    `json:"-"            gorm:"column:password;type:varchar"`
	IdNo          *string    `json:"-"            gorm:"column:idno;type:varchar;unique;"`
	TpUuid        *string    `json:"-"            gorm:"column:uuid;type:varchar;unique;"`
	TpAccount     *string    `json:"TpAccount"    gorm:"column:tp_account;type:varchar"`
	TpMemberType  *string    `json:"-"            gorm:"column:member_type;type:varchar"`                           
	TpVerifyLevel *string    `json:"-"            gorm:"column:verify_level;type:varchar"`                          
	IsAdmin       bool       `json:"is_admin"     gorm:"column:is_admin;type:boolean;default:false"`       
	IsActive      bool       `json:"is_active"    gorm:"column:is_active;type:boolean;default:true"`        
	IsWhitelist   bool       `json:"is_whitelist" gorm:"column:is_whitelist;type:boolean;default:false"` 
	IsBlacked     bool       `json:"is_blacked"   gorm:"column:is_blacked;type:boolean;default:false"`    
	ExpiredAt     *time.Time `json:"expired_at"   gorm:"column:expired_at;type:timestamp with time zone;"` 
	CreatedAt     time.Time  `json:"created_at"   gorm:"column:created_at;type:timestamp with time zone;"`
	LoginAt       time.Time  `json:"login_at"     gorm:"column:login_at;type:timestamp with time zone;"`
}
```

**Columns of Note:**

`idno`, `tp_uuid`, `tp_account`, `tp_member_type`, `tp_verify_level` are used to store user information from Taipei Pass.

## roles

`PK` `id`

```go
type Role struct {
	Id            int    `json:"role_id"         gorm:"column:id;autoincrement;primaryKey"`
	Name          string `json:"role_name"       gorm:"column:name;type:varchar"`
	AccessControl bool   `json:"access_control"  gorm:"column:access_control;type:boolean;default:false"`
	Modify        bool   `json:"modify"          gorm:"column:modify;type:boolean;default:false"`
	Read          bool   `json:"read"            gorm:"column:read;type:boolean;default:false"`
}
```

**Snapshot:**

| id | name   | access_control | modify | read |
|----|--------|----------------|--------|------|
| 1  | admin  | true           | true   | true |
| 2  | editor | false          | true   | true |
| 3  | viewer | false          | false  | true |

## groups

`PK` `id` `FK` `create_by`

```go

type Group struct {
	Id         int      `json:"group_id"    gorm:"column:id;autoincrement;primaryKey"`
	Name       string   `json:"group_name"  gorm:"column:name;type:varchar"`
	IsPersonal bool     `json:"is_personal" gorm:"column:is_personal;type:boolean;default:false"`
	CreateBy   int      `json:"create_by"   gorm:"column:create_by;"`
}
```

<!-- Any public content is assigned to the `public` group, `id` 1. When a new user is created, a personal group is created for them, and they are assigned to it. -->

`v3.0.0`
Added public groups for Taipei (name=taipei) and Metro Taipei (name=metrotaipei).

## auth_user_group_roles

`PK` `FK` `user_id` `group_id` `role_id`

```go
type AuthUserGroupRole struct {
	AuthUserID int      `json:"user_id"     gorm:"column:auth_user_id;primaryKey"`
	GroupID    int      `json:"group_id"    gorm:"column:group_id;primaryKey;"`
	RoleID     int      `json:"role_id"     gorm:"column:role_id;primaryKey"`
}
```