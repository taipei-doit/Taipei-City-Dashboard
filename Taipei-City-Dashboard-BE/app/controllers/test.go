package controllers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type ScopeRequest struct {
	Lng float64 `json:"lng"`
	Lat float64 `json:"lat"`
}

func TestHandler(c *gin.Context){
	var req ScopeRequest

	// 解析 JSON 並驗證
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format. 'lat' and 'lng' are required.",
		})
		return
	}

	// 回傳收到的經緯度
	c.JSON(http.StatusOK, gin.H{
		"message": "Scope info received successfully",
		"lat":     req.Lat,
		"lng":     req.Lng,
	})
}