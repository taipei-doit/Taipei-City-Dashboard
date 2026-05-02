package services

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

const (
	defaultEvidenceTopK           = 5
	maxEvidenceTopK               = 8
	defaultEvidenceScoreThreshold = 0.85
	maxEvidenceArrayItems         = 30
)

var (
	searchQdrantComponentsForEvidence = SearchQdrantComponents
	fetchComponentDataForEvidence     = FetchComponentChartDataByIndexAndTime
)

type ComponentEvidenceQuery struct {
	UserQuestion   string  `json:"user_question"`
	City           string  `json:"city"`
	TimeFrom       string  `json:"time_from"`
	TimeTo         string  `json:"time_to"`
	TopK           int     `json:"top_k"`
	ScoreThreshold float32 `json:"score_threshold"`
}

type EvidenceTimeRange struct {
	From      string `json:"from"`
	To        string `json:"to"`
	Defaulted bool   `json:"defaulted"`
}

type EvidenceRetrieval struct {
	TopK           int     `json:"top_k"`
	ScoreThreshold float32 `json:"score_threshold"`
	CandidateCount int     `json:"candidate_count"`
	ReturnedCount  int     `json:"returned_count"`
}

type EvidenceAnswerability struct {
	Status string `json:"status"`
	Reason string `json:"reason"`
}

type ComponentEvidence struct {
	ID        interface{} `json:"id,omitempty"`
	Index     string      `json:"index"`
	Name      string      `json:"name"`
	City      string      `json:"city"`
	Score     float32     `json:"score"`
	QueryType string      `json:"query_type,omitempty"`
	Unit      string      `json:"unit"`
	Status    string      `json:"status"`
	Reason    string      `json:"reason,omitempty"`
	Data      interface{} `json:"data,omitempty"`
	Truncated bool        `json:"truncated,omitempty"`
}

type ComponentEvidencePack struct {
	Question               string                `json:"question"`
	City                   string                `json:"city"`
	TimeRange              EvidenceTimeRange     `json:"time_range"`
	Retrieval              EvidenceRetrieval     `json:"retrieval"`
	Answerability          EvidenceAnswerability `json:"answerability"`
	Components             []ComponentEvidence   `json:"components"`
	InsufficientComponents []ComponentEvidence   `json:"insufficient_components"`
	InstructionsForLLM     []string              `json:"instructions_for_llm"`
}

// BuildComponentEvidencePack finds relevant components, fetches each component's
// existing chart data, and returns structured evidence for an LLM answer.
func BuildComponentEvidencePack(ctx context.Context, query ComponentEvidenceQuery) (ComponentEvidencePack, error) {
	query = normalizeEvidenceQuery(query)

	pack := ComponentEvidencePack{
		Question: query.UserQuestion,
		City:     query.City,
		TimeRange: EvidenceTimeRange{
			From: query.TimeFrom,
			To:   query.TimeTo,
		},
		Retrieval: EvidenceRetrieval{
			TopK:           query.TopK,
			ScoreThreshold: query.ScoreThreshold,
		},
		Components:             []ComponentEvidence{},
		InsufficientComponents: []ComponentEvidence{},
		InstructionsForLLM: []string{
			"Use only values present in components[].data.",
			"Do not invent, estimate, or infer missing numeric values.",
			"Do not generate SQL or ask for table and column names.",
			"Every numeric value must include the component unit from components[].unit; if unit is empty or missing, write 單位未提供.",
			"Answer with 2-3 summary sentences, key indicators with units, comparative analysis, decision-support suggestions, and data limitations.",
			"Suggestions must be framed as decision support, not final policy conclusions.",
			"For policy effectiveness questions, if evidence only contains demographic structure, background indicators, or static values, state that the evidence is insufficient to judge policy effectiveness and can only describe demand background or pressure.",
			"For policy effectiveness questions, list missing evidence such as service usage rate, number of care sites, care workforce, waiting time, beds, satisfaction, time series, or before-after policy comparison.",
			"Use only components directly relevant to the user question; do not include unrelated retrieved components in the main analysis.",
			"If unrelated components appear in retrieval results, briefly say they were not used because their relation to the question is low.",
			"Recommendations must be supported by evidence. If evidence is insufficient, recommend only what additional data or indicators should be reviewed.",
			"Do not add percent signs to indicators with empty or missing unit, including aging index. Use 單位未提供 unless the component unit explicitly says otherwise.",
			"State which components were used.",
			"When answerability.status is partial or not_answerable, explicitly mention what data is unavailable.",
		},
	}

	timeFrom, timeTo, defaulted := NormalizeComponentTimeRange(query.TimeFrom, query.TimeTo)
	pack.TimeRange = EvidenceTimeRange{From: timeFrom, To: timeTo, Defaulted: defaulted}

	candidates, err := searchQdrantComponentsForEvidence(ctx, query.UserQuestion, query.TopK, query.ScoreThreshold)
	if err != nil {
		pack.Answerability = EvidenceAnswerability{
			Status: "not_answerable",
			Reason: fmt.Sprintf("semantic search failed: %v", err),
		}
		return pack, nil
	}
	pack.Retrieval.CandidateCount = len(candidates)

	for _, candidate := range candidates {
		component := ComponentEvidence{
			ID:     candidate.ID,
			Index:  candidate.Index,
			Name:   candidate.Name,
			City:   query.City,
			Score:  candidate.Score,
			Status: "ok",
		}

		result, fetchErr := fetchComponentDataForEvidence(candidate.Index, query.City, timeFrom, timeTo)
		component.QueryType = result.QueryType
		component.Unit = result.Unit
		if result.City != "" {
			component.City = result.City
		}

		switch {
		case fetchErr != nil && isUnsupportedComponentError(fetchErr):
			component.Status = "unsupported"
			component.Reason = fetchErr.Error()
			pack.InsufficientComponents = append(pack.InsufficientComponents, component)
		case fetchErr != nil:
			component.Status = "error"
			component.Reason = fetchErr.Error()
			pack.InsufficientComponents = append(pack.InsufficientComponents, component)
		case isEmptyComponentData(result.Data):
			component.Status = "no_data"
			component.Reason = "No chart data returned for this component and time range."
			pack.InsufficientComponents = append(pack.InsufficientComponents, component)
		default:
			component.Data, component.Truncated = truncateForEvidence(result.Data, maxEvidenceArrayItems)
			pack.Components = append(pack.Components, component)
		}
	}

	pack.Retrieval.ReturnedCount = len(pack.Components)
	pack.Answerability = determineAnswerability(len(pack.Components), len(pack.InsufficientComponents), len(candidates))
	return pack, nil
}

