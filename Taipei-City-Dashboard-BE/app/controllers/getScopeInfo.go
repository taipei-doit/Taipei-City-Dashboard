package controllers

import (
	"math"
	"net/http"

	"github.com/gin-gonic/gin"
)

type MapInput struct {
	Lng float64 `json:"lng"`
	Lat float64 `json:"lat"`
}

// the struct of fake info is defined here
type Location struct {
	Name string  `json:"name"`
	Lat  float64 `json:"lat"`
	Lng  float64 `json:"lng"`
}

func GetScopeInfoHandler(c *gin.Context){
	var req struct {
		Lat float64 `json:"lat"`
		Lng float64 `json:"lng"`
	}

	// fake info
	data := []Location{
		{"台北101", 25.033964, 121.564468},
		{"中正紀念堂", 25.0340, 121.5210},
		{"台大", 25.0173, 121.5395},
		{"士林夜市", 25.088, 121.525},
		{"淡水老街", 25.1696, 121.4459},
	}
	
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// get the 4 point
	distanceKm :=1.6
	latOffset := distanceKm / 111.0 // 緯度每度約 111 公里

	// 經度的偏移需考慮緯度的餘弦值
	lngOffset := distanceKm / (111.0 * math.Cos(req.Lat*math.Pi/180.0))

	// 各方向座標
	north := gin.H{"lat": req.Lat + latOffset, "lng": req.Lng}
	south := gin.H{"lat": req.Lat - latOffset, "lng": req.Lng}
	east := gin.H{"lat": req.Lat, "lng": req.Lng + lngOffset}
	west := gin.H{"lat": req.Lat, "lng": req.Lng - lngOffset} 
	

	var inScope []Location
	for _, loc := range data {
		if haversine(req.Lat, req.Lng, loc.Lat, loc.Lng) <= 1.6 {
			inScope = append(inScope, loc)
		}
	}

	// TODO: 根據經緯度查資料庫，回傳 1.6 公里範圍內資料
	c.JSON(http.StatusOK, gin.H{
		"center": gin.H{"lat": req.Lat, "lng": req.Lng},
		"scope": gin.H{
			"north": north,
			"south": south,
			"east":  east,
			"west":  west,
		},
	})
}

// haversine function calculate the distance
func haversine(lat1, lng1, lat2, lng2 float64) float64 {
	const R = 6371 // 地球半徑 (km)

	dLat := (lat2 - lat1) * math.Pi / 180.0
	dLng := (lng2 - lng1) * math.Pi / 180.0

	lat1Rad := lat1 * math.Pi / 180.0
	lat2Rad := lat2 * math.Pi / 180.0

	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Sin(dLng/2)*math.Sin(dLng/2)*math.Cos(lat1Rad)*math.Cos(lat2Rad)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))

	return R * c
}
