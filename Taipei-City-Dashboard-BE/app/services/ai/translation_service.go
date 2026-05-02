package ai

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"sync"
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
		return text
	}

	// Sanitize output
	translated = strings.Trim(translated, "\"")
	translated = strings.TrimSpace(translated)

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

// TranslateBatch translates multiple strings in parallel.
func (s *TranslationService) TranslateBatch(ctx context.Context, texts []string, targetLang string, contextHint string) []string {
	if len(texts) == 0 {
		return texts
	}

	results := make([]string, len(texts))
	var wg sync.WaitGroup

	for i, text := range texts {
		wg.Add(1)
		go func(index int, t string) {
			defer wg.Done()
			results[index] = s.Translate(ctx, t, targetLang, contextHint)
		}(i, text)
	}

	wg.Wait()
	return results
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
	"category":    true,
	"description": true,
	"value":       true,
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

// TranslateJSON recursively walks through a JSON object and translates string values of whitelisted keys in parallel.
func (s *TranslationService) TranslateJSON(ctx context.Context, data []byte, targetLang string, contextHint string) []byte {
	if len(data) == 0 || targetLang == "" || targetLang == "zh-TW" || targetLang == "zh-Hant" {
		return data
	}

	var obj interface{}
	if err := json.Unmarshal(data, &obj); err != nil {
		logs.FError("Failed to unmarshal JSON for translation: %v", err)
		return data
	}

	// 1. Collect all translatable string pointers
	type stringPtr struct {
		val *string
	}
	var pointers []stringPtr

	var findPointers func(v interface{})
	findPointers = func(v interface{}) {
		switch val := v.(type) {
		case map[string]interface{}:
			for k, item := range val {
				if str, ok := item.(string); ok && TranslatableKeys[k] {
					s := str
					val[k] = &s
					pointers = append(pointers, stringPtr{val: val[k].(*string)})
				} else {
					findPointers(item)
				}
			}
		case []interface{}:
			for _, item := range val {
				findPointers(item)
			}
		}
	}

	findPointers(obj)

	// 2. Extract texts and translate in batch (Parallel)
	if len(pointers) > 0 {
		texts := make([]string, len(pointers))
		for i, p := range pointers {
			texts[i] = *p.val
		}

		translated := s.TranslateBatch(ctx, texts, targetLang, contextHint)

		// 3. Write back translated values
		for i, p := range pointers {
			*p.val = translated[i]
		}
	}

	// 4. Clean up pointers back to strings
	var cleanup func(v interface{})
	cleanup = func(v interface{}) {
		switch val := v.(type) {
		case map[string]interface{}:
			for k, item := range val {
				if sPtr, ok := item.(*string); ok {
					val[k] = *sPtr
				} else {
					cleanup(item)
				}
			}
		case []interface{}:
			for _, item := range val {
				cleanup(item)
			}
		}
	}
	cleanup(obj)

	translatedData, err := json.Marshal(obj)
	if err != nil {
		logs.FError("Failed to marshal translated JSON: %v", err)
		return data
	}

	return translatedData
}

func (s *TranslationService) callLLM(ctx context.Context, text, targetLang string) (string, error) {
	prompt := fmt.Sprintf("Translate the following text to %s. Return ONLY the translated text without any explanations or quotes.\nText: %s", targetLang, text)

	if err := aiSemaphore.Acquire(ctx, 1); err != nil {
		return "", err
	}
	defer aiSemaphore.Release(1)

	resp, err := s.llm.Call(ctx, prompt, llms.WithTemperature(0.1))
	if err != nil {
		return "", err
	}

	return resp, nil
}
