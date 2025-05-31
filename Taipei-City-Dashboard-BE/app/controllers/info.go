package controllers

import (
	"encoding/json"
	"fmt"
	"math"

	"github.com/gin-gonic/gin"
	"github.com/paulmach/go.geo"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// AddressInfo 定義共用欄位
type AddressInfo struct {
	ID      int     `gorm:"column:Id" json:"id"`
	Name    string  `gorm:"column:Name" json:"name"`
	Address string  `gorm:"column:Address" json:"address"`
	X       float64 `gorm:"column:X" json:"x"`
	Y       float64 `gorm:"column:Y" json:"y"`
}

// Library 對應 library 表
type NTLibrary struct {
	gorm.Model
	AddressInfo
}

func (NTLibrary) TableName() string {
	return "nt_libnary"
}

type TLibrary struct {
	gorm.Model
	AddressInfo
}

func (TLibrary) TableName() string {
	return "t_libnary"
}

// Hospital 對應 hospital 表
type THospital struct {
	gorm.Model
	AddressInfo
}

func (THospital) TableName() string {
	return "t_hospital"
}

type NTHospital struct {
	gorm.Model
	AddressInfo
}

func (NTHospital) TableName() string {
	return "nt_hospital"
}

// Shopping 對應 shopping 表
type Tshopping struct {
	gorm.Model
	AddressInfo
}

func (Tshopping) TableName() string {
	return "t_shopping"
}

type NTshopping struct {
	gorm.Model
	AddressInfo
}

func (NTshopping) TableName() string {
	return "nt_shopping"
}

// Rental 對應 rental 表
type Rental struct {
	gorm.Model
	AddressInfo
}

func (Rental) TableName() string {
	return "rental_data"
}

// Market 對應 market 表
type TMarket struct {
	gorm.Model
	AddressInfo
}

func (TMarket) TableName() string {
	return "t_market"
}

type NTMarket struct {
	gorm.Model
	AddressInfo
}

func (NTMarket) TableName() string {
	return "nt_market"
}

// Data 對應 JSON 的 "data" 對象
type Data struct {
	Library  []AddressInfo `json:"library"`
	Hospital []AddressInfo `json:"hospital"`
	Shopping []AddressInfo `json:"shopping"`
	Rental   []AddressInfo `json:"rental"`
	Market   []AddressInfo `json:"market"`
}

// Root 對應 JSON 回應結構
type Root struct {
	Data Data `json:"data"`
}

// Point 對應 JSON 輸入
type Point struct {
	X float64 `json:"x"` // 修正拼寫錯誤：float -> float64
	Y float64 `json:"y"` // 修正拼寫錯誤：falot -> float64
}

// GetInfos 查詢 1.6 公里範圍內的記錄
// GET /scope/info
func GetInfos(c *gin.Context) {
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

	lib_data := make([]AddressInfo, 0)
	hospital_data := make([]AddressInfo, 0)
	shopping_data := make([]AddressInfo, 0)
	rental_data := make([]AddressInfo, 0)
	market_data := make([]AddressInfo, 0)
	p := geo.NewPoint(point.X, point.Y)
	// 查詢各表
	var t_libraries []TLibrary
	result := db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&t_libraries)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for t_library: " + err.Error()})
		return
	}
	for _, d := range t_libraries {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			lib_data = append(lib_data, d.AddressInfo)
		}
	}

	var nt_libraries []NTLibrary
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&nt_libraries)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for nt_library: " + err.Error()})
		return
	}
	for _, d := range nt_libraries {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			lib_data = append(lib_data, d.AddressInfo)
		}
	}

	var t_hospitals []THospital
	var nt_hospitals []NTHospital
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&t_hospitals)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range t_hospitals {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			hospital_data = append(hospital_data, d.AddressInfo)
		}
	}
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&nt_hospitals)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range nt_hospitals {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			hospital_data = append(hospital_data, d.AddressInfo)
		}
	}

	var t_shoppings []Tshopping
	var nt_shoppings []NTshopping
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&t_shoppings)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range t_shoppings {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			shopping_data = append(shopping_data, d.AddressInfo)
		}
	}
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&nt_shoppings)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range nt_shoppings {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			shopping_data = append(shopping_data, d.AddressInfo)
		}
	}

	var rentals []Rental
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&rentals)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range rentals {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			rental_data = append(rental_data, d.AddressInfo)
		}
	}

	var t_markets []TMarket
	var nt_markets []NTMarket
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&t_markets)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range t_markets {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			market_data = append(market_data, d.AddressInfo)
		}
	}
	result = db.Select("DISTINCT x, y").Where("X > ? AND X < ? AND Y > ? AND Y < ?",
		xLower, xHigher, yLower, yHigher).Find(&nt_markets)
	if result.Error != nil {
		c.JSON(500, gin.H{"error": "Query failed for library: " + err.Error()})
		return
	}
	for _, d := range nt_markets {
		if p.DistanceFrom(geo.NewPoint(d.X, d.Y)) <= distance {
			market_data = append(market_data, d.AddressInfo)
		}
	}

	// 構建回應
	root := Root{
		Data: Data{
			Library:  lib_data,
			Hospital: hospital_data,
			Shopping: shopping_data,
			Rental:   rental_data,
			Market:   market_data,
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

// calculateSquareBounds 計算 1.6 公里範圍的經緯度邊界
func calculateSquareBounds(lat, lon, distance float64) (xLower, xHigher, yLower, yHigher float64) {
	const earthRadiusKm = 6371.0
	delta := distance / earthRadiusKm
	latRad := lat * math.Pi / 180
	lonRad := lon * math.Pi / 180
	yLowerRad := latRad - delta
	yHigherRad := latRad + delta
	yLower = yLowerRad * 180 / math.Pi
	yHigher = yHigherRad * 180 / math.Pi
	deltaLon := delta / math.Cos(latRad)
	xLowerRad := lonRad - deltaLon
	xHigherRad := lonRad + deltaLon
	xLower = xLowerRad * 180 / math.Pi
	xHigher = xHigherRad * 180 / math.Pi
	return xLower, xHigher, yLower, yHigher
}
