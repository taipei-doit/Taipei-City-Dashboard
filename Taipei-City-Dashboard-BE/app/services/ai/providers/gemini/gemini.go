package gemini

import (
	"TaipeiCityDashboardBE/app/services/ai/providers/utils"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"github.com/tmc/langchaingo/llms"
	"github.com/tmc/langchaingo/llms/googleai"
)

type GeminiAdapter struct {
	llm   *googleai.GoogleAI
	model string
}

var _ llms.Model = (*GeminiAdapter)(nil)

func New(ctx context.Context, apiKey, baseURL, model string) (*GeminiAdapter, error) {
	opts := []googleai.Option{
		googleai.WithAPIKey(apiKey),
		googleai.WithDefaultModel(model),
	}
	// Native Gemini API
	llm, err := googleai.New(ctx, opts...)
	if err != nil {
		return nil, err
	}
	return &GeminiAdapter{llm: llm, model: model}, nil
}

func (m *GeminiAdapter) GenerateContent(ctx context.Context, messages []llms.MessageContent, options ...llms.CallOption) (*llms.ContentResponse, error) {
	callOpts := llms.CallOptions{}
	for _, opt := range options {
		opt(&callOpts)
	}

	// 1. Clean Messages: Gemini is very strict and forbids empty text parts.
	cleanMessages := make([]llms.MessageContent, 0, len(messages))
	for _, msg := range messages {
		newParts := make([]llms.ContentPart, 0, len(msg.Parts))
		for _, part := range msg.Parts {
			if txt, ok := part.(llms.TextContent); ok && txt.Text == "" {
				continue 
			}
			newParts = append(newParts, part)
		}
		if len(newParts) > 0 {
			msg.Parts = newParts
			cleanMessages = append(cleanMessages, msg)
		}
	}

	// 2. Ensure Tools' Parameters are not nil (Google AI SDK requirement)
	finalOptions := make([]llms.CallOption, 0, len(options))
	finalOptions = append(finalOptions, options...)
	if len(callOpts.Tools) > 0 {
		refinedTools := make([]llms.Tool, len(callOpts.Tools))
		for i, t := range callOpts.Tools {
			refinedTools[i] = t
			if t.Function != nil && t.Function.Parameters == nil {
				fDef := *t.Function
				fDef.Parameters = map[string]interface{}{"type": "object", "properties": map[string]interface{}{}}
				refinedTools[i].Function = &fDef
			}
		}
		finalOptions = append(finalOptions, llms.WithTools(refinedTools))
	}

	// Diagnostic Log
	msgJSON, _ := json.Marshal(cleanMessages)
	logs.FInfo("Native Gemini Request Messages: %s", string(msgJSON))

	resp, err := m.llm.GenerateContent(ctx, cleanMessages, finalOptions...)
	if err != nil {
		return nil, err
	}

	// 3. Bridge Response
	if len(resp.Choices) > 0 {
		choice := resp.Choices[0]
		if choice.GenerationInfo == nil {
			choice.GenerationInfo = make(map[string]interface{})
		}
		choice.GenerationInfo["model"] = m.model

		if len(choice.ToolCalls) > 0 {
			choice.GenerationInfo["tool_calls"] = choice.ToolCalls
		}

		// Map Usage: Handle Gemini 2.5/3.0 'usageMetadata' and older 'usage' formats
		var it, ot, tt int
		
		// Priority 1: usageMetadata (Gemini 2.5/3.0 native structure)
		if umObj, ok := choice.GenerationInfo["usageMetadata"]; ok {
			if um, ok := umObj.(map[string]interface{}); ok {
				it = utils.ParseUsageInt(um["promptTokenCount"])
				
				// Sum candidates and thoughts for total output
				cand := utils.ParseUsageInt(um["candidatesTokenCount"])
				thought := utils.ParseUsageInt(um["thoughtsTokenCount"])
				ot = cand + thought
				
				tt = utils.ParseUsageInt(um["totalTokenCount"])
				if tt == 0 { tt = it + ot }
			}
		}

		// Priority 2: Fallback to 'usage' if metadata was missing or incomplete
		if it == 0 && ot == 0 {
			if uObj, ok := choice.GenerationInfo["usage"]; ok {
				if u, ok := uObj.(map[string]interface{}); ok {
					it = utils.ParseUsageInt(u["PromptTokens"])
					if it == 0 { it = utils.ParseUsageInt(u["prompt_token_count"]) }
					
					ot = utils.ParseUsageInt(u["CandidatesTokens"])
					if ot == 0 { ot = utils.ParseUsageInt(u["candidates_token_count"]) }
					if ot == 0 { ot = utils.ParseUsageInt(u["CompletionTokens"]) }
					
					tt = utils.ParseUsageInt(u["TotalTokens"])
				}
			}
		}

		if it > 0 || ot > 0 {
			if tt == 0 { tt = it + ot }
			choice.GenerationInfo["usage"] = map[string]interface{}{
				"input_tokens":  it,
				"output_tokens": ot,
				"total_tokens":  tt,
			}
			logs.FInfo("Gemini Usage Captured: Input=%d, Output=%d (including thoughts)", it, ot)
		} else {
			// Diagnostic Log: help identify future structure changes
			genInfoJSON, _ := json.Marshal(choice.GenerationInfo)
			logs.FInfo("Gemini Usage Missing: %s", string(genInfoJSON))
		}
	}

	return resp, nil
}

func (m *GeminiAdapter) Call(ctx context.Context, prompt string, options ...llms.CallOption) (string, error) {
	return llms.GenerateFromSinglePrompt(ctx, m, prompt, options...)
}
