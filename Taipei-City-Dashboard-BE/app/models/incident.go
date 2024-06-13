package models

import (
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"
)

type Incident struct {
	ID          int64     `gorm:"primaryKey"`
	Type        string    `json:"inctype"`
	Description string    `json:"description"`
	Distance    float64   `json:"distance"`
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	Place       string    `json:"place"`
	Time        time.Time `json:"reportTime"`
	Status      string    `json:"status"`
}

type PlaceResponse struct {
	CtyName     string `xml:"ctyName"`
	TownName    string `xml:"townName"`
	SectName    string `xml:"sectName"`
	VillageName string `xml:"villageName"`
}

func GetAllIncident(pageSize int, pageNum int, filterByStatus string, sort string, order string) (incidents []Incident, totalIncidents int64, resultNum int64, err error) {
	tempDB := DBManager.Table("incidents")

	// Count the total amount of incidents
	tempDB.Count(&totalIncidents)

	// Filter by status
	if filterByStatus != "" {
		statuses := strings.Split(filterByStatus, ",")
		tempDB = tempDB.Where("incidents.status IN (?)", statuses)
	}

	tempDB.Count(&resultNum)

	// Sort the issues
	if sort != "" {
		tempDB = tempDB.Order(sort + " " + order)
	}

	// Paginate the issues
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	// Get the incidents
	err = tempDB.Find(&incidents).Error

	return incidents, totalIncidents, resultNum, err
}

func GetLocationData(latitude, longitude float64) (*PlaceResponse, error) {
	/* This API currently doesn't work in production. Needs fixing. */
	// Fetch location
	apiURL := fmt.Sprintf(
		"https://api.nlsc.gov.tw/other/TownVillagePointQuery/%s/%s",
		strconv.FormatFloat(longitude, 'f', -1, 64),
		strconv.FormatFloat(latitude, 'f', -1, 64),
	)
	resp, err := http.Get(apiURL)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var locationData PlaceResponse
	if err := xml.Unmarshal(body, &locationData); err != nil {
		return nil, fmt.Errorf("failed to parse XML: %w", err)
	}

	return &locationData, nil
}

func CreateIncident(incidentType, description string, distance, latitude, longitude float64, status string) (incident Incident, err error) {
	locationData, err := GetLocationData(latitude, longitude)
	if err != nil {
		fmt.Printf("Error fetching location data: %v\n", err)
		return
	}
	place := locationData.CtyName + locationData.TownName + locationData.SectName + locationData.VillageName

	incident = Incident{
		Type:        incidentType,
		Description: description,
		Distance:    distance,
		Latitude:    latitude,
		Longitude:   longitude,
		Place:       place,
		Time:        time.Now(),
		Status:      status,
	}
	// Insert the incident into the database
	err = DBManager.Create(&incident).Error
	return incident, err
}

func UpdateIncidentByID(id string, status string) (incident Incident, err error) {
	// Only update status by admin
	incident.Status = status

	err = DBManager.Table("incidents").Where("id = ?", id).Updates(&incident).Error
	return incident, err
}

func DeleteIncident(id int64) (incident Incident, err error) {
	if err := DBManager.Where("ID = ?", id).First(&incident).Error; err != nil {
		// Handle error (e.g., incident not found)
		fmt.Printf("Incident not found")
		return Incident{}, err
	}

	// Delete the incident
	err = DBManager.Delete(&incident).Error
	return incident, err
}
