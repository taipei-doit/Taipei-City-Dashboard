package services

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/ai"
	"TaipeiCityDashboardBE/logs"
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"unicode/utf8"

	"github.com/tmc/langchaingo/llms"
)

const (
	rssLLMCandidateStoryLimit      = 24
	rssLLMComponentsInPromptCap    = 150
	rssLLMMaxNewsSummaryRunes      = 280
	rssLLMMaxComponentDescRunes     = 140
	rssLLMRecommendOutputCap      = 3
	rssLLMMatchesJSONMaxNewTokens = 4096
)

type llmRSSMatchEntry struct {
	NewsIndex   int   `json:"news_index"`
	Related     bool  `json:"related"`
	ComponentID int64 `json:"component_id"`
}

type llmRSSMatchFile struct {
	Matches []llmRSSMatchEntry `json:"matches"`
}

type rssStoryWithComponent struct {
	story rssStory
	comp  models.PublicComponentForNewsMatch
}

func truncateRunesHard(s string, max int) string {
	if utf8.RuneCountInString(s) <= max {
		return s
	}
	rs := []rune(s)
	if len(rs) <= max {
		return s
	}
	return string(rs[:max]) + "…"
}

func unwrapLLMAnswerJSON(answer string) string {
	s := strings.TrimSpace(answer)
	s = strings.TrimPrefix(s, "```json")
	s = strings.TrimPrefix(s, "```JSON")
	s = strings.TrimPrefix(s, "```")
	s = strings.TrimSpace(s)
	if i := strings.LastIndex(s, "```"); i >= 0 {
		s = strings.TrimSpace(s[:i])
	}
	return strings.TrimSpace(s)
}

func selectRSSStoriesForLLM(stories []rssStory) []rssStory {
	n := rssLLMCandidateStoryLimit
	if len(stories) < n {
		n = len(stories)
	}
	return stories[:n]
}

func selectComponentsForRSSPrompt(comps []models.PublicComponentForNewsMatch) []models.PublicComponentForNewsMatch {
	if len(comps) <= rssLLMComponentsInPromptCap {
		return comps
	}
	logs.FWarn("RSS LLM：公開組件共 %d 筆，提示僅納入前 %d 筆", len(comps), rssLLMComponentsInPromptCap)
	return comps[:rssLLMComponentsInPromptCap]
}

func buildRSSLLMNewsBlock(indices []rssStory) string {
	var b strings.Builder
	for i := range indices {
		s := indices[i]
		b.WriteString(fmt.Sprintf("[#%d] 標題：%s\n摘要：%s\n\n",
			i, strings.TrimSpace(s.title), truncateRunesHard(strings.TrimSpace(s.description), rssLLMMaxNewsSummaryRunes)))
	}
	return b.String()
}

func buildRSSLLMComponentCatalog(comps []models.PublicComponentForNewsMatch) string {
	var b strings.Builder
	for _, c := range comps {
		b.WriteString(fmt.Sprintf("id:%d\tindex:%s\tcity:%s\tname:%s\tdesc:%s\n",
			c.ID,
			strings.TrimSpace(c.Index),
			strings.TrimSpace(c.City),
			strings.TrimSpace(c.Name),
			truncateRunesHard(strings.TrimSpace(c.ShortDesc), rssLLMMaxComponentDescRunes)))
	}
	return b.String()
}

func parseRSSLLMMatchJSON(answer string) (*llmRSSMatchFile, error) {
	raw := unwrapLLMAnswerJSON(answer)
	var f llmRSSMatchFile
	if err := json.Unmarshal([]byte(raw), &f); err != nil {
		return nil, fmt.Errorf("%w（前 240 字：%s）", err, truncateRunesHard(raw, 240))
	}
	return &f, nil
}

