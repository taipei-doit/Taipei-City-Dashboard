package tools

import (
	"TaipeiCityDashboardBE/app/models"
	"context"
	"encoding/json"
	"fmt"
	"time"
)

// ToolFunc defines the signature for a tool function
type ToolFunc func(ctx context.Context, args string) (string, error)

var registry = make(map[string]ToolFunc)

func init() {
	// Register demo tools
	Register("get_current_time", GetCurrentTime)
	Register("get_population_summary", GetPopulationSummary)
	Register("get_nearby_stations", GetNearbyStations)
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
		return "", fmt.Errorf("invalid arguments: %v", err)
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

// NearbyStationsArgs defines the arguments for the get_nearby_stations tool
type NearbyStationsArgs struct {
	Lat    float64 `json:"lat"`
	Lng    float64 `json:"lng"`
	Radius int     `json:"radius"`
}

// GetNearbyStations returns MRT accessibility facilities (elevator/ramp exits)
// within the given radius (meters) of the user's coordinate, joined with the
// latest active alert per station. Returned as a JSON string for the LLM.
func GetNearbyStations(ctx context.Context, args string) (string, error) {
	var params NearbyStationsArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}
	if params.Lat == 0 && params.Lng == 0 {
		return "", fmt.Errorf("lat/lng are required")
	}

	radius := params.Radius
	if radius <= 0 {
		radius = 500
	}

	stations, err := models.GetMrtStationsNearby(params.Lat, params.Lng, radius)
	if err != nil {
		return "", fmt.Errorf("查詢附近站點失敗: %v", err)
	}

	if len(stations) == 0 {
		return fmt.Sprintf(
			`{"radius_m":%d,"count":0,"stations":[],"note":"半徑內無資料，可建議使用者擴大查詢半徑"}`,
			radius,
		), nil
	}

	alertCount := 0
	for _, s := range stations {
		if s.AlertStatus == "active" {
			alertCount++
		}
	}

	payload := map[string]interface{}{
		"radius_m":           radius,
		"count":              len(stations),
		"active_alert_count": alertCount,
		"stations":           stations,
	}
	b, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("序列化結果失敗: %v", err)
	}
	return string(b), nil
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

// Helper to parse JSON arguments if needed in future tools
func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
