package ai

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai/providers"
	"TaipeiCityDashboardBE/app/services/ai/providers/utils"
	"TaipeiCityDashboardBE/app/services/ai/tools"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/tmc/langchaingo/llms"
	"golang.org/x/sync/semaphore"
	"google.golang.org/api/googleapi"
)

var (
	// aiSemaphore limits the number of concurrent AI requests
	aiSemaphore *semaphore.Weighted
	
	// modelsRegistry stores initialized llms.Model instances for each provider
	modelsRegistry sync.Map
)

func init() {
	aiSemaphore = semaphore.NewWeighted(int64(global.AI.MaxConcurrent))
}

// getModel retrieves or initializes a model for a specific provider
func getModel(provider string) (llms.Model, error) {
	if m, ok := modelsRegistry.Load(provider); ok {
		return m.(llms.Model), nil
	}

	// Double-checked locking or just let providers handle concurrency if needed.
	// For simplicity and to avoid complex locks, we just use a simple factory call.
	m, err := providers.GetModel(provider)
	if err != nil {
		return nil, err
	}

	modelsRegistry.Store(provider, m)
	return m, nil
}

type AIChatRequest struct {
	SessionID string                 `json:"session"`
	UserID    string                 `json:"user_id"`
	IPAddress string                 `json:"ip_address"`
	Messages  []llms.MessageContent  `json:"messages"`
	Params    map[string]interface{} `json:"params"`
	Provider  string                 `json:"provider"` // Added to track which provider to use
}

// ChatWithTWCC is kept for backward compatibility, now delegates to ChatWithProvider
func ChatWithTWCC(ctx context.Context, req AIChatRequest, options ...llms.CallOption) (*models.AIChatLog, error) {
	return ChatWithProvider(ctx, "twcc", req, options...)
}

// ChatWithProvider handles the AI conversation logic for a specific provider.
func ChatWithProvider(ctx context.Context, provider string, req AIChatRequest, options ...llms.CallOption) (*models.AIChatLog, error) {
	if err := aiSemaphore.Acquire(ctx, 1); err != nil {
		return nil, fmt.Errorf("server too busy: %v", err)
	}
	defer aiSemaphore.Release(1)

	model, err := getModel(provider)
	if err != nil {
		return nil, err
	}

	req.Provider = provider
	session := newSession(ctx, model, req, options...)
	return session.run(ctx)
}

func newSession(ctx context.Context, model llms.Model, req AIChatRequest, options ...llms.CallOption) *aiSession {
	s := &aiSession{
		model:           model,
		req:             req,
		options:         options,
		currentMessages: make([]llms.MessageContent, 0),
		startTime:       time.Now(),
	}

	// 1. Apply options to get callOpts
	for _, opt := range options {
		opt(&s.callOpts)
	}

	// 2. Universal Streaming Wrapper: 
	// Ensure all providers' raw text output is wrapped in the project's expected JSON format.
	if s.callOpts.StreamingFunc != nil {
		originalFunc := s.callOpts.StreamingFunc
		wrappedFunc := func(ctx context.Context, chunk []byte) error {
			// If chunk is already formatted (like heartbeat or JSON data), pass it through
			if bytes.HasPrefix(chunk, []byte("data: {")) || bytes.Equal(chunk, []byte(": heartbeat\n\n")) {
				return originalFunc(ctx, chunk)
			}
			// Otherwise, wrap raw text into TWCC-style JSON {"generated_text": "..."}
			formatted := utils.FormatSSE(string(chunk), 0, 0)
			return originalFunc(ctx, formatted)
		}
		
		// Override the StreamingFunc in the session's options slice
		s.options = append(s.options, llms.WithStreamingFunc(wrappedFunc))
		// Update callOpts for the session's own use (e.g., heartbeats)
		s.callOpts.StreamingFunc = wrappedFunc
	}

	s.injectInstructions()
	return s
}

type aiSession struct {
	model           llms.Model
	req             AIChatRequest
	options         []llms.CallOption
	callOpts        llms.CallOptions
	currentMessages []llms.MessageContent
	totalInput      int
	totalOutput     int
	toolUsed        bool
	executedTools   []string
	lastResp        *llms.ContentResponse
	lastErr         error
	startTime       time.Time
}

func (s *aiSession) run(ctx context.Context) (*models.AIChatLog, error) {
	maxLoops := 5
	s.executedTools = make([]string, 0)
	for i := 0; i < maxLoops; i++ {
		s.sendHeartbeat(ctx)

		if err := s.generate(ctx); err != nil {
			break
		}

		toolCalls := s.extractToolCalls()
		if len(toolCalls) == 0 {
			break
		}

		s.toolUsed = true
		logs.FInfo("Loop %d: Processing %d tool calls", i, len(toolCalls))
		if err := s.executeTools(ctx, toolCalls); err != nil {
			break
		}
	}
	return s.finalize()
}

