package twcc

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/logs"
	"github.com/tmc/langchaingo/llms"
)

type TWCC struct {
	APIKey      string
	BaseURL     string
	ModelName   string
	HTTPClient  *http.Client
	Temperature float64
	MaxTokens   int
}

// Ensure TWCC implements llms.Model
var _ llms.Model = (*TWCC)(nil)

func New(apiKey, baseURL, model string, timeout int) *TWCC {
	return &TWCC{
		APIKey:     apiKey,
		BaseURL:    baseURL,
		ModelName:  model,
		HTTPClient: &http.Client{Timeout: time.Duration(timeout) * time.Second},
		Temperature: 0.7,
		MaxTokens:   350,
	}
}

func (m *TWCC) GenerateContent(ctx context.Context, messages []llms.MessageContent, options ...llms.CallOption) (*llms.ContentResponse, error) {
	// 0. Handle Options
	opts := llms.CallOptions{}
	for _, opt := range options {
		opt(&opts)
	}

	// 1. Convert langchaingo messages to TWCC format
	twccMessages := make([]TWCCMessage, 0)
	for _, mc := range messages {
		role := string(mc.Role)
		var toolCallID string
		var twccToolCalls []TWCCToolCall

		// Map langchaingo roles to TWCC roles
		switch mc.Role {
		case llms.ChatMessageTypeHuman:
			role = "user"
		case llms.ChatMessageTypeAI:
			role = "assistant"
		case llms.ChatMessageTypeSystem:
			role = "system"
		case llms.ChatMessageTypeTool:
			role = "tool"
		}

		content := ""
		for _, part := range mc.Parts {
			switch p := part.(type) {
			case llms.TextContent:
				content = p.Text
			case llms.ToolCall:
				twccToolCalls = append(twccToolCalls, TWCCToolCall{
					ID:   p.ID,
					Type: p.Type,
					Function: struct {
						Name      string `json:"name"`
						Arguments string `json:"arguments"`
					}{
						Name:      p.FunctionCall.Name,
						Arguments: p.FunctionCall.Arguments,
					},
				})
			case llms.ToolCallResponse:
				toolCallID = p.ToolCallID
				content = p.Content
			}
		}

		twccMessages = append(twccMessages, TWCCMessage{
			Role:       role,
			Content:    content,
			ToolCalls:  twccToolCalls,
			ToolCallID: toolCallID,
		})
	}

	// 2. Build Request Payload using Metadata for precise mapping
	twccParams := TWCCParameters{}
	if val, ok := opts.Metadata["max_new_tokens"].(int); ok {
		twccParams.MaxNewTokens = &val
	}
	if val, ok := opts.Metadata["temperature"].(float64); ok {
		twccParams.Temperature = &val
	}
	if val, ok := opts.Metadata["top_p"].(float64); ok {
		twccParams.TopP = &val
	}
	if val, ok := opts.Metadata["top_k"].(int); ok {
		twccParams.TopK = &val
	}
	if val, ok := opts.Metadata["frequence_penalty"].(float64); ok {
		twccParams.FrequencePenalty = &val
	}
	if val, ok := opts.Metadata["stop_sequences"].([]string); ok {
		twccParams.StopSequences = val
	}
	if val, ok := opts.Metadata["seed"].(int); ok {
		twccParams.Seed = &val
	}

	isStreaming := opts.StreamingFunc != nil
	twccParams.Stream = isStreaming

	reqBody := TWCCRequest{
		Model:      m.ModelName,
		Messages:   twccMessages,
		Parameters: twccParams,
		Stream:     isStreaming,
	}

	// Handle Tools
	if len(opts.Tools) > 0 {
		twccTools := make([]TWCCTool, 0)
		for _, t := range opts.Tools {
			params := t.Function.Parameters
			if params == nil {
				params = map[string]interface{}{
					"type":       "object",
					"properties": map[string]interface{}{},
				}
			}
			twccTools = append(twccTools, TWCCTool{
				Type: t.Type,
				Function: TWCCToolFunction{
					Name:        t.Function.Name,
					Description: t.Function.Description,
					Parameters:  params,
				},
			})
		}
		reqBody.Tools = twccTools
		if opts.ToolChoice != nil {
			reqBody.ToolChoice = opts.ToolChoice
		} else {
			reqBody.ToolChoice = "auto"
		}
	}

	// 3. Send Request
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	endpoint := fmt.Sprintf("%s/models/conversation", m.BaseURL)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-KEY", m.APIKey)

	client := m.HTTPClient
	if isStreaming {
		client = &http.Client{Timeout: 0}
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request to TWCC: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		rawBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("TWCC API returned error status %d: %s", resp.StatusCode, string(rawBody))
	}

	// 4. Handle Streaming vs Standard Response
	if isStreaming {
		reader := bufio.NewReader(resp.Body)
		var fullContent strings.Builder
		var lastUsage *TWCCStreamResponse
		var toolCallsMap = make(map[int]*TWCCToolCall)
		var isToolCalling bool

		for {
			line, err := reader.ReadString('\n')
			if line != "" {
				trimmedLine := strings.TrimSpace(line)
				jsonData := ""
				if strings.HasPrefix(trimmedLine, "data:") {
					jsonData = strings.TrimPrefix(trimmedLine, "data:")
					jsonData = strings.TrimSpace(jsonData)
				}

				if jsonData != "" && jsonData != "[DONE]" {
					var streamResp TWCCStreamResponse
					if unmarshalErr := json.Unmarshal([]byte(jsonData), &streamResp); unmarshalErr == nil {
						// Detection: Does THIS chunk have tools?
						thisChunkHasTools := len(streamResp.ToolCalls) > 0
						if len(streamResp.Choices) > 0 && len(streamResp.Choices[0].Delta.ToolCalls) > 0 {
							thisChunkHasTools = true
						}

						if thisChunkHasTools {
							isToolCalling = true
							// Process ToolCalls from root
							for _, tc := range streamResp.ToolCalls {
								if _, exists := toolCallsMap[0]; !exists {
									toolCallsMap[0] = &TWCCToolCall{ID: tc.ID, Type: tc.Type}
									toolCallsMap[0].Function.Name = tc.Function.Name
								}
								toolCallsMap[0].Function.Arguments += tc.Function.Arguments
							}
							// Process ToolCalls from choices
							if len(streamResp.Choices) > 0 {
								for _, tc := range streamResp.Choices[0].Delta.ToolCalls {
									if _, exists := toolCallsMap[0]; !exists {
										toolCallsMap[0] = &TWCCToolCall{ID: tc.ID, Type: tc.Type}
										toolCallsMap[0].Function.Name = tc.Function.Name
									}
									toolCallsMap[0].Function.Arguments += tc.Function.Arguments
								}
							}
						} else {
							// Normal text chunk: Pass the ORIGINAL line to keep SSE protocol (\n included)
							if streamErr := opts.StreamingFunc(ctx, []byte(line)); streamErr != nil {
								return nil, streamErr
							}
							if len(streamResp.Choices) > 0 && streamResp.Choices[0].Delta.Content != "" {
								fullContent.WriteString(streamResp.Choices[0].Delta.Content)
							}
						}

						if streamResp.Usage != nil {
							lastUsage = &streamResp
						}
					}
				} else if jsonData == "[DONE]" {
					// End of stream
					if !isToolCalling {
						opts.StreamingFunc(ctx, []byte(line))
					}
				} else {
					// This is likely an empty line or non-data SSE line (like a retry or comment)
					// Pass it through to keep the connection alive/valid
					if !isToolCalling {
						opts.StreamingFunc(ctx, []byte(line))
					}
				}
			}

			if err != nil {
				if err == io.EOF {
					break
				}
				return nil, fmt.Errorf("error reading stream: %v", err)
			}
		}

		finalResp := &llms.ContentResponse{
			Choices: []*llms.ContentChoice{
				{
					Content: fullContent.String(),
					GenerationInfo: map[string]interface{}{
						"model": m.ModelName,
					},
				},
			},
		}

		if isToolCalling {
			ltc := make([]llms.ToolCall, 0)
			for _, tc := range toolCallsMap {
				ltc = append(ltc, llms.ToolCall{
					ID:   tc.ID,
					Type: tc.Type,
					FunctionCall: &llms.FunctionCall{
						Name:      tc.Function.Name,
						Arguments: tc.Function.Arguments,
					},
				})
			}
			finalResp.Choices[0].GenerationInfo["tool_calls"] = ltc
		}
		if lastUsage != nil && lastUsage.Usage != nil {
			finalResp.Choices[0].GenerationInfo["usage"] = map[string]interface{}{
				"input_tokens":  lastUsage.Usage.PromptTokens,
				"output_tokens": lastUsage.Usage.GeneratedTokens,
				"total_tokens":  lastUsage.Usage.TotalTokens,
			}
		}
		return finalResp, nil
	}

	// Standard Non-Streaming Path
	rawBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %v", err)
	}

	// Log the raw response for debugging
	logs.FInfo("TWCC Raw Response: %s", string(rawBody))

	var twccResp TWCCResponse
	if err := json.Unmarshal(rawBody, &twccResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %v", err)
	}

	content := twccResp.GeneratedText
	var toolCalls []llms.ToolCall

	// 1. Try to get tool_calls from root level first (as seen in log)
	if len(twccResp.ToolCalls) > 0 {
		for _, tc := range twccResp.ToolCalls {
			toolCalls = append(toolCalls, llms.ToolCall{
				ID:   tc.ID,
				Type: tc.Type,
				FunctionCall: &llms.FunctionCall{
					Name:      tc.Function.Name,
					Arguments: tc.Function.Arguments,
				},
			})
		}
	}

	// 2. Fallback to choices if root level is empty
	if len(twccResp.Choices) > 0 {
		choice := twccResp.Choices[0]
		if choice.Message.Content != "" {
			content = choice.Message.Content
		}
		if len(toolCalls) == 0 && len(choice.Message.ToolCalls) > 0 {
			for _, tc := range choice.Message.ToolCalls {
				toolCalls = append(toolCalls, llms.ToolCall{
					ID:   tc.ID,
					Type: tc.Type,
					FunctionCall: &llms.FunctionCall{
						Name:      tc.Function.Name,
						Arguments: tc.Function.Arguments,
					},
				})
			}
		}
	}

	genInfo := map[string]interface{}{
		"model": m.ModelName,
		"usage": map[string]interface{}{
			"input_tokens":  twccResp.PromptTokens,
			"output_tokens": twccResp.GeneratedTokens,
			"total_tokens":  twccResp.TotalTokens,
		},
	}
	if len(toolCalls) > 0 {
		genInfo["tool_calls"] = toolCalls
	}

	return &llms.ContentResponse{
		Choices: []*llms.ContentChoice{
			{
				Content:        content,
				GenerationInfo: genInfo,
			},
		},
	}, nil
}

func (m *TWCC) Call(ctx context.Context, prompt string, options ...llms.CallOption) (string, error) {
	msg := llms.MessageContent{
		Role:  llms.ChatMessageTypeHuman,
		Parts: []llms.ContentPart{llms.TextContent{Text: prompt}},
	}
	resp, err := m.GenerateContent(ctx, []llms.MessageContent{msg}, options...)
	if err != nil {
		return "", err
	}
	return resp.Choices[0].Content, nil
}
