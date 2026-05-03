## Overview

The `dashboards` table stores the main configurations of dashboards. The `dashboard_groups` table stores the relationship between permission groups and dashboards.

When querying for dashboards, the `dashboard_groups` table is joined with the `dashboards` via the `dashboard_groups.dashboard_id` and `dashboards.id` columns. The permission groups the user belongs to is then matched with the `dashboard_groups.group_id` column to retrieve the dashboards the user has access to.

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

More information on front-end requirements for the `dashboards` table can be found in the [here](/front-end/introduction-to-dashboards).

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
