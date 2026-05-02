// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync"

	"github.com/gin-gonic/gin"
)

// NavigationGeoJSONRequest represents the request body for navigation GeoJSON endpoint
type NavigationGeoJSONRequest struct {
	Type     string                 `json:"type" binding:"required,eq=FeatureCollection"`
	Features []interface{}          `json:"features" binding:"required"`
	Bbox     []float64              `json:"bbox,omitempty"`
	Crs      map[string]interface{} `json:"crs,omitempty"`
	Files    []string               `json:"files,omitempty"` // List of reference files to check for overlap
}

// NavigationGeoJSONResponse represents the response body for navigation GeoJSON endpoint
type NavigationGeoJSONResponse struct {
	Status        string                 `json:"status"`
	FeatureCount  int                    `json:"feature_count"`
	GeometryTypes map[string]int         `json:"geometry_types"`
	BoundingBox   []float64              `json:"bounding_box,omitempty"`
	Properties    map[string]interface{} `json:"properties,omitempty"`
	Overlaps      []OverlapResult        `json:"overlaps,omitempty"` // Overlap detection results
	Message       string                 `json:"message,omitempty"`
}

// OverlapResult holds the result of an overlap check against a reference file
type OverlapResult struct {
	ReferenceFile       string        `json:"reference_file"`
	OverlappingFeatures []interface{} `json:"overlapping_features"` // Actual overlapping geometries
	OverlapCount        int           `json:"overlap_count"`
}

// Cache for loaded GeoJSON files to avoid repeated disk reads
var geoJSONCache = map[string]interface{}{}
var cacheMutex sync.RWMutex

// HandleNavigationGeoJSON processes incoming navigation GeoJSON data
// POST /api/v1/navigation/geojson
func HandleNavigationGeoJSON(c *gin.Context) {
	var navReq NavigationGeoJSONRequest
	if err := c.ShouldBindJSON(&navReq); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"status":  "error",
			"message": "Invalid GeoJSON format: " + err.Error(),
		})
		return
	}

	// Initialize response
	response := NavigationGeoJSONResponse{
		Status:        "success",
		FeatureCount:  len(navReq.Features),
		GeometryTypes: make(map[string]int),
		Properties:    make(map[string]interface{}),
		Message:       "GeoJSON processed successfully",
	}

	// Process features to extract statistics
	var allCoords [][]float64
	hasValidCoords := false

	for _, feature := range navReq.Features {
		featureMap, ok := feature.(map[string]interface{})
		if !ok {
			continue
		}

		geometry, ok := featureMap["geometry"].(map[string]interface{})
		if !ok {
			continue
		}

		geomType, ok := geometry["type"].(string)
		if !ok {
			continue
		}

		response.GeometryTypes[geomType]++

		if coordinates, ok := geometry["coordinates"].(interface{}); ok {
			coords := extractCoordinates(coordinates)
			if len(coords) > 0 {
				allCoords = append(allCoords, coords...)
				hasValidCoords = true
			}
		}

		if properties, ok := featureMap["properties"].(map[string]interface{}); ok {
			for key, value := range properties {
				if _, exists := response.Properties[key]; !exists {
					response.Properties[key] = value
				}
			}
		}
	}

	// Calculate bounding box if we have valid coordinates
	if hasValidCoords && len(allCoords) > 0 {
		minX, minY, maxX, maxY := allCoords[0][0], allCoords[0][1], allCoords[0][0], allCoords[0][1]

		for _, coord := range allCoords {
			if len(coord) >= 2 {
				if coord[0] < minX {
					minX = coord[0]
				}
				if coord[0] > maxX {
					maxX = coord[0]
				}
				if coord[1] < minY {
					minY = coord[1]
				}
				if coord[1] > maxY {
					maxY = coord[1]
				}
			}
		}

		response.BoundingBox = []float64{minX, minY, maxX, maxY}
	}

	// Check if overlap detection is requested
	if len(navReq.Files) > 0 {
		overlapResults, err := processOverlapDetection(navReq.Features, navReq.Files)
		if err != nil {
			response.Overlaps = []OverlapResult{}
		} else {
			response.Overlaps = overlapResults
		}
	} else {
		files, err := getGeoJSONFilesInPipeline()
		if err != nil {
			response.Overlaps = []OverlapResult{}
		} else if len(files) > 0 {
			overlapResults, err := processOverlapDetection(navReq.Features, files)
			if err != nil {
				response.Overlaps = []OverlapResult{}
			} else {
				response.Overlaps = overlapResults
			}
		}
	}

	c.JSON(http.StatusOK, response)
}

// processOverlapDetection checks for overlaps between features and reference files
func processOverlapDetection(navFeatures []interface{}, referenceFiles []string) ([]OverlapResult, error) {
	var results []OverlapResult

	for _, refFile := range referenceFiles {
		refData, err := loadGeoJSONFile(refFile)
		if err != nil {
			continue
		}

		refFeatures, err := extractFeaturesFromGeoJSON(refData)
		if err != nil {
			continue
		}

		var overlappingFeatures []interface{}
		for _, navFeature := range navFeatures {
			for _, refFeature := range refFeatures {
				if geometriesOverlap(navFeature, refFeature) {
					if intersection := calculateIntersection(navFeature, refFeature); intersection != nil {
						overlappingFeatures = append(overlappingFeatures, intersection)
					}
				}
			}
		}

		if len(overlappingFeatures) > 0 {
			results = append(results, OverlapResult{
				ReferenceFile:       refFile,
				OverlappingFeatures: overlappingFeatures,
				OverlapCount:        len(overlappingFeatures),
			})
		}
	}

	return results, nil
}

