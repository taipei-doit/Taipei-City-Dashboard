package isochrone

// GeoJSON types for FeatureCollection output.

type FeatureCollection struct {
	Type     string    `json:"type"`
	Features []Feature `json:"features"`
}

type Feature struct {
	Type       string                 `json:"type"`
	Properties map[string]interface{} `json:"properties"`
	Geometry   Geometry               `json:"geometry"`
}

type Geometry struct {
	Type        string      `json:"type"`
	Coordinates interface{} `json:"coordinates"`
}

func newFeatureCollection(features []Feature) FeatureCollection {
	return FeatureCollection{Type: "FeatureCollection", Features: features}
}

func newPolygonFeature(rings [][][2]float64, props map[string]interface{}) Feature {
	return Feature{
		Type:       "Feature",
		Properties: props,
		Geometry: Geometry{
			Type:        "Polygon",
			Coordinates: rings,
		},
	}
}

func newMultiPolygonFeature(polygons [][][][2]float64, props map[string]interface{}) Feature {
	return Feature{
		Type:       "Feature",
		Properties: props,
		Geometry: Geometry{
			Type:        "MultiPolygon",
			Coordinates: polygons,
		},
	}
}

func newPointFeature(lon, lat float64, props map[string]interface{}) Feature {
	return Feature{
		Type:       "Feature",
		Properties: props,
		Geometry: Geometry{
			Type:        "Point",
			Coordinates: [2]float64{lon, lat},
		},
	}
}

func newLineStringFeature(coords [][2]float64, props map[string]interface{}) Feature {
	return Feature{
		Type:       "Feature",
		Properties: props,
		Geometry: Geometry{
			Type:        "LineString",
			Coordinates: coords,
		},
	}
}
