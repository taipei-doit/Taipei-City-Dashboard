package models

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"
)

// CwaStationWind holds the latest wind observation for one automatic weather station.
// Stored in the dashboard DB (table: cwa_auto_station_wind).
type CwaStationWind struct {
	ID               int64    `gorm:"primaryKey;autoIncrement"  json:"id"`
	StationId        string   `gorm:"column:station_id;not null" json:"station_id"`
	StationName      string   `gorm:"column:station_name"        json:"station_name"`
	CountyName       string   `gorm:"column:county_name"         json:"county_name"`
	TownName         string   `gorm:"column:town_name"           json:"town_name"`
	StationAltitude  *float64 `gorm:"column:station_altitude"    json:"station_altitude"`
	Latitude         float64  `gorm:"column:latitude;not null"   json:"latitude"`
	Longitude        float64  `gorm:"column:longitude;not null"  json:"longitude"`
	WindDirection    *float64 `gorm:"column:wind_direction"      json:"wind_direction"`
	WindSpeed        *float64 `gorm:"column:wind_speed"          json:"wind_speed"`
	AirTemperature   *float64 `gorm:"column:air_temperature"     json:"air_temperature"`
	RelativeHumidity *float64 `gorm:"column:relative_humidity"   json:"relative_humidity"`
	AirPressure      *float64 `gorm:"column:air_pressure"        json:"air_pressure"`
	GustSpeed        *float64 `gorm:"column:gust_speed"          json:"gust_speed"`
	GustDirection    *float64 `gorm:"column:gust_direction"      json:"gust_direction"`
	ObsTime          time.Time `gorm:"column:obs_time"           json:"obs_time"`
	UpdatedAt        time.Time `gorm:"column:updated_at;autoUpdateTime" json:"updated_at"`
}

func (CwaStationWind) TableName() string { return "cwa_auto_station_wind" }

// ── CWA API response structs ──────────────────────────────────────────────────

type cwaWindResponse struct {
	Success string `json:"success"`
	Records struct {
		Station []cwaWindStation `json:"Station"`
	} `json:"records"`
}

type cwaWindStation struct {
	StationId   string `json:"StationId"`
	StationName string `json:"StationName"`
	GeoInfo     struct {
		Coordinates []struct {
			CoordinateName   string `json:"CoordinateName"`
			StationLatitude  string `json:"StationLatitude"`
			StationLongitude string `json:"StationLongitude"`
		} `json:"Coordinates"`
		StationAltitude string `json:"StationAltitude"`
		CountyName      string `json:"CountyName"`
		TownName        string `json:"TownName"`
	} `json:"GeoInfo"`
	WeatherElement struct {
		WindDirection    string `json:"WindDirection"`
		WindSpeed        string `json:"WindSpeed"`
		AirTemperature   string `json:"AirTemperature"`
		RelativeHumidity string `json:"RelativeHumidity"`
		AirPressure      string `json:"AirPressure"`
		GustInfo         struct {
			PeakGustSpeed string `json:"PeakGustSpeed"`
			OccurredAt    struct {
				WindDirection string `json:"WindDirection"`
			} `json:"Occurred_at"`
		} `json:"GustInfo"`
	} `json:"WeatherElement"`
	ObsTime struct {
		DateTime string `json:"DateTime"`
	} `json:"ObsTime"`
}

// ── helpers ───────────────────────────────────────────────────────────────────

const cwaNoData = -99.0

// parseFloat converts the string values returned by CWA into *float64.
// Values equal to the CWA "no data" sentinel (-99) are treated as nil.
func parseFloat(s string) *float64 {
	v, err := strconv.ParseFloat(s, 64)
	if err != nil || v == cwaNoData {
		return nil
	}
	return &v
}

// wgs84Coords returns the WGS84 lat/lon from the Coordinates slice.
// Falls back to the first entry when WGS84 is not explicitly labelled.
func wgs84Coords(coords []struct {
	CoordinateName   string `json:"CoordinateName"`
	StationLatitude  string `json:"StationLatitude"`
	StationLongitude string `json:"StationLongitude"`
}) (lat, lon float64, ok bool) {
	parse := func(s string) (float64, bool) {
		v, err := strconv.ParseFloat(s, 64)
		return v, err == nil
	}
	for _, c := range coords {
		if c.CoordinateName == "WGS84" {
			la, okLa := parse(c.StationLatitude)
			lo, okLo := parse(c.StationLongitude)
			if okLa && okLo {
				return la, lo, true
			}
		}
	}
	if len(coords) > 0 {
		la, okLa := parse(coords[0].StationLatitude)
		lo, okLo := parse(coords[0].StationLongitude)
		if okLa && okLo {
			return la, lo, true
		}
	}
	return 0, 0, false
}

