package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/app/util"
	"context"
	"encoding/json"
	"fmt"
	"html"
	"net/http"
	"regexp"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/tmc/langchaingo/llms"
)

type AssistantHistoryMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type AssistantChatInput struct {
	SessionID string                    `json:"session"`
	Message   string                    `json:"message" binding:"required"`
	History   []AssistantHistoryMessage `json:"history"`
}

// ChatWithDashboardAgent provides a fixed-tool agent endpoint for the Taipei dashboard assistant.
func ChatWithDashboardAgent(c *gin.Context) {
	var input AssistantChatInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":     "error",
			"error_code": "INVALID_REQUEST",
			"message":    err.Error(),
		})
		return
	}

	message := strings.TrimSpace(input.Message)
	if message == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":     "error",
			"error_code": "INVALID_REQUEST",
			"message":    "message is required",
		})
		return
	}

	sessionID := strings.TrimSpace(input.SessionID)
	if sessionID == "" {
		sessionID = "session_" + util.GenerateRandomString(10)
	}
	sessionID = html.EscapeString(sessionID)

	_, accountID, _, _, _ := util.GetUserInfoFromContext(c)
	userID := "guest"
	if accountID > 0 {
		userID = fmt.Sprintf("%d", accountID)
	}

	references, ragContext := getReferencesForUserQuery(message)
	messages := buildAssistantMessages(input.History, message, ragContext)

	req := ai.AIChatRequest{
		SessionID: sessionID,
		UserID:    userID,
		IPAddress: c.ClientIP(),
		Messages:  messages,
	}

	options := []llms.CallOption{
		llms.WithTools(buildAgentTools()),
		llms.WithToolChoice("auto"),
	}

	logEntry, err := ai.ChatWithTWCC(c.Request.Context(), req, options...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":     "error",
			"error_code": "AI_SERVICE_ERROR",
			"message":    err.Error(),
		})
		return
	}

	rankedReferences := rerankReferencesByLLM(c.Request.Context(), message, references)
	if len(rankedReferences) > 0 {
		references = rankedReferences
	}

	alignedReferences := alignReferencesWithAnswer(logEntry.Answer, references)
	if len(alignedReferences) > 0 {
		references = alignedReferences
	}

	finalAnswer := synchronizeAnswerWithReferences(logEntry.Answer, references)

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"data": gin.H{
			"session": sessionID,
			"content": finalAnswer,
			"usage": gin.H{
				"input_tokens":  logEntry.InputTokens,
				"output_tokens": logEntry.OutputTokens,
				"total_tokens":  logEntry.TotalTokens,
			},
			"tool_used":  logEntry.ToolUsed,
			"latency_ms": logEntry.LatencyMS,
			"model":      logEntry.Model,
			"provider":   logEntry.Provider,
			"references": references,
		},
	})
}

type llmRankItem struct {
	ID    int64   `json:"id"`
	City  string  `json:"city"`
	Rank  int     `json:"rank"`
	Score float64 `json:"score"`
}

func rerankReferencesByLLM(ctx context.Context, userQuery string, references []models.CityComponentScore) []models.CityComponentScore {
	if len(references) == 0 {
		return references
	}

	candidatesJSON, err := json.Marshal(references)
	if err != nil {
		return references
	}

	messages := []llms.MessageContent{
		{
			Role: llms.ChatMessageTypeSystem,
			Parts: []llms.ContentPart{llms.TextContent{Text: `你是排序器。請根據使用者問題與候選組件，回傳 JSON 陣列。
規則：
1) 只能輸出 JSON 陣列，不要任何多餘文字。
2) 每個元素格式：{"id":數字,"city":"taipei|metrotaipei","rank":數字,"score":0~1}。
3) 僅可使用候選組件中存在的 id 與 city。
4) rank 必須由小到大連續。`}},
		},
		{
			Role: llms.ChatMessageTypeHuman,
			Parts: []llms.ContentPart{llms.TextContent{Text: fmt.Sprintf("使用者問題：%s\n候選組件：%s", userQuery, string(candidatesJSON))}},
		},
	}

	req := ai.AIChatRequest{
		SessionID: "rerank_" + util.GenerateRandomString(8),
		UserID:    "system",
		IPAddress: "127.0.0.1",
		Messages:  messages,
	}

	logEntry, err := ai.ChatWithTWCC(ctx, req)
	if err != nil || strings.TrimSpace(logEntry.Answer) == "" {
		return references
	}

	ranked, ok := parseLLMRankAnswer(logEntry.Answer)
	if !ok {
		return references
	}

	ordered := mergeRankedReferences(references, ranked)
	if len(ordered) == 0 {
		return references
	}

	return ordered
}

