package models

import "time"

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

// ─── C3: alert-trend-30d (three_d, from history table) ──────────────────────

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