func (s *aiSession) sendHeartbeat(ctx context.Context) {
	if s.callOpts.StreamingFunc != nil {
		s.callOpts.StreamingFunc(ctx, []byte(": heartbeat\n\n"))
	}
}

func (s *aiSession) generate(ctx context.Context) error {
	// Disable retries to avoid 429 errors during debugging or per user request
	maxRetry := 0

	for i := 0; i <= maxRetry; i++ {
		s.lastResp, s.lastErr = s.model.GenerateContent(ctx, s.currentMessages, s.options...)
		if s.lastErr == nil {
			s.updateTokens()
			return nil
		}
		
		errMsg := s.lastErr.Error()
		var gErr *googleapi.Error
		if errors.As(s.lastErr, &gErr) {
			// Extract as much as possible from Google API error
			details, _ := json.Marshal(gErr.Errors)
			errMsg = fmt.Sprintf("GoogleAPI Error %d: %s | Message: %s | Details: %s", gErr.Code, gErr.Error(), gErr.Message, string(details))
		} else {
			// Brutal logging for unknown error types
			errMsg = fmt.Sprintf("[%T] %#v", s.lastErr, s.lastErr)
		}
		
		logs.FError("Attempt %d failed: %s", i+1, errMsg)
		if i < maxRetry {
			time.Sleep(500 * time.Millisecond)
		}
	}
	return s.lastErr
}

func (s *aiSession) extractToolCalls() []llms.ToolCall {
	if s.lastResp == nil || len(s.lastResp.Choices) == 0 {
		return nil
	}
	tc, _ := s.lastResp.Choices[0].GenerationInfo["tool_calls"].([]llms.ToolCall)
	return tc
}

func (s *aiSession) updateTokens() {
	if s.lastResp == nil || len(s.lastResp.Choices) == 0 {
		return
	}
	
	genInfo := s.lastResp.Choices[0].GenerationInfo
	if genInfo == nil {
		return
	}

	it, ot, tt := 0, 0, 0

	// 1. Try to find 'usage' nested map (Standard langchaingo pattern)
	if usage, ok := genInfo["usage"].(map[string]interface{}); ok {
		it = utils.ParseUsageInt(usage["input_tokens"])
		ot = utils.ParseUsageInt(usage["output_tokens"])
		tt = utils.ParseUsageInt(usage["total_tokens"])
	}

	// 2. Fallback: Check root of GenerationInfo (Common for some providers or direct API responses)
	if it == 0 {
		it = utils.ParseUsageInt(genInfo["input_tokens"])
		if it == 0 { it = utils.ParseUsageInt(genInfo["PromptTokens"]) }
	}
	if ot == 0 {
		ot = utils.ParseUsageInt(genInfo["output_tokens"])
		if ot == 0 { ot = utils.ParseUsageInt(genInfo["CompletionTokens"]) }
	}
	if tt == 0 {
		tt = utils.ParseUsageInt(genInfo["total_tokens"])
		if tt == 0 { tt = utils.ParseUsageInt(genInfo["TotalTokens"]) }
	}

	if it > 0 || ot > 0 {
		s.totalInput += it
		s.totalOutput += ot
		logs.FInfo("Tokens Updated: Input=%d, Output=%d", it, ot)
	}
}

func (s *aiSession) executeTools(ctx context.Context, toolCalls []llms.ToolCall) error {
	choice := s.lastResp.Choices[0]

	// 1. Ensure tool calls have IDs and Type for internal consistency
	for i := range toolCalls {
		if toolCalls[i].ID == "" {
			toolCalls[i].ID = fmt.Sprintf("call_%d_%d", time.Now().UnixNano(), i)
		}
		if toolCalls[i].Type == "" {
			toolCalls[i].Type = "function"
		}
	}

	// 2. Add Assistant's intent (AI message)
	aiParts := make([]llms.ContentPart, 0, len(toolCalls)+1)
	if choice.Content != "" {
		aiParts = append(aiParts, llms.TextContent{Text: choice.Content})
	}
	aiParts = append(aiParts, toolsToParts(toolCalls)...)

	s.currentMessages = append(s.currentMessages, llms.MessageContent{
		Role:  llms.ChatMessageTypeAI,
		Parts: aiParts,
	})

	// 3. Execute tools and collect results
	for _, tc := range toolCalls {
		s.executedTools = append(s.executedTools, tc.FunctionCall.Name)
		result, err := tools.Execute(ctx, tc.FunctionCall.Name, tc.FunctionCall.Arguments)
		if err != nil {
			result = fmt.Sprintf("Error: %v. Please verify arguments.", err)
			logs.FError("Tool Error: %v", err)
		}

		s.currentMessages = append(s.currentMessages, llms.MessageContent{
			Role: llms.ChatMessageTypeTool,
			Parts: []llms.ContentPart{llms.ToolCallResponse{
				ToolCallID: tc.ID,
				Name:       tc.FunctionCall.Name,
				Content:    result,
			}},
		})
	}

	return nil
}

