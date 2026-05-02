package models

import (
	"time"

	"gorm.io/gorm/clause"
)

// ForeignCuisineRestaurant stores foreign cuisine POIs for map rendering.
type ForeignCuisineRestaurant struct {
	ID         int64     `json:"id" gorm:"column:id;primaryKey;autoIncrement"`
	City       string    `json:"city" gorm:"column:city;type:text;not null;index:idx_fcr_city;uniqueIndex:udx_fcr_identity,priority:1"`
	Source     string    `json:"source" gorm:"column:source;type:text;not null;uniqueIndex:udx_fcr_identity,priority:2"`
	SourceID   string    `json:"source_id" gorm:"column:source_id;type:text;not null;uniqueIndex:udx_fcr_identity,priority:3"`
	Name       string    `json:"name" gorm:"column:name;type:text;not null"`
	CuisineRaw string    `json:"cuisine_raw" gorm:"column:cuisine_raw;type:text"`
	CuisineZh  string    `json:"cuisine_zh" gorm:"column:cuisine_zh;type:text"`
	Address    string    `json:"address" gorm:"column:address;type:text"`
	District   string    `json:"district" gorm:"column:district;type:text"`
	Lon        float64   `json:"lon" gorm:"column:lon;type:double precision;not null"`
	Lat        float64   `json:"lat" gorm:"column:lat;type:double precision;not null"`
	CreatedAt  time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt  time.Time `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}

func (ForeignCuisineRestaurant) TableName() string {
	return "foreign_cuisine_restaurants"
}

func EnsureForeignCuisineTable() error {
	return DBDashboard.AutoMigrate(&ForeignCuisineRestaurant{})
}

func UpsertForeignCuisineRestaurants(rows []ForeignCuisineRestaurant) error {
	if len(rows) == 0 {
		return nil
	}

	return DBDashboard.
		Clauses(clause.OnConflict{
			Columns: []clause.Column{{Name: "city"}, {Name: "source"}, {Name: "source_id"}},
			DoUpdates: clause.AssignmentColumns([]string{
				"name",
				"cuisine_raw",
				"cuisine_zh",
				"address",
				"district",
				"lon",
				"lat",
				"updated_at",
			}),
		}).
		Create(&rows).Error
}

func ListForeignCuisineRestaurants(city string, limit int) (rows []ForeignCuisineRestaurant, err error) {
	if limit <= 0 || limit > 5000 {
		limit = 2000
	}

	err = DBDashboard.
		Where("city = ?", city).
		Order("updated_at desc").
		Limit(limit).
		Find(&rows).Error

	return rows, err
}
