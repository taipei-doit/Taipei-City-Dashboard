package openai

import (
	"TaipeiCityDashboardBE/app/services/ai/providers/utils"
	"context"
	"github.com/tmc/langchaingo/llms"
	"github.com/tmc/langchaingo/llms/openai"
)

type OpenAIAdapter struct {
	llm   *openai.LLM
	model string
}

var _ llms.Model = (*OpenAIAdapter)(nil)

func New(apiKey, baseURL, model string) (*OpenAIAdapter, error) {
	opts := []openai.Option{
		openai.WithToken(apiKey),
		openai.WithModel(model),
	}
	if baseURL != "" {
		opts = append(opts, openai.WithBaseURL(baseURL))
	}
	llm, err := openai.New(opts...)
	if err != nil {
		return nil, err
	}
	return &OpenAIAdapter{llm: llm, model: model}, nil
}

func (m *OpenAIAdapter) GenerateContent(ctx context.Context, messages []llms.MessageContent, options ...llms.CallOption) (*llms.ContentResponse, error) {
	callOpts := llms.CallOptions{}
	for _, opt := range options {
		opt(&callOpts)
	}

	finalOptions := make([]llms.CallOption, 0, len(options))
	finalOptions = append(finalOptions, options...)

	// 1. Filter Metadata to avoid conflicts with standard parameters.
	// Some OpenAI-compatible gateways (like AFS) validate 'metadata' and error on redundant/wrongly typed fields.
	if len(callOpts.Metadata) > 0 {
		cleanMeta := make(map[string]interface{})
		for k, v := range callOpts.Metadata {
			// Skip keys that are already handled by standard langchaingo CallOptions
			switch k {
			case "frequence_penalty", "temperature", "max_new_tokens", "top_p", "top_k", "stop_sequences", "seed":
				continue
			}
			cleanMeta[k] = v
		}
		finalOptions = append(finalOptions, llms.WithMetadata(cleanMeta))
	}

	resp, err := m.llm.GenerateContent(ctx, messages, finalOptions...)
	if err != nil {
		return nil, err
	}

	// 2. Bridge langchaingo's standard response to our project's custom internal format
	if len(resp.Choices) > 0 {
		choice := resp.Choices[0]
		if choice.GenerationInfo == nil {
			choice.GenerationInfo = make(map[string]interface{})
		}
		choice.GenerationInfo["model"] = m.model

		// Map ToolCalls: our ai_service.go looks for them in GenerationInfo["tool_calls"]
		if len(choice.ToolCalls) > 0 {
			choice.GenerationInfo["tool_calls"] = choice.ToolCalls
		}

		// Map Usage: Support various naming conventions and structures from different providers
		var it, ot, tt int
		if usageObj, ok := choice.GenerationInfo["usage"]; ok {
			// Try to extract from usage map/struct (snake_case or PascalCase)
			if usage, ok := usageObj.(map[string]interface{}); ok {
				it = utils.ParseUsageInt(usage["prompt_tokens"])
				if it == 0 { it = utils.ParseUsageInt(usage["PromptTokens"]) }
				ot = utils.ParseUsageInt(usage["completion_tokens"])
				if ot == 0 { ot = utils.ParseUsageInt(usage["CompletionTokens"]) }
				tt = utils.ParseUsageInt(usage["total_tokens"])
				if tt == 0 { tt = utils.ParseUsageInt(usage["TotalTokens"]) }
			}
		}

		// Fallback: Check root level of GenerationInfo (Confirmed format for AFS OpenAI Gateway)
		if it == 0 { it = utils.ParseUsageInt(choice.GenerationInfo["PromptTokens"]) }
		if it == 0 { it = utils.ParseUsageInt(choice.GenerationInfo["prompt_tokens"]) }
		if ot == 0 { ot = utils.ParseUsageInt(choice.GenerationInfo["CompletionTokens"]) }
		if ot == 0 { ot = utils.ParseUsageInt(choice.GenerationInfo["completion_tokens"]) }

		if it > 0 || ot > 0 {
			if tt == 0 { tt = utils.ParseUsageInt(choice.GenerationInfo["TotalTokens"]) }
			if tt == 0 { tt = utils.ParseUsageInt(choice.GenerationInfo["total_tokens"]) }
			if tt == 0 { tt = it + ot }
			
			choice.GenerationInfo["usage"] = map[string]interface{}{
				"input_tokens":  it,
				"output_tokens": ot,
				"total_tokens":  tt,
			}
		}
	}

	return resp, nil
}

func (m *OpenAIAdapter) Call(ctx context.Context, prompt string, options ...llms.CallOption) (string, error) {
	return llms.GenerateFromSinglePrompt(ctx, m, prompt, options...)
}
