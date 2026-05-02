package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/services/ai/providers/twcc"
	"TaipeiCityDashboardBE/global"
	"net/http"

	"github.com/gin-gonic/gin"
)

// BatchTranslateRequest defines the structure for POST /translate
type BatchTranslateRequest struct {
	SourceLocale string   `json:"source_locale"`
	TargetLocale string   `json:"target_locale"`
	Texts        []string `json:"texts"`
}

// BatchTranslate handles POST /api/v1/translate
func BatchTranslate(c *gin.Context) {
	var req BatchTranslateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// 1. Get target language (priority: Body > Header)
	targetLang := req.TargetLocale
	if targetLang == "" {
		langInterface, exists := c.Get("lang")
		if exists {
			targetLang = langInterface.(string)
		} else {
			targetLang = "zh-TW"
		}
	}

	// 2. Use the global translator if available, otherwise initialize a new one
	var translations []string
	if global.GlobalTranslator != nil {
		translations = make([]string, len(req.Texts))
		for i, text := range req.Texts {
			translations[i] = global.GlobalTranslator.Translate(c.Request.Context(), text, targetLang, "batch_api")
		}
	} else {
		// Fallback: Initialize service if global is missing (should not happen in production)
		twccLLM := twcc.New(global.TWCC.ApiKey, global.TWCC.ApiUrl, global.TWCC.Model, 60)
		service := ai.NewTranslationService(models.DBManager, twccLLM)
		translations = make([]string, len(req.Texts))
		for i, text := range req.Texts {
			translations[i] = service.Translate(c.Request.Context(), text, targetLang, "batch_api")
		}
	}

	// 3. Return the translations array as expected by the frontend store
	c.JSON(http.StatusOK, gin.H{
		"translations": translations,
	})
}

// GetStaticTranslations handles GET /api/v1/translation/static
func GetStaticTranslations(c *gin.Context) {
	// 1. Get target language from Context
	langInterface, exists := c.Get("lang")
	targetLang := "zh-TW"
	if exists {
		targetLang = langInterface.(string)
	}

	// 2. Prepare Response Dictionary
	dictionary := make(map[string]string)
	ctx := c.Request.Context()

	if global.GlobalTranslator != nil {
		for key, originalText := range ai.StaticUITranslations {
			dictionary[key] = global.GlobalTranslator.Translate(ctx, originalText, targetLang, "ui_static")
		}
	} else {
		// Fallback
		twccLLM := twcc.New(global.TWCC.ApiKey, global.TWCC.ApiUrl, global.TWCC.Model, 60)
		service := ai.NewTranslationService(models.DBManager, twccLLM)
		for key, originalText := range ai.StaticUITranslations {
			dictionary[key] = service.Translate(ctx, originalText, targetLang, "ui_static")
		}
	}

	// 3. Return the language pack
	c.JSON(http.StatusOK, gin.H{
		"locale":  targetLang,
		"strings": dictionary,
	})
}
