package twcc

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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
	opts := llms.CallOptions{
		Temperature: m.Temperature,
		MaxTokens:   m.MaxTokens,
		TopP:        1.0, // Default TopP
		TopK:        50,  // Default TopK
		RepetitionPenalty: 1.0, // Default FrequencePenalty
	}
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

	// 2. Build Request Payload with optional pointers
	// Map LangChain RepetitionPenalty back to TWCC frequence_penalty
	frequencePenalty := float64(opts.RepetitionPenalty)
	topP := opts.TopP
	topK := opts.TopK

	reqBody := TWCCRequest{
		Model:    m.ModelName,
		Messages: twccMessages,
		Parameters: TWCCParameters{
			MaxNewTokens:     opts.MaxTokens,
			Temperature:      &opts.Temperature,
			TopP:             &topP,
			TopK:             &topK,
			FrequencePenalty: &frequencePenalty,
		},
	}

	// 3. Send Request
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}

	// 診斷 Log: 查看發送給台智雲的完整內容
	fmt.Printf("TWCC SENDING REQUEST: %s\n", string(jsonData))

	// endpoint: {BaseURL}/models/conversation
	endpoint := fmt.Sprintf("%s/models/conversation", m.BaseURL)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-KEY", m.APIKey)
	
	resp, err := m.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request to TWCC: %v", err)
	}
	defer resp.Body.Close()

	// 一次性讀取 Body，避免重複讀取串流
	rawBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("TWCC API returned error status %d: %s", resp.StatusCode, string(rawBody))
	}

	// 4. Parse Response using rawBody
	var twccResp TWCCResponse
	if err := json.Unmarshal(rawBody, &twccResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %v, body: %s", err, string(rawBody))
	}

	// 5. Convert to langchaingo ContentResponse
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
