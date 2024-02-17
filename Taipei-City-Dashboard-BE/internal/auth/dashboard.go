package auth

import (
	"time"

	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"TaipeiCityDashboardBE/logs"

	"github.com/lib/pq"
)

// CreateDashboard creates a new dashboard in the database.
func CreateDashboard(index, name, icon string, belongGroup int) (dashboard models.Dashboard, err error) {
	dashboard = models.Dashboard{
		Index: index,
		Name:  name,
		Icon:  icon,
		// Components: components,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	tx := postgres.DBManager.Begin()

	// Create the dashboard
	if err := tx.Create(&dashboard).Error; err != nil {
		tx.Rollback()
		return models.Dashboard{}, err
	}

	// Create a new dashboard group
	dashboardGroup := models.DashboardGroup{
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
		return models.Dashboard{}, err
	}

	tx.Commit()
	return dashboard, nil // Return the dashboard ID and nil error.
}

// DeleteDashboard deletes a dashboard from the database based on its ID.
func DeleteDashboard(dashboardID int) error {
	tx := postgres.DBManager.Begin()

	var dashboard models.Dashboard
	if err := tx.Where("id = ?", dashboardID).First(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}

	if err := tx.Delete(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}

	tx.Commit()
	return nil
}

// UpdateDashboard updates an existing dashboard in the database.
func UpdateDashboard(dashboardID int, newName, newIcon string, newComponents pq.Int64Array) error {
	tx := postgres.DBManager.Begin()

	var dashboard models.Dashboard
	if err := tx.Where("id = ?", dashboardID).First(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}

	dashboard.Name = newName
	dashboard.Icon = newIcon
	dashboard.Components = newComponents
	dashboard.UpdatedAt = time.Now()

	if err := tx.Save(&dashboard).Error; err != nil {
		tx.Rollback()
		return err
	}

	tx.Commit()
	return nil
}
