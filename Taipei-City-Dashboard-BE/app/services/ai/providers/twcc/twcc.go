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
		var toolName string
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

		var contentText string
		for _, part := range mc.Parts {
			switch p := part.(type) {
			case llms.TextContent:
				contentText = p.Text
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
				toolName = p.Name
				contentText = p.Content
			}
		}

		msg := TWCCMessage{
			Role:       role,
			ToolCalls:  twccToolCalls,
			ToolCallID: toolCallID,
			Name:       toolName,
		}
		// AFS requires content to be present for most roles, 
		// but assistant messages with tool_calls might have empty/null content.
		if role == "assistant" && len(twccToolCalls) > 0 && contentText == "" {
			// Don't set content pointer, it will be omitted from JSON
		} else {
			msg.Content = strPtr(contentText)
		}

		twccMessages = append(twccMessages, msg)
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
	logs.FInfo("TWCC Outgoing Request: %s", string(jsonData))

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
		
		// Detection State
		var isToolCalling bool
		var detectionConfirmed bool
		var lineBuffer []string
		var contentBuffer strings.Builder

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
						// A. Structural Detection (Highest Priority)
						hasFields := len(streamResp.ToolCalls) > 0
						if len(streamResp.Choices) > 0 {
							if len(streamResp.Choices[0].Delta.ToolCalls) > 0 || streamResp.Choices[0].FinishReason == "tool_calls" {
								hasFields = true
							}
						}

						if hasFields && !isToolCalling {
							isToolCalling = true
							detectionConfirmed = true
						}

						// B. Extract Content and Heuristic Detection
						deltaText := ""
						if len(streamResp.Choices) > 0 {
							deltaText = streamResp.Choices[0].Delta.Content
						}
						if deltaText == "" {
							deltaText = streamResp.GeneratedText
						}

						if !detectionConfirmed {
							contentBuffer.WriteString(deltaText)
							combined := contentBuffer.String()
							
							// Check for XML-like tags common in AFS
							if strings.Contains(combined, "<function=") || strings.Contains(combined, "tool<function") {
								isToolCalling = true
								detectionConfirmed = true
							} else if len(combined) > 64 {
								isToolCalling = false
								detectionConfirmed = true
								
								// Flush buffered lines to frontend
								for _, bl := range lineBuffer {
									if streamErr := opts.StreamingFunc(ctx, []byte(bl)); streamErr != nil {
										return nil, streamErr
									}
								}
								lineBuffer = nil
							}
						} else if !isToolCalling {
							// DYNAMIC INTERCEPTION with Pre-emptive Buffering:
							// We buffer lines that look like they COULD be the start of a tool call.
							contentBuffer.WriteString(deltaText)
							lineBuffer = append(lineBuffer, line)
							
							combined := contentBuffer.String()
							if strings.Contains(combined, "<function=") || strings.Contains(combined, "tool<function") {
								isToolCalling = true
								lineBuffer = nil // Wipe the leaked/buffered tool tags
								contentBuffer.Reset()
							} else {
								// Check if the current buffer ends with a potential tool marker prefix
								if isPotentialToolPrefix(combined) {
									// Holding potential tool prefix...
								} else {
									// Safe to flush all buffered pass-through lines
									for _, bl := range lineBuffer {
										if streamErr := opts.StreamingFunc(ctx, []byte(bl)); streamErr != nil {
											return nil, streamErr
										}
									}
									lineBuffer = nil
									contentBuffer.Reset()
								}
							}
						}

						// C. Action based on confirmed state
						if detectionConfirmed {
							if isToolCalling {
								// SILENT MODE: Accumulate tool call data, do NOT stream to frontend
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
							}
							// Note: Pass-through is now handled by the logic above to support buffering
						} else {
							lineBuffer = append(lineBuffer, line)
						}

						// Always keep track of full content for the final return
						fullContent.WriteString(deltaText)

						if streamResp.PromptTokens > 0 || streamResp.GeneratedTokens > 0 || streamResp.Usage != nil {
							lastUsage = &streamResp
						}
					}
				} else if jsonData == "[DONE]" {
					// End of stream handling
					if !detectionConfirmed {
						// If we reach [DONE] and never confirmed Tool vs Text, 
						// and there's content in the buffer, it must be Text.
						isToolCalling = false
						detectionConfirmed = true
						for _, bl := range lineBuffer {
							opts.StreamingFunc(ctx, []byte(bl))
						}
						lineBuffer = nil
					}

					if !isToolCalling {
						// Stream the final [DONE] if it's a normal conversation
						opts.StreamingFunc(ctx, []byte(line))
					}
				} else {
					// Handle empty or heart-beat lines
					if !detectionConfirmed {
						lineBuffer = append(lineBuffer, line)
					} else if !isToolCalling {
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

		// Final flush if the stream ended without [DONE] or confirming type
		if !detectionConfirmed && len(lineBuffer) > 0 {
			logs.FInfo("TWCC Action: Finalizing stream, flushing remaining buffer (length: %d)", len(lineBuffer))
			isToolCalling = false
			detectionConfirmed = true
			for _, bl := range lineBuffer {
				if streamErr := opts.StreamingFunc(ctx, []byte(bl)); streamErr != nil {
					return nil, streamErr
				}
			}
			lineBuffer = nil
		}

		// Prepare Final Response Object for ai_service.go
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
			
			// If we have structural tool calls, process them
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

			// If no structural tool calls found but isToolCalling is true, 
			// or if we want to support mixed mode, try heuristic XML extraction
			if len(ltc) == 0 && (strings.Contains(fullContent.String(), "<function=") || strings.Contains(fullContent.String(), "tool<")) {
				extracted, cleaned := extractXMLToolCalls(fullContent.String())
				if len(extracted) > 0 {
					ltc = extracted
					finalResp.Choices[0].Content = cleaned
				}
			}

			finalResp.Choices[0].GenerationInfo["tool_calls"] = ltc
		}
		if lastUsage != nil {
			inputTokens := lastUsage.PromptTokens
			outputTokens := lastUsage.GeneratedTokens
			totalTokens := lastUsage.TotalTokens

			if lastUsage.Usage != nil {
				if inputTokens == 0 { inputTokens = lastUsage.Usage.PromptTokens }
				if outputTokens == 0 { outputTokens = lastUsage.Usage.GeneratedTokens }
				if totalTokens == 0 { totalTokens = lastUsage.Usage.TotalTokens }
			}

			if inputTokens > 0 || outputTokens > 0 {
				finalResp.Choices[0].GenerationInfo["usage"] = map[string]interface{}{
					"input_tokens":  inputTokens,
					"output_tokens": outputTokens,
					"total_tokens":  totalTokens,
				}
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

	// 1. Try to get tool_calls from root level first
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

	// 2. Fallback to choices
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

	// 3. Heuristic Parsing: If still no tools, try to parse XML tags from content
	if len(toolCalls) == 0 && (strings.Contains(content, "<function=") || strings.Contains(content, "tool<")) {
		extractedTools, cleanedContent := extractXMLToolCalls(content)
		if len(extractedTools) > 0 {
			toolCalls = extractedTools
			content = cleanedContent
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

// extractXMLToolCalls identifies <function=NAME>{ARGS}</function> in text,
// extracts them as ToolCalls, and returns the text with tags removed.
func extractXMLToolCalls(text string) ([]llms.ToolCall, string) {
	var toolCalls []llms.ToolCall
	remainingText := text

	// Basic regex-free parsing for reliability with AFS fragments
	// Pattern: <function=([^>]+)>(.*?)</function>
	for {
		startTag := "<function="
		startIdx := strings.Index(remainingText, startTag)
		if startIdx == -1 {
			// Try the other common AFS format: tool<function=...
			startTag = "tool<function="
			startIdx = strings.Index(remainingText, startTag)
			if startIdx == -1 { break }
		}

		nameEndIdx := strings.Index(remainingText[startIdx:], ">")
		if nameEndIdx == -1 { break }
		nameEndIdx += startIdx

		funcName := remainingText[startIdx+len(startTag) : nameEndIdx]

		endTag := "</function>"
		endIdx := strings.Index(remainingText[nameEndIdx:], endTag)
		if endIdx == -1 { break }
		endIdx += nameEndIdx

		args := remainingText[nameEndIdx+1 : endIdx]

		toolCalls = append(toolCalls, llms.ToolCall{
			ID:   fmt.Sprintf("call_%d", time.Now().UnixNano()),
			Type: "function",
			FunctionCall: &llms.FunctionCall{
				Name:      funcName,
				Arguments: args,
			},
		})

		// Remove the tag from content to prevent 400 errors in next round
		remainingText = remainingText[:startIdx] + remainingText[endIdx+len(endTag):]
	}

	return toolCalls, strings.TrimSpace(remainingText)
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

func strPtr(s string) *string {
	return &s
}

// isPotentialToolPrefix checks if the string ends with a potential start of an XML tool call tag.
func isPotentialToolPrefix(s string) bool {
	if len(s) > 20 {
		s = s[len(s)-20:]
	}
	s = strings.ToLower(s)

	// Check for prefixes of "tool<function" or "<function"
	prefixes := []string{" tool<", "tool<", "<func", "<f", " <"}
	for _, p := range prefixes {
		if strings.HasSuffix(s, p) {
			return true
		}
	}

	// Also catch the word "tool" preceded by a space or newline
	if strings.HasSuffix(s, " tool") {
		return true
	}

	return false
}
