// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/database"
	"TaipeiCityDashboardBE/app/database/models"

	"github.com/gin-gonic/gin"
)

/*
GetComponentChartData retrieves the chart data for a component.
/api/v1/components/:id/chart

header: time_from, time_to (optional)
*/
func GetComponentChartData(c *gin.Context) {
	var chartDataQuery models.ChartDataQuery

	// 1. Get the component id from the URL
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid component ID"})
		return
	}

	// 2. Get the chart data query and chart data type from the database
	err = database.DBManager.
		Table("components").
		Select("query_type, query_chart").
		Where("components.id = ?", id).
		Find(&chartDataQuery).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if (chartDataQuery.QueryChart == "") || (chartDataQuery.QueryType == "") {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "No chart data available"})
		return
	}

	// 3. Get and parse the chart data based on chart data type
	switch chartDataQuery.QueryType {
	case "two_d":
		getTwoDimensionalData(&chartDataQuery.QueryChart, c)
	case "three_d":
		getThreeDimensionalData(&chartDataQuery.QueryChart, c)
	// Percentage data uses the same format but series no. must be 2.
	case "percent":
		getThreeDimensionalData(&chartDataQuery.QueryChart, c)
	case "time":
		getTimeSeriesData(&chartDataQuery.QueryChart, c)
	case "map_legend":
		getMapLegendData(&chartDataQuery.QueryChart, c)
	}
}

/*
GetComponentHistoryData retrieves the history data for a component.
/api/v1/components/:id/history

header: time_from, time_to (optional)
timesteps are automatically determined based on the time range:
  - Within 24hrs: hour
  - Within 1 month: day
  - Within 3 months: week
  - Within 2 years: month
  - More than 2 years: year
*/
func GetComponentHistoryData(c *gin.Context) {
	var historyDataQuery models.HistoryDataQuery

	// 1. Get the component id from the URL
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid component ID"})
		return
	}

	// 2. Get the history data query from the database
	err = database.DBManager.
		Table("components").
		Select("query_history").
		Where("components.id = ?", id).
		Find(&historyDataQuery).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if historyDataQuery.QueryHistory == "" {
		c.JSON(http.StatusNotFound, gin.H{"status": "error", "message": "No history data available"})
		return
	}

	// 3. Determine the time range of the query and timestep unit
	timeFrom, timeTo := utilGetTime(c)
	var timeStepUnit string

	timeFromTime, err := time.Parse("2006-01-02T15:04:05+08:00", timeFrom)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	timeToTime, err := time.Parse("2006-01-02T15:04:05+08:00", timeTo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if timeToTime.Sub(timeFromTime).Hours() <= 24 {
		timeStepUnit = "hour" // Within 24hrs
	} else if timeToTime.Sub(timeFromTime).Hours() < 24*32 {
		timeStepUnit = "day" // Within 1 month
	} else if timeToTime.Sub(timeFromTime).Hours() < 24*93 {
		timeStepUnit = "week" // Within 3 months
	} else if timeToTime.Sub(timeFromTime).Hours() < 24*740 {
		timeStepUnit = "month" // Within 2 years
	} else {
		timeStepUnit = "year" // More than 2 years
	}

	// 4. Insert the time range and timestep unit into the query
	var queryInsertStrings []any

	if strings.Count(historyDataQuery.QueryHistory, "%s")%3 != 0 {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Invalid query. Please contact the administrator."})
		return
	}

	for i := 0; i < strings.Count(historyDataQuery.QueryHistory, "%s")/3; i++ {
		queryInsertStrings = append(queryInsertStrings, timeStepUnit, timeFrom, timeTo)
	}

	historyDataQuery.QueryHistory = fmt.Sprintf(historyDataQuery.QueryHistory, queryInsertStrings...)

	// 5. Get and parse the history data
	getTimeSeriesData(&historyDataQuery.QueryHistory, c)
}

/*
Below are the parsing functions for the four data types:
two_d, three_d, percent, and time. three_d and percent data share a common handler.
*/

