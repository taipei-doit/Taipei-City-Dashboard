package services

import (
	"fmt"
	"time"

	"TaipeiCityDashboardBE/app/models"
)

const taipeiTimeLayout = "2006-01-02T15:04:05+08:00"

// ComponentChartDataResult is the controlled output from an existing
// query_charts.query_chart lookup. It never accepts SQL from callers.
type ComponentChartDataResult struct {
	Index     string      `json:"index"`
	City      string      `json:"city"`
	QueryType string      `json:"query_type"`
	Unit      string      `json:"unit"`
	Data      interface{} `json:"data,omitempty"`
}

// NormalizeComponentTimeRange returns a concrete time range, defaulting to the
// most recent 24 hours in Taipei time.
func NormalizeComponentTimeRange(timeFrom string, timeTo string) (string, string, bool) {
	defaulted := false
	loc, _ := time.LoadLocation("Asia/Taipei")
	now := time.Now().In(loc)

	if timeTo == "" {
		timeTo = now.Format(taipeiTimeLayout)
		defaulted = true
	}
	if timeFrom == "" {
		timeFrom = now.Add(-24 * time.Hour).Format(taipeiTimeLayout)
		defaulted = true
	}

	return timeFrom, timeTo, defaulted
}

// FetchComponentChartDataByIndexAndTime uses only existing component metadata
// and parser functions. It does not allow LLM-provided SQL, table names, or
// column names.
func FetchComponentChartDataByIndexAndTime(index string, city string, timeFrom string, timeTo string) (ComponentChartDataResult, error) {
	info, err := models.GetComponentQueryInfoByIndex(index, city)
	if err != nil {
		return ComponentChartDataResult{}, fmt.Errorf("query component config failed: %w", err)
	}
	if info.QueryChart == "" {
		return ComponentChartDataResult{
			Index:     index,
			City:      city,
			QueryType: info.QueryType,
			Unit:      info.Unit,
		}, nil
	}

	result := ComponentChartDataResult{
		Index:     index,
		City:      city,
		QueryType: info.QueryType,
		Unit:      info.Unit,
	}

	var fetchErr error
	switch info.QueryType {
	case "two_d":
		result.Data, fetchErr = models.GetTwoDimensionalData(&info.QueryChart, timeFrom, timeTo)
	case "three_d", "percent":
		var categories []string
		var data interface{}
		data, categories, fetchErr = models.GetThreeDimensionalData(&info.QueryChart, timeFrom, timeTo)
		result.Data = map[string]interface{}{"data": data, "categories": categories}
	case "time":
		result.Data, fetchErr = models.GetTimeSeriesData(&info.QueryChart, timeFrom, timeTo)
	case "map_legend":
		result.Data, fetchErr = models.GetMapLegendData(&info.QueryChart, timeFrom, timeTo)
	default:
		return result, fmt.Errorf("unsupported query type: %s", info.QueryType)
	}
	if fetchErr != nil {
		return result, fetchErr
	}

	return result, nil
}
