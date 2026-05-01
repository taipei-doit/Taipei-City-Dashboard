package models

import (
	"math"
	"time"
)

// ─── Row shapes (for GORM scanning) ─────────────────────────────────────────

// MrtA11yAlertCount is the row shape for the alert-count query (two_d).
type MrtA11yAlertCount struct {
	Xaxis string  `gorm:"column:x_axis" json:"x"`
	Data  float64 `gorm:"column:data"   json:"y"`
}

// mrtA11yLineCountRow is the raw row shape for line-grouped counts (C2, C3).
type mrtA11yLineCountRow struct {
	Xaxis string `gorm:"column:x_axis"`
	Icon  string `gorm:"column:icon"`
	Yaxis string `gorm:"column:y_axis"`
	Data  int    `gorm:"column:data"`
}

// MrtA11yStation is the row shape for the station overview map data (C4).
// Each row represents one elevator/ramp exit, joined with its latest active alert if any.
type MrtA11yStation struct {
	Station          string     `gorm:"column:station"            json:"station"`
	ExitNo           string     `gorm:"column:exit_no"            json:"exit_no"`
	FacilityName     string     `gorm:"column:facility_name"      json:"facility_name"`
	FacilityType     string     `gorm:"column:facility_type"      json:"facility_type"`
	Lng              float64    `gorm:"column:lng"                json:"lng"`
	Lat              float64    `gorm:"column:lat"                json:"lat"`
	AlertStatus      string     `gorm:"column:alert_status"       json:"alert_status"`
	AlertDescription *string    `gorm:"column:alert_description"  json:"alert_description,omitempty"`
	AlertPublishTime *time.Time `gorm:"column:alert_publish_time" json:"alert_publish_time,omitempty"`
}

// ─── C1: alert-count (two_d) ────────────────────────────────────────────────