func parseLLMRankAnswer(answer string) ([]llmRankItem, bool) {
	normalized := strings.TrimSpace(answer)
	start := strings.Index(normalized, "[")
	end := strings.LastIndex(normalized, "]")
	if start >= 0 && end > start {
		normalized = normalized[start : end+1]
	}

	var ranked []llmRankItem
	if err := json.Unmarshal([]byte(normalized), &ranked); err != nil || len(ranked) == 0 {
		return nil, false
	}

	return ranked, true
}

func mergeRankedReferences(references []models.CityComponentScore, ranked []llmRankItem) []models.CityComponentScore {
	refMap := make(map[string]models.CityComponentScore, len(references))
	for _, ref := range references {
		key := fmt.Sprintf("%d|%s", ref.ID, strings.ToLower(strings.TrimSpace(ref.City)))
		refMap[key] = ref
	}

	ordered := make([]models.CityComponentScore, 0, len(ranked))
	for _, item := range ranked {
		key := fmt.Sprintf("%d|%s", item.ID, strings.ToLower(strings.TrimSpace(item.City)))
		if ref, ok := refMap[key]; ok {
			if item.Score > 0 && item.Score <= 1 {
				ref.Score = item.Score
			}
			ordered = append(ordered, ref)
			delete(refMap, key)
		}
	}

	if len(ordered) == 0 {
		return nil
	}

	return ordered
}

func alignReferencesWithAnswer(answer string, references []models.CityComponentScore) []models.CityComponentScore {
	trimmed := strings.TrimSpace(answer)
	if trimmed == "" || len(references) == 0 {
		return nil
	}

	nameOrder := extractAnswerNameOrder(trimmed)
	if len(nameOrder) == 0 {
		return nil
	}

	nameMap, exactNameMap := buildReferenceNameMaps(references)

	aligned := make([]models.CityComponentScore, 0, len(nameOrder))
	seen := make(map[string]bool, len(nameOrder))
	for _, name := range nameOrder {
		ref, normalized, ok := resolveReferenceForAnswerName(name, nameMap, exactNameMap, seen)
		if ok {
			aligned = append(aligned, ref)
			seen[normalized] = true
		}
	}

	if len(aligned) == 0 {
		return nil
	}

	return aligned
}

func synchronizeAnswerWithReferences(answer string, references []models.CityComponentScore) string {
	trimmed := strings.TrimSpace(answer)
	if trimmed == "" || len(references) == 0 {
		return answer
	}

	linePattern := regexp.MustCompile(`^\s*\d+\.\s*.+\s*$`)
	lines := strings.Split(answer, "\n")
	listLines := buildNumberedListLines(references)
	if len(listLines) == 0 {
		return answer
	}

	out := make([]string, 0, len(lines))
	inserted := false
	for _, line := range lines {
		if linePattern.MatchString(strings.TrimSpace(line)) {
			if !inserted {
				out = append(out, listLines...)
				inserted = true
			}
			continue
		}
		out = append(out, line)
	}

	if !inserted {
		return answer
	}

	joined := strings.Join(out, "\n")
	joined = strings.ReplaceAll(joined, "\n\n\n", "\n\n")
	return strings.TrimSpace(joined)
}

func buildNumberedListLines(references []models.CityComponentScore) []string {
	list := make([]string, 0, len(references))
	for i, ref := range references {
		name := strings.TrimSpace(ref.Name)
		if name == "" {
			continue
		}
		list = append(list, fmt.Sprintf("%d. %s", i+1, name))
	}

	return list
}

