package isochrone

import (
	"container/heap"
	"encoding/json"
	"math"

	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

// DefaultCutoffs are the five isochrone thresholds in seconds.
var DefaultCutoffs = []int32{900, 1800, 3600, 5400, 7200}

const (
	walkEdgeMaxDist = 800.0 // metres ??max walking edge between stops
	walkSpd         = 1.4   // m/s
	latRef          = 25.0
	mPerDeg         = 111320.0
	cosLatRef       = 0.9063077870366499 // cos(25°)
)

// walkEdge is a directed edge in the walking graph.
type walkEdge struct {
	to       int
	walkTime float64 // seconds
}

// Generate builds a GeoJSON FeatureCollection with one polygon Feature per
// cutoff using network-based isochrone: RAPTOR transit + Dijkstra walking
// expansion + cut-edge boundary tracing.
//
// Deprecated: Use IsochroneIndex.Query instead, which uses a precomputed
// spatial index for sub-second queries instead of rebuilding the walk graph
// and grid on every call.
func Generate(rd *raptor.RaptorData, tau []int32, depTime int32, cutoffs []int32) ([]byte, error) {
	if len(cutoffs) == 0 {
		cutoffs = DefaultCutoffs
	}

	var maxCutoff int32
	for _, c := range cutoffs {
		if c > maxCutoff {
			maxCutoff = c
		}
	}
	maxTime := float64(depTime + maxCutoff)

	n := len(rd.Stops)

	// Project all stops.
	projX := make([]float64, n)
	projY := make([]float64, n)
	for i, s := range rd.Stops {
		projX[i], projY[i] = project(s.Lat, s.Lon)
	}

	// Step 1: Build walking graph.
	graph := buildWalkGraph(rd, projX, projY)

	// Step 2: Multi-source Dijkstra.
	cost := dijkstraExpand(graph, tau, maxTime)

	// Step 3: For each cutoff, extract boundary polygon.
	var features []Feature
	for _, cutoff := range cutoffs {
		threshold := float64(depTime + cutoff)

		rings := extractBoundary(graph, cost, projX, projY, threshold)
		if len(rings) == 0 {
			continue
		}

		geoRings := make([][][2]float64, len(rings))
		for ri, ring := range rings {
			lr := make([][2]float64, len(ring))
			for pi, pt := range ring {
				lat, lon := unproject(pt[0], pt[1])
				lr[pi] = [2]float64{lon, lat}
			}
			geoRings[ri] = lr
		}

		features = append(features, newPolygonFeature(geoRings, map[string]interface{}{
			"cutoff":  cutoff,
			"minutes": cutoff / 60,
		}))
	}

	fc := newFeatureCollection(features)
	return json.Marshal(fc)
}

func buildWalkGraph(rd *raptor.RaptorData, projX, projY []float64) [][]walkEdge {
	n := len(rd.Stops)
	graph := make([][]walkEdge, n)
	maxDSq := walkEdgeMaxDist * walkEdgeMaxDist

	for i := 0; i < n; i++ {
		if rd.Stops[i].Lat == 0 && rd.Stops[i].Lon == 0 {
			continue
		}
		for j := i + 1; j < n; j++ {
			if rd.Stops[j].Lat == 0 && rd.Stops[j].Lon == 0 {
				continue
			}
			dx := projX[i] - projX[j]
			dy := projY[i] - projY[j]
			dSq := dx*dx + dy*dy
			if dSq > maxDSq {
				continue
			}
			wt := math.Sqrt(dSq) / walkSpd
			graph[i] = append(graph[i], walkEdge{to: j, walkTime: wt})
			graph[j] = append(graph[j], walkEdge{to: i, walkTime: wt})
		}
	}
	return graph
}

func dijkstraExpand(graph [][]walkEdge, tau []int32, maxTime float64) []float64 {
	n := len(tau)
	cost := make([]float64, n)
	for i := range cost {
		cost[i] = math.Inf(1)
	}

	pq := &minHeap{}
	heap.Init(pq)

	for i, t := range tau {
		if t != raptor.Unreachable {
			ft := float64(t)
			if ft <= maxTime {
				cost[i] = ft
				heap.Push(pq, heapItem{cost: ft, idx: i})
			}
		}
	}

	for pq.Len() > 0 {
		top := heap.Pop(pq).(heapItem)
		u := top.idx
		if top.cost > cost[u] {
			continue
		}
		for _, e := range graph[u] {
			nc := cost[u] + e.walkTime
			if nc < cost[e.to] && nc <= maxTime {
				cost[e.to] = nc
				heap.Push(pq, heapItem{cost: nc, idx: e.to})
			}
		}
	}

	return cost
}

func project(lat, lon float64) (x, y float64) {
	x = lon * mPerDeg * cosLatRef
	y = lat * mPerDeg
	return
}

func unproject(x, y float64) (lat, lon float64) {
	lat = y / mPerDeg
	lon = x / (mPerDeg * cosLatRef)
	return
}

// --- Min-heap for Dijkstra ---

type heapItem struct {
	cost float64
	idx  int
}

type minHeap []heapItem

func (h minHeap) Len() int            { return len(h) }
func (h minHeap) Less(i, j int) bool  { return h[i].cost < h[j].cost }
func (h minHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x interface{}) { *h = append(*h, x.(heapItem)) }
func (h *minHeap) Pop() interface{} {
	old := *h
	n := len(old)
	item := old[n-1]
	*h = old[:n-1]
	return item
}