func (s *aiSession) injectInstructions() {
	// Only inject extra instructions for TWCC to improve tool calling reliability
	if s.req.Provider != "twcc" {
		s.currentMessages = s.req.Messages
		return
	}

	toolNames := ""
	for i, t := range s.callOpts.Tools {
		if i > 0 {
			toolNames += ", "
		}
		toolNames += t.Function.Name
	}

	instruction := fmt.Sprintf("\nSystem Instruction:\n1. Use ONLY: [%s].\n2. NEVER nest tool calls \n3. Arguments MUST be literal values (strings, integers, etc.), never function calls \n4. For dependent tasks, call tools sequentially in separate turns.\n5. If stuck, respond with text.", toolNames)

	s.currentMessages = make([]llms.MessageContent, 0)
	merged := false
	for _, m := range s.req.Messages {
		if m.Role == llms.ChatMessageTypeSystem && !merged {
			s.currentMessages = append(s.currentMessages, mergeSystemMsg(m, instruction))
			merged = true
		} else {
			s.currentMessages = append(s.currentMessages, m)
		}
	}

	if !merged {
		s.currentMessages = append([]llms.MessageContent{{
			Role: llms.ChatMessageTypeSystem,
			Parts: []llms.ContentPart{llms.TextContent{Text: "Instruction: Use tools: [" + toolNames + "]."}},
		}}, s.currentMessages...)
	}
}

func (s *aiSession) finalize() (*models.AIChatLog, error) {
	provider := s.req.Provider
	model := ""
	switch provider {
	case "openai":
		model = global.OpenAI.Model
	case "gemini":
		model = global.Gemini.Model
	default:
		model = global.TWCC.Model
	}


	log := &models.AIChatLog{
		SessionID: s.req.SessionID, UserID: s.req.UserID, IPAddress: s.req.IPAddress,
		Provider: provider, Model: model, LatencyMS: int(time.Since(s.startTime).Milliseconds()),
		Status: "success", Tools: "[]", CreatedAt: s.startTime,
	}

	if len(s.req.Messages) > 0 {
		log.Question = extractText(s.req.Messages[len(s.req.Messages)-1])
	}

	if s.lastErr != nil {
		log.Status, log.ErrorCode, log.ErrorMessage = "error", "MODEL_ERROR", s.lastErr.Error()
		models.CreateAIChatLog(log)
		return log, s.lastErr
	}

	if s.lastResp != nil && len(s.lastResp.Choices) > 0 {
		log.Answer = s.lastResp.Choices[0].Content
		log.InputTokens, log.OutputTokens = s.totalInput, s.totalOutput
		log.TotalTokens = s.totalInput + s.totalOutput
		if s.toolUsed {
			log.ToolUsed = true
			if toolJSON, err := json.Marshal(s.executedTools); err == nil {
				log.Tools = string(toolJSON)
			}
		}
	}

	if err := models.CreateAIChatLog(log); err != nil {
		logs.FError("DB Log Error: %v", err)
	}
	return log, nil
}

func toolsToParts(calls []llms.ToolCall) []llms.ContentPart {
	parts := make([]llms.ContentPart, len(calls))
	for i, c := range calls { parts[i] = c }
	return parts
}

func mergeSystemMsg(m llms.MessageContent, instruction string) llms.MessageContent {
	newParts := make([]llms.ContentPart, len(m.Parts))
	for i, p := range m.Parts {
		if tp, ok := p.(llms.TextContent); ok {
			newParts[i] = llms.TextContent{Text: tp.Text + instruction}
		} else {
			newParts[i] = p
		}
	}
	return llms.MessageContent{Role: m.Role, Parts: newParts}
}

func extractText(m llms.MessageContent) string {
	for _, p := range m.Parts {
		if t, ok := p.(llms.TextContent); ok { return t.Text }
	}
	return ""
}

func parseUsageInt(val interface{}) int {
	switch v := val.(type) {
	case int: return v
	case float64: return int(v)
	default: return 0
	}
}
