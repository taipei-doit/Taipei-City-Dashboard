package controllers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func WriteMap(c *gin.Context) {
	var data any
	if err := c.ShouldBindJSON(&data); err != nil {
		fmt.Println(err)
	}

	// Open a file for writing (create if not exists, truncate if exists)
	file, err := os.Create("incident.geojson")
	if err != nil {
		fmt.Println("Error creating file:", err)
		return
	}
	defer file.Close()

	// Create a JSON encoder using the file as the output destination
	encoder := json.NewEncoder(file)

	// Encode the struct to JSON and write it to the file
	if err := encoder.Encode(data); err != nil {
		fmt.Println("Error encoding JSON:", err)
		return
	}

	fmt.Println("JSON data written to person.json")	
	c.JSON(http.StatusOK, gin.H{"message": "data write success"})	
}
