package models

import (
	"time"
)

// Translation is the model for the translations table, used as a cache for LLM translations.
type Translation struct {
	ID             int64     `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	SourceText     string    `json:"source_text" gorm:"column:source_text;type:text;not null;uniqueIndex:idx_source_lang"`
	TargetLang     string    `json:"target_lang" gorm:"column:target_lang;type:varchar(10);not null;uniqueIndex:idx_source_lang"`
	TranslatedText string    `json:"translated_text" gorm:"column:translated_text;type:text;not null"`
	ContextHint    string    `json:"context_hint" gorm:"column:context_hint;type:varchar(255)"`
	UpdatedAt      time.Time `json:"updated_at" gorm:"column:updated_at;autoUpdateTime"`
}
