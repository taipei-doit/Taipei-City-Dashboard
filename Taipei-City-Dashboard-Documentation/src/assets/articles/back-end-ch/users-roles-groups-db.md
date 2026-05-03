## 概述

`auth_users`、`roles` 和 `groups` 表用於管理用戶資訊與權限。`auth_users` 包含用戶資訊；`roles` 包含三個預定義角色（admin、editor、viewer）及其權限；而 `groups` 包含用戶可以被分配到的權限群組。

`auth_user_group_roles` 表用於管理用戶、群組和角色之間的關係。用戶可以被分配到多個群組，且每個群組可以有多個角色。

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

**值得注意的欄位**

`idno`、`tp_uuid`、`tp_account`、`tp_member_type`、`tp_verify_level` 用於儲存使用臺北通登入的用戶資訊。

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

**概覽：**

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

<!-- 任何公開內容都會被分配到 `public` 群組，`id` 為 1。當建立新用戶時，應用程式會為他們建立一個私人群組，並將新用戶分配到該群組。 -->

`v3.0.0`
新增了台北 (name=taipei)，雙北 (name=metrotaipei) public group。

## auth_user_group_roles

`PK` `FK` `user_id` `group_id` `role_id`

```go
type AuthUserGroupRole struct {
	AuthUserID int      `json:"user_id"     gorm:"column:auth_user_id;primaryKey"`
	GroupID    int      `json:"group_id"    gorm:"column:group_id;primaryKey;"`
	RoleID     int      `json:"role_id"     gorm:"column:role_id;primaryKey"`
}
```