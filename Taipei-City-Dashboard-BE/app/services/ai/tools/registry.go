package tools

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services"
	"context"
	"encoding/json"
	"fmt"
	"time"
)

// ToolFunc defines the signature for a tool function
type ToolFunc func(ctx context.Context, args string) (string, error)

var registry = make(map[string]ToolFunc)

func init() {
	Register("get_current_time", GetCurrentTime)
	Register("search_dashboards", SearchDashboardsTool)
	Register("get_component_data", GetComponentDataTool)
	Register("query_city_data", QueryCityDataTool)
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

	// 預設時間範圍：最近 24 小時
	loc, _ := time.LoadLocation("Asia/Taipei")
	if params.TimeTo == "" {
		params.TimeTo = time.Now().In(loc).Format("2006-01-02T15:04:05+08:00")
	}
	if params.TimeFrom == "" {
		params.TimeFrom = time.Now().In(loc).Add(-24 * time.Hour).Format("2006-01-02T15:04:05+08:00")
	}

	queryType, queryString, err := models.GetComponentChartDataByIndex(params.Index, params.City)
	if err != nil {
		return "", fmt.Errorf("查詢組件設定失敗: %v", err)
	}
	if queryString == "" {
		return fmt.Sprintf("組件 %s 在 %s 目前沒有可用資料", params.Index, params.City), nil
	}

	var result interface{}
	switch queryType {
	case "two_d":
		data, err := models.GetTwoDimensionalData(&queryString, params.TimeFrom, params.TimeTo)
		if err != nil {
			return "", fmt.Errorf("取得 2D 資料失敗: %v", err)
		}
		result = data
	case "three_d", "percent":
		data, categories, err := models.GetThreeDimensionalData(&queryString, params.TimeFrom, params.TimeTo)
		if err != nil {
			return "", fmt.Errorf("取得 3D 資料失敗: %v", err)
		}
		result = map[string]interface{}{"data": data, "categories": categories}
	case "time":
		data, err := models.GetTimeSeriesData(&queryString, params.TimeFrom, params.TimeTo)
		if err != nil {
			return "", fmt.Errorf("取得時序資料失敗: %v", err)
		}
		result = data
	case "map_legend":
		data, err := models.GetMapLegendData(&queryString, params.TimeFrom, params.TimeTo)
		if err != nil {
			return "", fmt.Errorf("取得地圖資料失敗: %v", err)
		}
		result = data
	default:
		return fmt.Sprintf("不支援的資料類型: %s", queryType), nil
	}

	resultBytes, _ := json.Marshal(result)
	return string(resultBytes), nil
}

// QueryCityDataTool 一次完成「搜尋組件 → 取得實際數據」，避免 AI 需要連續呼叫兩個工具
func QueryCityDataTool(ctx context.Context, args string) (string, error) {
	var params struct {
		Query    string `json:"query"`
		City     string `json:"city"`
		TimeFrom string `json:"time_from"`
		TimeTo   string `json:"time_to"`
	}
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("參數解析失敗: %v", err)
	}
	if params.Query == "" {
		return "", fmt.Errorf("query 不可為空")
	}
	if params.City == "" {
		params.City = "taipei"
	}

	loc, _ := time.LoadLocation("Asia/Taipei")
	if params.TimeTo == "" {
		params.TimeTo = time.Now().In(loc).Format("2006-01-02T15:04:05+08:00")
	}
	if params.TimeFrom == "" {
		params.TimeFrom = time.Now().In(loc).Add(-24 * time.Hour).Format("2006-01-02T15:04:05+08:00")
	}

	// 步驟一：向量搜尋找最相關的組件
	components, err := services.SearchQdrantComponents(ctx, params.Query, 3, 0.8)
	if err != nil {
		return "", fmt.Errorf("向量搜尋失敗: %v", err)
	}
	if len(components) == 0 {
		return "找不到與查詢相關的組件", nil
	}

	// 步驟二：取第一個（最相關）組件的實際數據
	best := components[0]
	queryType, queryString, err := models.GetComponentChartDataByIndex(best.Index, params.City)
	if err != nil {
		return "", fmt.Errorf("查詢組件設定失敗: %v", err)
	}
	if queryString == "" {
		return fmt.Sprintf("組件「%s」(%s) 目前沒有可用資料", best.Name, best.Index), nil
	}

	var chartData interface{}
	switch queryType {
	case "two_d":
		chartData, err = models.GetTwoDimensionalData(&queryString, params.TimeFrom, params.TimeTo)
	case "three_d", "percent":
		var categories []string
		var data interface{}
		data, categories, err = models.GetThreeDimensionalData(&queryString, params.TimeFrom, params.TimeTo)
		chartData = map[string]interface{}{"data": data, "categories": categories}
	case "time":
		chartData, err = models.GetTimeSeriesData(&queryString, params.TimeFrom, params.TimeTo)
	case "map_legend":
		chartData, err = models.GetMapLegendData(&queryString, params.TimeFrom, params.TimeTo)
	default:
		return fmt.Sprintf("不支援的資料類型: %s", queryType), nil
	}
	if err != nil {
		return "", fmt.Errorf("取得資料失敗: %v", err)
	}

	result := map[string]interface{}{
		"component": map[string]interface{}{
			"index": best.Index,
			"name":  best.Name,
			"city":  best.City,
			"score": best.Score,
		},
		"query_type": queryType,
		"data":       chartData,
	}
	resultBytes, _ := json.Marshal(result)
	return string(resultBytes), nil
}

func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
