package controllers

import (
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/util"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/tmc/langchaingo/llms"
)

// AIChatInput matches the Request Schema in specification
type AIChatInput struct {
	SessionID string `json:"session_id"`
	Messages  []struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	} `json:"messages"`
	MaxNewTokens     int     `json:"max_new_tokens"`
	Temperature      float64 `json:"temperature"`
	TopP             float64 `json:"top_p"`
	TopK             int     `json:"top_k"`
	FrequencePenalty float64 `json:"frequence_penalty"`
}

// ChatWithTWCC is the controller for POST /api/v1/ai/chat/twai
func ChatWithTWCC(c *gin.Context) {
	var input AIChatInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "error",
			"error_code": "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	// 1. Convert input to Service Request
	serviceMsgs := make([]llms.MessageContent, 0)
	for _, m := range input.Messages {
		role := llms.ChatMessageTypeHuman
		switch m.Role {
		case "assistant": role = llms.ChatMessageTypeAI
		case "system":    role = llms.ChatMessageTypeSystem
		}
		
		serviceMsgs = append(serviceMsgs, llms.MessageContent{
			Role:  role,
			Parts: []llms.ContentPart{llms.TextContent{Text: m.Content}},
		})
	}

	// 2. Extract UserID from Token (using project utility)
	_, accountID, _, _, _ := util.GetUserInfoFromContext(c)
	userID := fmt.Sprintf("%d", accountID)
	
	req := ai.AIChatRequest{
		SessionID: input.SessionID,
		UserID:    userID,
		Messages:  serviceMsgs,
	}

	// 3. Call AI Service with dynamic options
	options := make([]llms.CallOption, 0)
	if input.MaxNewTokens > 0 {
		options = append(options, llms.WithMaxTokens(input.MaxNewTokens))
	}
	if input.Temperature > 0 {
		options = append(options, llms.WithTemperature(input.Temperature))
	}
	if input.TopP > 0 {
		options = append(options, llms.WithTopP(input.TopP))
	}
	// Note: For TopK and FrequencePenalty, if langchaingo doesn't have WithTopK,
	// we will handle them in the twcc provider via general metadata or custom logic.
	if input.TopK > 0 {
		options = append(options, llms.WithTopK(input.TopK))
	}
	if input.FrequencePenalty > 0 {
		options = append(options, llms.WithRepetitionPenalty(input.FrequencePenalty))
	}

	logEntry, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error_code": "AI_SERVICE_ERROR",
			"message": err.Error(),
		})
		return
	}

	// 4. Return success response per specification
	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"content":     logEntry.Answer,
			"usage": gin.H{
				"input_tokens":  logEntry.InputTokens,
				"output_tokens": logEntry.OutputTokens,
				"total_tokens":  logEntry.TotalTokens,
			},
			"tool_used":   logEntry.ToolUsed,
			"latency_ms":  logEntry.LatencyMS,
			"model":       logEntry.Model,
			"provider":    logEntry.Provider,
		},
	})
}
