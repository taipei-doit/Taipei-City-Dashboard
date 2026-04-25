package models

// MrtA11yAlertCount is the row shape for the alert-count query (two_d).
type MrtA11yAlertCount struct {
	Xaxis string  `gorm:"column:x_axis" json:"x"`
	Data  float64 `gorm:"column:data" json:"y"`
}

// MrtA11yAlertByLine is the raw row shape for the by-line query (three_d).
type MrtA11yAlertByLine struct {
	Xaxis string `gorm:"column:x_axis"`
	Icon  string `gorm:"column:icon"`
	Yaxis string `gorm:"column:y_axis"`
	Data  int    `gorm:"column:data"`
}

// MrtA11yStationOverview is the row shape for the station-overview query (map_legend).
type MrtA11yStationOverview struct {
	Name  string  `gorm:"column:name"  json:"name"`
	Type  string  `gorm:"column:type"  json:"type"`
	Icon  string  `gorm:"column:icon"  json:"icon"`
	Value float64 `gorm:"column:value" json:"value"`
}

// GetMrtAlertCount returns total active alert count for C1 (two_d card).
func GetMrtAlertCount() ([]TwoDimensionalDataOutput, error) {
	var rows []MrtA11yAlertCount
	err := DBDashboard.Raw(`
		SELECT '今日異常設施' AS x_axis, COUNT(*)::float AS data
		FROM mrt_a11y_alert_tpe
		WHERE status = 'active'
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return []TwoDimensionalDataOutput{{Data: func() []TwoDimensionalData {
		out := make([]TwoDimensionalData, len(rows))
		for i, r := range rows {
			out[i] = TwoDimensionalData{Xaxis: r.Xaxis, Data: r.Data}
		}
		return out
	}()}}, nil
}

// GetMrtAlertByLine returns per-line abnormal station counts for C2 (three_d bar).
func GetMrtAlertByLine() (data []ThreeDimensionalDataOutput, categories []string, err error) {
	var rows []MrtA11yAlertByLine
	err = DBDashboard.Raw(`
		SELECT line AS x_axis, '' AS icon, '異常站數' AS y_axis,
		       COUNT(DISTINCT station)::int AS data
		FROM mrt_a11y_alert_tpe
		WHERE status = 'active'
		GROUP BY line
		ORDER BY data DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	// Group by y_axis (series name) and collect x_axis as categories.
	for _, r := range rows {
		categories = append(categories, r.Xaxis)
		var found bool
		for i, d := range data {
			if d.Name == r.Yaxis {
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

// GetMrtAlertByType returns per-equipment-type counts for C3 (percent pie).
// Response shape is identical to three_d; query_type "percent" controls FE rendering.
func GetMrtAlertByType() (data []ThreeDimensionalDataOutput, categories []string, err error) {
	var rows []MrtA11yAlertByLine
	err = DBDashboard.Raw(`
		SELECT equipment_type AS x_axis, '' AS icon, equipment_type AS y_axis,
		       COUNT(*)::int AS data
		FROM mrt_a11y_alert_tpe
		WHERE status = 'active'
		GROUP BY equipment_type
		ORDER BY data DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, nil, err
	}
	for _, r := range rows {
		categories = append(categories, r.Xaxis)
		data = append(data, ThreeDimensionalDataOutput{
			Name: r.Yaxis,
			Icon: r.Icon,
			Data: []int{r.Data},
		})
	}
	if len(categories) == 0 {
		categories = []string{}
	}
	return data, categories, nil
}

// GetMrtStationOverview returns normal/alert station legend counts for C4 (map_legend).
func GetMrtStationOverview() ([]MrtA11yStationOverview, error) {
	var rows []MrtA11yStationOverview
	err := DBDashboard.Raw(`
		WITH alerted AS (
			SELECT DISTINCT station FROM mrt_a11y_alert_tpe WHERE status = 'active'
		)
		SELECT
			CASE WHEN a.station IS NOT NULL THEN '異常' ELSE '正常' END AS name,
			CASE WHEN a.station IS NOT NULL THEN 'alert' ELSE 'normal' END AS type,
			'mrt_station' AS icon,
			COUNT(*)::float AS value
		FROM (SELECT DISTINCT station FROM mrt_a11y_elevator_tpe) e
		LEFT JOIN alerted a ON e.station = a.station
		GROUP BY name, type, icon
		ORDER BY type DESC
	`).Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	return rows, nil
}
