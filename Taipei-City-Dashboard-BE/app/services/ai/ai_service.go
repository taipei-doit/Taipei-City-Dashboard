package ai

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai/providers/twcc"
	"TaipeiCityDashboardBE/app/services/ai/tools"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"
	"context"
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
	IPAddress string                `json:"ip_address"`
	Messages  []llms.MessageContent `json:"messages"`
	Params    map[string]interface{} `json:"params"`
}

// ChatWithTWCC handles the AI conversation logic including retries, tool calling loop, and logging
func ChatWithTWCC(ctx context.Context, req AIChatRequest, options ...llms.CallOption) (*models.AIChatLog, error) {
	// 1. Concurrency Control
	if err := aiSemaphore.Acquire(ctx, 1); err != nil {
		return nil, fmt.Errorf("server too busy: %v", err)
	}
	defer aiSemaphore.Release(1)

	startTime := time.Now()
	var finalResp *llms.ContentResponse
	var lastErr error

	// Extract CallOptions for retry logic
	opts := llms.CallOptions{}
	for _, opt := range options {
		opt(&opts)
	}

	// 2. Main Tool Calling Loop
	maxToolLoops := 5
	currentMessages := req.Messages
	totalInputTokens := 0
	totalOutputTokens := 0
	var toolUsed bool

	for loop := 0; loop < maxToolLoops; loop++ {
		// Generate Content with Retries
		maxRetry := global.TWCC.MaxRetry
		if opts.StreamingFunc != nil {
			maxRetry = 0
		}

		var currentResp *llms.ContentResponse
		for i := 0; i <= maxRetry; i++ {
			// CRITICAL: We pass the original options (including StreamingFunc) to every call.
			// The provider (twcc.go) is responsible for INTERCEPTING tool chunks 
			// and ONLY calling StreamingFunc for actual text content.
			currentResp, lastErr = twccModel.GenerateContent(ctx, currentMessages, options...)
			if lastErr == nil {
				break
			}
			logs.FError("TWCC Attempt %d failed: %v", i+1, lastErr)
			if i < maxRetry {
				time.Sleep(500 * time.Millisecond)
			}
		}

		if lastErr != nil {
			break
		}

		if currentResp == nil || len(currentResp.Choices) == 0 {
			lastErr = fmt.Errorf("empty response from model")
			break
		}

		choice := currentResp.Choices[0]
		finalResp = currentResp 

		// Accumulate tokens
		if usage, ok := choice.GenerationInfo["usage"].(map[string]interface{}); ok {
			totalInputTokens += parseUsageInt(usage["input_tokens"])
			totalOutputTokens += parseUsageInt(usage["output_tokens"])
		}

		// Check for Tool Calls (this will be populated even in streaming if it was intercepted)
		toolCalls, ok := choice.GenerationInfo["tool_calls"].([]llms.ToolCall)
		if !ok || len(toolCalls) == 0 {
			break
		}

		toolUsed = true
		logs.FInfo("Model requested %d tool calls at loop %d (Streaming: %v)", len(toolCalls), loop, opts.StreamingFunc != nil)

		// Create Assistant message with ToolCalls to keep history
		assistantParts := []llms.ContentPart{llms.TextContent{Text: choice.Content}}
		for _, tc := range toolCalls {
			assistantParts = append(assistantParts, tc)
		}

		assistantMsg := llms.MessageContent{
			Role:  llms.ChatMessageTypeAI,
			Parts: assistantParts,
		}
		currentMessages = append(currentMessages, assistantMsg)

		// Execute Tools and append results
		for _, tc := range toolCalls {
			result, err := tools.Execute(ctx, tc.FunctionCall.Name, tc.FunctionCall.Arguments)
			if err != nil {
				result = fmt.Sprintf("Error executing tool %s: %v", tc.FunctionCall.Name, err)
				logs.FError(result)
			}

			toolResMsg := llms.MessageContent{
				Role: llms.ChatMessageTypeTool,
				Parts: []llms.ContentPart{llms.ToolCallResponse{
					ToolCallID: tc.ID,
					Name:       tc.FunctionCall.Name,
					Content:    result,
				}},
			}
			currentMessages = append(currentMessages, toolResMsg)
		}
	}

	latency := int(time.Since(startTime).Milliseconds())

	// 3. Prepare Log Entry
	chatLog := &models.AIChatLog{
		SessionID: req.SessionID,
		UserID:    req.UserID,
		IPAddress: req.IPAddress,
		Provider:  "twcc",
		Model:     global.TWCC.Model,
		LatencyMS: latency,
		Status:    "success",
		Tools:     "[]",
		CreatedAt: startTime,
	}

	// Extract question
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

	// 4. Finalize Answer and Usage
	if finalResp != nil && len(finalResp.Choices) > 0 {
		chatLog.Answer = finalResp.Choices[0].Content
		chatLog.InputTokens = totalInputTokens
		chatLog.OutputTokens = totalOutputTokens
		chatLog.TotalTokens = totalInputTokens + totalOutputTokens
		
		if toolUsed {
			chatLog.ToolUsed = true
			chatLog.Tools = "[\"tool_calling_loop_executed\"]"
		}
	}

	// 5. Persist Log
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