func normalizeEvidenceQuery(query ComponentEvidenceQuery) ComponentEvidenceQuery {
	if query.City != "metrotaipei" {
		query.City = "taipei"
	}
	if query.TopK <= 0 {
		query.TopK = defaultEvidenceTopK
	}
	if query.TopK > maxEvidenceTopK {
		query.TopK = maxEvidenceTopK
	}
	if query.ScoreThreshold <= 0 || query.ScoreThreshold > 1 {
		query.ScoreThreshold = defaultEvidenceScoreThreshold
	}
	return query
}

func determineAnswerability(okCount int, insufficientCount int, candidateCount int) EvidenceAnswerability {
	switch {
	case candidateCount == 0:
		return EvidenceAnswerability{Status: "not_answerable", Reason: "No relevant components were found."}
	case okCount == 0:
		return EvidenceAnswerability{Status: "not_answerable", Reason: "Relevant components were found, but none returned usable data."}
	case insufficientCount > 0:
		return EvidenceAnswerability{Status: "partial", Reason: "Some relevant components returned data, while others were unavailable or unsupported."}
	default:
		return EvidenceAnswerability{Status: "answerable", Reason: "Relevant components returned usable data."}
	}
}

func isUnsupportedComponentError(err error) bool {
	return err != nil && strings.HasPrefix(err.Error(), "unsupported query type")
}

func isEmptyComponentData(data interface{}) bool {
	if data == nil {
		return true
	}

	raw, err := json.Marshal(data)
	if err != nil {
		return false
	}
	var normalized interface{}
	if err := json.Unmarshal(raw, &normalized); err != nil {
		return false
	}
	return isEmptyJSONValue(normalized)
}

func isEmptyJSONValue(value interface{}) bool {
	switch v := value.(type) {
	case nil:
		return true
	case []interface{}:
		if len(v) == 0 {
			return true
		}
		for _, item := range v {
			if !isEmptyJSONValue(item) {
				return false
			}
		}
		return true
	case map[string]interface{}:
		if len(v) == 0 {
			return true
		}
		for _, item := range v {
			if !isEmptyJSONValue(item) {
				return false
			}
		}
		return true
	default:
		return false
	}
}

func truncateForEvidence(data interface{}, maxItems int) (interface{}, bool) {
	raw, err := json.Marshal(data)
	if err != nil {
		return data, false
	}

	var normalized interface{}
	if err := json.Unmarshal(raw, &normalized); err != nil {
		return data, false
	}

	truncated := false
	return truncateJSONValue(normalized, maxItems, &truncated), truncated
}

func truncateJSONValue(value interface{}, maxItems int, truncated *bool) interface{} {
	switch v := value.(type) {
	case []interface{}:
		if len(v) > maxItems {
			v = v[:maxItems]
			*truncated = true
		}
		for i := range v {
			v[i] = truncateJSONValue(v[i], maxItems, truncated)
		}
		return v
	case map[string]interface{}:
		for key, item := range v {
			v[key] = truncateJSONValue(item, maxItems, truncated)
		}
		return v
	default:
		return value
	}
}
