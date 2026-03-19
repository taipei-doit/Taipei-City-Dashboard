package twcc

type TWCCMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type TWCCParameters struct {
	MaxNewTokens     int      `json:"max_new_tokens,omitempty"`
	Temperature      *float64 `json:"temperature,omitempty"`
	TopK             *int     `json:"top_k,omitempty"`
	TopP             *float64 `json:"top_p,omitempty"`
	FrequencePenalty *float64 `json:"frequence_penalty,omitempty"`
}

type TWCCRequest struct {
	Model      string         `json:"model"`
	Messages   []TWCCMessage  `json:"messages"`
	Parameters TWCCParameters `json:"parameters"`
	// Future-proofing for Tool Calling
	Tools      []interface{}  `json:"tools,omitempty"`
	ToolChoice interface{}    `json:"tool_choice,omitempty"`
}

type TWCCResponse struct {
	GeneratedText string `json:"generated_text"`
	Choices       []struct {
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
	// TWCC AFS Specific Token Fields (at root level)
	PromptTokens    int `json:"prompt_tokens"`
	GeneratedTokens int `json:"generated_tokens"`
	TotalTokens     int `json:"total_tokens"`
}
