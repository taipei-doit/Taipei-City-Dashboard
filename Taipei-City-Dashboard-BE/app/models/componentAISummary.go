// Package models stores the models for the postgreSQL databases.
package models

import "time"

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