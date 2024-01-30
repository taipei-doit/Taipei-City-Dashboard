// Package models stores the models for the postgreSQL databases.
package models

import (
	"time"
)

// ChartDataQuery is the model for getting the chart data query.
type ChartDataQuery struct {
	QueryType  string `json:"query_type" gorm:"column:query_type"`
	QueryChart string `json:"query_chart" gorm:"column:query_chart"`
}

// HistoryDataQuery is the model for getting the history data query.
type HistoryDataQuery struct {
	QueryHistory string `json:"query_history" gorm:"column:query_history"`
}

/*
TwoDimensionalData Json Format:

	{
		"data": [
			{
				"data": [
					{ "x": "", "y": 17 },
					...
				]
			}
		]
	}
*/
type TwoDimensionalData struct {
	Xaxis string  `gorm:"column:x_axis" json:"x"`
	Data  float64 `gorm:"column:data" json:"y"`
}
type TwoDimensionalDataOutput struct {
	Data []TwoDimensionalData `json:"data"`
}

/*
ThreeDimensionalData & PercentData Json Format:

	{
		"data": [
			{
				"name": ""
				"data": [...]
			},
			...
		]
	}

>> ThreeDimensionalData is shared by 3D and percentage data
*/
type ThreeDimensionalData struct {
	Xaxis string `gorm:"column:x_axis"`
	Icon  string `gorm:"column:icon"`
	Yaxis string `gorm:"column:y_axis"`
	Data  int    `gorm:"column:data"`
}

type ThreeDimensionalDataOutput struct {
	Name string `json:"name"`
	Icon string `json:"icon"`
	Data []int  `json:"data"`
}

/*
TimeSeriesData Json Format:

	{
		"data": [
			{
				"name": "",
				"data": [
					{ "x": "2023-05-25T06:29:00+08:00", "y": 17 },
					...
				]
			},
			...
		]
	}
*/
type TimeSeriesData struct {
	Xaxis time.Time `gorm:"column:x_axis"`
	Yaxis string    `gorm:"column:y_axis"`
	Data  float64   `gorm:"column:data"`
}

type TimeSeriesDataItem struct {
	X string  `json:"x"`
	Y float64 `json:"y"`
}

type TimeSeriesDataOutput struct {
	Name string               `json:"name"`
	Data []TimeSeriesDataItem `json:"data"`
}

/*
MapLegendData Json Format:
*/
type MapLegendData struct {
	Name  string  `gorm:"column:name" json:"name"`
	Type  string  `gorm:"column:type" json:"type"`
	Icon  string  `gorm:"column:icon" json:"icon"`
	Value float64 `gorm:"column:value" json:"value"`
}
