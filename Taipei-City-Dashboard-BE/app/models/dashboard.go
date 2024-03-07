// Package models stores the models for the postgreSQL databases.
package models

import (
	"fmt"
	"time"

	"TaipeiCityDashboardBE/logs"

	"github.com/lib/pq"
)

/* ----- Models ----- */

type Dashboard struct {
	ID         int           `json:"-"         gorm:"column:id;autoincrement;primaryKey"`
	Index      string        `json:"index" gorm:"column:index;type:varchar;unique;not null"     `
	Name       string        `json:"name"       gorm:"column:name;type:varchar;not null"`
	Components pq.Int64Array `json:"components" gorm:"column:components;type:int[]"`
	Icon       string        `json:"icon"       goem:"column:icon;type:varchar;not null"`
	UpdatedAt  time.Time     `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
	CreatedAt  time.Time     `json:"-" gorm:"column:created_at;type:timestamp with time zone;not null"`
}

type DashboardGroup struct {
	DashboardID int       `json:"dashboard_id" gorm:"column:dashboard_id;primaryKey"`
	GroupID     int       `json:"group_id"     gorm:"column:group_id;primaryKey"`
	Dashboard   Dashboard `gorm:"foreignKey:DashboardID"`
	Group       Group     `gorm:"foreignKey:GroupID"`
}

/* ----- Handlers ----- */

type allDashboards struct {
	Public   []Dashboard `json:"public"`
	Personal []Dashboard `json:"personal"`
}

func GetAllDashboards(personalGroups []int) (dashboards allDashboards, err error) {
	// Get all the public group dashboards
	err = DBManager.
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id = ?", 1).
		Order("dashboards.id").
		Find(&dashboards.Public).
		Error

	if err != nil {
		return dashboards, err
	}

	// Get all the Personal dashboards
	err = DBManager.
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", personalGroups).
		Order("dashboards.id").
		Find(&dashboards.Personal).
		Error
	return dashboards, err
}

func GetDashboardByIndex(index string, groups []int) (components []Component, err error) {
	tempDB := createTempComponentDB()

	type componentArray struct {
		Components pq.Int64Array `gorm:"type:int[]"`
	}
	var componentIds componentArray

	// 1. Make sure the dashboard exists
	err = DBManager.Table("dashboards").Select("components").Where("index = ?", index).First(&componentIds).Error
	if err != nil {
		return components, err
	}

	// 2. Make sure the user has access to the dashboard
	err = DBManager.
		Table("dashboards").Select("components").
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", index).
		Order("dashboards.id").
		First(&componentIds).
		Error
	if err != nil {
		return components, err
	}

	// 3. Format component ids into slice and string
	var componentIdsSlice []int64
	for _, v := range componentIds.Components {
		componentIdsSlice = append(componentIdsSlice, int64(v))
	}

	if len(componentIdsSlice) == 0 {
		return components, err
	}

	var componentIdsString string
	for i, v := range componentIdsSlice {
		if i > 0 {
			componentIdsString += ","
		}
		componentIdsString += fmt.Sprintf("%d", v)
	}

	// 4. Get components by ids
	err = tempDB.
		Where(componentIdsSlice).
		Order(fmt.Sprintf("ARRAY_POSITION(ARRAY[%s], components.id)", componentIdsString)).
		Find(&components).Error

	return components, err
}

func CheckDashboardIndex(index string) (bool, error) {
	var count int64
	err := DBManager.Table("dashboards").Where("index = ?", index).Count(&count).Error
	return count < 1, err
}

func CreateDashboard(index, name, icon string, components pq.Int64Array, belongGroup int) (dashboard Dashboard, err error) {
	dashboard = Dashboard{
		Index:      index,
		Name:       name,
		Icon:       icon,
		Components: components,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	tx := DBManager.Begin()

	// Create the dashboard
	if err := tx.Create(&dashboard).Error; err != nil {
		tx.Rollback()
		return Dashboard{}, err
	}

	// Create a new dashboard group
	dashboardGroup := DashboardGroup{
		DashboardID: dashboard.ID,
		GroupID:     belongGroup,
	}

	if err := tx.Create(&dashboardGroup).Error; err != nil {
		tx.Rollback()
		// If an error occurs while creating the dashboard group, delete the dashboard to maintain consistency.
		if deleteErr := tx.Delete(&dashboard).Error; deleteErr != nil {
			// If deletion fails, log the error.
			logs.FError("Failed to delete dashboard after failed group creation: %v", deleteErr)
		}
		return Dashboard{}, err
	}

	tx.Commit()
	return dashboard, nil
}

func UpdateDashboard(index string, name, icon string, components pq.Int64Array, groups []int) (dashboard Dashboard, err error) {
	tx := DBManager.Begin()

	// Check if the dashboard exists
	if err = tx.Where("index = ?", index).First(&dashboard).Error; err != nil {
		tx.Rollback()
		return dashboard, err
	}
	// Check if the user has edit access to the dashboard
	err = DBManager.
		Table("dashboards").
		Joins("JOIN dashboard_groups ON dashboards.id = dashboard_groups.dashboard_id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", index).
		First(&dashboard).
		Error
	if err != nil {
		tx.Rollback()
		return dashboard, err
	}

	dashboard.Name = name
	dashboard.Icon = icon
	dashboard.Components = components
	dashboard.UpdatedAt = time.Now()

	// Save the updated dashboard
	if err := tx.Table("dashboards").Where("index = ?", index).Updates(&dashboard).Error; err != nil {
		tx.Rollback()
		return dashboard, err
	}

	if err := tx.Table("dashboards").Where("index = ?", index).Find(&dashboard).Error; err != nil {
		return dashboard, err
	}

	tx.Commit()
	return dashboard, nil
}

func DeleteDashboard(index string, groups []int) (err error) {
	tx := DBManager.Begin()

	var dashboard Dashboard
	var dashboardGroup DashboardGroup
	var deleteDashboard DashboardGroup

	// Check if the dashboard exists
	if err := tx.Where("index = ?", index).First(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}
	// Check if the user has edit access to the dashboard
	err = DBManager.
		Select("dashboard_groups.group_id").
		Joins("JOIN dashboards ON dashboard_groups.dashboard_id = dashboards.id AND dashboard_groups.group_id IN (?)", groups).
		Where("index = ?", index).
		First(&deleteDashboard).
		Error
	if err != nil {
		return err
	}

	// Delete the dashboard group
	if err := DBManager.Table("dashboard_groups").Where("dashboard_id = ?", dashboard.ID).Delete(&dashboardGroup).Error; err != nil {
		tx.Rollback()
		return err
	}
	// Delete the dashboard
	if err := tx.Delete(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}

	tx.Commit()
	return nil
}
