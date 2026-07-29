// Developed by Bombs King, Taipei Codefest 2026

package raptor

import (
	"fmt"
	"math"
	"sort"
	"strings"

	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
)

const sameNameBusStopMergeMaxM = 120.0

// Build constructs a RaptorData from one or more GTFS feeds.
// Each feed's IDs are namespaced with its Prefix to avoid collisions.
func Build(feeds []*gtfs.Feed) (*RaptorData, error) {
	rd := &RaptorData{
		StopIndex: make(map[string]int),
	}

	// --- Pass 1: collect all stops that appear in stop_times across all feeds ---
	usedStops := make(map[string]struct{}) // prefixed stop_id
	for _, f := range feeds {
		for _, sts := range f.StopTimes {
			for _, st := range sts {
				usedStops[f.Prefix+st.StopID] = struct{}{}
			}
		}
		// Also include stops referenced by expanded frequency trips
		for _, et := range gtfs.ExpandFrequencies(f) {
			for _, st := range et.StopTimes {
				usedStops[f.Prefix+st.StopID] = struct{}{}
			}
		}
	}

	// --- Pass 2: register stops ---
	// Sort for deterministic ordering
	sortedStopIDs := make([]string, 0, len(usedStops))
	for id := range usedStops {
		sortedStopIDs = append(sortedStopIDs, id)
	}
	sort.Strings(sortedStopIDs)

	// Build a lookup from prefixed stop ID to raw stop data
	rawStops := make(map[string]*gtfs.RawStop)
	for _, f := range feeds {
		for id, s := range f.Stops {
			rawStops[f.Prefix+id] = s
		}
	}

	busClustersByName := make(map[string][]int)
	stopMergeCounts := make([]int, 0, len(sortedStopIDs))

	for _, pid := range sortedStopIDs {
		s, ok := rawStops[pid]
		if !ok {
			continue
		}
		if s.Lat == 0 && s.Lon == 0 {
			continue
		}

		if strings.HasPrefix(pid, "bus:") {
			if idx, ok := findSameNameBusStopCluster(rd, busClustersByName, s); ok {
				rd.StopIndex[pid] = idx
				count := stopMergeCounts[idx]
				rd.Stops[idx].Lat = (rd.Stops[idx].Lat*float64(count) + s.Lat) / float64(count+1)
				rd.Stops[idx].Lon = (rd.Stops[idx].Lon*float64(count) + s.Lon) / float64(count+1)
				stopMergeCounts[idx] = count + 1
				continue
			}
		}

		idx := len(rd.Stops)
		rd.StopIndex[pid] = idx
		rd.Stops = append(rd.Stops, RaptorStop{
			ID:   pid,
			Name: s.Name,
			Lat:  s.Lat,
			Lon:  s.Lon,
		})
		stopMergeCounts = append(stopMergeCounts, 1)
		if strings.HasPrefix(pid, "bus:") {
			name := normalizeStopName(s.Name)
			if name != "" {
				busClustersByName[name] = append(busClustersByName[name], idx)
			}
		}
	}

	// --- Pass 3: build routes ---
	type tripRecord struct {
		routeKey  string
		stopSeq   []int
		serviceID string
		times     []StopTimeEntry
	}

	var allTrips []tripRecord
	routeKeyStops := make(map[string][]int)
	routeKeyShapes := make(map[string][]Coord)

	processTripStopTimes := func(f *gtfs.Feed, serviceID, routeID, shapeID string, rawSts []gtfs.RawStopTime) {
		if len(rawSts) < 2 {
			return
		}
		stopSeq := make([]int, 0, len(rawSts))
		times := make([]StopTimeEntry, 0, len(rawSts))
		for _, st := range rawSts {
			pid := f.Prefix + st.StopID
			h, ok := rd.StopIndex[pid]
			if !ok {
				return
			}
			stopSeq = append(stopSeq, h)
			times = append(times, StopTimeEntry{
				Arrival:   st.Arrival,
				Departure: st.Dep,
			})
		}

		key := routeKey(f.Prefix+routeID, stopSeq)
		if _, exists := routeKeyStops[key]; !exists {
			routeKeyStops[key] = stopSeq
		}
		if shapeID != "" {
			shape := rawShapeToCoords(f.Shapes[shapeID])
			if len(shape) >= 2 {
				if _, exists := routeKeyShapes[key]; !exists {
					routeKeyShapes[key] = shape
				}
			}
		}
		allTrips = append(allTrips, tripRecord{
			routeKey:  key,
			stopSeq:   stopSeq,
			serviceID: serviceID,
			times:     times,
		})
	}

	for _, f := range feeds {
		for tripID, rawSts := range f.StopTimes {
			if _, isFreq := f.Freqs[tripID]; isFreq {
				continue
			}
			trip, ok := f.Trips[tripID]
			if !ok {
				continue
			}
			processTripStopTimes(f, trip.ServiceID, trip.RouteID, trip.ShapeID, rawSts)
		}
		for _, et := range gtfs.ExpandFrequencies(f) {
			processTripStopTimes(f, et.ServiceID, et.RouteID, et.ShapeID, et.StopTimes)
		}
	}

	// --- Pass 4: assemble RaptorRoute slices, sort trips by first departure ---
	sortedRouteKeys := make([]string, 0, len(routeKeyStops))
	for k := range routeKeyStops {
		sortedRouteKeys = append(sortedRouteKeys, k)
	}
	sort.Strings(sortedRouteKeys)

	routeKeyIdx := make(map[string]int, len(sortedRouteKeys))
	for i, k := range sortedRouteKeys {
		routeKeyIdx[k] = i
		rd.Routes = append(rd.Routes, RaptorRoute{
			ID:            k,
			Stops:         routeKeyStops[k],
			SegmentShapes: buildSegmentShapes(routeKeyStops[k], routeKeyShapes[k], rd.Stops),
		})
	}

	for _, tr := range allTrips {
		ri := routeKeyIdx[tr.routeKey]
		rd.Routes[ri].Trips = append(rd.Routes[ri].Trips, RaptorTrip{
			ServiceID: tr.serviceID,
			Times:     tr.times,
		})
	}

	for i := range rd.Routes {
		sort.Slice(rd.Routes[i].Trips, func(a, b int) bool {
			ta := rd.Routes[i].Trips[a].Times[0].Departure
			tb := rd.Routes[i].Trips[b].Times[0].Departure
			return ta < tb
		})
	}

	// --- Pass 5: build StopRoutes index ---
	rd.StopRoutes = make([][]RouteStopPos, len(rd.Stops))
	for ri, route := range rd.Routes {
		for pos, sh := range route.Stops {
			rd.StopRoutes[sh] = append(rd.StopRoutes[sh], RouteStopPos{
				RouteIdx: ri,
				StopPos:  pos,
			})
		}
	}

	// --- Pass 6: build FootPaths for walking transfers ---
	const maxFootM = 500.0
	for i := 0; i < len(rd.Stops); i++ {
		for j := i + 1; j < len(rd.Stops); j++ {
			d := haversine(rd.Stops[i].Lat, rd.Stops[i].Lon, rd.Stops[j].Lat, rd.Stops[j].Lon)
			if d <= maxFootM {
				rd.FootPaths = append(rd.FootPaths, FootPath{From: i, To: j, DistM: d})
				rd.FootPaths = append(rd.FootPaths, FootPath{From: j, To: i, DistM: d})
			}
		}
	}

	return rd, nil
}