func extractAnswerNameOrder(answer string) []string {
	linePattern := regexp.MustCompile(`(?m)^\s*\d+\.\s*(.+?)\s*$`)
	matches := linePattern.FindAllStringSubmatch(answer, -1)
	if len(matches) == 0 {
		return nil
	}

	nameOrder := make([]string, 0, len(matches))
	for _, m := range matches {
		if len(m) < 2 {
			continue
		}

		name := strings.TrimSpace(m[1])
		if name != "" {
			nameOrder = append(nameOrder, name)
		}
	}

	return nameOrder
}

func buildReferenceNameMaps(references []models.CityComponentScore) (map[string]models.CityComponentScore, map[string]models.CityComponentScore) {
	nameMap := make(map[string]models.CityComponentScore, len(references))
	exactNameMap := make(map[string]models.CityComponentScore, len(references))

	for _, ref := range references {
		normalized := normalizeComponentName(ref.Name)
		if normalized != "" {
			nameMap[normalized] = ref
		}
		exactNameMap[strings.TrimSpace(ref.Name)] = ref
	}

	return nameMap, exactNameMap
}

func resolveReferenceForAnswerName(name string, nameMap map[string]models.CityComponentScore, exactNameMap map[string]models.CityComponentScore, seen map[string]bool) (models.CityComponentScore, string, bool) {
	normalized := normalizeComponentName(name)
	if normalized == "" || seen[normalized] {
		return models.CityComponentScore{}, normalized, false
	}

	if ref, ok := nameMap[normalized]; ok {
		return ref, normalized, true
	}

	if ref, ok := exactNameMap[strings.TrimSpace(name)]; ok {
		return ref, normalized, true
	}

	return models.CityComponentScore{}, normalized, false
}

func normalizeComponentName(name string) string {
	normalized := strings.TrimSpace(name)
	if normalized == "" {
		return ""
	}

	replacer := strings.NewReplacer(
		" ", "",
		"　", "",
		"（", "(",
		"）", ")",
		"：", ":",
		"，", ",",
		"。", "",
		"；", ";",
	)
	return strings.ToLower(replacer.Replace(normalized))
}

func buildAssistantMessages(history []AssistantHistoryMessage, latestUserMessage string, ragContext string) []llms.MessageContent {
	messages := []llms.MessageContent{{
		Role: llms.ChatMessageTypeSystem,
		Parts: []llms.ContentPart{llms.TextContent{Text: `你是「臺北城市儀表板小幫手 Agent」。
任務：
1) 先理解使用者需求，再使用工具取得事實資料。
2) 回答時必須以繁體中文。
3) 優先給出可執行建議，例如應建立哪些儀表板組件。
4) 若資料不足，明確說明缺口並提出下一步提問。
5) 禁止臆測不存在的指標或資料來源。
6) 你會收到一段 RAG 檢索上下文，請優先依據這份上下文整合成一次完整回答，而不是只列原始結果。
7) 回覆內容請以摘要與建議為主，不要輸出 Markdown 表格。`}},
	}}

	if ragContext != "" {
		messages = append(messages, llms.MessageContent{
			Role: llms.ChatMessageTypeSystem,
			Parts: []llms.ContentPart{llms.TextContent{Text: "RAG_CONTEXT:\n" + ragContext}},
		})
	}

	if len(history) > 12 {
		history = history[len(history)-12:]
	}

	for _, item := range history {
		content := strings.TrimSpace(item.Content)
		if content == "" {
			continue
		}

		msgRole := llms.ChatMessageTypeHuman
		switch item.Role {
		case "assistant", "bot":
			msgRole = llms.ChatMessageTypeAI
		case "system":
			msgRole = llms.ChatMessageTypeSystem
		default:
			msgRole = llms.ChatMessageTypeHuman
		}

		messages = append(messages, llms.MessageContent{
			Role:  msgRole,
			Parts: []llms.ContentPart{llms.TextContent{Text: content}},
		})
	}

	messages = append(messages, llms.MessageContent{
		Role:  llms.ChatMessageTypeHuman,
		Parts: []llms.ContentPart{llms.TextContent{Text: latestUserMessage}},
	})

	return messages
}