// GetMrtAlertCount returns the number of currently active accessibility alerts.
func GetMrtAlertCount() ([]TwoDimensionalDataOutput, error) {
	var rows []MrtA11yAlertCount
	err := DBDashboard.Raw(`
		SELECT '今日異常公告' AS x_axis, COUNT(*)::float AS data
		FROM mrtp_a11y_alert
		WHERE status = 'active'
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	out := make([]TwoDimensionalData, len(rows))
	for i, r := range rows {
		out[i] = TwoDimensionalData{Xaxis: r.Xaxis, Data: r.Data}
	}
	return []TwoDimensionalDataOutput{{Data: out}}, nil
}

// ─── C2: alert-by-line (three_d) ────────────────────────────────────────────

// GetMrtAlertByLine returns active-alert distinct station counts grouped by MRT line.
func GetMrtAlertByLine() (data []ThreeDimensionalDataOutput, categories []string, err error) {
	var rows []mrtA11yLineCountRow
	err = DBDashboard.Raw(`
		SELECT line AS x_axis, '' AS icon, '異常站數' AS y_axis,
		       COUNT(DISTINCT station)::int AS data
		FROM mrtp_a11y_alert
		WHERE status = 'active'
		GROUP BY line
		ORDER BY data DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	return groupLineRows(rows)
}

// ─── C3: alert-by-type (three_d, JOIN elevator for facility_type) ──────────

// GetMrtAlertByType returns active-alert distinct station counts grouped by facility type.
// alert table 沒有 facility_type，需 JOIN elevator ON station 取得設施類型。
// type 用 CASE 直接 mapping 成中文 label，與 alert-by-line 的 line 中文化作風一致。
func GetMrtAlertByType() (data []ThreeDimensionalDataOutput, categories []string, err error) {
	var rows []mrtA11yLineCountRow
	err = DBDashboard.Raw(`
		SELECT
			CASE e.facility_type
				WHEN 'elevator' THEN '電梯'
				WHEN 'ramp'     THEN '坡道'
				ELSE '其他'
			END                            AS x_axis,
			''                             AS icon,
			'異常設施數'                   AS y_axis,
			COUNT(DISTINCT e.station)::int AS data
		FROM mrtp_a11y_elevator e
		JOIN mrtp_a11y_alert a
		  ON a.station = e.station AND a.status = 'active'
		GROUP BY e.facility_type
		ORDER BY data DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	return groupLineRows(rows)
}

// ─── C3-history: alert-trend-30d (three_d, from history table) ─────────────

// GetMrtAlertTrend30d returns count of distinct alert events per line over the last 30 days.
// DISTINCT (publish_time, line, station, description) deduplicates the 15-min snapshots
// that current+history load_behavior accumulates in the history table.
func GetMrtAlertTrend30d() (data []ThreeDimensionalDataOutput, categories []string, err error) {
	var rows []mrtA11yLineCountRow
	err = DBDashboard.Raw(`
		SELECT line AS x_axis, '' AS icon, '近30天公告數' AS y_axis,
		       COUNT(*)::int AS data
		FROM (
			SELECT DISTINCT publish_time, line, station, description
			FROM mrtp_a11y_alert_history
			WHERE data_time >= NOW() - INTERVAL '30 days'
		) t
		GROUP BY line
		ORDER BY data DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	return groupLineRows(rows)
}

// MrtA11yActiveAlert is the row shape for a single active公告 record from
// `mrtp_a11y_alert`, used to feed the LLM with the raw公告 text so it can
// answer "which stations are abnormal right now and why".
type MrtA11yActiveAlert struct {
	Line        string     `gorm:"column:line"         json:"line"`
	Station     string     `gorm:"column:station"      json:"station"`
	PublishTime *time.Time `gorm:"column:publish_time" json:"publish_time,omitempty"`
	Description string     `gorm:"column:description"  json:"description"`
}

// GetActiveAlerts returns every currently-active accessibility alert as raw
// rows from `mrtp_a11y_alert`. The result is small (typically a handful of
// rows) and is intended to be JSON-serialized into an LLM system prompt.
func GetActiveAlerts() ([]MrtA11yActiveAlert, error) {
	var rows []MrtA11yActiveAlert
	err := DBDashboard.Raw(`
		SELECT line, station, publish_time, description
		FROM mrtp_a11y_alert
		WHERE status = 'active'
		ORDER BY publish_time DESC NULLS LAST, line, station
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return rows, nil
}

// ─── C4: stations (point array) ─────────────────────────────────────────────

// GetMrtStations returns every elevator/ramp exit point joined with its latest active alert (if any).
// FE renders one map marker per row, colored by alert_status ('active' = red, 'normal' = green).
func GetMrtStations() ([]MrtA11yStation, error) {
	var rows []MrtA11yStation
	err := DBDashboard.Raw(`
		SELECT
			e.station,
			e.exit_no,
			e.facility_name,
			e.facility_type,
			e.lng,
			e.lat,
			COALESCE(a.status, 'normal') AS alert_status,
			a.description                AS alert_description,
			a.publish_time               AS alert_publish_time
		FROM mrtp_a11y_elevator e
		LEFT JOIN LATERAL (
			SELECT status, description, publish_time
			FROM mrtp_a11y_alert
			WHERE station = e.station AND status = 'active'
			ORDER BY publish_time DESC
			LIMIT 1
		) a ON TRUE
		-- Active first (regardless of alphabetical order of the status string).
		ORDER BY (COALESCE(a.status, 'normal') = 'active') DESC, e.station, e.exit_no
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return rows, nil
}

// ─── C4-nearby: stations within radius (Haversine filter) ─────────────────

// MrtA11yStationNearby augments MrtA11yStation with the great-circle distance
// (in meters) from the user's query coordinate, so the LLM can reason about
// "closest" / "furthest" without re-deriving it.
type MrtA11yStationNearby struct {
	MrtA11yStation
	DistanceM int `json:"distance_m"`
}

// GetMrtStationsNearby returns elevator/ramp exits within radiusM meters of (lat, lng),
// sorted by ascending distance. Filtering is done in Go because the dataset is small
// (~hundreds of rows) and `mrtp_a11y_elevator` has no spatial index.
func GetMrtStationsNearby(lat, lng float64, radiusM int) ([]MrtA11yStationNearby, error) {
	all, err := GetMrtStations()
	if err != nil {
		return nil, err
	}
	out := make([]MrtA11yStationNearby, 0)
	for _, s := range all {
		d := haversineMeters(lat, lng, s.Lat, s.Lng)
		if d <= float64(radiusM) {
			out = append(out, MrtA11yStationNearby{
				MrtA11yStation: s,
				DistanceM:      int(math.Round(d)),
			})
		}
	}
	for i := 1; i < len(out); i++ {
		for j := i; j > 0 && out[j-1].DistanceM > out[j].DistanceM; j-- {
			out[j-1], out[j] = out[j], out[j-1]
		}
	}
	return out, nil
}

// haversineMeters returns the great-circle distance (meters) between two WGS84 points.
func haversineMeters(lat1, lng1, lat2, lng2 float64) float64 {
	const earthRadiusM = 6371000.0
	rad := func(d float64) float64 { return d * math.Pi / 180 }
	dLat := rad(lat2 - lat1)
	dLng := rad(lng2 - lng1)
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(rad(lat1))*math.Cos(rad(lat2))*math.Sin(dLng/2)*math.Sin(dLng/2)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
	return earthRadiusM * c
}

// ─── C4-overview: station-overview (legend cards) ──────────────────────────

// MrtA11yStationOverviewItem is one legend card row.
type MrtA11yStationOverviewItem struct {
	Name  string `json:"name"`
	Type  string `json:"type"`
	Icon  string `json:"icon"`
	Value int    `json:"value"`
}

// GetMrtStationOverview returns a 2-row alert / normal summary of distinct stations.
// elevator 表是「全部站」基準集合；alert 表 (status='active') 標記哪些站目前有異常公告。
func GetMrtStationOverview() ([]MrtA11yStationOverviewItem, error) {
	var row struct {
		AlertCount  int `gorm:"column:alert_count"`
		NormalCount int `gorm:"column:normal_count"`
	}
	err := DBDashboard.Raw(`
		WITH stations AS (
			SELECT DISTINCT station FROM mrtp_a11y_elevator
		),
		alert_stations AS (
			SELECT DISTINCT station FROM mrtp_a11y_alert WHERE status = 'active'
		)
		SELECT
			(SELECT COUNT(*) FROM stations s WHERE     EXISTS (SELECT 1 FROM alert_stations a WHERE a.station = s.station)) AS alert_count,
			(SELECT COUNT(*) FROM stations s WHERE NOT EXISTS (SELECT 1 FROM alert_stations a WHERE a.station = s.station)) AS normal_count
	`).Scan(&row).Error
	if err != nil {
		return nil, err
	}
	return []MrtA11yStationOverviewItem{
		{Name: "異常", Type: "alert", Icon: "mrt_station", Value: row.AlertCount},
		{Name: "正常", Type: "normal", Icon: "mrt_station", Value: row.NormalCount},
	}, nil
}

// ─── helpers ────────────────────────────────────────────────────────────────

// groupLineRows reshapes flat line-count rows into the standard three_d response
// (one series per y_axis value, with categories collected from x_axis).
func groupLineRows(rows []mrtA11yLineCountRow) (data []ThreeDimensionalDataOutput, categories []string, err error) {
	for _, r := range rows {
		categories = append(categories, r.Xaxis)
		var found bool
		for i := range data {
			if data[i].Name == r.Yaxis {
				data[i].Data = append(data[i].Data, r.Data)
				found = true
				break
			}
		}
		if !found {
			data = append(data, ThreeDimensionalDataOutput{Name: r.Yaxis, Icon: r.Icon, Data: []int{r.Data}})
		}
	}
	if categories == nil {
		categories = []string{}
	}
	return data, categories, nil
}
