// Developed by Bombs King, Taipei Codefest 2026

package isochrone

import (
	"encoding/json"
	"math"
	"testing"

	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

func TestNewIsochroneIndex(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "s1", Name: "Stop 1", Lat: 25.05, Lon: 121.50},
			{ID: "s2", Name: "Stop 2", Lat: 25.10, Lon: 121.55},
			{ID: "s3", Name: "Stop 3", Lat: 25.15, Lon: 121.45},
			{ID: "s4", Name: "Stop 4", Lat: 24.90, Lon: 121.40},
			{ID: "s5", Name: "Stop 5", Lat: 25.30, Lon: 121.70},
		},
	}

	idx := NewIsochroneIndex(rd)
	if idx == nil {
		t.Fatal("NewIsochroneIndex returned nil")
	}

	if idx.nx <= 0 || idx.ny <= 0 {
		t.Fatalf("invalid grid dimensions: nx=%d ny=%d", idx.nx, idx.ny)
	}

	if idx.xMin >= idx.xMax || idx.yMin >= idx.yMax {
		t.Fatalf("invalid index extent: x=[%f,%f] y=[%f,%f]", idx.xMin, idx.xMax, idx.yMin, idx.yMax)
	}

	// Check that Stop 1 is inside the dynamic full-GTFS extent.
	stop1X, stop1Y := project(25.05, 121.50)
	qx := int((stop1X - idx.xMin) / idxCellSize)
	qy := int((stop1Y - idx.yMin) / idxCellSize)
	if qx < 0 || qx >= idx.nx || qy < 0 || qy >= idx.ny {
		t.Fatalf("Stop 1 grid cell out of bounds: qx=%d qy=%d nx=%d ny=%d", qx, qy, idx.nx, idx.ny)
	}
}

func TestQueryBasic(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Near", Lat: 25.05, Lon: 121.52},
			{ID: "s2", Name: "Far", Lat: 25.20, Lon: 121.60},
		},
	}

	idx := NewIsochroneIndex(rd)

	// Origin reachable at t=28800 (08:00), others slightly later.
	tau := make([]int32, len(rd.Stops))
	tau[0] = 28800        // reachable now
	tau[1] = 28800 + 300  // reachable in 5 min
	tau[2] = 28800 + 1800 // reachable in 30 min

	result, err := idx.Query(tau, 28800, []int32{900, 1800}, 0, false)
	if err != nil {
		t.Fatalf("Query returned error: %v", err)
	}
	if len(result) == 0 {
		t.Error("Query returned empty result")
	}

	// Should produce valid GeoJSON.
	if result[0] != '{' {
		t.Errorf("expected GeoJSON starting with '{', got %c", result[0])
	}
}

func TestQueryAllUnreachable(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Other", Lat: 25.10, Lon: 121.55},
		},
	}

	idx := NewIsochroneIndex(rd)

	// All stops unreachable.
	tau := make([]int32, len(rd.Stops))
	for i := range tau {
		tau[i] = raptor.Unreachable
	}

	result, err := idx.Query(tau, 28800, []int32{900}, 0, false)
	if err != nil {
		t.Fatalf("Query returned error: %v", err)
	}
	// With all unreachable stops, the isochrone should be empty or very small.
	if len(result) == 0 {
		t.Log("Query returned empty result for all-unreachable (expected)")
	}
}

func TestQueryIgnoresArrivalBeforeDeparture(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Invalid Early", Lat: 25.40, Lon: 121.90},
		},
	}
	idx := NewIsochroneIndex(rd)
	tau := []int32{28800, 60}

	result, err := idx.Query(tau, 28800, []int32{900}, 0, false)
	if err != nil {
		t.Fatalf("Query returned error: %v", err)
	}

	bbox := polygonBBox(t, result, 15)
	if bbox[2] > 121.7 || bbox[3] > 25.3 {
		t.Fatalf("pre-departure stop appears to affect bbox: %#v", bbox)
	}
}

func TestQueryCutoffBBoxesDoNotShrinkForSimpleLine(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Near", Lat: 25.0550, Lon: 121.5300},
			{ID: "s2", Name: "Far", Lat: 25.0700, Lon: 121.5600},
		},
	}
	idx := NewIsochroneIndex(rd)
	tau := []int32{28800, 29100, 30600}

	result, err := idx.Query(tau, 28800, []int32{900, 1800}, 0, false)
	if err != nil {
		t.Fatalf("Query returned error: %v", err)
	}

	b15 := polygonBBox(t, result, 15)
	b30 := polygonBBox(t, result, 30)
	area15 := (b15[2] - b15[0]) * (b15[3] - b15[1])
	area30 := (b30[2] - b30[0]) * (b30[3] - b30[1])
	if area30 < area15 {
		t.Fatalf("30-minute bbox shrank: 15=%#v area=%f 30=%#v area=%f", b15, area15, b30, area30)
	}
}

func TestChaikinSmooth(t *testing.T) {
	// Square ring: 4 corners + closing point.
	square := [][2]float64{
		{0, 0}, {10, 0}, {10, 10}, {0, 10}, {0, 0},
	}
	result := chaikinSmooth(square, 2)

	// After 2 iterations of Chaikin, the ring should have more vertices.
	if len(result) <= len(square) {
		t.Errorf("expected more vertices after Chaikin, got %d <= %d", len(result), len(square))
	}

	// Result should still be closed.
	if result[0] != result[len(result)-1] {
		t.Error("Chaikin result should be closed (first == last point)")
	}
}

