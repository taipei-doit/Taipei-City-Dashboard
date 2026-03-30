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

		for _, part := range mc.Parts {
			if text, ok := part.(llms.TextContent); ok {
				twccMessages = append(twccMessages, TWCCMessage{
					Role:    role,
					Content: text.Text,
				})
			}
		}
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
	
	// Use a dedicated client for streaming to avoid global timeout issues
	client := m.HTTPClient
	if isStreaming {
		client = &http.Client{Timeout: 0} // No global timeout, rely on context
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
		// Use bufio.Reader for more precise control over SSE lines
		reader := bufio.NewReader(resp.Body)
		var fullContent strings.Builder
		var lastUsage *TWCCStreamResponse
		
		for {
			line, err := reader.ReadString('\n')
			
			// Process the line if it's not empty, even if err is io.EOF
			if line != "" {
				// Pass RAW data line to StreamingFunc (preserving the original \n)
				if streamErr := opts.StreamingFunc(ctx, []byte(line)); streamErr != nil {
					return nil, streamErr
				}

				// Internal extraction for logging
				// Be robust: trim spaces and handle both "data: " and "data:"
				trimmedLine := strings.TrimSpace(line)
				jsonData := trimmedLine
				if strings.HasPrefix(trimmedLine, "data:") {
					jsonData = strings.TrimPrefix(trimmedLine, "data:")
					jsonData = strings.TrimSpace(jsonData)
				}
				
				if jsonData != "" && jsonData != "[DONE]" {
					var streamResp TWCCStreamResponse
					if unmarshalErr := json.Unmarshal([]byte(jsonData), &streamResp); unmarshalErr == nil {
						// Capture content from either GeneratedText or Choices
						if streamResp.GeneratedText != "" {
							fullContent.WriteString(streamResp.GeneratedText)
						} else if len(streamResp.Choices) > 0 {
							fullContent.WriteString(streamResp.Choices[0].Delta.Content)
						}

						if streamResp.Usage != nil {
							lastUsage = &streamResp
						}
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

		// Prepare a final Response object for downstream use (logging)
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

	var twccResp TWCCResponse
	if err := json.Unmarshal(rawBody, &twccResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %v, body: %s", err, string(rawBody))
	}

	content := ""
	if len(twccResp.Choices) > 0 {
		content = twccResp.Choices[0].Message.Content
	} else {
		content = twccResp.GeneratedText
	}

	return &llms.ContentResponse{
		Choices: []*llms.ContentChoice{
			{
				Content: content,
				GenerationInfo: map[string]interface{}{
					"model": m.ModelName,
					"usage": map[string]interface{}{
						"input_tokens":  twccResp.PromptTokens,
						"output_tokens": twccResp.GeneratedTokens,
						"total_tokens":  twccResp.TotalTokens,
					},
				},
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
