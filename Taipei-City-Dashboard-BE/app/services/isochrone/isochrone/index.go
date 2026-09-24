// Developed by Bombs King, Taipei Codefest 2026

package isochrone

import (
	"encoding/json"
	"math"
	"sort"

	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

const (
	idxCellSize     = 200.0 // metres per grid cell
	idxK            = 5     // nearest stops considered per cell
	idxCandidateCap = 48    // nearby stops scanned before discarding unreachable ones
	idxBinSize      = 1000.0
	idxExtentMargin = 12000.0
)

type indexStopInfo struct {
	idx  int
	x, y float64
}

type nearestCandidate struct {
	dSq float64
	idx int
}

// IsochroneIndex holds projected stops and a spatial bin index. Query builds
// only the grid window needed for the current reachable stops, so the index can
// cover the full GTFS extent without forcing every query to scan that extent.
type IsochroneIndex struct {
	nx, ny int
	xMin   float64
	yMin   float64
	xMax   float64
	yMax   float64

	stopX     []float64
	stopY     []float64
	validStop []bool

	binNX int
	binNY int
	bins  [][]indexStopInfo
}

// NewIsochroneIndex builds a spatial index from the full GTFS stop extent.
func NewIsochroneIndex(rd *raptor.RaptorData) *IsochroneIndex {
	n := len(rd.Stops)
	stopX := make([]float64, n)
	stopY := make([]float64, n)
	valid := make([]bool, n)

	minX, minY := math.Inf(1), math.Inf(1)
	maxX, maxY := math.Inf(-1), math.Inf(-1)
	validCount := 0
	for i, s := range rd.Stops {
		if s.Lat == 0 && s.Lon == 0 {
			continue
		}
		x, y := project(s.Lat, s.Lon)
		stopX[i], stopY[i] = x, y
		valid[i] = true
		validCount++
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

	if validCount == 0 {
		minX, minY = project(25.0478, 121.5174)
		maxX, maxY = minX, minY
	}

	xMin := minX - idxExtentMargin
	yMin := minY - idxExtentMargin
	xMax := maxX + idxExtentMargin
	yMax := maxY + idxExtentMargin

	nx := int(math.Ceil((xMax-xMin)/idxCellSize)) + 1
	ny := int(math.Ceil((yMax-yMin)/idxCellSize)) + 1
	if nx < 3 {
		nx = 3
	}
	if ny < 3 {
		ny = 3
	}

	binNX := int(math.Ceil((xMax-xMin)/idxBinSize)) + 1
	binNY := int(math.Ceil((yMax-yMin)/idxBinSize)) + 1
	if binNX < 1 {
		binNX = 1
	}
	if binNY < 1 {
		binNY = 1
	}

	idx := &IsochroneIndex{
		nx:        nx,
		ny:        ny,
		xMin:      xMin,
		yMin:      yMin,
		xMax:      xMax,
		yMax:      yMax,
		stopX:     stopX,
		stopY:     stopY,
		validStop: valid,
		binNX:     binNX,
		binNY:     binNY,
		bins:      make([][]indexStopInfo, binNX*binNY),
	}

	for i := 0; i < n; i++ {
		if !valid[i] {
			continue
		}
		bx := idx.binX(stopX[i])
		by := idx.binY(stopY[i])
		if bx >= 0 && bx < idx.binNX && by >= 0 && by < idx.binNY {
			off := idx.binOffset(bx, by)
			idx.bins[off] = append(idx.bins[off], indexStopInfo{i, stopX[i], stopY[i]})
		}
	}

	return idx
}

// Query builds isochrone polygons for given RAPTOR results using the spatial
// index. sourceIdx is the stop handle of the query origin.
func (idx *IsochroneIndex) Query(tau []int32, timeSec int32, cutoffs []int32, sourceIdx int, isArrival bool) ([]byte, error) {
	if !isArrival {
		return idx.QueryDeparture(tau, timeSec, cutoffs, sourceIdx)
	}

	// For arrival queries, tau[i] is latest departure time to reach destination.
	// We convert this to duration: travelTime = targetTime - tau[i]
	// and then call QueryDeparture with timeSec=0 and a modified tau.
	n := len(tau)
	durations := make([]int32, n)
	for i, t := range tau {
		if t == raptor.UnreachableBackward {
			durations[i] = raptor.Unreachable
		} else {
			durations[i] = timeSec - t
		}
	}
	return idx.QueryDeparture(durations, 0, cutoffs, sourceIdx)
}

func (idx *IsochroneIndex) QueryDeparture(tau []int32, depTime int32, cutoffs []int32, sourceIdx int) ([]byte, error) {
	if len(cutoffs) == 0 {
		cutoffs = DefaultCutoffs
	}
	if sourceIdx < 0 || sourceIdx >= len(idx.stopX) || !idx.validStop[sourceIdx] {
		fc := newFeatureCollection(nil)
		return json.Marshal(fc)
	}

	maxCutoff := int32(0)
	for _, c := range cutoffs {
		if c > maxCutoff {
			maxCutoff = c
		}
	}
	maxTime := float64(depTime + maxCutoff)

	stopCost := make([]float64, len(tau))
	for i := range stopCost {
		stopCost[i] = math.Inf(1)
	}

	minX, minY := math.Inf(1), math.Inf(1)
	maxX, maxY := math.Inf(-1), math.Inf(-1)
	hasReachable := false
	for i, t := range tau {
		if i >= len(idx.validStop) || !idx.validStop[i] {
			continue
		}
		if t == raptor.Unreachable || t < depTime || float64(t) > maxTime {
			continue
		}
		stopCost[i] = float64(t)
		hasReachable = true
		x, y := idx.stopX[i], idx.stopY[i]
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

	if !hasReachable {
		fc := newFeatureCollection(nil)
		return json.Marshal(fc)
	}

	padding := float64(maxCutoff)*walkSpd + idxBinSize
	if padding < idxBinSize*2 {
		padding = idxBinSize * 2
	}

	qxGlobal := clampInt(int((idx.stopX[sourceIdx]-idx.xMin)/idxCellSize), 0, idx.nx-1)
	qyGlobal := clampInt(int((idx.stopY[sourceIdx]-idx.yMin)/idxCellSize), 0, idx.ny-1)

	ixMin := clampInt(int(math.Floor((minX-padding-idx.xMin)/idxCellSize)), 0, idx.nx-1)
	iyMin := clampInt(int(math.Floor((minY-padding-idx.yMin)/idxCellSize)), 0, idx.ny-1)
	ixMax := clampInt(int(math.Ceil((maxX+padding-idx.xMin)/idxCellSize)), 0, idx.nx-1)
	iyMax := clampInt(int(math.Ceil((maxY+padding-idx.yMin)/idxCellSize)), 0, idx.ny-1)

	if qxGlobal < ixMin {
		ixMin = clampInt(qxGlobal-2, 0, idx.nx-1)
	}
	if qxGlobal > ixMax {
		ixMax = clampInt(qxGlobal+2, 0, idx.nx-1)
	}
	if qyGlobal < iyMin {
		iyMin = clampInt(qyGlobal-2, 0, idx.ny-1)
	}
	if qyGlobal > iyMax {
		iyMax = clampInt(qyGlobal+2, 0, idx.ny-1)
	}

	localNX := ixMax - ixMin + 1
	localNY := iyMax - iyMin + 1
	if localNX < 3 || localNY < 3 {
		fc := newFeatureCollection(nil)
		return json.Marshal(fc)
	}

	grid := make([]float64, localNX*localNY)
	maxRing := int(math.Ceil(padding/idxBinSize)) + 2
	if maxRing < 2 {
		maxRing = 2
	}

	candidates := make([]nearestCandidate, 0, idxCandidateCap)
	for ix := 0; ix < localNX; ix++ {
		cx := idx.xMin + float64(ixMin+ix)*idxCellSize
		for iy := 0; iy < localNY; iy++ {
			cy := idx.yMin + float64(iyMin+iy)*idxCellSize
			candidates = idx.collectNearest(cx, cy, maxRing, candidates)
			best := math.Inf(1)
			used := 0
			for k := 0; k < len(candidates) && used < idxK; k++ {
				c := candidates[k]
				sc := stopCost[c.idx]
				if math.IsInf(sc, 1) {
					continue
				}
				total := sc + math.Sqrt(c.dSq)/walkSpd
				if total < best {
					best = total
				}
				used++
			}
			grid[ix*localNY+iy] = best
		}
	}

	sigma := math.Max(1.0, 50.0/idxCellSize)
	penalty := maxTime + 7200.0
	grid = normalizedGaussianBlurFlat(grid, localNX, localNY, sigma, penalty)

	var features []Feature
	for _, cutoff := range cutoffs {
		threshold := float64(depTime + cutoff)

		masked := make([]float64, len(grid))
		copy(masked, grid)
		for ix := 0; ix < localNX; ix++ {
			masked[ix*localNY+0] = threshold + 1e6
			masked[ix*localNY+localNY-1] = threshold + 1e6
		}
		for iy := 0; iy < localNY; iy++ {
			masked[iy] = threshold + 1e6
			masked[(localNX-1)*localNY+iy] = threshold + 1e6
		}

		rings := extractAllContoursFromGrid(masked, localNX, localNY, threshold)
		if len(rings) == 0 {
			continue
		}

		polygons := make([][][][2]float64, 0, len(rings))
		for _, ring := range rings {
			geoRing := make([][2]float64, len(ring))
			for pi, pt := range ring {
				x := idx.xMin + float64(ixMin)*idxCellSize + pt[0]*idxCellSize
				y := idx.yMin + float64(iyMin)*idxCellSize + pt[1]*idxCellSize
				lat, lon := unproject(x, y)
				geoRing[pi] = [2]float64{lon, lat}
			}
			polygons = append(polygons, [][][2]float64{geoRing})
		}

		props := map[string]interface{}{
			"cutoff":  cutoff,
			"minutes": cutoff / 60,
		}
		if len(polygons) == 1 {
			features = append(features, newPolygonFeature(polygons[0], props))
		} else {
			features = append(features, newMultiPolygonFeature(polygons, props))
		}
	}

	fc := newFeatureCollection(features)
	return json.Marshal(fc)
}

func (idx *IsochroneIndex) collectNearest(cx, cy float64, maxRing int, candidates []nearestCandidate) []nearestCandidate {
	candidates = candidates[:0]
	bxC := idx.binX(cx)
	byC := idx.binY(cy)

	for ring := 0; ring <= maxRing && len(candidates) < idxCandidateCap; ring++ {
		for dbx := -ring; dbx <= ring; dbx++ {
			for dby := -ring; dby <= ring; dby++ {
				if ring > 0 && dbx > -ring && dbx < ring && dby > -ring && dby < ring {
					continue
				}
				bx := bxC + dbx
				by := byC + dby
				if bx < 0 || bx >= idx.binNX || by < 0 || by >= idx.binNY {
					continue
				}
				for _, s := range idx.bins[idx.binOffset(bx, by)] {
					dx := cx - s.x
					dy := cy - s.y
					candidates = append(candidates, nearestCandidate{dSq: dx*dx + dy*dy, idx: s.idx})
				}
			}
		}
	}

	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].dSq < candidates[j].dSq
	})
	return candidates
}

func (idx *IsochroneIndex) binX(x float64) int {
	return int((x - idx.xMin) / idxBinSize)
}

func (idx *IsochroneIndex) binY(y float64) int {
	return int((y - idx.yMin) / idxBinSize)
}

func (idx *IsochroneIndex) binOffset(bx, by int) int {
	return bx*idx.binNY + by
}

func clampInt(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
