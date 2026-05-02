package models

import (
	"encoding/json"
	"fmt"
	"regexp"
)

var dashboardTableNamePattern = regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_]*$`)

type geoJSONResult struct {
	GeoJSON string `gorm:"column:geojson"`
}

func GetMapGeoJSON(tableName string) (json.RawMessage, error) {
	if !dashboardTableNamePattern.MatchString(tableName) {
		return nil, fmt.Errorf("invalid map data table name")
	}

	query := fmt.Sprintf(`
		SELECT json_build_object(
			'type', 'FeatureCollection',
			'features', COALESCE(json_agg(
				json_build_object(
					'type', 'Feature',
					'geometry', ST_AsGeoJSON(wkb_geometry)::json,
					'properties', to_jsonb(t) - 'wkb_geometry'
				)
			), '[]'::json)
		)::text AS geojson
		FROM public.%s t
		WHERE wkb_geometry IS NOT NULL
	`, tableName)

	var result geoJSONResult
	if err := DBDashboard.Raw(query).Scan(&result).Error; err != nil {
		return nil, err
	}
	if result.GeoJSON == "" {
		return json.RawMessage(`{"type":"FeatureCollection","features":[]}`), nil
	}
	return json.RawMessage(result.GeoJSON), nil
}
