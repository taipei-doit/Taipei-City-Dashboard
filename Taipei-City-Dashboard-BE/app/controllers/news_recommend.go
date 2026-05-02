package controllers

import (
	"TaipeiCityDashboardBE/app/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// RecommendNewsFromRSS serves POST /api/v1/ai/recommend-news/crawl — RSS ingestion + lightweight keyword tagging to components.
func RecommendNewsFromRSS(c *gin.Context) {
	items, err := services.FetchSimpleRSSNewsRecommendations(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"status":  "error",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"items": items,
		},
	})
}