func findSameNameBusStopCluster(
	rd *RaptorData,
	clustersByName map[string][]int,
	stop *gtfs.RawStop,
) (int, bool) {
	name := normalizeStopName(stop.Name)
	if name == "" {
		return 0, false
	}
	candidates := clustersByName[name]
	bestIdx := -1
	bestDist := math.MaxFloat64
	for _, idx := range candidates {
		candidate := rd.Stops[idx]
		d := haversine(stop.Lat, stop.Lon, candidate.Lat, candidate.Lon)
		if d <= sameNameBusStopMergeMaxM && d < bestDist {
			bestIdx = idx
			bestDist = d
		}
	}
	if bestIdx < 0 {
		return 0, false
	}
	return bestIdx, true
}

func normalizeStopName(name string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(name)), " ")
}

func routeKey(routeID string, stops []int) string {
	key := routeID
	for _, s := range stops {
		key += fmt.Sprintf(":%d", s)
	}
	return key
}

func rawShapeToCoords(points []gtfs.RawShapePoint) []Coord {
	if len(points) < 2 {
		return nil
	}
	coords := make([]Coord, 0, len(points))
	for _, pt := range points {
		if pt.Lat == 0 && pt.Lon == 0 {
			continue
		}
		coords = append(coords, Coord{Lon: pt.Lon, Lat: pt.Lat, Part: pt.Part})
	}
	return coords
}

