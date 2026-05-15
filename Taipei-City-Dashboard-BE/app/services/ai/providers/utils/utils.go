package utils

import (
	"encoding/json"
	"fmt"
)

// TWCCSSEChunk represents the SSE JSON format expected by the frontend (TWCC style)
type TWCCSSEChunk struct {
	GeneratedText   string `json:"generated_text"`
	PromptTokens    int    `json:"prompt_tokens,omitempty"`
	GeneratedTokens int    `json:"generated_tokens,omitempty"`
	TotalTokens     int    `json:"total_tokens,omitempty"`
}

// FormatSSE converts a chunk of text and token info into the TWCC SSE format string
func FormatSSE(text string, promptTokens, generatedTokens int) []byte {
	chunk := TWCCSSEChunk{
		GeneratedText:   text,
		PromptTokens:    promptTokens,
		GeneratedTokens: generatedTokens,
		TotalTokens:     promptTokens + generatedTokens,
	}
	data, _ := json.Marshal(chunk)
	return []byte(fmt.Sprintf("data: %s\n\n", string(data)))
}

// ParseUsageInt converts various numeric types to int
func ParseUsageInt(val interface{}) int {
	if val == nil {
		return 0
	}
	switch v := val.(type) {
	case int:
		return v
	case int32:
		return int(v)
	case int64:
		return int(v)
	case float32:
		return int(v)
	case float64:
		return int(v)
	case string:
		// Optional: handle cases where tokens might be returned as strings
		var i int
		fmt.Sscanf(v, "%d", &i)
		return i
	default:
		return 0
	}
}
