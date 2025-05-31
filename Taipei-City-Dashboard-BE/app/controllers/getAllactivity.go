package controllers

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type dbConfig struct {
	Host     string
	Port     int
	User     string
	DBName   string
	Password string
}
type Activity struct {
	ID      int     `json:"Id" gorm:"column:id"`
	Name    string  `json:"Name" gorm:"column:title"`
	Address string  `json:"Address" gorm:"column:address"`
	X       float32 `json:"X" gorm:"column:x"`
	Y       float32 `json:"Y" gorm:"column:y"`
}

type ActivityResponse struct {
	Data struct {
		Activity []Activity `json:"activity"`
	} `json:"data"`
}

func (Activity) TableName() string {
	return "t_activity"
}

func GetAllActivityHandler(c *gin.Context) {

	dbargs := dbConfig{
		Host:     "codefest2025.rm-rf.uk",
		Port:     5433,
		User:     "postgres",
		DBName:   "dashboard",
		Password: "mGPuAE2JTDDmdui8",
	}

	dsn := fmt.Sprintf("host=%s port=%d user=%s dbname=%s password=%s sslmode=disable",
		dbargs.Host,
		dbargs.Port,
		dbargs.User,
		dbargs.DBName,
		dbargs.Password,
	)
	// Establish a connection to the database using gorm.Open and the constructed connection string
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic("failed to connect to database")
	}
	// Query all activities
	var allActivities []Activity

	// Fetch from t_activity
	var tActivities []Activity
	if err := db.Table("t_activity").Distinct("title", "address").Select("id, title, address, x, y").Find(&tActivities).Error; err != nil {
		log.Fatal("error querying t_activity:", err)
	}

	// Fetch from nt_activity
	var ntActivities []Activity
	if err := db.Table("nt_activity").Distinct("title", "address").Select("id, title, address, x, y").Find(&ntActivities).Error; err != nil {
		log.Fatal("error querying nt_activity:", err)
	}

	// Combine both
	allActivities = append(tActivities, ntActivities...)

	// Create response
	response := ActivityResponse{}
	response.Data.Activity = allActivities

	// Marshal to JSON
	jsonData, err := json.MarshalIndent(response, "", "  ")
	if err != nil {
		log.Fatal("failed to marshal JSON:", err)
	}

	c.JSON(http.StatusOK, string(jsonData)) 

}
