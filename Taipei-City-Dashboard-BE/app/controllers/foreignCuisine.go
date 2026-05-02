package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services"
	"context"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

func GetForeignCuisineRestaurants(c *gin.Context) {
	city := c.Query("city")
	if city == "" {
		city = "taipei"
	}

	if city != "taipei" && city != "metrotaipei" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid City Name"})
		return
	}

	limit, err := strconv.Atoi(c.DefaultQuery("limit", "2000"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "invalid limit"})
		return
	}

	rows, err := models.ListForeignCuisineRestaurants(city, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"total":  len(rows),
		"data":   rows,
	})
}

func SyncForeignCuisineRestaurants(c *gin.Context) {
	city := c.Query("city")
	if city == "" {
		city = "taipei"
	}

	if city != "taipei" && city != "metrotaipei" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "Invalid City Name"})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	count, err := services.SyncForeignCuisineData(ctx, city)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "success",
		"city":   city,
		"count":  count,
	})
}
