package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services"
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"
	"context"
	"fmt"
	"html"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/tmc/langchaingo/llms"
)

// AIChatInput matches the Request Schema in specification。https://docs.twcloud.ai/docs/user-guides/twcc/afs/api-and-parameters/api-parameter-information#模型說明
type AIChatInput struct {
	SessionID string `json:"session"`
	Stream    bool   `json:"stream"`
	Messages  []struct {
		Role      string `json:"role" binding:"required,oneof=system user assistant tool"`
		Content   string `json:"content" binding:"required"`
		ToolCalls []struct {
			ID       string `json:"id"`
			Type     string `json:"type"`
			Function struct {
				Name      string `json:"name"`
				Arguments string `json:"arguments"`
			} `json:"function"`
		} `json:"tool_calls,omitempty"`
		ToolCallID string `json:"tool_call_id,omitempty"`
	} `json:"messages" binding:"required,gt=0"`
	MaxNewTokens     *int      `json:"max_new_tokens" binding:"omitempty,gt=0"`
	Temperature      *float64  `json:"temperature" binding:"omitempty,gt=0"`
	TopP             *float64  `json:"top_p" binding:"omitempty,gt=0,lte=1"`
	TopK             *int      `json:"top_k" binding:"omitempty,gte=1,lte=100"`
	FrequencePenalty *float64  `json:"frequence_penalty" binding:"omitempty,gt=0"`
	StopSequences    []string  `json:"stop_sequences" binding:"omitempty,max=4"`
	Seed             *int      `json:"seed" binding:"omitempty,gte=0"`
	Tools            []struct {
		Type     string `json:"type" binding:"required,eq=function"`
		Function struct {
			Name        string      `json:"name" binding:"required"`
			Description string      `json:"description,omitempty"`
			Parameters  interface{} `json:"parameters,omitempty"`
		} `json:"function" binding:"required"`
	} `json:"tools,omitempty"`
	ToolChoice interface{} `json:"tool_choice,omitempty"`
}

type ExtractInsightInput struct {
	Url string `json:"url"`
}

// ChatWithTWCC is the controller for POST /api/v1/ai/chat/twai
func ChatWithTWCC(c *gin.Context) {
	var input AIChatInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status": "error",
			"error_code": "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	// 1. Session ID Management
	sessionID := input.SessionID
	if sessionID == "" {
		sessionID = "session_" + util.GenerateRandomString(10)
	}
	sessionID = html.EscapeString(sessionID)

	// 2. Prepare AI Request
	_, accountID, _, _, _ := util.GetUserInfoFromContext(c)
	req := ai.AIChatRequest{
		SessionID: sessionID,
		UserID:    fmt.Sprintf("%d", accountID),
		IPAddress: c.ClientIP(),
		Messages:  input.ToServiceMessages(),
	}

	// 3. Prepare Dynamic Options
	options := input.ToCallOptions()

	// 4. Handle Streaming Response
	if input.Stream {
		c.Header("Content-Type", "text/event-stream")
		c.Header("Cache-Control", "no-cache")
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("Connection", "keep-alive")

		// Add Streaming Callback
		options = append(options, llms.WithStreamingFunc(func(ctx context.Context, chunk []byte) error {
			if string(chunk) == ": heartbeat\n\n" {
				return nil
			}
			_, err := c.Writer.Write(chunk)
			if err != nil {
				return err
			}
			c.Writer.Flush()
			return nil
		}))

		_, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
		if err != nil {
			if !c.Writer.Written() {
				c.JSON(http.StatusInternalServerError, gin.H{
					"status": "error",
					"error_code": "AI_SERVICE_STREAM_ERROR",
					"message": err.Error(),
				})
			}
		}
		return
	}

	// 5. Standard Non-Streaming Response
	logEntry, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error_code": "AI_SERVICE_ERROR",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"session":     logEntry.SessionID,
			"content":     logEntry.Answer,
			"usage": gin.H{
				"input_tokens":  logEntry.InputTokens,
				"output_tokens": logEntry.OutputTokens,
				"total_tokens":  logEntry.TotalTokens,
			},
			"tool_used":   logEntry.ToolUsed,
			"latency_ms":  logEntry.LatencyMS,
			"model":       logEntry.Model,
			"provider":    logEntry.Provider,
		},
	})
}