// loadGeoJSONFile loads and caches a GeoJSON file
func loadGeoJSONFile(filename string) (interface{}, error) {
	cacheMutex.RLock()
	if data, exists := geoJSONCache[filename]; exists {
		cacheMutex.RUnlock()
		return data, nil
	}
	cacheMutex.RUnlock()

	// Use fullPath to avoid shadowing the filepath package
	fullPath := filepath.Join("pipeline", filename)
	raw, err := os.ReadFile(fullPath)
	if err != nil {
		return nil, err
	}

	var parsed interface{}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		return nil, err
	}

	cacheMutex.Lock()
	geoJSONCache[filename] = parsed
	cacheMutex.Unlock()

	return parsed, nil
}

// getGeoJSONFilesInPipeline returns all .geojson files in the pipeline directory
func getGeoJSONFilesInPipeline() ([]string, error) {
	files, err := filepath.Glob(filepath.Join("pipeline", "*.geojson"))
	if err != nil {
		return nil, err
	}

	var result []string
	for _, file := range files {
		result = append(result, filepath.Base(file))
	}
	return result, nil
}

// extractFeaturesFromGeoJSON extracts the features array from parsed GeoJSON data
func extractFeaturesFromGeoJSON(data interface{}) ([]interface{}, error) {
	geoJSON, ok := data.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid GeoJSON structure")
	}

	features, ok := geoJSON["features"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("no features found in GeoJSON")
	}

	return features, nil
}

// geometriesOverlap checks if two GeoJSON feature geometries overlap via bounding box
func geometriesOverlap(geom1, geom2 interface{}) bool {
	g1Map, ok1 := geom1.(map[string]interface{})
	g2Map, ok2 := geom2.(map[string]interface{})
	if !ok1 || !ok2 {
		return false
	}

	geom1Map, ok1 := g1Map["geometry"].(map[string]interface{})
	geom2Map, ok2 := g2Map["geometry"].(map[string]interface{})
	if !ok1 || !ok2 {
		return false
	}

	return boundingBoxesOverlap(geom1Map["coordinates"], geom2Map["coordinates"])
}

// boundingBoxesOverlap checks if the bounding boxes of two coordinate sets overlap
func boundingBoxesOverlap(coords1, coords2 interface{}) bool {
	bbox1 := calculateBoundingBox(coords1)
	bbox2 := calculateBoundingBox(coords2)

	if len(bbox1) != 4 || len(bbox2) != 4 {
		return false
	}

	if bbox1[2] < bbox2[0] || bbox2[2] < bbox1[0] {
		return false
	}
	if bbox1[3] < bbox2[1] || bbox2[3] < bbox1[1] {
		return false
	}

	return true
}

// calculateBoundingBox calculates the bounding box [minX, minY, maxX, maxY] for coordinates
func calculateBoundingBox(coords interface{}) []float64 {
	var minX, minY, maxX, maxY float64
	initialized := false

	var processCoords func(interface{})
	processCoords = func(c interface{}) {
		switch v := c.(type) {
		case []interface{}:
			if len(v) == 2 {
				x, ok1 := v[0].(float64)
				y, ok2 := v[1].(float64)
				if ok1 && ok2 {
					if !initialized {
						minX, maxX, minY, maxY = x, x, y, y
						initialized = true
					} else {
						if x < minX {
							minX = x
						}
						if x > maxX {
							maxX = x
						}
						if y < minY {
							minY = y
						}
						if y > maxY {
							maxY = y
						}
					}
				}
			} else {
				for _, item := range v {
					processCoords(item)
				}
			}
		case map[string]interface{}:
			for _, value := range v {
				processCoords(value)
			}
		}
	}

	processCoords(coords)

	if !initialized {
		return []float64{0, 0, 0, 0}
	}
	return []float64{minX, minY, maxX, maxY}
}

// calculateIntersection returns a placeholder intersection geometry.
// A full implementation would compute actual geometric intersection.
func calculateIntersection(geom1, geom2 interface{}) interface{} {
	return geom1
}

// extractCoordinates recursively extracts coordinate pairs from nested GeoJSON structures
func extractCoordinates(coord interface{}) [][]float64 {
	var result [][]float64

	switch v := coord.(type) {
	case []interface{}:
		if len(v) == 2 {
			if lat, ok1 := v[0].(float64); ok1 {
				if lng, ok2 := v[1].(float64); ok2 {
					result = append(result, []float64{lat, lng})
				}
			}
		} else {
			for _, item := range v {
				result = append(result, extractCoordinates(item)...)
			}
		}
	case map[string]interface{}:
		for _, value := range v {
			result = append(result, extractCoordinates(value)...)
		}
	}

	return result
}