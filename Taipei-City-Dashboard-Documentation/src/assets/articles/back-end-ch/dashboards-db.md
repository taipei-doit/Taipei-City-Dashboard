## 概述

`dashboards` 表儲存儀表板配置。`dashboard_groups` 表儲存權限群組與各儀表板之間的關係。

在檢索儀表板時，`dashboard_groups` 表透過 `dashboard_groups.dashboard_id` 和 `dashboards.id` 欄與 `dashboards` 表連接。然後將用戶所屬的權限群組與 `dashboard_groups.group_id` 欄相互比對，以獲取用戶可以檢視的儀表板。

## dashboards

`PK` `id`

```go
type Dashboard struct {
	ID         int           `json:"-"          gorm:"column:id;autoincrement;primaryKey"`
	Index      string        `json:"index"      gorm:"column:index;type:varchar;unique;not null"     `
	Name       string        `json:"name"       gorm:"column:name;type:varchar;not null"`
	Components pq.Int64Array `json:"components" gorm:"column:components;type:int[]"`
	Icon       string        `json:"icon"       goem:"column:icon;type:varchar;not null"`
	UpdatedAt  time.Time     `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
	CreatedAt  time.Time     `json:"-"          gorm:"column:created_at;type:timestamp with time zone;not null"`
}
```

`dashboards` 表各欄位的詳細填寫方式（以確保前端相容性）可以在[這裡](/front-end/introduction-to-dashboards)找到。

## dashboard_groups

`PK` `FK` `dashboard_id` `group_id`

```go
type DashboardGroup struct {
	DashboardID int       `gorm:"column:dashboard_id;primaryKey"`
	GroupID     int       `gorm:"column:group_id;primaryKey"`
	Dashboard   Dashboard `gorm:"foreignKey:DashboardID"`
	Group       Group     `gorm:"foreignKey:GroupID"`
}
```
