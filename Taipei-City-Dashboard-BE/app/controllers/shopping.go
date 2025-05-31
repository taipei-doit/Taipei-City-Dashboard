
package controllers

import (
	"encoding/json"
	"fmt"

	"github.com/gin-gonic/gin"
	geo "github.com/paulmach/go.geo"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// GetInfos 查詢 1.6 公里範圍內的記錄
// GET /scope/info
func GetNearbyShopping(c *gin.Context) {
	var point Point
	if err := c.ShouldBindJSON(&point); err != nil {
		c.JSON(400, gin.H{"error": "Invalid JSON: " + err.Error()})
		return
	}

	// 連線 PostgreSQL
	host := "codefest2025.rm-rf.uk"
	port := 5433
	user := "postgres"
	password := "mGPuAE2JTDDmdui8"
	dbname := "dashboard"
	sqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable", host, port, user, password, dbname)
	db, err := gorm.Open(postgres.Open(sqlInfo), &gorm.Config{})
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to connect to database: " + err.Error()})
		return
	}

	// 計算 1.6 公里範圍
	distance := 1.6 * 1000
	xLower, xHigher, yLower, yHigher := calculateSquareBounds(point.Y, point.X, distance)

	shopping_data := make([]AddressInfo, 0)
	p := geo.NewPoint(point.X, point.Y)
	// 查詢各表
	var t_shoppings []Tshopping
	var nt_shoppings []NTshopping
	// 初始範圍
	xMin, xMax := xLower, xHigher
	yMin, yMax := yLower, yHigher

	// 設定最大重試次數，避免死循環
	maxRetries := 5
	retry := 0

	for {
		result := db.Select("x, y, address, name").Where(
			"x > ? AND x < ? AND y > ? AND y < ?",
			xMin, xMax, yMin, yMax,
		).Find(&t_shoppings)

		if result.Error != nil {
			c.JSON(500, gin.H{"error": "Query failed: " + result.Error.Error()})
			return
		}

		if len(t_shoppings) > 0 {
			break // 有資料就跳出迴圈
		}

		retry++
		if retry > maxRetries {
			c.JSON(404, gin.H{"error": "No data found after expanding search area"})
			return
		}

		// 擴大範圍：以中心點為基礎放大
		xCenter := (xMin + xMax) / 2
		yCenter := (yMin + yMax) / 2

		xRange := (xMax - xMin) * 1.5 / 2
		yRange := (yMax - yMin) * 1.5 / 2

		xMin = xCenter - xRange
		xMax = xCenter + xRange
		yMin = yCenter - yRange
		yMax = yCenter + yRange
	}
	for _, d := range t_shoppings {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			shopping_data = append(shopping_data, d.AddressInfo)
		}
	}
	// 初始範圍
	xMin, xMax = xLower, xHigher
	yMin, yMax = yLower, yHigher

	// 設定最大重試次數，避免死循環
	maxRetries = 5
	retry = 0
	for {
		result := db.Select("x, y, address, name").Where(
			"X > ? AND X < ? AND Y > ? AND Y < ?",
			xMin, xMax, yMin, yMax,
		).Find(&nt_shoppings)

		if result.Error != nil {
			c.JSON(500, gin.H{"error": "Query failed: " + result.Error.Error()})
			return
		}

		if len(nt_shoppings) > 0 {
			break // 有資料就跳出迴圈
		}

		retry++
		if retry > maxRetries {
			c.JSON(404, gin.H{"error": "No data found after expanding search area"})
			return
		}

		// 擴大範圍：以中心點為基礎放大
		xCenter := (xMin + xMax) / 2
		yCenter := (yMin + yMax) / 2

		xRange := (xMax - xMin) * 1.5 / 2
		yRange := (yMax - yMin) * 1.5 / 2

		xMin = xCenter - xRange
		xMax = xCenter + xRange
		yMin = yCenter - yRange
		yMax = yCenter + yRange
	}
	for _, d := range nt_shoppings {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			shopping_data = append(shopping_data, d.AddressInfo)
		}
	}

	// 構建回應
	root := Root{
		Data: Data{
			Shopping: shopping_data,
		},
	}

	// 序列化為 JSON
	jsonData, err := json.MarshalIndent(root, "", "  ")
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to serialize to JSON: " + err.Error()})
		return
	}

	// 回應 JSON
	c.Data(200, "application/json", jsonData)
}