// ToServiceMessages converts input messages to langchaingo internal format
func (input *AIChatInput) ToServiceMessages() []llms.MessageContent {
	serviceMsgs := make([]llms.MessageContent, 0)
	for _, m := range input.Messages {
		role := llms.ChatMessageTypeHuman
		var parts []llms.ContentPart
		parts = append(parts, llms.TextContent{Text: m.Content})

		switch m.Role {
		case "assistant":
			role = llms.ChatMessageTypeAI
			if len(m.ToolCalls) > 0 {
				for _, tc := range m.ToolCalls {
					parts = append(parts, llms.ToolCall{
						ID:   tc.ID,
						Type: tc.Type,
						FunctionCall: &llms.FunctionCall{
							Name:      tc.Function.Name,
							Arguments: tc.Function.Arguments,
						},
					})
				}
			}
		case "system":
			role = llms.ChatMessageTypeSystem
		case "tool":
			role = llms.ChatMessageTypeTool
			parts = []llms.ContentPart{llms.ToolCallResponse{
				ToolCallID: m.ToolCallID,
				Content:    m.Content,
			}}
		}

		serviceMsgs = append(serviceMsgs, llms.MessageContent{
			Role:  role,
			Parts: parts,
		})
	}
	return serviceMsgs
}

// ToCallOptions extracts and maps AI generation options and tools
func (input *AIChatInput) ToCallOptions() []llms.CallOption {
	options := make([]llms.CallOption, 0)
	params := make(map[string]interface{})

	// Map numerical parameters
	if input.MaxNewTokens != nil {
		options = append(options, llms.WithMaxTokens(*input.MaxNewTokens))
		params["max_new_tokens"] = *input.MaxNewTokens
	}
	if input.Temperature != nil {
		options = append(options, llms.WithTemperature(*input.Temperature))
		params["temperature"] = *input.Temperature
	}
	if input.TopP != nil {
		options = append(options, llms.WithTopP(*input.TopP))
		params["top_p"] = *input.TopP
	}
	if input.TopK != nil {
		options = append(options, llms.WithTopK(*input.TopK))
		params["top_k"] = *input.TopK
	}
	if input.FrequencePenalty != nil {
		options = append(options, llms.WithRepetitionPenalty(*input.FrequencePenalty))
		params["frequence_penalty"] = *input.FrequencePenalty
	}
	if len(input.StopSequences) > 0 {
		options = append(options, llms.WithStopWords(input.StopSequences))
		params["stop_sequences"] = input.StopSequences
	}
	if input.Seed != nil {
		params["seed"] = *input.Seed
	}

	// Map Tools
	if len(input.Tools) > 0 {
		lt := make([]llms.Tool, 0)
		for _, t := range input.Tools {
			lt = append(lt, llms.Tool{
				Type: t.Type,
				Function: &llms.FunctionDefinition{
					Name:        t.Function.Name,
					Description: t.Function.Description,
					Parameters:  t.Function.Parameters,
				},
			})
		}
		options = append(options, llms.WithTools(lt))
		if input.ToolChoice != nil {
			options = append(options, llms.WithToolChoice(input.ToolChoice))
		}
	}

	if len(params) > 0 {
		options = append(options, llms.WithMetadata(params))
	}

	return options
}

