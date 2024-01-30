// Package models stores the models for the postgreSQL databases.
package models

import (
	"time"

	"github.com/lib/pq"
)

// Dashboard is the model for the dashboards table.
type Dashboard struct {
	ID         int           `json:"-"         gorm:"column:id;autoincrement;primaryKey"`
	Index      string        `json:"index" gorm:"column:index;type:varchar;unique;not null"     `
	Name       string        `json:"name"       gorm:"column:name;type:varchar;not null"`
	Components pq.Int64Array `json:"components" gorm:"column:components;type:int[]"`
	Icon       string        `json:"icon"       goem:"column:icon;type:varchar;not null"`
	UpdatedAt  time.Time     `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
	CreatedAt  time.Time     `json:"-" gorm:"column:created_at;type:timestamp with time zone;not null"`
}

type UpdateDashboard struct {
	Index      string        `json:"index" gorm:"column:index;type:varchar;unique;not null"     `
	Name       string        `json:"name"       gorm:"column:name;type:varchar;not null"`
	Components pq.Int64Array `json:"components" gorm:"column:components;type:int[]"`
	Icon       string        `json:"icon"       goem:"column:icon;type:varchar;not null"`
	UpdatedAt  time.Time     `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}

type DashboardGroup struct {
	DashboardID int       `json:"dashboard_id" gorm:"column:dashboard_id;primaryKey"`
	GroupID     int       `json:"group_id"     gorm:"column:group_id;primaryKey"`
	Dashboard   Dashboard `gorm:"foreignKey:DashboardID"`
	Group       Group     `gorm:"foreignKey:GroupID"`
}