// matchRSSStoriesToComponentsViaLLM 呼叫系統設定之 TWCC 模型；僅將 related==true 且 component_id 在清單內的新聞納入結果，至多 maxOut 則。
func matchRSSStoriesToComponentsViaLLM(ctx context.Context, stories []rssStory, comps []models.PublicComponentForNewsMatch, maxOut int) ([]rssStoryWithComponent, error) {
	if len(stories) == 0 || len(comps) == 0 {
		return nil, nil
	}

	candidateStories := selectRSSStoriesForLLM(stories)
	compsSubset := selectComponentsForRSSPrompt(comps)
	newsBlock := buildRSSLLMNewsBlock(candidateStories)
	catalog := buildRSSLLMComponentCatalog(compsSubset)

	systemText := strings.TrimSpace(`
你是協助「城市公開儀表板」策展的編輯。下方有多則RSS新聞（以 #數字 編號）以及儀表板「公開組件」清單（每行組件以一個數字 id 標識，另有 index、city、name、desc）。
對每一則新聞，判斷其主題是否與某一組件的數據主題有直接關聯（讀者可透過該組件資料理解新聞背景或議題）。
僅在主題有直接關聯時將 related 設為 true，並填入該組件整數 component_id（必須與清單中的 id 完全一致）。
泛政治新聞、與任一組件主題無關的國際花絮、無法對應到清單內任一組件的內容，一律 related=false。
只輸出一段 JSON物件，不要有其他說明或 markdown。Schema 為：
{"matches":[{"news_index":0,"related":false},{"news_index":1,"related":true,"component_id":123}]}
matches 須列出新聞索引 0 到 ` + fmt.Sprintf("%d", len(candidateStories)-1) + ` 每一筆，且每個 news_index 僅出現一次，順序可任意。`)

	userText := strings.TrimSpace(`【RSS 新聞（請依編號對應 news_index）】
` + newsBlock + `
【公開組件清單（僅可使用下列 id）】
` + catalog)

	req := ai.AIChatRequest{
		SessionID: "rss-recommend-llm",
		Messages: []llms.MessageContent{
			{Role: llms.ChatMessageTypeSystem, Parts: []llms.ContentPart{llms.TextContent{Text: systemText}}},
			{Role: llms.ChatMessageTypeHuman, Parts: []llms.ContentPart{llms.TextContent{Text: userText}}},
		},
	}

	meta := map[string]any{
		"max_new_tokens": rssLLMMatchesJSONMaxNewTokens,
		"temperature":    0.15,
		"source":         "rss_recommend",
	}

	logEntry, err := ai.ChatWithTWCC(ctx, req, llms.WithMetadata(meta))
	if err != nil || logEntry == nil {
		if err != nil {
			return nil, fmt.Errorf("LLM 關聯判斷失敗：%w", err)
		}
		return nil, fmt.Errorf("LLM 關聯判斷失敗：無回應")
	}

	parsed, err := parseRSSLLMMatchJSON(logEntry.Answer)
	if err != nil {
		return nil, fmt.Errorf("解析 LLM 判斷結果失敗：%v", err)
	}

	validComp := make(map[int64]models.PublicComponentForNewsMatch, len(compsSubset))
	for _, c := range compsSubset {
		validComp[c.ID] = c
	}

	seenNewsIdx := map[int]struct{}{}
	seenTitle := map[string]struct{}{}
	var out []rssStoryWithComponent
	for _, ent := range parsed.Matches {
		if ent.NewsIndex < 0 || ent.NewsIndex >= len(candidateStories) {
			continue
		}
		if _, dup := seenNewsIdx[ent.NewsIndex]; dup {
			continue
		}
		seenNewsIdx[ent.NewsIndex] = struct{}{}
		if !ent.Related {
			continue
		}
		comp, known := validComp[ent.ComponentID]
		if !known {
			logs.FWarn("RSS LLM：略過未定義 component_id=%d（news_index=%d）", ent.ComponentID, ent.NewsIndex)
			continue
		}
		st := candidateStories[ent.NewsIndex]
		key := strings.ToLower(strings.TrimSpace(st.title))
		if _, dup := seenTitle[key]; dup {
			continue
		}
		seenTitle[key] = struct{}{}
		out = append(out, rssStoryWithComponent{story: st, comp: comp})
		if len(out) >= maxOut {
			break
		}
	}

	return out, nil
}
