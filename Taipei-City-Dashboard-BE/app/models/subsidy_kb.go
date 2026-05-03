package models

import "gorm.io/gorm"

type SubsidyKB struct {
    ID      int64  `gorm:"primaryKey"`
    Content string `gorm:"type:text"`
    Title   string
    City    string
}

func CreateSubsidyKBTable(db *gorm.DB) error {
    return db.AutoMigrate(&SubsidyKB{})
}