package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/services/ai/providers/twcc"
	"TaipeiCityDashboardBE/global"
	"net/http"

	"github.com/gin-gonic/gin"
)

// GetStaticTranslations handles GET /api/v1/translation/static
func GetStaticTranslations(c *gin.Context) {
	// 1. Get target language from Context (set by LanguageHandler middleware)
	langInterface, exists := c.Get("lang")
	targetLang := "zh-TW"
	if exists {
		targetLang = langInterface.(string)
	}

	// 2. Initialize Translation Service
	// In a real app, this might be a global instance, but we follow the current pattern.
	twccLLM := twcc.New(global.TWCC.ApiKey, global.TWCC.ApiUrl, global.TWCC.Model, 60)
	service := ai.NewTranslationService(models.DBManager, twccLLM)

	// 3. Prepare Response Dictionary
	dictionary := make(map[string]string)
	for key, originalText := range ai.StaticUITranslations {
		// Use the service to get translation (Async supported)
		dictionary[key] = service.Translate(c.Request.Context(), originalText, targetLang, "ui_static")
	}

	// 4. Return the language pack
	c.JSON(http.StatusOK, gin.H{
		"locale":  targetLang,
		"strings": dictionary,
	})
}
