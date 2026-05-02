package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"TaipeiCityDashboardBE/app/services"
)

// ToolFunc defines the signature for a tool function
type ToolFunc func(ctx context.Context, args string) (string, error)

var registry = make(map[string]ToolFunc)

func init() {
	Register("get_current_time", GetCurrentTime)
	Register("search_dashboards", SearchDashboardsTool)
	Register("get_component_data", GetComponentDataTool)
	Register("query_city_data", QueryCityDataTool)
	Register("answer_city_data_question", AnswerCityDataQuestionTool)
}

// Register adds a tool to the registry
func Register(name string, fn ToolFunc) {
	registry[name] = fn
}

// Execute calls a registered tool with the given arguments
func Execute(ctx context.Context, name string, args string) (string, error) {
	fn, ok := registry[name]
	if !ok {
		return "", fmt.Errorf("tool %s not found", name)
	}
	return fn(ctx, args)
}

// GetCurrentTime is a demo tool that returns the current Taipei time
func GetCurrentTime(ctx context.Context, args string) (string, error) {
	loc, err := time.LoadLocation("Asia/Taipei")
	if err != nil {
		return time.Now().Format(time.RFC3339), nil
	}
	return time.Now().In(loc).Format("2006-01-02 15:04:05"), nil
}

func SearchDashboardsTool(ctx context.Context, args string) (string, error) {
	var params map[string]string
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("參數解析失敗: %v", err)
	}
	query := params["query"]

	if query == "" {
		return "[]", nil
	}

	results, err := services.SearchQdrantComponents(ctx, query, 10, 0.8)
	if err != nil {
		return "", fmt.Errorf("向量搜尋失敗: %v", err)
	}

	if len(results) == 0 {
		return "[]", nil
	}

	resultBytes, _ := json.Marshal(results)
	return string(resultBytes), nil
}

// GetComponentDataTool 依組件 index 從資料庫取得實際數據
func GetComponentDataTool(ctx context.Context, args string) (string, error) {
	var params struct {
		Index    string `json:"index"`
		City     string `json:"city"`
		TimeFrom string `json:"time_from"`
		TimeTo   string `json:"time_to"`
	}
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("參數解析失敗: %v", err)
	}
	if params.Index == "" {
		return "", fmt.Errorf("index 不可為空")
	}
	if params.City == "" {
		params.City = "taipei"
	}

	params.TimeFrom, params.TimeTo, _ = services.NormalizeComponentTimeRange(params.TimeFrom, params.TimeTo)
	result, err := services.FetchComponentChartDataByIndexAndTime(params.Index, params.City, params.TimeFrom, params.TimeTo)
	if err != nil {
		return "", fmt.Errorf("取得組件資料失敗: %v", err)
	}
	if result.Data == nil {
		return fmt.Sprintf("組件 %s 在 %s 目前沒有可用資料", params.Index, params.City), nil
	}

	resultBytes, _ := json.Marshal(result.Data)
	return string(resultBytes), nil
}

// QueryCityDataTool 依 index 直接取得實際數據（AI 從組件清單選定 index 後呼叫）
// 若未提供 index，則退而使用向量搜尋
func QueryCityDataTool(ctx context.Context, args string) (string, error) {
	var params struct {
		Index    string `json:"index"`
		Query    string `json:"query"`
		City     string `json:"city"`
		TimeFrom string `json:"time_from"`
		TimeTo   string `json:"time_to"`
	}
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("參數解析失敗: %v", err)
	}
	if params.City == "" {
		params.City = "taipei"
	}

	params.TimeFrom, params.TimeTo, _ = services.NormalizeComponentTimeRange(params.TimeFrom, params.TimeTo)

	targetIndex := params.Index
	componentName := ""

	// index 未提供時，退而使用向量搜尋
	if targetIndex == "" {
		if params.Query == "" {
			return "", fmt.Errorf("index 或 query 至少需要提供一個")
		}
		components, err := services.SearchQdrantComponents(ctx, params.Query, 3, 0.8)
		if err != nil || len(components) == 0 {
			return "找不到與查詢相關的組件，請確認組件清單是否有此主題", nil
		}
		targetIndex = components[0].Index
		componentName = components[0].Name
		if params.City == "taipei" && components[0].City != "" {
			params.City = components[0].City
		}
	}

	chartResult, err := services.FetchComponentChartDataByIndexAndTime(targetIndex, params.City, params.TimeFrom, params.TimeTo)
	if err != nil {
		return "", fmt.Errorf("取得資料失敗: %v", err)
	}
	if chartResult.Data == nil {
		return fmt.Sprintf("組件 %s 在 %s 目前沒有可用資料", targetIndex, params.City), nil
	}

	result := map[string]interface{}{
		"index":      targetIndex,
		"name":       componentName,
		"unit":       chartResult.Unit,
		"query_type": chartResult.QueryType,
		"data":       chartResult.Data,
	}
	resultBytes, _ := json.Marshal(result)
	return string(resultBytes), nil
}

// AnswerCityDataQuestionTool returns structured evidence for cross-component
// city-data questions. It never accepts SQL, table names, or column names.
func AnswerCityDataQuestionTool(ctx context.Context, args string) (string, error) {
	var params struct {
		UserQuestion   string  `json:"user_question"`
		City           string  `json:"city"`
		TimeFrom       string  `json:"time_from"`
		TimeTo         string  `json:"time_to"`
		TopK           int     `json:"top_k"`
		ScoreThreshold float32 `json:"score_threshold"`
	}
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("參數解析失敗: %v", err)
	}
	if params.UserQuestion == "" {
		return "", fmt.Errorf("user_question 不可為空")
	}

	pack, err := services.BuildComponentEvidencePack(ctx, services.ComponentEvidenceQuery{
		UserQuestion:   params.UserQuestion,
		City:           params.City,
		TimeFrom:       params.TimeFrom,
		TimeTo:         params.TimeTo,
		TopK:           params.TopK,
		ScoreThreshold: params.ScoreThreshold,
	})
	if err != nil {
		return "", err
	}

	resultBytes, _ := json.Marshal(pack)
	return string(resultBytes), nil
}

func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