// ── public API ────────────────────────────────────────────────────────────────

// FetchAndSaveCwaStationWind fetches O-A0001-001 from the CWA OpenData API,
// then replaces the entire cwa_auto_station_wind table with the latest snapshot.
func FetchAndSaveCwaStationWind() error {
	if global.CWAApiKey == "" {
		return fmt.Errorf("CWA_API_KEY is not set")
	}

	// 1. Fetch
	url := fmt.Sprintf(
		"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=%s&format=JSON",
		global.CWAApiKey,
	)
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("CWA API request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("CWA API returned HTTP %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("reading CWA response body: %w", err)
	}

	var raw cwaWindResponse
	if err := json.Unmarshal(body, &raw); err != nil {
		return fmt.Errorf("parsing CWA JSON: %w", err)
	}
	if raw.Success != "true" {
		return fmt.Errorf("CWA API success=false")
	}
	if len(raw.Records.Station) == 0 {
		return fmt.Errorf("CWA API returned 0 stations")
	}

	// 2. Transform — only keep Taipei City (臺北市) and New Taipei City (新北市)
	records := make([]CwaStationWind, 0, len(raw.Records.Station))
	for _, s := range raw.Records.Station {
		county := s.GeoInfo.CountyName
		if county != "臺北市" && county != "新北市" {
			continue
		}

		lat, lon, ok := wgs84Coords(s.GeoInfo.Coordinates)
		if !ok {
			logs.FInfo("cwa_station_wind: skipping station %s (no coordinates)", s.StationId)
			continue
		}

		obsTime, _ := time.Parse(time.RFC3339, s.ObsTime.DateTime)

		we := s.WeatherElement
		records = append(records, CwaStationWind{
			StationId:        s.StationId,
			StationName:      s.StationName,
			CountyName:       s.GeoInfo.CountyName,
			TownName:         s.GeoInfo.TownName,
			StationAltitude:  parseFloat(s.GeoInfo.StationAltitude),
			Latitude:         lat,
			Longitude:        lon,
			WindDirection:    parseFloat(we.WindDirection),
			WindSpeed:        parseFloat(we.WindSpeed),
			AirTemperature:   parseFloat(we.AirTemperature),
			RelativeHumidity: parseFloat(we.RelativeHumidity),
			AirPressure:      parseFloat(we.AirPressure),
			GustSpeed:        parseFloat(we.GustInfo.PeakGustSpeed),
			GustDirection:    parseFloat(we.GustInfo.OccurredAt.WindDirection),
			ObsTime:          obsTime,
		})
	}

	if len(records) == 0 {
		return fmt.Errorf("no valid station records after parsing")
	}

	// 3. Replace: truncate then bulk-insert
	tx := DBDashboard.Begin()
	if tx.Error != nil {
		return fmt.Errorf("beginning transaction: %w", tx.Error)
	}

	if err := tx.Exec("TRUNCATE TABLE cwa_auto_station_wind").Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("truncating cwa_auto_station_wind: %w", err)
	}

	if err := tx.CreateInBatches(records, 100).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("inserting cwa_auto_station_wind: %w", err)
	}

	if err := tx.Commit().Error; err != nil {
		return fmt.Errorf("committing cwa_auto_station_wind: %w", err)
	}

	logs.FInfo("cwa_station_wind: saved %d stations", len(records))

	if err := writeCwaGeoJSON(records); err != nil {
		logs.FInfo("cwa_station_wind: geojson write failed (non-fatal): %v", err)
	}

	if err := writeCwaStationDensityGeoJSON(); err != nil {
		logs.FInfo("cwa_station_wind: density geojson write failed (non-fatal): %v", err)
	}

	return nil
}

