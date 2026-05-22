// Developed by Bombs King, Taipei Codefest 2026

package isochrone

import (
	"encoding/json"
	"sort"
	"strings"

	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

var typeColor = map[string]string{
	"walk":     "#888888",
	"bus":      "#F7B731",
	"jumpfrog": "#A55EEA",
	"rail":     "#20BF6B",
	"train":    "#EB3B5A",
}

// GenerateNetwork builds a GeoJSON FeatureCollection of transit network elements
// (stop markers, route line segments, and walking transfers) reachable within the given cutoffs.
// transfers[i] = number of transfers to reach stop i, or -1 if unreachable.
// maxTransfers caps the number of allowed transfers; -1 means no limit.
// usedFP contains footpaths that actually improved arrival times during the RAPTOR query.
func GenerateNetwork(
	rd *raptor.RaptorData,
	tau []int32,
	transfers []int,
	usedFP map[raptor.FPKey]bool,
	timeSec int32,
	cutoffs []int32,
	maxTransfers int,
	layerColor string,
	isArrival bool,
) ([]byte, error) {
	if !isArrival {
		return GenerateNetworkWithOptions(rd, tau, transfers, usedFP, timeSec, cutoffs, maxTransfers, layerColor, false)
	}

	// For arrival queries, tau[i] is latest departure time.
	// Convert to duration: travelTime = targetTime - tau[i]
	n := len(tau)
	durations := make([]int32, n)
	for i, t := range tau {
		if t == raptor.UnreachableBackward {
			durations[i] = raptor.Unreachable
		} else {
			durations[i] = timeSec - t
		}
	}
	// In duration mode, "departure time" is 0, and we want segments where duration >= 0
	return GenerateNetworkWithOptions(rd, durations, transfers, usedFP, 0, cutoffs, maxTransfers, layerColor, false)
}

func GenerateNetworkWithOptions(
	rd *raptor.RaptorData, tau []int32, transfers []int,
	usedFP map[raptor.FPKey]bool,
	depTime int32, cutoffs []int32, maxTransfers int,
	layerColor string,
	includeWalkPaths bool,
) ([]byte, error) {
	if len(cutoffs) == 0 {
		cutoffs = DefaultCutoffs
	}

	sorted := make([]int32, len(cutoffs))
	copy(sorted, cutoffs)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })

	// For each stop, find the earliest cutoff index where it becomes reachable.
	stopCutoffIdx := make([]int, len(rd.Stops))
	for i := range stopCutoffIdx {
		stopCutoffIdx[i] = -1
	}

	isDurationMode := depTime == 0

	for i, t := range tau {
		if t == raptor.Unreachable || t == raptor.UnreachableBackward {
			continue
		}
		// In duration mode, t is travel time from/to origin, depTime is 0.
		if !isDurationMode && t < depTime {
			continue
		}
		if maxTransfers >= 0 && (transfers[i] < 0 || transfers[i] > maxTransfers) {
			continue
		}
		for ci, c := range sorted {
			if isDurationMode {
				if t <= c {
					stopCutoffIdx[i] = ci
					break
				}
			} else {
				if t <= depTime+c {
					stopCutoffIdx[i] = ci
					break
				}
			}
		}
	}

	var features []Feature
	timeTypeLabel := "departure"
	if isDurationMode {
		timeTypeLabel = "arrival"
	}

	// --- Stop Point features ---
	for i, ci := range stopCutoffIdx {
		if ci < 0 {
			continue
		}
		s := rd.Stops[i]
		if s.Lat == 0 && s.Lon == 0 {
			continue
		}
		tType := extractTransitType(s.ID)
		features = append(features, newPointFeature(s.Lon, s.Lat, map[string]interface{}{
			"stop_id":      s.ID,
			"stop_name":    s.Name,
			"arrival_time": tau[i],
			"cutoff":       sorted[ci],
			"minutes":      sorted[ci] / 60,
			"transit_type": tType,
			"stroke":       strokeColor(tType, layerColor),
			"time_type":    timeTypeLabel,
		}))
	}

	// --- Route segment LineString features (deduplicated) ---
	type segKey struct{ lo, hi int }
	type segInfo struct {
		cutoffIdx   int
		transitType string
		routeID     string
		shape       []raptor.Coord
	}

	segments := make(map[segKey]segInfo)
	for _, route := range rd.Routes {
		tType := extractTransitType(route.ID)
		stops := route.Stops
		for j := 0; j < len(stops)-1; j++ {
			a, b := stops[j], stops[j+1]
			if a == b {
				continue
			}
			ciA := stopCutoffIdx[a]
			ciB := stopCutoffIdx[b]
			if ciA < 0 || ciB < 0 {
				continue
			}
			ciBoth := ciA
			if ciB > ciBoth {
				ciBoth = ciB
			}
			lo, hi := a, b
			if lo > hi {
				lo, hi = hi, lo
			}
			key := segKey{lo, hi}
			shape := routeSegmentShape(route, j)
			if existing, ok := segments[key]; ok {
				if ciBoth < existing.cutoffIdx {
					segments[key] = segInfo{ciBoth, existing.transitType, existing.routeID, shape}
				}
			} else {
				segments[key] = segInfo{ciBoth, tType, route.ID, shape}
			}
		}
	}

	for key, info := range segments {
		sA := rd.Stops[key.lo]
		sB := rd.Stops[key.hi]
		if (sA.Lat == 0 && sA.Lon == 0) || (sB.Lat == 0 && sB.Lon == 0) {
			continue
		}
		coords := coordsFromShape(info.shape)
		if len(coords) < 2 {
			coords = [][2]float64{
				{sA.Lon, sA.Lat},
				{sB.Lon, sB.Lat},
			}
		}
		features = append(features, newLineStringFeature(coords, map[string]interface{}{
			"cutoff":       sorted[info.cutoffIdx],
			"minutes":      sorted[info.cutoffIdx] / 60,
			"transit_type": info.transitType,
			"route_id":     info.routeID,
			"stroke":       strokeColor(info.transitType, layerColor),
			"time_type":    timeTypeLabel,
		}))
	}

	// --- Walking transfer segments ---
	// Show footpaths that are: (a) inter-modal, OR (b) actually used in the query.
	if includeWalkPaths {
		for _, fp := range rd.FootPaths {
			ciA := stopCutoffIdx[fp.From]
			ciB := stopCutoffIdx[fp.To]
			if ciA < 0 || ciB < 0 {
				continue
			}
			sA := rd.Stops[fp.From]
			sB := rd.Stops[fp.To]
			if (sA.Lat == 0 && sA.Lon == 0) || (sB.Lat == 0 && sB.Lon == 0) {
				continue
			}
			interModal := extractTransitType(sA.ID) != extractTransitType(sB.ID)
			used := usedFP[raptor.FPKey{fp.From, fp.To}] || usedFP[raptor.FPKey{fp.To, fp.From}]
			if !interModal && !used {
				continue
			}
			ciBoth := ciA
			if ciB > ciBoth {
				ciBoth = ciB
			}
			coords := [][2]float64{
				{sA.Lon, sA.Lat},
				{sB.Lon, sB.Lat},
			}
			features = append(features, newLineStringFeature(coords, map[string]interface{}{
				"cutoff":       sorted[ciBoth],
				"minutes":      sorted[ciBoth] / 60,
				"transit_type": "walk",
				"stroke":       strokeColor("walk", layerColor),
				"time_type":    timeTypeLabel,
			}))
		}
	}

	fc := newFeatureCollection(features)
	return json.Marshal(fc)
}

func routeSegmentShape(route raptor.RaptorRoute, segmentIdx int) []raptor.Coord {
	if segmentIdx < 0 || segmentIdx >= len(route.SegmentShapes) {
		return nil
	}
	return route.SegmentShapes[segmentIdx]
}

func coordsFromShape(shape []raptor.Coord) [][2]float64 {
	if len(shape) < 2 {
		return nil
	}
	coords := make([][2]float64, 0, len(shape))
	for _, pt := range shape {
		coords = append(coords, [2]float64{pt.Lon, pt.Lat})
	}
	return coords
}

func extractTransitType(id string) string {
	if idx := strings.Index(id, ":"); idx >= 0 {
		return id[:idx]
	}
	return "unknown"
}

func colorFor(tType string) string {
	if c, ok := typeColor[tType]; ok {
		return c
	}
	return "#AAAAAA"
}

func strokeColor(tType, layerColor string) string {
	if layerColor != "" {
		return layerColor
	}
	return colorFor(tType)
}
