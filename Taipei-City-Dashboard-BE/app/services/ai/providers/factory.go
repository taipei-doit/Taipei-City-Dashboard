package providers

import (
	"TaipeiCityDashboardBE/app/services/ai/providers/gemini"
	"TaipeiCityDashboardBE/app/services/ai/providers/openai"
	"TaipeiCityDashboardBE/app/services/ai/providers/twcc"
	"TaipeiCityDashboardBE/global"
	"context"
	"fmt"
	"github.com/tmc/langchaingo/llms"
	"TaipeiCityDashboardBE/logs"
)

// GetModel returns the appropriate llms.Model based on the provider name.
// It returns nil and an error if the provider is not configured.
func GetModel(provider string) (llms.Model, error) {
	ctx := context.Background()
	logs.FInfo("Initializing AI Model (Provider: %s, MaxConcurrent: %d)", provider, global.AI.MaxConcurrent)

	switch provider {
	case "openai":
		if global.OpenAI.ApiKey == "" {
			return nil, fmt.Errorf("OpenAI API key is not configured")
		}
		logs.FInfo("OpenAI Config: URL=%s, Model=%s", global.OpenAI.ApiUrl, global.OpenAI.Model)
		m, err := openai.New(global.OpenAI.ApiKey, global.OpenAI.ApiUrl, global.OpenAI.Model)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize OpenAI provider: %v", err)
		}
		return m, nil

	case "gemini":
		if global.Gemini.ApiKey == "" {
			return nil, fmt.Errorf("Gemini API key is not configured")
		}
		logs.FInfo("Gemini Config: URL=%s, Model=%s", global.Gemini.ApiUrl, global.Gemini.Model)
		m, err := gemini.New(ctx, global.Gemini.ApiKey, global.Gemini.ApiUrl, global.Gemini.Model)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize Gemini provider: %v", err)
		}
		return m, nil

	case "twcc":
		if global.TWCC.ApiKey == "" || global.TWCC.ApiKey == "default_your_twcc_api_key_here" {
			return nil, fmt.Errorf("TWCC API key is not configured")
		}
		logs.FInfo("TWCC Config: URL=%s, Model=%s", global.TWCC.ApiUrl, global.TWCC.Model)
		return twcc.New(
			global.TWCC.ApiKey,
			global.TWCC.ApiUrl,
			global.TWCC.Model,
			global.AI.Timeout,
		), nil

	default:
		return nil, fmt.Errorf("unknown provider: %s", provider)
	}
}
