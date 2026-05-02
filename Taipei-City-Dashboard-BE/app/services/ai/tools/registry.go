package tools

import (
	"TaipeiCityDashboardBE/app/models"
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// ToolFunc defines the signature for a tool function
type ToolFunc func(ctx context.Context, args string) (string, error)

const invalidArgumentsErrorFormat = "invalid arguments: %v"

var registry = make(map[string]ToolFunc)

func init() {
	// Register demo tools
	Register("get_current_time", GetCurrentTime)
	Register("get_population_summary", GetPopulationSummary)
	Register("search_dashboard_components", SearchDashboardComponents)
	Register("get_component_detail", GetComponentDetail)
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

// PopulationArgs defines the arguments for the get_population_summary tool
type PopulationArgs struct {
	City string `json:"city"`
	Year int    `json:"year"`
}

// GetPopulationSummary queries the population age distribution from the dashboard database
func GetPopulationSummary(ctx context.Context, args string) (string, error) {
	var params PopulationArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf(invalidArgumentsErrorFormat, err)
	}

	// Default to Taipei if not specified or unrecognized
	tableName := "population_age_distribution_tpe"
	cityName := "台北市"
	if params.City == "new_taipei" {
		tableName = "population_age_distribution_new_tpe"
		cityName = "新北市"
	}

	// Define result structure based on database schema
	var result struct {
		Year      int `gorm:"column:year"`
		Young     int `gorm:"column:young_population"`
		Working   int `gorm:"column:working_age_population"`
		Elderly   int `gorm:"column:elderly_population"`
		DataTime  time.Time `gorm:"column:data_time"`
	}

	// Query the dashboard database
	err := models.DBDashboard.Table(tableName).
		Where("year = ?", params.Year).
		Order("data_time DESC"). // Get the latest record for that year
		First(&result).Error

	if err != nil {
		return "", fmt.Errorf("找不到 %s %d 年的人口統計資料: %v", cityName, params.Year, err)
	}

	// Format the response for the LLM
	return fmt.Sprintf(
		"【%d年 %s 人口結構概況】\n- 幼年人口 (0-14歲)：%d 人\n- 青壯年人口 (15-64歲)：%d 人\n- 老年人口 (65歲以上)：%d 人\n- 總人口： %d 人\n- 數據更新時間：%s",
		result.Year, cityName, result.Young, result.Working, result.Elderly,
		result.Young+result.Working+result.Elderly,
		result.DataTime.Format("2006-01-02"),
	), nil
}

// GetCurrentTime is a demo tool that returns the current Taipei time
func GetCurrentTime(ctx context.Context, args string) (string, error) {
	loc, err := time.LoadLocation("Asia/Taipei")
	if err != nil {
		// Fallback to UTC if timezone data is missing
		return time.Now().Format(time.RFC3339), nil
	}
	return time.Now().In(loc).Format("2006-01-02 15:04:05"), nil
}

type SearchDashboardComponentsArgs struct {
	Query          string  `json:"query"`
	Limit          int     `json:"limit"`
	ScoreThreshold float64 `json:"score_threshold"`
	City           string  `json:"city"`
}

// SearchDashboardComponents retrieves semantically similar dashboard components and returns compact RAG context.
func SearchDashboardComponents(ctx context.Context, args string) (string, error) {
	var params SearchDashboardComponentsArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf(invalidArgumentsErrorFormat, err)
	}

	params.Query = strings.TrimSpace(params.Query)
	if params.Query == "" {
		return "", fmt.Errorf("query is required")
	}
	if params.Limit <= 0 || params.Limit > 20 {
		params.Limit = 8
	}
	if params.ScoreThreshold <= 0 || params.ScoreThreshold > 1 {
		params.ScoreThreshold = 0.72
	}

	results, err := models.GetComponentByQueryVector(params.Query, params.Limit, params.ScoreThreshold)
	if err != nil {
		return "", err
	}

	cityFilter := strings.ToLower(strings.TrimSpace(params.City))
	contextList := make([]map[string]interface{}, 0)
	for _, item := range results {
		if cityFilter != "" && strings.ToLower(item.City) != cityFilter {
			continue
		}

		detail, detailErr := models.GetComponentByID(int(item.ID), item.City)
		if detailErr != nil {
			contextList = append(contextList, map[string]interface{}{
				"id":    item.ID,
				"index": item.Index,
				"name":  item.Name,
				"city":  item.City,
				"score": item.Score,
			})
			continue
		}

		contextList = append(contextList, map[string]interface{}{
			"id":               detail.ID,
			"index":            detail.Index,
			"name":             detail.Name,
			"city":             detail.City,
			"score":            item.Score,
			"short_desc":       detail.ShortDesc,
			"long_desc":        detail.LongDesc,
			"use_case":         detail.UseCase,
			"source":           detail.Source,
			"update_freq":      detail.UpdateFreq,
			"update_freq_unit": detail.UpdateFreqUnit,
		})
	}

	payload, err := json.Marshal(map[string]interface{}{
		"query":   params.Query,
		"results": contextList,
	})
	if err != nil {
		return "", err
	}

	return string(payload), nil
}

type GetComponentDetailArgs struct {
	ID   int64  `json:"id"`
	City string `json:"city"`
}

// GetComponentDetail returns rich metadata for one dashboard component.
func GetComponentDetail(ctx context.Context, args string) (string, error) {
	var params GetComponentDetailArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf(invalidArgumentsErrorFormat, err)
	}
	if params.ID <= 0 {
		return "", fmt.Errorf("id must be greater than 0")
	}
	params.City = strings.TrimSpace(params.City)
	if params.City == "" {
		return "", fmt.Errorf("city is required")
	}

	detail, err := models.GetComponentByID(int(params.ID), params.City)
	if err != nil {
		return "", err
	}

	payload, err := json.Marshal(map[string]interface{}{
		"id":               detail.ID,
		"index":            detail.Index,
		"name":             detail.Name,
		"city":             detail.City,
		"short_desc":       detail.ShortDesc,
		"long_desc":        detail.LongDesc,
		"use_case":         detail.UseCase,
		"source":           detail.Source,
		"time_from":        detail.TimeFrom,
		"time_to":          detail.TimeTo,
		"update_freq":      detail.UpdateFreq,
		"update_freq_unit": detail.UpdateFreqUnit,
		"links":            detail.Links,
	})
	if err != nil {
		return "", err
	}

	return string(payload), nil
}

// Helper to parse JSON arguments if needed in future tools
func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