func TestNormalizedGaussianBlurFlat(t *testing.T) {
	nx, ny := 30, 30
	grid := make([]float64, nx*ny)
	// Set center cells to finite values, others to inf.
	for i := range grid {
		grid[i] = math.Inf(1)
	}
	for ix := 12; ix < 18; ix++ {
		for iy := 12; iy < 18; iy++ {
			grid[ix*ny+iy] = 100.0
		}
	}

	result := normalizedGaussianBlurFlat(grid, nx, ny, 1.0, 1000000.0)

	// Check that interior cells got blurred values (finite and not inf).
	for ix := 13; ix < 17; ix++ {
		for iy := 13; iy < 17; iy++ {
			v := result[ix*ny+iy]
			if math.IsInf(v, 1) {
				t.Errorf("interior cell (%d,%d) should be finite after blur, got inf", ix, iy)
			}
		}
	}

	// Check that cells far from any finite value got the penalty.
	if v := result[0*ny+0]; v != 1000000.0 {
		t.Errorf("far-away cell should get penalty, got %v", v)
	}
}

func TestExtractContourFromGrid(t *testing.T) {
	nx, ny := 20, 20
	grid := make([]float64, nx*ny)
	// Create a circular reachable region in the center.
	cx, cy := 10.0, 10.0
	radius := 5.0
	for ix := 0; ix < nx; ix++ {
		for iy := 0; iy < ny; iy++ {
			dx := float64(ix) - cx
			dy := float64(iy) - cy
			dist := math.Sqrt(dx*dx + dy*dy)
			if dist <= radius {
				grid[ix*ny+iy] = dist * 100 // cost proportional to distance
			} else {
				grid[ix*ny+iy] = 100000 // high cost outside
			}
		}
	}
	// Force border cells high.
	for ix := 0; ix < nx; ix++ {
		grid[ix*ny+0] = 100000
		grid[ix*ny+ny-1] = 100000
	}
	for iy := 0; iy < ny; iy++ {
		grid[0*ny+iy] = 100000
		grid[(nx-1)*ny+iy] = 100000
	}

	threshold := 300.0
	ring := extractContourFromGrid(grid, nx, ny, 10, 10, threshold)
	if len(ring) == 0 {
		t.Error("expected non-empty contour ring")
	}

	// Ring should be closed.
	if len(ring) > 0 && ring[0] != ring[len(ring)-1] {
		t.Error("contour ring should be closed")
	}
}

func TestExtractContourFromGridSelectsRingContainingQuery(t *testing.T) {
	nx, ny := 40, 40
	grid := make([]float64, nx*ny)
	for i := range grid {
		grid[i] = 100000
	}
	for ix := 5; ix < 35; ix++ {
		for iy := 5; iy < 35; iy++ {
			grid[ix*ny+iy] = 100
		}
	}
	for ix := 10; ix < 30; ix++ {
		for iy := 10; iy < 30; iy++ {
			grid[ix*ny+iy] = 100000
		}
	}

	ring := extractContourFromGrid(grid, nx, ny, 6, 6, 500)
	if len(ring) == 0 {
		t.Fatal("expected non-empty contour ring")
	}
	if !pointInRing(6, 6, ring) {
		t.Fatalf("selected ring does not contain query cell")
	}
}

func TestStitchSegmentsDropsOpenRings(t *testing.T) {
	segments := [][2][2]float64{
		{{0, 0}, {1, 0}},
		{{1, 0}, {1, 1}},
		{{1, 1}, {0, 1}},
	}

	rings := stitchSegments(segments)
	if len(rings) != 0 {
		t.Fatalf("expected open contour to be dropped, got %d rings", len(rings))
	}
}

func polygonBBox(t *testing.T, data []byte, minutes int) [4]float64 {
	t.Helper()
	var fc struct {
		Features []struct {
			Properties map[string]interface{} `json:"properties"`
			Geometry   struct {
				Type        string          `json:"type"`
				Coordinates json.RawMessage `json:"coordinates"`
			} `json:"geometry"`
		} `json:"features"`
	}
	if err := json.Unmarshal(data, &fc); err != nil {
		t.Fatalf("unmarshal geojson: %v", err)
	}
	for _, f := range fc.Features {
		if int(f.Properties["minutes"].(float64)) != minutes {
			continue
		}
		var coords [][][]float64
		if err := json.Unmarshal(f.Geometry.Coordinates, &coords); err != nil {
			t.Fatalf("unmarshal polygon coords: %v", err)
		}
		bbox := [4]float64{math.Inf(1), math.Inf(1), math.Inf(-1), math.Inf(-1)}
		for _, ring := range coords {
			for _, pt := range ring {
				bbox[0] = math.Min(bbox[0], pt[0])
				bbox[1] = math.Min(bbox[1], pt[1])
				bbox[2] = math.Max(bbox[2], pt[0])
				bbox[3] = math.Max(bbox[3], pt[1])
			}
		}
		return bbox
	}
	t.Fatalf("minutes=%d polygon not found", minutes)
	return [4]float64{}
}
