package twcc

type TWCCMessage struct {
	Role       string         `json:"role"`
	Content    *string        `json:"content,omitempty"`
	Name       string         `json:"name,omitempty"`
	ToolCalls  []TWCCToolCall `json:"tool_calls,omitempty"`
	ToolCallID string         `json:"tool_call_id,omitempty"`
}

type TWCCParameters struct {
	MaxNewTokens     *int      `json:"max_new_tokens,omitempty"`
	Temperature      *float64  `json:"temperature,omitempty"`
	TopK             *int     `json:"top_k,omitempty"`
	TopP             *float64  `json:"top_p,omitempty"`
	FrequencePenalty *float64  `json:"frequence_penalty,omitempty"`
	StopSequences    []string `json:"stop_sequences,omitempty"`
	Seed             *int     `json:"seed,omitempty"`
	Stream           bool     `json:"stream,omitempty"`
}

type TWCCRequest struct {
	Model      string         `json:"model"`
	Messages   []TWCCMessage  `json:"messages"`
	Parameters TWCCParameters `json:"parameters"`
	Stream     bool           `json:"stream,omitempty"`
	Tools      []TWCCTool     `json:"tools,omitempty"`
	ToolChoice interface{}    `json:"tool_choice,omitempty"`
}

type TWCCTool struct {
	Type     string         `json:"type"`
	Function TWCCToolFunction `json:"function"`
}

type TWCCToolFunction struct {
	Name        string      `json:"name"`
	Description string      `json:"description,omitempty"`
	Parameters  interface{} `json:"parameters"`
}

type TWCCToolCall struct {
	ID       string `json:"id"`
	Type     string `json:"type"`
	Function struct {
		Name      string `json:"name"`
		Arguments string `json:"arguments"`
	} `json:"function"`
}

type TWCCResponse struct {
	GeneratedText string         `json:"generated_text"`
	ToolCalls     []TWCCToolCall `json:"tool_calls,omitempty"`
	Choices       []struct {
		Message struct {
			Role      string         `json:"role"`
			Content   string         `json:"content"`
			ToolCalls []TWCCToolCall `json:"tool_calls,omitempty"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	// TWCC AFS Specific Token Fields (at root level)
	PromptTokens    int `json:"prompt_tokens"`
	GeneratedTokens int `json:"generated_tokens"`
	TotalTokens     int `json:"total_tokens"`
}

type TWCCStreamResponse struct {
	ID            string         `json:"id"`
	Model         string         `json:"model"`
	GeneratedText string         `json:"generated_text"`
	ToolCalls     []TWCCToolCall `json:"tool_calls,omitempty"`
	Choices       []struct {
		Index int `json:"index"`
		Delta struct {
			Content   string         `json:"content"`
			Role      string         `json:"role"`
			ToolCalls []TWCCToolCall `json:"tool_calls,omitempty"`
		} `json:"delta"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	// AFS sends these at root level in streaming chunks
	PromptTokens    int `json:"prompt_tokens"`
	GeneratedTokens int `json:"generated_tokens"`
	TotalTokens     int `json:"total_tokens"`
	// Keep Usage for compatibility with other formats/future changes
	Usage *struct {
		PromptTokens    int `json:"prompt_tokens"`
		GeneratedTokens int `json:"generated_tokens"`
		TotalTokens     int `json:"total_tokens"`
	} `json:"usage,omitempty"`
}
