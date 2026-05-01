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
	Register("get_current_time", GetCurrentTime)
	Register("get_population_summary", GetPopulationSummary)
	Register("get_pedestrian_hotspot", GetPedestrianHotspot)
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

// GetCurrentTime is a demo tool that returns the current Taipei time
func GetCurrentTime(ctx context.Context, args string) (string, error) {
	loc, err := time.LoadLocation("Asia/Taipei")
	if err != nil {
		// Fallback to UTC if timezone data is missing
		return time.Now().Format(time.RFC3339), nil
	}
	return time.Now().In(loc).Format("2006-01-02 15:04:05"), nil
}

// PedestrianHotspotArgs defines arguments for get_pedestrian_hotspot
type PedestrianHotspotArgs struct {
	Location string `json:"location"` // 路口名稱，如 "信義路/基隆路"
	City     string `json:"city"`     // "taipei" or "ntpc"
}

// GetPedestrianHotspot queries the pedestrian hotspot table for a given location
func GetPedestrianHotspot(ctx context.Context, args string) (string, error) {
	var params PedestrianHotspotArgs
	if err := parseArgs(args, &params); err != nil {
		return "", fmt.Errorf("invalid arguments: %v", err)
	}

	var result struct {
		City            string  `gorm:"column:city"`
		NearLocation    string  `gorm:"column:near_location"`
		AccidentCount   int     `gorm:"column:accident_count"`
		DeathCount      int     `gorm:"column:death_count"`
		InjuryCount     int     `gorm:"column:injury_count"`
		TopCause        string  `gorm:"column:top_cause"`
		TopHour         int     `gorm:"column:top_hour"`
		TopSignal       string  `gorm:"column:top_signal"`
		IntersectionPct int     `gorm:"column:intersection_pct"`
		CenterLng       float64 `gorm:"column:center_lng"`
		CenterLat       float64 `gorm:"column:center_lat"`
	}

	query := models.DBDashboard.Table("traffic_pedestrian_hotspot")
	if params.Location != "" {
		query = query.Where("near_location ILIKE ?", "%"+params.Location+"%")
	}
	if params.City != "" {
		query = query.Where("city = ?", params.City)
	}
	err := query.Order("accident_count DESC").First(&result).Error
	if err != nil {
		return fmt.Sprintf("查無符合「%s」的路口資料，請嘗試其他關鍵字。", params.Location), nil
	}

	cityName := "臺北市"
	if result.City == "ntpc" {
		cityName = "新北市"
	}

	signalInfo := "號誌資訊不明"
	if result.TopSignal != "" {
		signalInfo = result.TopSignal
	}

	locationInfo := ""
	if result.IntersectionPct > 0 {
		locationInfo = fmt.Sprintf("其中約 %d%% 發生於交叉路口", result.IntersectionPct)
	}

	return fmt.Sprintf(
		"【%s 行人事故熱點資料】\n路口：%s\n近三年事故件數：%d 件（死亡 %d 人、受傷 %d 人）\n主要肇因：%s\n高峰時段：%02d:00 時\n號誌情況：%s\n%s\n座標：%.4f, %.4f",
		cityName,
		result.NearLocation,
		result.AccidentCount,
		result.DeathCount,
		result.InjuryCount,
		result.TopCause,
		result.TopHour,
		signalInfo,
		locationInfo,
		result.CenterLng,
		result.CenterLat,
	), nil
}

// Helper to parse JSON arguments if needed in future tools
func parseArgs(args string, v interface{}) error {
	return json.Unmarshal([]byte(args), v)
}