// writeCwaGeoJSON writes the station snapshot as a GeoJSON file for the frontend.
func writeCwaGeoJSON(records []CwaStationWind) error {
	type geometry struct {
		Type        string     `json:"type"`
		Coordinates [2]float64 `json:"coordinates"`
	}
	type properties struct {
		StationId        string   `json:"station_id"`
		StationName      string   `json:"station_name"`
		CountyName       string   `json:"county_name"`
		TownName         string   `json:"town_name"`
		WindSpeed        *float64 `json:"wind_speed"`
		WindDirection    *float64 `json:"wind_direction"`
		AirTemperature   *float64 `json:"air_temperature"`
		RelativeHumidity *float64 `json:"relative_humidity"`
		AirPressure      *float64 `json:"air_pressure"`
		GustSpeed        *float64 `json:"gust_speed"`
		ObsTime          string   `json:"obs_time"`
	}
	type feature struct {
		Type       string     `json:"type"`
		Geometry   geometry   `json:"geometry"`
		Properties properties `json:"properties"`
	}
	type featureCollection struct {
		Type     string    `json:"type"`
		Features []feature `json:"features"`
	}

	features := make([]feature, 0, len(records))
	for _, r := range records {
		features = append(features, feature{
			Type:     "Feature",
			Geometry: geometry{Type: "Point", Coordinates: [2]float64{r.Longitude, r.Latitude}},
			Properties: properties{
				StationId:        r.StationId,
				StationName:      r.StationName,
				CountyName:       r.CountyName,
				TownName:         r.TownName,
				WindSpeed:        r.WindSpeed,
				WindDirection:    r.WindDirection,
				AirTemperature:   r.AirTemperature,
				RelativeHumidity: r.RelativeHumidity,
				AirPressure:      r.AirPressure,
				GustSpeed:        r.GustSpeed,
				ObsTime:          r.ObsTime.Format(time.RFC3339),
			},
		})
	}

	fc := featureCollection{Type: "FeatureCollection", Features: features}
	data, err := json.MarshalIndent(fc, "", "  ")
	if err != nil {
		return err
	}

	outPath := filepath.Join(global.MapDataDir, "cwa_auto_station_wind.geojson")
	return os.WriteFile(outPath, data, 0644)
}

// writeCwaStationDensityGeoJSON reads metrotaipei_town.geojson, joins station
// counts per district from the DB, and writes cwa_station_density.geojson.
func writeCwaStationDensityGeoJSON() error {
	// 1. Read base boundary file
	basePath := filepath.Join(global.MapDataDir, "metrotaipei_town.geojson")
	raw, err := os.ReadFile(basePath)
	if err != nil {
		return fmt.Errorf("reading base geojson: %w", err)
	}

	// Parse as generic map so we preserve all existing fields
	var fc map[string]interface{}
	if err := json.Unmarshal(raw, &fc); err != nil {
		return fmt.Errorf("parsing base geojson: %w", err)
	}

	// 2. Query station counts per town from DB
	type townCount struct {
		TownName string
		Count    int
	}
	var rows []townCount
	if err := DBDashboard.Raw(
		"SELECT town_name, COUNT(*)::int AS count FROM cwa_auto_station_wind GROUP BY town_name",
	).Scan(&rows).Error; err != nil {
		return fmt.Errorf("querying town counts: %w", err)
	}
	counts := make(map[string]int, len(rows))
	for _, r := range rows {
		counts[r.TownName] = r.Count
	}

	// 3. Merge counts into each feature's properties
	features, ok := fc["features"].([]interface{})
	if !ok {
		return fmt.Errorf("features field missing or wrong type")
	}
	for _, f := range features {
		feat, ok := f.(map[string]interface{})
		if !ok {
			continue
		}
		props, ok := feat["properties"].(map[string]interface{})
		if !ok {
			continue
		}
		tname, _ := props["TNAME"].(string)
		pname, _ := props["PNAME"].(string)
		props["station_count"] = counts[tname]
		props["town_name"] = tname
		props["county_name"] = pname
	}

	// 4. Write output
	out, err := json.Marshal(fc)
	if err != nil {
		return err
	}
	outPath := filepath.Join(global.MapDataDir, "cwa_station_density.geojson")
	return os.WriteFile(outPath, out, 0644)
}

// GetCwaStationWindAll returns all rows from cwa_auto_station_wind.
func GetCwaStationWindAll() ([]CwaStationWind, error) {
	var rows []CwaStationWind
	err := DBDashboard.Order("station_id").Find(&rows).Error
	return rows, err
}