func getTwoDimensionalData(query *string, c *gin.Context) {
	var chartData []models.TwoDimensionalData
	var chartDataOutput []models.TwoDimensionalDataOutput
	var queryString string

	// 1. Check if query contains substring '%s'. If so, the component can be queried by time.
	timeFrom, timeTo := utilGetTime(c)

	if strings.Count(*query, "%s") == 2 {
		queryString = fmt.Sprintf(*query, timeFrom, timeTo)
	} else {
		queryString = *query
	}

	// 2. Get the data from the database
	err := database.DBDashboard.Raw(queryString).Scan(&chartData).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if len(chartData) == 0 {
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": nil})
		return
	}

	// 3. Convert the data to the format required by the front-end
	chartDataOutput = append(chartDataOutput, models.TwoDimensionalDataOutput{Data: chartData})

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartDataOutput})
}

func getThreeDimensionalData(query *string, c *gin.Context) {
	var chartData []models.ThreeDimensionalData
	var chartDataOutput []models.ThreeDimensionalDataOutput
	var categories []string
	var queryString string

	// 1. Check if query contains substring '%s'. If so, the component can be queried by time.
	timeFrom, timeTo := utilGetTime(c)

	if strings.Count(*query, "%s") == 2 {
		queryString = fmt.Sprintf(*query, timeFrom, timeTo)
	} else {
		queryString = *query
	}

	// 2. Get the data from the database
	err := database.DBDashboard.Raw(queryString).Scan(&chartData).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if len(chartData) == 0 {
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": nil})
		return
	}

	// 3. Convert the data to the format required by the front-end
	for _, data := range chartData {
		// Get unique categories from xAxis
		var foundX bool
		for _, category := range categories {
			if category == data.Xaxis {
				foundX = true
				break
			}
		}

		// If a unique xAxis is found, append it to the existing list of categories
		if !foundX {
			categories = append(categories, data.Xaxis)
		}

		// Group data together by yAxis
		var foundY bool
		for i, output := range chartDataOutput {
			if output.Name == data.Yaxis {
				// Append the data to the output
				chartDataOutput[i].Data = append(output.Data, data.Data)
				foundY = true
				break
			}
		}

		// If a unique yAxis is found, create a new entry in the output
		if !foundY {
			chartDataOutput = append(chartDataOutput, models.ThreeDimensionalDataOutput{Name: data.Yaxis, Icon: data.Icon, Data: []int{data.Data}})
		}
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartDataOutput, "categories": categories})
}

func getTimeSeriesData(query *string, c *gin.Context) {
	var chartData []models.TimeSeriesData
	var chartDataOutput []models.TimeSeriesDataOutput

	var queryString string

	// 1. Check if query contains substring '%s'. If so, the component can be queried by time.
	timeFrom, timeTo := utilGetTime(c)

	if strings.Count(*query, "%s") == 2 {
		queryString = fmt.Sprintf(*query, timeFrom, timeTo)
	} else {
		queryString = *query
	}

	// 2. Get the data from the database
	err := database.DBDashboard.Raw(queryString).Scan(&chartData).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if len(chartData) == 0 {
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": nil})
		return
	}

	// 3. Convert the data to the format required by the front-end
	for _, data := range chartData {
		// Group data together by yAxis
		var foundY bool
		formattedDate := data.Xaxis.Format("2006-01-02T15:04:05+08:00")
		for i, output := range chartDataOutput {
			if output.Name == data.Yaxis {
				// Append the data to the output
				chartDataOutput[i].Data = append(output.Data, models.TimeSeriesDataItem{X: formattedDate, Y: data.Data})
				foundY = true
				break
			}
		}

		// If a unique yAxis is found, create a new entry in the output
		if !foundY {
			chartDataOutput = append(chartDataOutput, models.TimeSeriesDataOutput{Name: data.Yaxis, Data: []models.TimeSeriesDataItem{{X: formattedDate, Y: data.Data}}})
		}
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartDataOutput})
}

func getMapLegendData(query *string, c *gin.Context) {
	var chartData []models.MapLegendData

	var queryString string

	// 1. Check if query contains substring '%s'. If so, the component can be queried by time.
	timeFrom, timeTo := utilGetTime(c)

	if strings.Count(*query, "%s") == 2 {
		queryString = fmt.Sprintf(*query, timeFrom, timeTo)
	} else {
		queryString = *query
	}

	// 2. Get the data from the database
	err := database.DBDashboard.Raw(queryString).Scan(&chartData).Error
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	if len(chartData) == 0 {
		c.JSON(http.StatusOK, gin.H{"status": "success", "data": nil})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chartData})
}
