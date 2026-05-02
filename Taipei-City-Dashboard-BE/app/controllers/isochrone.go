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
	TimeType       string   `json:"time_type"`      // "departure" (default) or "arrival"
	TimeDirection  string   `json:"time_direction"` // Alias for time_type
	DepartureTime  string   `json:"departure_time"` // RFC3339; defaults to now
	ArrivalTime    string   `json:"arrival_time"`   // Alias for departure_time
	ServiceProfile string   `json:"service_profile"`
	Cutoffs        []int32  `json:"cutoffs"` // seconds; nil ??defaults
	Modes          []string `json:"modes"`
}

// GetIsochrone handles POST /api/v1/isochrone.
// Returns a GeoJSON FeatureCollection with one polygon per cutoff.
func GetIsochrone(c *gin.Context) {
	var req isochroneRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	timeStr := req.DepartureTime
	if timeStr == "" {
		timeStr = req.ArrivalTime
	}

	timeType := req.TimeType
	if timeType == "" {
		timeType = req.TimeDirection
	}

	depTime, ok := parseDepartureTime(c, timeStr)
	if !ok {
		return
	}

	svc, err := transit.DefaultService()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "error", "message": "transit service not ready"})
		return
	}

	result, err := svc.Query(transit.IsochroneRequest{
		Lat:            req.Lat,
		Lon:            req.Lon,
		TimeType:       timeType,
		DepartureTime:  depTime,
		Cutoffs:        req.Cutoffs,
		ServiceProfile: req.ServiceProfile,
		Modes:          req.Modes,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.Data(http.StatusOK, "application/json", result)
}

type networkRequest struct {
	Lat            float64  `json:"lat" binding:"required"`
	Lon            float64  `json:"lng" binding:"required"`
	TimeType       string   `json:"time_type"`      // "departure" (default) or "arrival"
	TimeDirection  string   `json:"time_direction"` // Alias for time_type
	DepartureTime  string   `json:"departure_time"` // RFC3339; defaults to now
	ArrivalTime    string   `json:"arrival_time"`   // Alias for departure_time
	Cutoffs        []int32  `json:"cutoffs"`        // seconds; nil defaults to 15/30/60/90/120 min
	MaxTransfers   *int     `json:"max_transfers"`  // -1 means no limit (default)
	ServiceProfile string   `json:"service_profile"`
	Modes          []string `json:"modes"`
}

// GetFull handles POST /api/v1/transit/isochrone/full.
// Minimal body: {"lat":25.0478,"lng":121.5174}.
// Returns isochrone polygons plus reachable network up to 120 minutes.
func GetFull(c *gin.Context) {
	req, timeStr, timeType, maxTransfers, ok := parseNetworkRequest(c)
	if !ok {
		return
	}

	depTime, ok := parseDepartureTime(c, timeStr)
	if !ok {
		return
	}

	svc, err := transit.DefaultService()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "error", "message": "transit service not ready"})
		return
	}

	result, err := svc.Full(transit.FullRequest{
		Lat:            req.Lat,
		Lon:            req.Lon,
		TimeType:       timeType,
		DepartureTime:  depTime,
		Cutoffs:        req.Cutoffs,
		MaxTransfers:   maxTransfers,
		ServiceProfile: req.ServiceProfile,
		Modes:          req.Modes,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.Data(http.StatusOK, "application/json", result)
}

// GetNetwork handles POST /api/v1/transit/isochrone/network.
// Returns a GeoJSON FeatureCollection of reachable transit network elements.
func GetNetwork(c *gin.Context) {
	req, timeStr, timeType, maxTransfers, ok := parseNetworkRequest(c)
	if !ok {
		return
	}

	depTime, ok := parseDepartureTime(c, timeStr)
	if !ok {
		return
	}

	svc, err := transit.DefaultService()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "error", "message": "transit service not ready"})
		return
	}

	result, err := svc.Network(transit.NetworkRequest{
		Lat:            req.Lat,
		Lon:            req.Lon,
		TimeType:       timeType,
		DepartureTime:  depTime,
		Cutoffs:        req.Cutoffs,
		MaxTransfers:   maxTransfers,
		ServiceProfile: req.ServiceProfile,
		Modes:          req.Modes,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.Data(http.StatusOK, "application/json", result)
}

func parseNetworkRequest(c *gin.Context) (networkRequest, string, string, int, bool) {
	var req networkRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return req, "", "", -1, false
	}

	timeStr := req.DepartureTime
	if timeStr == "" {
		timeStr = req.ArrivalTime
	}

	timeType := req.TimeType
	if timeType == "" {
		timeType = req.TimeDirection
	}

	maxTransfers := -1
	if req.MaxTransfers != nil {
		maxTransfers = *req.MaxTransfers
	}

	return req, timeStr, timeType, maxTransfers, true
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
	c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "departure_time must be RFC3339 or HH:MM"})
	return time.Time{}, false
}
