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

	// 1. Get target language
	targetLang := req.TargetLocale
	if targetLang == "" {
		langInterface, exists := c.Get("lang")
		if exists {
			targetLang = langInterface.(string)
		} else {
			targetLang = "zh-TW"
		}
	}

	// 2. Use parallel Batch translation
	var translations []string
	if global.GlobalTranslator != nil {
		translations = global.GlobalTranslator.TranslateBatch(c.Request.Context(), req.Texts, targetLang, "batch_api")
	} else {
		twccLLM := twcc.New(global.TWCC.ApiKey, global.TWCC.ApiUrl, global.TWCC.Model, 60)
		service := ai.NewTranslationService(models.DBManager, twccLLM)
		translations = service.TranslateBatch(c.Request.Context(), req.Texts, targetLang, "batch_api")
	}

	c.JSON(http.StatusOK, gin.H{
		"translations": translations,
	})
}

// GetStaticTranslations handles GET /api/v1/translation/static
func GetStaticTranslations(c *gin.Context) {
	langInterface, exists := c.Get("lang")
	targetLang := "zh-TW"
	if exists {
		targetLang = langInterface.(string)
	}

	dictionary := make(map[string]string)
	ctx := c.Request.Context()

	// 收集所有 key 並批次處理
	keys := make([]string, 0, len(ai.StaticUITranslations))
	originalTexts := make([]string, 0, len(ai.StaticUITranslations))
	for k, v := range ai.StaticUITranslations {
		keys = append(keys, k)
		originalTexts = append(originalTexts, v)
	}

	var translatedTexts []string
	if global.GlobalTranslator != nil {
		translatedTexts = global.GlobalTranslator.TranslateBatch(ctx, originalTexts, targetLang, "ui_static")
	} else {
		twccLLM := twcc.New(global.TWCC.ApiKey, global.TWCC.ApiUrl, global.TWCC.Model, 60)
		service := ai.NewTranslationService(models.DBManager, twccLLM)
		translatedTexts = service.TranslateBatch(ctx, originalTexts, targetLang, "ui_static")
	}

	for i, key := range keys {
		dictionary[key] = translatedTexts[i]
	}

	c.JSON(http.StatusOK, gin.H{
		"locale":  targetLang,
		"strings": dictionary,
	})
}
