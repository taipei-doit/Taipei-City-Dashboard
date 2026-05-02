package controllers

import (
	"net/http"
	"strconv"

	"TaipeiCityDashboardBE/app/models"

	"github.com/gin-gonic/gin"
)

// 市民綠色飲食行為流程儀表板 — controller layer
// API contract: docs/eco_diet_openapi.yaml

// ─── C1a: GET /api/v1/eco_diet/restaurant/points ────────────────────

// GetEcoRestaurantPoints returns all eco-restaurants (Taipei + New Taipei).
func GetEcoRestaurantPoints(c *gin.Context) {
	data, err := models.GetEcoRestaurantPoints()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C1b: GET /api/v1/eco_diet/restaurant/density-by-district ───────

// GetEcoRestaurantDensityByDistrict returns per-district counts; optional ?city=
// filters to a single city ('臺北市' or '新北市').
func GetEcoRestaurantDensityByDistrict(c *gin.Context) {
	city := c.Query("city")
	data, err := models.GetEcoRestaurantDensityByDistrict(city)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C2: GET /api/v1/eco_diet/restaurant/count-by-city ──────────────

// GetEcoRestaurantCountByCity returns the 2-row Taipei/New-Taipei summary.
func GetEcoRestaurantCountByCity(c *gin.Context) {
	data, err := models.GetEcoRestaurantCountByCity()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C3: GET /api/v1/eco_diet/restaurant/list ───────────────────────

// GetEcoRestaurantList returns eco-restaurants filtered by optional district / action / city.
// `action` matches against the env_actions text[] column (Taipei-only data).
func GetEcoRestaurantList(c *gin.Context) {
	district := c.Query("district")
	action := c.Query("action")
	city := c.Query("city")
	data, err := models.GetEcoRestaurantList(district, action, city)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C4: GET /api/v1/eco_diet/green_store/points ────────────────────

// GetGreenStorePoints returns all green stores; optional ?store_type= and ?city= filters.
func GetGreenStorePoints(c *gin.Context) {
	storeType := c.Query("store_type")
	city := c.Query("city")
	data, err := models.GetGreenStorePoints(storeType, city)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C5: GET /api/v1/eco_diet/waste/yearly ──────────────────────────

// GetWasteYearly returns the 8 series (2 cities × 4 metrics) yearly waste trend.
func GetWasteYearly(c *gin.Context) {
	data, categories, err := models.GetWasteYearly()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})
}

// ─── C7a: GET /api/v1/eco_diet/food_bank/points ─────────────────────

// GetFoodBankPoints returns all food bank locations (~80 rows).
func GetFoodBankPoints(c *gin.Context) {
	data, err := models.GetFoodBankPoints()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}

// ─── C7b: GET /api/v1/eco_diet/food_bank/nearby ─────────────────────

// GetFoodBankNearby returns food banks sorted by Haversine distance from (lat, lng).
// Required: ?lat&lng. Optional: ?limit (default 3, max 100).
func GetFoodBankNearby(c *gin.Context) {
	latStr := c.Query("lat")
	lngStr := c.Query("lng")
	if latStr == "" || lngStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "lat and lng are required"})
		return
	}
	lat, err := strconv.ParseFloat(latStr, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "lat must be a number"})
		return
	}
	lng, err := strconv.ParseFloat(lngStr, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "lng must be a number"})
		return
	}

	limit := 3
	if s := c.Query("limit"); s != "" {
		v, err := strconv.Atoi(s)
		if err != nil || v < 1 {
			c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "limit must be a positive integer"})
			return
		}
		if v > 100 {
			v = 100
		}
		limit = v
	}

	data, err := models.GetFoodBankNearby(lat, lng, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}
