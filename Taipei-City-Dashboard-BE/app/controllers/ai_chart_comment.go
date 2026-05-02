package controllers

import (
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/util"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/tmc/langchaingo/llms"
)

const (
	chartCommentPromptLimit   = 6000
	chartCommentPromptVersion = "v5-25-50-char-summary"
	chartCommentTargetRunes   = 40
	chartCommentMinRunes      = 25
	chartCommentMaxRunes      = 50
	chartCommentMaxAttempts   = 4
	defaultChartCommentTTL    = 15 * time.Minute
)

type AIChartCommentInput struct {
	ComponentID    int         `json:"component_id"`
	Index          string      `json:"index"`
	City           string      `json:"city"`
	Name           string      `json:"name" binding:"required"`
	Source         string      `json:"source"`
	TimeFrom       string      `json:"time_from"`
	TimeTo         string      `json:"time_to"`
	UpdateFreq     interface{} `json:"update_freq"`
	UpdateFreqUnit string      `json:"update_freq_unit"`
	ShortDesc      string      `json:"short_desc"`
	LongDesc       string      `json:"long_desc"`
	ChartConfig    interface{} `json:"chart_config" binding:"required"`
	ChartData      interface{} `json:"chart_data" binding:"required"`
}

type chartCommentCacheEntry struct {
	Comment   string
	ExpiresAt time.Time
	CreatedAt time.Time
}

var chartCommentCache = struct {
	sync.RWMutex
	items map[string]chartCommentCacheEntry
}{
	items: make(map[string]chartCommentCacheEntry),
}

// GetAIChartComment returns a cached AI summary for a chart, generating it when stale.
func GetAIChartComment(c *gin.Context) {
	var input AIChartCommentInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":     "error",
			"error_code": "INVALID_REQUEST",
			"message":    err.Error(),
		})
		return
	}

	cacheKey := buildChartCommentCacheKey(input)
	if entry, ok := getChartCommentCache(cacheKey); ok {
		c.JSON(http.StatusOK, gin.H{
			"status": "success",
			"data": gin.H{
				"comment":    entry.Comment,
				"cache_hit":  true,
				"expires_at": entry.ExpiresAt,
			},
		})
		return
	}

	_, accountID, _, _, _ := util.GetUserInfoFromContext(c)
	req := ai.AIChatRequest{
		SessionID: fmt.Sprintf("dashboard-comment-%s", cacheKey[:16]),
		UserID:    fmt.Sprintf("%d", accountID),
		IPAddress: c.ClientIP(),
		Messages: []llms.MessageContent{
			{
				Role: llms.ChatMessageTypeSystem,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: "你是臺北城市儀表板的資料分析助理，擅長用短句點出圖表重點。"},
				},
			},
			{
				Role: llms.ChatMessageTypeHuman,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: buildChartCommentPrompt(input, 0)},
				},
			},
		},
	}

	comment, err := generateChartComment(c, req, input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":     "error",
			"error_code": "AI_CHART_COMMENT_ERROR",
			"message":    err.Error(),
		})
		return
	}

	entry := setChartCommentCache(cacheKey, comment, chartCommentTTL(input))
	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"comment":    entry.Comment,
			"cache_hit":  false,
			"expires_at": entry.ExpiresAt,
		},
	})
}

func generateChartComment(c *gin.Context, req ai.AIChatRequest, input AIChartCommentInput) (string, error) {
	lastComment := ""
	for attempt := 0; attempt < chartCommentMaxAttempts; attempt++ {
		req.Messages[1].Parts = []llms.ContentPart{
			llms.TextContent{Text: buildChartCommentPrompt(input, attempt)},
		}

		logEntry, err := ai.ChatWithTWCC(
			c.Request.Context(),
			req,
			llms.WithMaxTokens(100),
			llms.WithTemperature(0.3),
			llms.WithTopP(0.9),
		)
		if err != nil {
			return "", err
		}

		comment := normalizeChartComment(logEntry.Answer)
		if comment == "" {
			continue
		}
		lastComment = comment
		if isChartCommentLengthValid(comment) {
			return comment, nil
		}
	}

	if lastComment != "" {
		return lastComment, nil
	}
	return "", fmt.Errorf("AI chart comment is empty")
}

func getChartCommentCache(key string) (chartCommentCacheEntry, bool) {
	now := time.Now()
	chartCommentCache.RLock()
	entry, ok := chartCommentCache.items[key]
	chartCommentCache.RUnlock()
	if !ok {
		return chartCommentCacheEntry{}, false
	}
	if now.Before(entry.ExpiresAt) {
		return entry, true
	}
	chartCommentCache.Lock()
	delete(chartCommentCache.items, key)
	chartCommentCache.Unlock()
	return chartCommentCacheEntry{}, false
}