func buildAgentTools() []llms.Tool {
	return []llms.Tool{
		{
			Type: "function",
			Function: &llms.FunctionDefinition{
				Name:        "search_dashboard_components",
				Description: "以語意檢索臺北城市儀表板組件，回傳與查詢最相關的組件與摘要。",
				Parameters: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"query": map[string]interface{}{
							"type":        "string",
							"description": "使用者查詢內容",
						},
						"limit": map[string]interface{}{
							"type":        "integer",
							"description": "回傳最多筆數，建議 5-10",
						},
						"score_threshold": map[string]interface{}{
							"type":        "number",
							"description": "相似度門檻，0-1",
						},
						"city": map[string]interface{}{
							"type":        "string",
							"description": "城市篩選，可用 taipei 或 metrotaipei",
						},
					},
					"required": []string{"query"},
				},
			},
		},
		{
			Type: "function",
			Function: &llms.FunctionDefinition{
				Name:        "get_component_detail",
				Description: "取得單一組件的詳細資訊（說明、來源、更新頻率等）。",
				Parameters: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"id": map[string]interface{}{
							"type":        "integer",
							"description": "組件 ID",
						},
						"city": map[string]interface{}{
							"type":        "string",
							"description": "城市，taipei 或 metrotaipei",
						},
					},
					"required": []string{"id", "city"},
				},
			},
		},
		{
			Type: "function",
			Function: &llms.FunctionDefinition{
				Name:        "get_population_summary",
				Description: "查詢人口年齡結構摘要。",
				Parameters: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"city": map[string]interface{}{"type": "string"},
						"year": map[string]interface{}{"type": "integer"},
					},
					"required": []string{"city", "year"},
				},
			},
		},
		{
			Type: "function",
			Function: &llms.FunctionDefinition{
				Name:        "get_current_time",
				Description: "取得目前臺北時間。",
				Parameters: map[string]interface{}{
					"type":       "object",
					"properties": map[string]interface{}{},
				},
			},
		},
	}
}

func getReferencesForUserQuery(query string) ([]models.CityComponentScore, string) {
	references, err := models.GetComponentByQueryVector(query, 8, 0.72)
	if err != nil {
		return []models.CityComponentScore{}, ""
	}

	type ragCandidate struct {
		ID          int64   `json:"id"`
		Index       string  `json:"index"`
		Name        string  `json:"name"`
		City        string  `json:"city"`
		Score       float64 `json:"score"`
		ShortDesc   string  `json:"short_desc,omitempty"`
		LongDesc    string  `json:"long_desc,omitempty"`
		UseCase     string  `json:"use_case,omitempty"`
		Source      string  `json:"source,omitempty"`
		UpdateFreq  *int64  `json:"update_freq,omitempty"`
		UpdateUnit  string  `json:"update_freq_unit,omitempty"`
	}

	candidates := make([]ragCandidate, 0, len(references))
	for _, ref := range references {
		candidate := ragCandidate{
			ID:    ref.ID,
			Index: ref.Index,
			Name:  ref.Name,
			City:  ref.City,
			Score: ref.Score,
		}

		detail, detailErr := models.GetComponentByID(int(ref.ID), ref.City)
		if detailErr == nil {
			candidate.ShortDesc = detail.ShortDesc
			candidate.LongDesc = detail.LongDesc
			candidate.UseCase = detail.UseCase
			candidate.Source = detail.Source
			candidate.UpdateFreq = detail.UpdateFreq
			candidate.UpdateUnit = detail.UpdateFreqUnit
		}

		candidates = append(candidates, candidate)
	}

	ragJSON, marshalErr := json.Marshal(map[string]interface{}{
		"query":      query,
		"candidates": candidates,
	})
	if marshalErr != nil {
		return references, ""
	}

	return references, string(ragJSON)
}