func buildSegmentShapes(stops []int, shape []Coord, rdStops []RaptorStop) [][]Coord {
	if len(stops) < 2 || len(shape) < 2 {
		return nil
	}
	result := make([][]Coord, len(stops)-1)
	for i := 0; i < len(stops)-1; i++ {
		a := rdStops[stops[i]]
		b := rdStops[stops[i+1]]
		ia, ib := nearestShapeSegment(shape, a.Lat, a.Lon, b.Lat, b.Lon)
		if ia < 0 || ib < 0 || ia == ib {
			continue
		}
		result[i] = shapeSlice(shape, ia, ib)
	}
	return result
}

func nearestShapeSegment(shape []Coord, aLat, aLon, bLat, bLon float64) (int, int) {
	bestA, bestB := -1, -1
	bestScore := math.MaxFloat64
	parts := make(map[int]struct{})
	for _, pt := range shape {
		parts[pt.Part] = struct{}{}
	}
	for part := range parts {
		ia := nearestShapePointInPart(shape, aLat, aLon, part)
		ib := nearestShapePointInPart(shape, bLat, bLon, part)
		if ia < 0 || ib < 0 || ia == ib {
			continue
		}
		score := haversine(aLat, aLon, shape[ia].Lat, shape[ia].Lon) +
			haversine(bLat, bLon, shape[ib].Lat, shape[ib].Lon)
		if score < bestScore {
			bestScore = score
			bestA = ia
			bestB = ib
		}
	}
	return bestA, bestB
}

func nearestShapePointInPart(shape []Coord, lat, lon float64, part int) int {
	best := -1
	bestDist := math.MaxFloat64
	for i, pt := range shape {
		if pt.Part != part {
			continue
		}
		d := haversine(lat, lon, pt.Lat, pt.Lon)
		if d < bestDist {
			bestDist = d
			best = i
		}
	}
	return best
}

func nearestShapePoint(shape []Coord, lat, lon float64) int {
	best := -1
	bestDist := math.MaxFloat64
	for i, pt := range shape {
		d := haversine(lat, lon, pt.Lat, pt.Lon)
		if d < bestDist {
			bestDist = d
			best = i
		}
	}
	return best
}

func shapeSlice(shape []Coord, from, to int) []Coord {
	if from <= to {
		out := make([]Coord, to-from+1)
		copy(out, shape[from:to+1])
		return out
	}
	out := make([]Coord, from-to+1)
	for i := range out {
		out[i] = shape[from-i]
	}
	return out
}

func haversine(lat1, lon1, lat2, lon2 float64) float64 {
	const R = 6371000.0
	dLat := (lat2 - lat1) * math.Pi / 180
	dLon := (lon2 - lon1) * math.Pi / 180
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(lat1*math.Pi/180)*math.Cos(lat2*math.Pi/180)*
			math.Sin(dLon/2)*math.Sin(dLon/2)
	return R * 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
}