func setChartCommentCache(key string, comment string, ttl time.Duration) chartCommentCacheEntry {
	now := time.Now()
	entry := chartCommentCacheEntry{
		Comment:   comment,
		CreatedAt: now,
		ExpiresAt: now.Add(ttl),
	}
	chartCommentCache.Lock()
	chartCommentCache.items[key] = entry
	chartCommentCache.Unlock()
	return entry
}

func buildChartCommentCacheKey(input AIChartCommentInput) string {
	payload := map[string]interface{}{
		"prompt_version":   chartCommentPromptVersion,
		"component_id":     input.ComponentID,
		"index":            input.Index,
		"city":             input.City,
		"time_from":        input.TimeFrom,
		"time_to":          input.TimeTo,
		"update_freq":      input.UpdateFreq,
		"update_freq_unit": input.UpdateFreqUnit,
		"chart_config":     input.ChartConfig,
		"chart_data":       input.ChartData,
	}
	raw, _ := json.Marshal(payload)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func buildChartCommentPrompt(input AIChartCommentInput, attempt int) string {
	payload := map[string]interface{}{
		"component": map[string]interface{}{
			"name":             input.Name,
			"source":           input.Source,
			"city":             input.City,
			"time_from":        input.TimeFrom,
			"time_to":          input.TimeTo,
			"update_freq":      input.UpdateFreq,
			"update_freq_unit": input.UpdateFreqUnit,
			"description":      firstNonEmpty(input.ShortDesc, input.LongDesc),
		},
		"chart_config": input.ChartConfig,
		"chart_data":   input.ChartData,
	}
	retryInstruction := ""
	if attempt > 0 {
		retryInstruction = "前一次短評未落在字數範圍，這次請控制在 25 到 50 字且保持完整句。"
	}
	return fmt.Sprintf(
		"請根據以下臺北城市儀表板圖表資料，產生一段繁體中文圖表短評。請只輸出單一完整段落，以約 %d 字為佳，字數需落在 %d 到 %d 字之間，不要使用 Markdown，也不要編造資料。聚焦最明顯的趨勢、異常或比較；若能給簡短建議，請自然帶入。%s\n\n%s",
		chartCommentTargetRunes,
		chartCommentMinRunes,
		chartCommentMaxRunes,
		retryInstruction,
		marshalPromptPayload(payload),
	)
}

func normalizeChartComment(value string) string {
	return strings.Trim(strings.Join(strings.Fields(strings.TrimSpace(value)), " "), "「」\"'` ")
}

func isChartCommentLengthValid(comment string) bool {
	length := len([]rune(comment))
	return length >= chartCommentMinRunes && length <= chartCommentMaxRunes
}

func marshalPromptPayload(payload interface{}) string {
	raw, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return "{}"
	}
	return truncateRunes(string(raw), chartCommentPromptLimit)
}

func truncateRunes(value string, limit int) string {
	runes := []rune(value)
	if len(runes) <= limit {
		return value
	}
	return string(runes[:limit]) + "\n...（資料已截斷）"
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

func chartCommentTTL(input AIChartCommentInput) time.Duration {
	frequency := parseUpdateFrequency(input.UpdateFreq)
	if frequency <= 0 {
		switch input.TimeFrom {
		case "static", "demo":
			return 24 * time.Hour
		case "current":
			return 5 * time.Minute
		default:
			return defaultChartCommentTTL
		}
	}

	switch strings.ToLower(input.UpdateFreqUnit) {
	case "minute", "minutes", "min":
		return clampChartCommentTTL(time.Duration(frequency) * time.Minute)
	case "hour", "hours":
		return clampChartCommentTTL(time.Duration(frequency) * time.Hour)
	case "day", "days":
		return clampChartCommentTTL(time.Duration(frequency) * 24 * time.Hour)
	case "week", "weeks":
		return clampChartCommentTTL(time.Duration(frequency) * 7 * 24 * time.Hour)
	case "month", "months":
		return clampChartCommentTTL(time.Duration(frequency) * 30 * 24 * time.Hour)
	default:
		return defaultChartCommentTTL
	}
}

func clampChartCommentTTL(ttl time.Duration) time.Duration {
	if ttl < time.Minute {
		return time.Minute
	}
	if ttl > 30*24*time.Hour {
		return 30 * 24 * time.Hour
	}
	return ttl
}

func parseUpdateFrequency(value interface{}) int {
	switch typed := value.(type) {
	case int:
		return typed
	case float64:
		return int(typed)
	case string:
		number, err := strconv.Atoi(typed)
		if err == nil {
			return number
		}
	}
	return 0
}
