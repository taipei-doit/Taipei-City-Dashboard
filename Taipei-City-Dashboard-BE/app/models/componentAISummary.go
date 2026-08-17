// Package models stores the models for the postgreSQL databases.
package models

import (
	"errors"
	"time"

	"gorm.io/gorm"
)

// ComponentAISummary is the model for the component_ai_summary table.
type ComponentAISummary struct {
	ID        int64     `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Index     string    `json:"index" gorm:"column:index;type:varchar;not null"`
	City      string    `json:"city" gorm:"column:city;type:text;not null"`
	Type      string    `json:"type" gorm:"column:type;type:text;not null"`
	Result    string    `json:"result" gorm:"column:result;type:text;not null"`
	UpdatedAt time.Time `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
	CreatedAt time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
}

// TableName pins this model to the existing singular table name.
func (ComponentAISummary) TableName() string {
	return "component_ai_summary"
}

// GetComponentAISummary returns the latest AI summary by index, city, and type.
func GetComponentAISummary(
	index string,
	city string,
	summaryType string,
) (summary ComponentAISummary, err error) {

	query := DBManager.Table("component_ai_summary")

	if index != "" {
		query = query.Where("\"index\" = ?", index)
	}

	if city != "" {
		query = query.Where("city = ?", city)
	}

	if summaryType != "" {
		query = query.Where("type = ?", summaryType)
	}

	err = query.
		Order("updated_at DESC, id DESC").
		First(&summary).Error

	return summary, err
}

// GetComponentAISummaryByID returns one AI summary row by id.
func GetComponentAISummaryByID(id int) (summary ComponentAISummary, err error) {
	err = DBManager.Table("component_ai_summary").Where("id = ?", id).First(&summary).Error
	return summary, err
}

// CreateComponentAISummary inserts a new AI summary row.
func CreateComponentAISummary(
	index string,
	city string,
	summaryType string,
	result string,
) (summary ComponentAISummary, err error) {
	summary.Index = index
	summary.City = city
	summary.Type = summaryType
	summary.Result = result
	summary.CreatedAt = time.Now()
	summary.UpdatedAt = time.Now()

	err = DBManager.Table("component_ai_summary").Create(&summary).Error
	return summary, err
}

// UpsertComponentAISummary updates the latest matching row, or creates one when none exists.
func UpsertComponentAISummary(
	index string,
	city string,
	summaryType string,
	result string,
) (summary ComponentAISummary, created bool, err error) {
	summary, err = GetComponentAISummary(index, city, summaryType)
	if err == nil {
		updated, updateErr := UpdateComponentAISummary(int(summary.ID), index, city, summaryType, result)
		return updated, false, updateErr
	}

	if !errors.Is(err, gorm.ErrRecordNotFound) {
		return summary, false, err
	}

	createdSummary, createErr := CreateComponentAISummary(index, city, summaryType, result)
	return createdSummary, true, createErr
}

// UpdateComponentAISummary updates one AI summary row by id.
func UpdateComponentAISummary(
	id int,
	index string,
	city string,
	summaryType string,
	result string,
) (summary ComponentAISummary, err error) {
	err = DBManager.Table("component_ai_summary").Where("id = ?", id).Updates(map[string]interface{}{
		"index":      index,
		"city":       city,
		"type":       summaryType,
		"result":     result,
		"updated_at": time.Now(),
	}).Error
	if err != nil {
		return summary, err
	}

	err = DBManager.Table("component_ai_summary").Where("id = ?", id).First(&summary).Error
	return summary, err
}
