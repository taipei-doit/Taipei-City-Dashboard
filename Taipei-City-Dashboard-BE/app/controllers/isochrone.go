// Developed by Bombs King, Taipei Codefest 2026

package controllers

import (
	"net/http"
	"time"

	"TaipeiCityDashboardBE/app/services/isochrone/transit"

	"github.com/gin-gonic/gin"
)

type isochroneRequest struct {
	Lat            float64  `json:"lat" binding:"required"`
	Lon            float64  `json:"lng" binding:"required"`
	TimeType       string   `json:"time_type"`
	TimeDirection  string   `json:"time_direction"`
	DepartureTime  string   `json:"departure_time"`
	ArrivalTime    string   `json:"arrival_time"`
	ServiceProfile string   `json:"service_profile"`
	Cutoffs        []int32  `json:"cutoffs"`
	Modes          []string `json:"modes"`
}

type networkRequest struct {
	Lat            float64  `json:"lat" binding:"required"`
	Lon            float64  `json:"lng" binding:"required"`
	TimeType       string   `json:"time_type"`
	TimeDirection  string   `json:"time_direction"`
	DepartureTime  string   `json:"departure_time"`
	ArrivalTime    string   `json:"arrival_time"`
	Cutoffs        []int32  `json:"cutoffs"`
	MaxTransfers   *int     `json:"max_transfers"`
	ServiceProfile string   `json:"service_profile"`
	Modes          []string `json:"modes"`
}

// GetIsochrone handles POST /api/v1/isochrone.
func GetIsochrone(c *gin.Context) {
	req, depTime, timeType, ok := parseIsochroneQuery(c)
	if !ok {
		return
	}

	result, err := queryTransit(c, func(svc *transit.Service) ([]byte, error) {
		return svc.Query(transit.IsochroneRequest{
			Lat:            req.Lat,
			Lon:            req.Lon,
			TimeType:       timeType,
			DepartureTime:  depTime,
			Cutoffs:        req.Cutoffs,
			ServiceProfile: req.ServiceProfile,
			Modes:          req.Modes,
		})
	})
	if err != nil {
		return
	}
	c.Data(http.StatusOK, "application/json", result)
}

// GetIsochroneFull handles POST /api/v1/transit/isochrone/full.
func GetIsochroneFull(c *gin.Context) {
	req, depTime, timeType, maxTransfers, ok := parseNetworkQuery(c)
	if !ok {
		return
	}

	result, err := queryTransit(c, func(svc *transit.Service) ([]byte, error) {
		return svc.Full(transit.FullRequest{
			Lat:            req.Lat,
			Lon:            req.Lon,
			TimeType:       timeType,
			DepartureTime:  depTime,
			Cutoffs:        req.Cutoffs,
			MaxTransfers:   maxTransfers,
			ServiceProfile: req.ServiceProfile,
			Modes:          req.Modes,
		})
	})
	if err != nil {
		return
	}
	c.Data(http.StatusOK, "application/json", result)
}

// GetIsochroneNetwork handles POST /api/v1/transit/isochrone/network.
func GetIsochroneNetwork(c *gin.Context) {
	req, depTime, timeType, maxTransfers, ok := parseNetworkQuery(c)
	if !ok {
		return
	}

	result, err := queryTransit(c, func(svc *transit.Service) ([]byte, error) {
		return svc.Network(transit.NetworkRequest{
			Lat:            req.Lat,
			Lon:            req.Lon,
			TimeType:       timeType,
			DepartureTime:  depTime,
			Cutoffs:        req.Cutoffs,
			MaxTransfers:   maxTransfers,
			ServiceProfile: req.ServiceProfile,
			Modes:          req.Modes,
		})
	})
	if err != nil {
		return
	}
	c.Data(http.StatusOK, "application/json", result)
}

func parseIsochroneQuery(c *gin.Context) (isochroneRequest, time.Time, string, bool) {
	var req isochroneRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		writeError(c, http.StatusBadRequest, err.Error())
		return req, time.Time{}, "", false
	}

	depTime, ok := parseDepartureTime(c, requestTime(req.DepartureTime, req.ArrivalTime))
	if !ok {
		return req, time.Time{}, "", false
	}
	return req, depTime, requestTimeType(req.TimeType, req.TimeDirection), true
}

func parseNetworkQuery(c *gin.Context) (networkRequest, time.Time, string, int, bool) {
	var req networkRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		writeError(c, http.StatusBadRequest, err.Error())
		return req, time.Time{}, "", transit.DefaultMaxTransfers, false
	}

	depTime, ok := parseDepartureTime(c, requestTime(req.DepartureTime, req.ArrivalTime))
	if !ok {
		return req, time.Time{}, "", transit.DefaultMaxTransfers, false
	}

	maxTransfers := transit.DefaultMaxTransfers
	if req.MaxTransfers != nil {
		maxTransfers = *req.MaxTransfers
	}
	return req, depTime, requestTimeType(req.TimeType, req.TimeDirection), maxTransfers, true
}

func requestTime(departureTime, arrivalTime string) string {
	if departureTime != "" {
		return departureTime
	}
	return arrivalTime
}

func requestTimeType(timeType, timeDirection string) string {
	if timeType != "" {
		return timeType
	}
	return timeDirection
}

func queryTransit(c *gin.Context, query func(*transit.Service) ([]byte, error)) ([]byte, error) {
	svc, err := transit.DefaultService()
	if err != nil {
		writeError(c, http.StatusServiceUnavailable, "transit service not ready")
		return nil, err
	}

	result, err := query(svc)
	if err != nil {
		writeError(c, http.StatusInternalServerError, err.Error())
		return nil, err
	}
	return result, nil
}

func writeError(c *gin.Context, status int, message string) {
	c.JSON(status, gin.H{"status": "error", "message": message})
}

func parseDepartureTime(c *gin.Context, value string) (time.Time, bool) {
	if value == "" {
		return time.Now(), true
	}
	if parsed, err := time.Parse(time.RFC3339, value); err == nil {
		return parsed, true
	}
	if parsed, err := time.ParseInLocation("15:04", value, time.Local); err == nil {
		now := time.Now()
		return time.Date(now.Year(), now.Month(), now.Day(), parsed.Hour(), parsed.Minute(), 0, 0, now.Location()), true
	}
	writeError(c, http.StatusBadRequest, "departure_time must be RFC3339 or HH:MM")
	return time.Time{}, false
}
