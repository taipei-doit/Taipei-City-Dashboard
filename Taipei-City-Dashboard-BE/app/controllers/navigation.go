// Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
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
	Files    []string               `json:"files,omitempty"`
}

// NavigationGeoJSONResponse represents the response body for navigation GeoJSON endpoint
type NavigationGeoJSONResponse struct {
	Status        string                 `json:"status"`
	FeatureCount  int                    `json:"feature_count"`
	GeometryTypes map[string]int         `json:"geometry_types"`
	BoundingBox   []float64              `json:"bounding_box,omitempty"`
	Properties    map[string]interface{} `json:"properties,omitempty"`
	Overlaps      []OverlapResult        `json:"overlaps,omitempty"`
	Message       string                 `json:"message,omitempty"`
}

// OverlapResult holds reference features that the route crosses
type OverlapResult struct {
	ReferenceFile       string        `json:"reference_file"`
	OverlappingFeatures []interface{} `json:"overlapping_features"` // Reference features crossed by the route
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

	response := NavigationGeoJSONResponse{
		Status:        "success",
		FeatureCount:  len(navReq.Features),
		GeometryTypes: make(map[string]int),
		Properties:    make(map[string]interface{}),
		Message:       "GeoJSON processed successfully",
	}

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

// processOverlapDetection finds reference features that the incoming route crosses.
// For each reference file, it returns the features (e.g. districts, zones) that
// the route geometry intersects.
func processOverlapDetection(navFeatures []interface{}, referenceFiles []string) ([]OverlapResult, error) {
	var results []OverlapResult

	for _, refFile := range referenceFiles {
		refData, err := loadGeoJSONFile(refFile)
		if err != nil {
			log.Printf("[Navigation] 無法載入參考檔案 %s: %v", refFile, err)
			continue
		}

		refFeatures, err := extractFeaturesFromGeoJSON(refData)
		if err != nil {
			log.Printf("[Navigation] 無法解析 features %s: %v", refFile, err)
			continue
		}

		// Collect reference features that the route crosses
		var crossedFeatures []interface{}
		for _, refFeature := range refFeatures {
			for _, navFeature := range navFeatures {
				if routeIntersectsFeature(navFeature, refFeature) {
					crossedFeatures = append(crossedFeatures, refFeature)
					break // 同一個 refFeature 只加一次
				}
			}
		}

		if len(crossedFeatures) > 0 {
			results = append(results, OverlapResult{
				ReferenceFile:       refFile,
				OverlappingFeatures: crossedFeatures,
				OverlapCount:        len(crossedFeatures),
			})
		}
	}

	return results, nil
}

// ─── Geometry Intersection ────────────────────────────────────────────────────

// routeIntersectsFeature checks whether a route feature (LineString) intersects
// a reference feature (Polygon, MultiPolygon, LineString, or Point).
func routeIntersectsFeature(routeFeature, refFeature interface{}) bool {
	routeGeom := extractGeometry(routeFeature)
	refGeom := extractGeometry(refFeature)
	if routeGeom == nil || refGeom == nil {
		return false
	}

	// Quick bounding box rejection
	if !boundingBoxesOverlap(routeGeom["coordinates"], refGeom["coordinates"]) {
		return false
	}

	routeType, _ := routeGeom["type"].(string)
	refType, _ := refGeom["type"].(string)

	// Build route segments from LineString
	var routeSegments [][2][2]float64
	if routeType == "LineString" {
		pts := extractPointList(routeGeom["coordinates"])
		for i := 0; i < len(pts)-1; i++ {
			routeSegments = append(routeSegments, [2][2]float64{pts[i], pts[i+1]})
		}
	}

	switch refType {
	case "Polygon":
		rings := extractRings(refGeom["coordinates"])
		if len(rings) == 0 {
			return false
		}
		outerRing := rings[0]
		// Check segment vs polygon edge intersection
		for _, seg := range routeSegments {
			for i := 0; i < len(outerRing)-1; i++ {
				if segmentsIntersect(seg[0], seg[1], outerRing[i], outerRing[i+1]) {
					return true
				}
			}
		}
		// Check if any route point is inside the polygon
		pts := extractPointList(routeGeom["coordinates"])
		for _, pt := range pts {
			if pointInPolygon(pt, outerRing) {
				return true
			}
		}

	case "MultiPolygon":
		polygons := extractMultiPolygonRings(refGeom["coordinates"])
		for _, rings := range polygons {
			if len(rings) == 0 {
				continue
			}
			outerRing := rings[0]
			for _, seg := range routeSegments {
				for i := 0; i < len(outerRing)-1; i++ {
					if segmentsIntersect(seg[0], seg[1], outerRing[i], outerRing[i+1]) {
						return true
					}
				}
			}
			pts := extractPointList(routeGeom["coordinates"])
			for _, pt := range pts {
				if pointInPolygon(pt, outerRing) {
					return true
				}
			}
		}

	case "LineString":
		refPts := extractPointList(refGeom["coordinates"])
		for _, seg1 := range routeSegments {
			for i := 0; i < len(refPts)-1; i++ {
				if segmentsIntersect(seg1[0], seg1[1], refPts[i], refPts[i+1]) {
					return true
				}
			}
		}

	case "Point":
		pt := extractSinglePoint(refGeom["coordinates"])
		for _, seg := range routeSegments {
			if pointNearSegment(pt, seg[0], seg[1], 0.0001) { // ~10m threshold
				return true
			}
		}
	}

	return false
}

// segmentsIntersect checks whether line segment (p1→p2) intersects (p3→p4)
// using the cross-product method.
func segmentsIntersect(p1, p2, p3, p4 [2]float64) bool {
	d1 := cross(p3, p4, p1)
	d2 := cross(p3, p4, p2)
	d3 := cross(p1, p2, p3)
	d4 := cross(p1, p2, p4)

	if ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
		((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0)) {
		return true
	}

	// Collinear cases
	if d1 == 0 && onSegment(p3, p4, p1) {
		return true
	}
	if d2 == 0 && onSegment(p3, p4, p2) {
		return true
	}
	if d3 == 0 && onSegment(p1, p2, p3) {
		return true
	}
	if d4 == 0 && onSegment(p1, p2, p4) {
		return true
	}

	return false
}

func cross(o, a, b [2]float64) float64 {
	return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
}

func onSegment(p, q, r [2]float64) bool {
	return math.Min(p[0], q[0]) <= r[0] && r[0] <= math.Max(p[0], q[0]) &&
		math.Min(p[1], q[1]) <= r[1] && r[1] <= math.Max(p[1], q[1])
}

// pointInPolygon uses the ray casting algorithm.
func pointInPolygon(pt [2]float64, ring [][2]float64) bool {
	inside := false
	n := len(ring)
	j := n - 1
	for i := 0; i < n; i++ {
		xi, yi := ring[i][0], ring[i][1]
		xj, yj := ring[j][0], ring[j][1]
		if ((yi > pt[1]) != (yj > pt[1])) &&
			(pt[0] < (xj-xi)*(pt[1]-yi)/(yj-yi)+xi) {
			inside = !inside
		}
		j = i
	}
	return inside
}

// pointNearSegment checks if a point is within `threshold` degrees of a segment.
func pointNearSegment(pt, a, b [2]float64, threshold float64) bool {
	dx := b[0] - a[0]
	dy := b[1] - a[1]
	if dx == 0 && dy == 0 {
		return math.Hypot(pt[0]-a[0], pt[1]-a[1]) < threshold
	}
	t := ((pt[0]-a[0])*dx + (pt[1]-a[1])*dy) / (dx*dx + dy*dy)
	t = math.Max(0, math.Min(1, t))
	nearX := a[0] + t*dx
	nearY := a[1] + t*dy
	return math.Hypot(pt[0]-nearX, pt[1]-nearY) < threshold
}

// ─── Coordinate Helpers ───────────────────────────────────────────────────────

func extractGeometry(feature interface{}) map[string]interface{} {
	fm, ok := feature.(map[string]interface{})
	if !ok {
		return nil
	}
	geom, ok := fm["geometry"].(map[string]interface{})
	if !ok {
		return nil
	}
	return geom
}

// extractPointList converts a LineString/ring coordinates array to [][2]float64
func extractPointList(coords interface{}) [][2]float64 {
	arr, ok := coords.([]interface{})
	if !ok {
		return nil
	}
	var result [][2]float64
	for _, item := range arr {
		pair, ok := item.([]interface{})
		if !ok || len(pair) < 2 {
			continue
		}
		x, ok1 := pair[0].(float64)
		y, ok2 := pair[1].(float64)
		if ok1 && ok2 {
			result = append(result, [2]float64{x, y})
		}
	}
	return result
}

// extractRings converts a Polygon coordinates array to rings of points
func extractRings(coords interface{}) [][][2]float64 {
	arr, ok := coords.([]interface{})
	if !ok {
		return nil
	}
	var rings [][][2]float64
	for _, ring := range arr {
		rings = append(rings, extractPointList(ring))
	}
	return rings
}

// extractMultiPolygonRings converts a MultiPolygon coordinates array
func extractMultiPolygonRings(coords interface{}) [][][][2]float64 {
	arr, ok := coords.([]interface{})
	if !ok {
		return nil
	}
	var result [][][][2]float64
	for _, polygon := range arr {
		result = append(result, extractRings(polygon))
	}
	return result
}

// extractSinglePoint converts a Point coordinates array to [2]float64
func extractSinglePoint(coords interface{}) [2]float64 {
	arr, ok := coords.([]interface{})
	if !ok || len(arr) < 2 {
		return [2]float64{}
	}
	x, _ := arr[0].(float64)
	y, _ := arr[1].(float64)
	return [2]float64{x, y}
}

// ─── File Helpers ─────────────────────────────────────────────────────────────

// loadGeoJSONFile loads and caches a GeoJSON file from the mapdata directory
func loadGeoJSONFile(filename string) (interface{}, error) {
	cacheMutex.RLock()
	if data, exists := geoJSONCache[filename]; exists {
		cacheMutex.RUnlock()
		return data, nil
	}
	cacheMutex.RUnlock()

	fullPath := filepath.Join("mapdata", filename)
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

// getGeoJSONFilesInPipeline returns all .geojson files in the mapdata directory
func getGeoJSONFilesInPipeline() ([]string, error) {
	wd, _ := os.Getwd()
	log.Printf("[Navigation] 工作目錄：%s", wd)

	pattern := filepath.Join("mapdata", "*.geojson")
	log.Printf("[Navigation] 搜尋目錄：%s", pattern)

	files, err := filepath.Glob(pattern)
	if err != nil {
		return nil, err
	}

	var result []string
	for _, file := range files {
		name := filepath.Base(file)
		log.Printf("[Navigation] 找到檔案：%s", name)
		result = append(result, name)
	}

	log.Printf("[Navigation] 共找到 %d 個檔案", len(result))
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

// ─── Bounding Box ─────────────────────────────────────────────────────────────

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