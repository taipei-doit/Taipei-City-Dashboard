package controllers

import (
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/util"
	"context"
	"fmt"
	"html"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/tmc/langchaingo/llms"
)

// AIChatInput matches the Request Schema in specification。https://docs.twcloud.ai/docs/user-guides/twcc/afs/api-and-parameters/api-parameter-information#模型說明
type AIChatInput struct {
	SessionID string `json:"session"`
	Stream    bool   `json:"stream"`
	Messages  []struct {
		Role      string `json:"role" binding:"required,oneof=system user assistant tool"`
		Content   string `json:"content" binding:"required"`
		ToolCalls []struct {
			ID       string `json:"id"`
			Type     string `json:"type"`
			Function struct {
				Name      string `json:"name"`
				Arguments string `json:"arguments"`
			} `json:"function"`
		} `json:"tool_calls,omitempty"`
		ToolCallID string `json:"tool_call_id,omitempty"`
	} `json:"messages" binding:"required,gt=0"`
	MaxNewTokens     *int      `json:"max_new_tokens" binding:"omitempty,gt=0"`
	Temperature      *float64  `json:"temperature" binding:"omitempty,gt=0"`
	TopP             *float64  `json:"top_p" binding:"omitempty,gt=0,lte=1"`
	TopK             *int      `json:"top_k" binding:"omitempty,gte=1,lte=100"`
	FrequencePenalty *float64  `json:"frequence_penalty" binding:"omitempty,gt=0"`
	StopSequences    []string  `json:"stop_sequences" binding:"omitempty,max=4"`
	Seed             *int      `json:"seed" binding:"omitempty,gte=0"`
	Tools            []struct {
		Type     string `json:"type" binding:"required,eq=function"`
		Function struct {
			Name        string      `json:"name" binding:"required"`
			Description string      `json:"description,omitempty"`
			Parameters  interface{} `json:"parameters,omitempty"`
		} `json:"function" binding:"required"`
	} `json:"tools,omitempty"`
	ToolChoice interface{} `json:"tool_choice,omitempty"`
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

	// 1. Session ID Management
	sessionID := input.SessionID
	if sessionID == "" {
		sessionID = "session_" + util.GenerateRandomString(10)
	}
	sessionID = html.EscapeString(sessionID)

	// 2. Prepare AI Request
	_, accountID, _, _, _ := util.GetUserInfoFromContext(c)
	req := ai.AIChatRequest{
		SessionID: sessionID,
		UserID:    fmt.Sprintf("%d", accountID),
		IPAddress: c.ClientIP(),
		Messages:  input.ToServiceMessages(),
	}

	// 3. Prepare Dynamic Options
	options := input.ToCallOptions()

	// 4. Handle Streaming Response
	if input.Stream {
		c.Header("Content-Type", "text/event-stream")
		c.Header("Cache-Control", "no-cache")
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("Connection", "keep-alive")

		// Add Streaming Callback
		options = append(options, llms.WithStreamingFunc(func(ctx context.Context, chunk []byte) error {
			if string(chunk) == ": heartbeat\n\n" {
				return nil
			}
			_, err := c.Writer.Write(chunk)
			if err != nil {
				return err
			}
			c.Writer.Flush()
			return nil
		}))

		_, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
		if err != nil {
			if !c.Writer.Written() {
				c.JSON(http.StatusInternalServerError, gin.H{
					"status": "error",
					"error_code": "AI_SERVICE_STREAM_ERROR",
					"message": err.Error(),
				})
			}
		}
		return
	}

	// 5. Standard Non-Streaming Response
	logEntry, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error_code": "AI_SERVICE_ERROR",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"session":     logEntry.SessionID,
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

// ToServiceMessages converts input messages to langchaingo internal format
func (input *AIChatInput) ToServiceMessages() []llms.MessageContent {
	serviceMsgs := make([]llms.MessageContent, 0)
	for _, m := range input.Messages {
		role := llms.ChatMessageTypeHuman
		var parts []llms.ContentPart
		parts = append(parts, llms.TextContent{Text: m.Content})

		switch m.Role {
		case "assistant":
			role = llms.ChatMessageTypeAI
			if len(m.ToolCalls) > 0 {
				for _, tc := range m.ToolCalls {
					parts = append(parts, llms.ToolCall{
						ID:   tc.ID,
						Type: tc.Type,
						FunctionCall: &llms.FunctionCall{
							Name:      tc.Function.Name,
							Arguments: tc.Function.Arguments,
						},
					})
				}
			}
		case "system":
			role = llms.ChatMessageTypeSystem
		case "tool":
			role = llms.ChatMessageTypeTool
			parts = []llms.ContentPart{llms.ToolCallResponse{
				ToolCallID: m.ToolCallID,
				Content:    m.Content,
			}}
		}

		serviceMsgs = append(serviceMsgs, llms.MessageContent{
			Role:  role,
			Parts: parts,
		})
	}
	return serviceMsgs
}

// ToCallOptions extracts and maps AI generation options and tools
func (input *AIChatInput) ToCallOptions() []llms.CallOption {
	options := make([]llms.CallOption, 0)
	params := make(map[string]interface{})

	// Map numerical parameters
	if input.MaxNewTokens != nil {
		options = append(options, llms.WithMaxTokens(*input.MaxNewTokens))
		params["max_new_tokens"] = *input.MaxNewTokens
	}
	if input.Temperature != nil {
		options = append(options, llms.WithTemperature(*input.Temperature))
		params["temperature"] = *input.Temperature
	}
	if input.TopP != nil {
		options = append(options, llms.WithTopP(*input.TopP))
		params["top_p"] = *input.TopP
	}
	if input.TopK != nil {
		options = append(options, llms.WithTopK(*input.TopK))
		params["top_k"] = *input.TopK
	}
	if input.FrequencePenalty != nil {
		options = append(options, llms.WithRepetitionPenalty(*input.FrequencePenalty))
		params["frequence_penalty"] = *input.FrequencePenalty
	}
	if len(input.StopSequences) > 0 {
		options = append(options, llms.WithStopWords(input.StopSequences))
		params["stop_sequences"] = input.StopSequences
	}
	if input.Seed != nil {
		params["seed"] = *input.Seed
	}

	// Map Tools
	if len(input.Tools) > 0 {
		lt := make([]llms.Tool, 0)
		for _, t := range input.Tools {
			lt = append(lt, llms.Tool{
				Type: t.Type,
				Function: &llms.FunctionDefinition{
					Name:        t.Function.Name,
					Description: t.Function.Description,
					Parameters:  t.Function.Parameters,
				},
			})
		}
		options = append(options, llms.WithTools(lt))
		if input.ToolChoice != nil {
			options = append(options, llms.WithToolChoice(input.ToolChoice))
		}
	}

	if len(params) > 0 {
		options = append(options, llms.WithMetadata(params))
	}

	return options
}

