package controllers

import (
	"TaipeiCityDashboardBE/app/services/ai"
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
// LLM 已限縮至小幫手向量／Storyline，此路由僅回傳原文以維持前端契約。
func BatchTranslate(c *gin.Context) {
	var req BatchTranslateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	translations := make([]string, len(req.Texts))
	copy(translations, req.Texts)

	c.JSON(http.StatusOK, gin.H{
		"translations": translations,
	})
}

// GetStaticTranslations handles GET /api/v1/translation/static
// 回傳後端備援之繁中原稿；各語翻譯以前端 frontendBundles 為準。
func GetStaticTranslations(c *gin.Context) {
	langInterface, exists := c.Get("lang")
	targetLang := "zh-TW"
	if exists {
		targetLang = langInterface.(string)
	}

	dictionary := make(map[string]string, len(ai.StaticUITranslations))
	for key, originalText := range ai.StaticUITranslations {
		dictionary[key] = originalText
	}

	c.JSON(http.StatusOK, gin.H{
		"locale":  targetLang,
		"strings": dictionary,
	})
}