func GetComponemtByNews(c *gin.Context){

	var req ExtractInsightInput

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	body := services.GetHTMLBody(req.Url)

	body = strings.ReplaceAll(body, "\n\n", "\n")
	body = strings.ReplaceAll(body, "\t\t", "\t")
	body = strings.ReplaceAll(body, "     ", " ")

	reqAIChatRequest := ai.AIChatRequest{
		SessionID: "",
		UserID:    "",
		IPAddress: "",
		Messages: []llms.MessageContent{
			{
				Role: llms.ChatMessageTypeSystem,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: "輸入：一段來自某新聞網站的 HTML 結構碼。\n目標：擷取主標題與正文全文。\n請嚴格依下列字面格式輸出（第一行行首文字須與示例一致）：\n新聞主標題：<一行標題>\n\n【正文開始】\n（此處接完整正文）\n【正文結束】\n\n注意：\n1. 標題／正文請保留來源語言（原文外文亦可），勿整篇譯為中文。\n2. 正文務必完整、不可摘要。\n3. 只輸出以上區塊，不要前言／後語／思考過程。\n"},
				},
			},
			{
				Role: llms.ChatMessageTypeHuman,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: body},
				},
			},
		},
	}
		// 1. 直接建構 options slice
	opts := []llms.CallOption{
		llms.WithTemperature(0.7),
		llms.WithTopP(0.9),
		llms.WithTopK(40),
		llms.WithRepetitionPenalty(1.1),
		llms.WithSeed(42),

		llms.WithMetadata(map[string]any{
			"source": "manual",
			"env":    "dev",
		}),
	}

	ctx := context.Background()
	logEntry, err := ai.ChatWithTWCC(ctx, reqAIChatRequest, opts...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status": "error",
			"error_code": "AI_SERVICE_ERROR",
			"message": err.Error(),
		})
		return
	}

	// --- 以下為新增的配對與故事線邏輯 ---
	newsContent := logEntry.Answer

	// 1. 提取新聞標題 (優先尋找包含「新聞主標題」的行)
	newsTitle := ""
	lines := strings.Split(newsContent, "\n")
	titlePrefixes := []string{
		"新聞主標題：", "新聞主標題:", "[新聞主標題]：", "[新聞主標題]:",
		"標題：", "標題:",
		"Title:", "TITLE:", "Headline:",
	}
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		found := ""
		for _, pre := range titlePrefixes {
			if strings.HasPrefix(trimmed, pre) {
				found = strings.TrimSpace(strings.TrimPrefix(trimmed, pre))
				break
			}
		}
		if found != "" && found != trimmed {
			newsTitle = found
			break
		}
	}
	// 舊格式或模型未嚴守前綴時之後備
	if newsTitle == "" {
		for _, line := range lines {
			t := strings.TrimSpace(line)
			if !strings.Contains(t, "新聞主標題") {
				continue
			}
			tmp := strings.ReplaceAll(t, "[新聞主標題]：", "")
			tmp = strings.ReplaceAll(tmp, "[新聞主標題]:", "")
			tmp = strings.ReplaceAll(tmp, "新聞主標題：", "")
			tmp = strings.ReplaceAll(tmp, "新聞主標題:", "")
			tmp = strings.TrimSpace(tmp)
			if tmp != "" && tmp != t {
				newsTitle = tmp
				break
			}
		}
	}
	if newsTitle == "" && len(lines) > 0 {
		for _, l := range lines {
			if strings.TrimSpace(l) != "" { newsTitle = l; break }
		}
	}

	// 2. 執行 HyDE (Hypothetical Document Embeddings)
	hydeReq := ai.AIChatRequest{
		Messages: []llms.MessageContent{
			{
				Role: llms.ChatMessageTypeSystem,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: "你是一位數據儀表板架構師。請根據提供的新聞標題與內容，想像一個『最能提供相關數據背景』的儀表板組件。\n新聞可為任一語種；請你自行理解議題。\n請只輸出一小段（恰好兩個完整句子）的功能描述：說明此組件涵蓋哪些指標／維度，且必須全部使用「繁體中文」書寫，以便與同為繁中文案的儀表板組件做語意對照。\n不要前言、小標題、引號以外的包裝。"},
				},
			},
			{
				Role: llms.ChatMessageTypeHuman,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: fmt.Sprintf("新聞標題:\n%s\n\n新聞內容（可能為外文，請據此作答）:\n%s", newsTitle, newsContent)},
				},
			},
		},
	}
	hydeLog, _ := ai.ChatWithTWCC(ctx, hydeReq, llms.WithTemperature(0.5))
	queryText := newsTitle
	if hydeLog != nil && hydeLog.Answer != "" {
		queryText = hydeLog.Answer
		fmt.Printf("[DEBUG] HyDE Hypothetical Doc: %s\n", queryText)
	}

	// 3. 向量檢索與詳細資訊抓取 (門檻 0.15)
	searchRes, _ := models.GetComponentByQueryVector(queryText, 3, 0.15)
	detailedComponents := make([]models.CityComponent, 0)
	componentSummaries := make([]string, 0)
	for _, res := range searchRes {
		comps, err := models.GetComponentByIDAll(int(res.ID))
		if err == nil && len(comps) > 0 {
			comp := comps[0]
			lang, _ := c.Get("lang")
			targetLang := "zh-TW"
			if lang != nil { targetLang = lang.(string) }
			if global.GlobalTranslator != nil && targetLang != "zh-TW" {
				comp.Name = global.GlobalTranslator.Translate(ctx, comp.Name, targetLang, "component_name")
				comp.ShortDesc = global.GlobalTranslator.Translate(ctx, comp.ShortDesc, targetLang, "short_desc")
				comp.UseCase = global.GlobalTranslator.Translate(ctx, comp.UseCase, targetLang, "use_case")
				comp.ChartConfig = global.GlobalTranslator.TranslateJSON(ctx, comp.ChartConfig, targetLang, "chart_config")
				comp.MapConfig = global.GlobalTranslator.TranslateJSON(ctx, comp.MapConfig, targetLang, "map_config")
			}
			detailedComponents = append(detailedComponents, comp)
			componentSummaries = append(componentSummaries, fmt.Sprintf("- %s: %s", comp.Name, comp.ShortDesc))
		}
	}

	// 4. 調用 LLM 串起故事線 (Storyline) - 無論如何都要生成
	storylineReq := ai.AIChatRequest{
		Messages: []llms.MessageContent{
			{
				Role: llms.ChatMessageTypeSystem,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: "你是一位資深城市數據分析師。請根據提供的新聞內容撰寫一段數據洞察敘事（Storyline）。\n1. 如果有推薦組件，請解釋這些數據如何幫助讀者理解新聞背後的社會脈絡。\n2. 如果沒有高度相關組件，請根據新聞內容分析其對城市發展的潛在數據趨勢影響。直接輸出結果，不需前言。"},
				},
			},
			{
				Role: llms.ChatMessageTypeHuman,
				Parts: []llms.ContentPart{
					llms.TextContent{Text: fmt.Sprintf("【新聞內容】\n%s\n\n【推薦組件摘要】\n%s", newsContent, strings.Join(componentSummaries, "\n"))},
				},
			},
		},
	}
	storyLog, err := ai.ChatWithTWCC(ctx, storylineReq, llms.WithTemperature(0.7))
	storyline := "針對此新聞，系統目前未發現直接關聯的數據。"
	if err == nil {
		storyline = storyLog.Answer
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"session":     logEntry.SessionID,
			"content":     logEntry.Answer,
			"storyline":   storyline,
			"components":  detailedComponents,
			"usage": gin.H{
				"input_tokens":  logEntry.InputTokens,
				"output_tokens": logEntry.OutputTokens,
				"total_tokens":  logEntry.TotalTokens,
			},
			"tool_used":   logEntry.ToolUsed,
			"latency_ms":  logEntry.LatencyMS,
			"model":       logEntry.Model,
			"provider":    logEntry.Provider,
		},
	})
	}