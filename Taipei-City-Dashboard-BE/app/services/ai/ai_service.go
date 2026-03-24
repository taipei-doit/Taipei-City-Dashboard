package ai

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai/providers/twcc"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/tmc/langchaingo/llms"
	"golang.org/x/sync/semaphore"
)

var (
	// aiSemaphore limits the number of concurrent AI requests
	aiSemaphore *semaphore.Weighted
	twccModel   llms.Model
)

func init() {
	// Initialize semaphore from config
	aiSemaphore = semaphore.NewWeighted(int64(global.TWCC.MaxConcurrent))
	
	// Initialize TWCC provider as the default LLM
	twccModel = twcc.New(
		global.TWCC.ApiKey,
		global.TWCC.ApiUrl,
		global.TWCC.Model,
		global.TWCC.Timeout,
	)
}

// AIChatRequest represents the incoming request structure for AI chat
type AIChatRequest struct {
	SessionID string                `json:"session_id"`
	UserID    string                `json:"user_id"`
	Messages  []llms.MessageContent `json:"messages"`
	Params    map[string]interface{} `json:"params"`
}

// ChatWithTWCC handles the AI conversation logic including retries and logging
func ChatWithTWCC(ctx context.Context, req AIChatRequest, options ...llms.CallOption) (*models.AIChatLog, error) {
	// 1. Concurrency Control
	if err := aiSemaphore.Acquire(ctx, 1); err != nil {
		return nil, fmt.Errorf("server too busy: %v", err)
	}
	defer aiSemaphore.Release(1)

	startTime := time.Now()
	var finalResp *llms.ContentResponse
	var lastErr error

	// 2. Retry Logic (Up to MaxRetry + 1 attempts)
	for i := 0; i <= global.TWCC.MaxRetry; i++ {
		finalResp, lastErr = twccModel.GenerateContent(ctx, req.Messages, options...)
		if lastErr == nil {
			break
		}
		logs.FError("TWCC Attempt %d failed: %v", i+1, lastErr)
		time.Sleep(500 * time.Millisecond) // Short delay between retries
	}

	latency := int(time.Since(startTime).Milliseconds())

	// 3. Prepare Log Entry
	chatLog := &models.AIChatLog{
		SessionID: req.SessionID,
		UserID:    req.UserID,
		Provider:  "twcc",
		Model:     global.TWCC.Model,
		LatencyMS: latency,
		Status:    "success",
		Tools:     "[]", // Ensure valid JSON format for PostgreSQL JSONB
		CreatedAt: startTime,
	}

	// Extract question from the last user message
	if len(req.Messages) > 0 {
		lastMsg := req.Messages[len(req.Messages)-1]
		for _, part := range lastMsg.Parts {
			if text, ok := part.(llms.TextContent); ok {
				chatLog.Question = text.Text
			}
		}
	}

	if lastErr != nil {
		chatLog.Status = "error"
		chatLog.ErrorCode = "MODEL_ERROR"
		chatLog.ErrorMessage = lastErr.Error()
		models.CreateAIChatLog(chatLog)
		return chatLog, lastErr
	}

	// 4. Extract Answer and Token Usage
	if finalResp != nil && len(finalResp.Choices) > 0 {
		chatLog.Answer = finalResp.Choices[0].Content
		
		// Extract usage info from GenerationInfo
		if usageInfo, ok := finalResp.Choices[0].GenerationInfo["usage"].(map[string]interface{}); ok {
			// Type conversion handling (JSON numbers can be float64 or int depending on decoder)
			chatLog.InputTokens = parseUsageInt(usageInfo["input_tokens"])
			chatLog.OutputTokens = parseUsageInt(usageInfo["output_tokens"])
			chatLog.TotalTokens = parseUsageInt(usageInfo["total_tokens"])
		}
		
		// Future proofing: Tool Calls
		if toolCalls, ok := finalResp.Choices[0].GenerationInfo["tool_calls"]; ok {
			toolsJSON, _ := json.Marshal(toolCalls)
			chatLog.Tools = string(toolsJSON)
			chatLog.ToolUsed = true
		}
	}

	// 5. Persist Log to PostgreSQL
	if err := models.CreateAIChatLog(chatLog); err != nil {
		logs.FError("Failed to save AI chatlog: %v", err)
	}

	return chatLog, nil
}

func parseUsageInt(val interface{}) int {
	switch v := val.(type) {
	case int: return v
	case float64: return int(v)
	default: return 0
	}
}
