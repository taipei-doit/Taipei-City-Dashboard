package ai

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/tmc/langchaingo/llms"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

// TranslationService handles the logic for translating text with caching.
type TranslationService struct {
	db  *gorm.DB
	llm llms.Model
}

// NewTranslationService creates a new instance of TranslationService.
func NewTranslationService(db *gorm.DB, model llms.Model) *TranslationService {
	return &TranslationService{
		db:  db,
		llm: model,
	}
}

// Translate translates a single string with cache-first logic.
// Now changed to SYNCHRONOUS to ensure UI consistency.
func (s *TranslationService) Translate(ctx context.Context, text string, targetLang string, contextHint string) string {
	if text == "" || targetLang == "" || targetLang == "zh-TW" || targetLang == "zh-Hant" {
		return text
	}

	// 1. Lookup in Cache
	var cached models.Translation
	err := s.db.Where("source_text = ? AND target_lang = ?", text, targetLang).First(&cached).Error
	if err == nil {
		return cached.TranslatedText
	}

	// 2. Cache Miss -> Synchronous Translation
	// We use a timeout to prevent the API from hanging too long
	syncCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	translated, err := s.callLLM(syncCtx, text, targetLang)
	if err != nil {
		logs.FError("LLM Translation failed for '%s': %v", text, err)
		return text // Fallback to original
	}

	// 3. Save to Cache
	newCache := models.Translation{
		SourceText:     text,
		TargetLang:     targetLang,
		TranslatedText: translated,
		ContextHint:    contextHint,
	}

	// Use Upsert logic
	err = s.db.Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "source_text"}, {Name: "target_lang"}},
		DoUpdates: clause.AssignmentColumns([]string{"translated_text", "context_hint", "updated_at"}),
	}).Create(&newCache).Error

	if err != nil {
		logs.FError("Failed to save translation to cache: %v", err)
	} else {
		logs.FInfo("Successfully translated and cached: '%s' -> '%s' (%s)", text, translated, targetLang)
	}

	return translated
}

// TranslatableKeys is a whitelist of JSON keys that should be translated.
var TranslatableKeys = map[string]bool{
	"title":       true,
	"name":        true,
	"unit":        true,
	"label":       true,
	"short_desc":  true,
	"long_desc":   true,
	"use_case":    true,
	"source":      true,
	"text":        true,
	"placeholder": true,
	"city":        true,
	"category":    true,
	"description": true,
	"value":       true, // Some charts use "value" as a label
	"legend":      true,
	"xAxis":       true,
	"yAxis":       true,
	"filter":      true,
	"group":       true,
	"sub_title":   true,
	"header":      true,
	"footer":      true,
	"content":     true,
	"tooltip":     true,
}

// TranslateJSON recursively walks through a JSON object and translates string values of whitelisted keys.
func (s *TranslationService) TranslateJSON(ctx context.Context, data []byte, targetLang string, contextHint string) []byte {
	if len(data) == 0 || targetLang == "" || targetLang == "zh-TW" || targetLang == "zh-Hant" {
		return data
	}

	var obj interface{}
	if err := json.Unmarshal(data, &obj); err != nil {
		logs.FError("Failed to unmarshal JSON for translation: %v", err)
		return data
	}

	s.walkAndTranslate(ctx, obj, targetLang, contextHint)

	translatedData, err := json.Marshal(obj)
	if err != nil {
		logs.FError("Failed to marshal translated JSON: %v", err)
		return data
	}

	return translatedData
}

func (s *TranslationService) walkAndTranslate(ctx context.Context, v interface{}, targetLang string, contextHint string) {
	switch val := v.(type) {
	case map[string]interface{}:
		for k, item := range val {
			if str, ok := item.(string); ok && TranslatableKeys[k] {
				// Translate the value and update the map
				val[k] = s.Translate(ctx, str, targetLang, contextHint)
			} else {
				// Recursive call for nested objects or arrays
				s.walkAndTranslate(ctx, item, targetLang, contextHint)
			}
		}
	case []interface{}:
		for i, item := range val {
			s.walkAndTranslate(ctx, item, targetLang, contextHint)
			val[i] = item // Update slice in case of replacement
		}
	}
}

func (s *TranslationService) callLLM(ctx context.Context, text, targetLang string) (string, error) {
	prompt := fmt.Sprintf("Translate the following text to %s. Return ONLY the translated text without any explanations or quotes.\nText: %s", targetLang, text)
	
	// We can use the global semaphore to respect rate limits
	if err := aiSemaphore.Acquire(ctx, 1); err != nil {
		return "", err
	}
	defer aiSemaphore.Release(1)

	resp, err := s.llm.Call(ctx, prompt, llms.WithTemperature(0.1)) // Low temperature for factual translation
	if err != nil {
		return "", err
	}

	return resp, nil
}
