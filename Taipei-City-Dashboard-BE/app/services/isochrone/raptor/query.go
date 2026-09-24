// Developed by Bombs King, Taipei Codefest 2026

package raptor

// Query runs the RAPTOR algorithm from sourceStopIdx at depTimeSec.
// activeServices is the set of service_ids running on the query date.
// maxCutoffSec is the maximum travel time in seconds (e.g. 7200 for 120 min).
//
// Returns tau[i] = earliest arrival time (seconds since midnight) at stop i,
// or Unreachable if the stop cannot be reached within maxCutoffSec.
func (rd *RaptorData) Query(
	sourceStopIdx int,
	depTimeSec int32,
	activeServices map[string]bool,
	maxCutoffSec int32,
) []int32 {
	n := len(rd.Stops)
	tau := make([]int32, n)
	for i := range tau {
		tau[i] = Unreachable
	}
	tau[sourceStopIdx] = depTimeSec

	marked := make([]bool, n)
	marked[sourceStopIdx] = true
	markedList := []int{sourceStopIdx}

	maxArrival := depTimeSec + maxCutoffSec

	// Walk speed: 1.4 m/s → time in seconds
	const walkSpeed = 1.4

	// Index foot paths by From stop for fast lookup
	footByFrom := make([][]FootPath, n)
	for i := range rd.FootPaths {
		fp := rd.FootPaths[i]
		footByFrom[fp.From] = append(footByFrom[fp.From], fp)
	}

	const maxRounds = 6

	for round := 0; round < maxRounds; round++ {
		if len(markedList) == 0 {
			break
		}

		// --- Foot path phase: walk from marked stops to nearby stops ---
		footMarked := make([]int, 0)
		for _, sh := range markedList {
			for _, fp := range footByFrom[sh] {
				walkTime := int32(fp.DistM / walkSpeed)
				arr := tau[sh] + walkTime
				if arr >= depTimeSec && arr < tau[fp.To] && arr <= maxArrival {
					tau[fp.To] = arr
					if !marked[fp.To] {
						marked[fp.To] = true
						footMarked = append(footMarked, fp.To)
					}
				}
			}
		}
		markedList = append(markedList, footMarked...)

		// Collect routes Q: routeIdx → earliest stop position among marked stops
		type qEntry struct {
			stopPos int
			stopIdx int
		}
		Q := make(map[int]qEntry, len(markedList)*3)

		for _, sh := range markedList {
			for _, rsp := range rd.StopRoutes[sh] {
				if e, exists := Q[rsp.RouteIdx]; !exists || rsp.StopPos < e.stopPos {
					Q[rsp.RouteIdx] = qEntry{stopPos: rsp.StopPos, stopIdx: sh}
				}
			}
		}

		// Reset marked for this round
		for _, sh := range markedList {
			marked[sh] = false
		}
		markedList = markedList[:0]

		// Scan each route in Q
		for ri, entry := range Q {
			route := &rd.Routes[ri]
			var curTrip *RaptorTrip

			for pos := entry.stopPos; pos < len(route.Stops); pos++ {
				sh := route.Stops[pos]

				if curTrip != nil {
					arr := curTrip.Times[pos].Arrival
					if arr < depTimeSec {
						continue
					}
					if arr < tau[sh] && arr <= maxArrival {
						tau[sh] = arr
						if !marked[sh] {
							marked[sh] = true
							markedList = append(markedList, sh)
						}
					}
				}

				stopTau := tau[sh]
				if stopTau == Unreachable || stopTau < depTimeSec {
					continue
				}
				if curTrip == nil || stopTau <= curTrip.Times[pos].Departure {
					t := earliestTrip(route, pos, stopTau, activeServices)
					if t != nil && (curTrip == nil || t.Times[pos].Departure < curTrip.Times[pos].Departure) {
						curTrip = t
					}
				}
			}
		}
	}

	return tau
}

func (rd *RaptorData) QueryWithScanner(
	sourceStopIdx int,
	depTimeSec int32,
	scanner *RouteScanner,
	maxCutoffSec int32,
) []int32 {
	return rd.QueryWithScannerSources([]Source{{StopIdx: sourceStopIdx, Time: depTimeSec}}, depTimeSec, scanner, maxCutoffSec)
}

func (rd *RaptorData) QueryWithScannerSources(
	sources []Source,
	depTimeSec int32,
	scanner *RouteScanner,
	maxCutoffSec int32,
) []int32 {
	n := len(rd.Stops)
	tau := make([]int32, n)
	for i := range tau {
		tau[i] = Unreachable
	}

	marked := make([]bool, n)
	markedList := make([]int, 0, len(sources))
	for _, source := range sources {
		if source.StopIdx < 0 || source.StopIdx >= n {
			continue
		}
		if source.Time < depTimeSec {
			source.Time = depTimeSec
		}
		if source.Time >= tau[source.StopIdx] {
			continue
		}
		tau[source.StopIdx] = source.Time
		if !marked[source.StopIdx] {
			marked[source.StopIdx] = true
			markedList = append(markedList, source.StopIdx)
		}
	}

	maxArrival := depTimeSec + maxCutoffSec

	const walkSpeed = 1.4

	footByFrom := make([][]FootPath, n)
	for i := range rd.FootPaths {
		fp := rd.FootPaths[i]
		footByFrom[fp.From] = append(footByFrom[fp.From], fp)
	}

	const maxRounds = 6

	for round := 0; round < maxRounds; round++ {
		if len(markedList) == 0 {
			break
		}

		footMarked := make([]int, 0)
		for _, sh := range markedList {
			for _, fp := range footByFrom[sh] {
				walkTime := int32(fp.DistM / walkSpeed)
				arr := tau[sh] + walkTime
				if arr >= depTimeSec && arr < tau[fp.To] && arr <= maxArrival {
					tau[fp.To] = arr
					if !marked[fp.To] {
						marked[fp.To] = true
						footMarked = append(footMarked, fp.To)
					}
				}
			}
		}
		markedList = append(markedList, footMarked...)

		type qEntry struct {
			stopPos int
			stopIdx int
		}
		Q := make(map[int]qEntry, len(markedList)*3)

		for _, sh := range markedList {
			for _, rsp := range rd.StopRoutes[sh] {
				if e, exists := Q[rsp.RouteIdx]; !exists || rsp.StopPos < e.stopPos {
					Q[rsp.RouteIdx] = qEntry{stopPos: rsp.StopPos, stopIdx: sh}
				}
			}
		}

		for _, sh := range markedList {
			marked[sh] = false
		}
		markedList = markedList[:0]

		for ri, entry := range Q {
			route := &rd.Routes[ri]
			var curTrip *RaptorTrip

			for pos := entry.stopPos; pos < len(route.Stops); pos++ {
				sh := route.Stops[pos]

				if curTrip != nil {
					arr := curTrip.Times[pos].Arrival
					if arr < depTimeSec {
						continue
					}
					if arr < tau[sh] && arr <= maxArrival {
						tau[sh] = arr
						if !marked[sh] {
							marked[sh] = true
							markedList = append(markedList, sh)
						}
					}
				}

				stopTau := tau[sh]
				if stopTau == Unreachable || stopTau < depTimeSec {
					continue
				}
				if curTrip == nil || stopTau <= curTrip.Times[pos].Departure {
					t := scanner.EarliestTrip(ri, pos, stopTau)
					if t != nil && (curTrip == nil || t.Times[pos].Departure < curTrip.Times[pos].Departure) {
						curTrip = t
					}
				}
			}
		}
	}

	return tau
}

// FPKey identifies a footpath by its endpoint stop handles.
type FPKey struct{ From, To int }

// QueryWithTransfers runs RAPTOR and returns earliest arrival times,
// transfer counts per stop, and the set of footpaths that actually
// improved arrival times during the query.
func (rd *RaptorData) QueryWithTransfers(
	sourceStopIdx int,
	depTimeSec int32,
	activeServices map[string]bool,
	maxCutoffSec int32,
) (tau []int32, transfers []int, usedFP map[FPKey]bool) {
	n := len(rd.Stops)
	tau = make([]int32, n)
	transfers = make([]int, n)
	for i := range tau {
		tau[i] = Unreachable
		transfers[i] = -1
	}
	tau[sourceStopIdx] = depTimeSec
	transfers[sourceStopIdx] = 0
	usedFP = make(map[FPKey]bool)

	marked := make([]bool, n)
	marked[sourceStopIdx] = true
	markedList := []int{sourceStopIdx}

	maxArrival := depTimeSec + maxCutoffSec

	const walkSpeed = 1.4

	footByFrom := make([][]FootPath, n)
	for i := range rd.FootPaths {
		fp := rd.FootPaths[i]
		footByFrom[fp.From] = append(footByFrom[fp.From], fp)
	}

	const maxRounds = 6

	for round := 0; round < maxRounds; round++ {
		if len(markedList) == 0 {
			break
		}

		// Foot path phase
		footMarked := make([]int, 0)
		for _, sh := range markedList {
			for _, fp := range footByFrom[sh] {
				walkTime := int32(fp.DistM / walkSpeed)
				arr := tau[sh] + walkTime
				if arr >= depTimeSec && arr < tau[fp.To] && arr <= maxArrival {
					tau[fp.To] = arr
					transfers[fp.To] = transfers[sh]
					usedFP[FPKey{fp.From, fp.To}] = true
					if !marked[fp.To] {
						marked[fp.To] = true
						footMarked = append(footMarked, fp.To)
					}
				}
			}
		}
		markedList = append(markedList, footMarked...)

		type qEntry struct {
			stopPos int
			stopIdx int
		}
		Q := make(map[int]qEntry, len(markedList)*3)

		for _, sh := range markedList {
			for _, rsp := range rd.StopRoutes[sh] {
				if e, exists := Q[rsp.RouteIdx]; !exists || rsp.StopPos < e.stopPos {
					Q[rsp.RouteIdx] = qEntry{stopPos: rsp.StopPos, stopIdx: sh}
				}
			}
		}

		for _, sh := range markedList {
			marked[sh] = false
		}
		markedList = markedList[:0]

		for ri, entry := range Q {
			route := &rd.Routes[ri]
			var curTrip *RaptorTrip

			for pos := entry.stopPos; pos < len(route.Stops); pos++ {
				sh := route.Stops[pos]

				if curTrip != nil {
					arr := curTrip.Times[pos].Arrival
					if arr < depTimeSec {
						continue
					}
					if arr < tau[sh] && arr <= maxArrival {
						tau[sh] = arr
						transfers[sh] = round
						if !marked[sh] {
							marked[sh] = true
							markedList = append(markedList, sh)
						}
					}
				}

				stopTau := tau[sh]
				if stopTau == Unreachable || stopTau < depTimeSec {
					continue
				}
				if curTrip == nil || stopTau <= curTrip.Times[pos].Departure {
					t := earliestTrip(route, pos, stopTau, activeServices)
					if t != nil && (curTrip == nil || t.Times[pos].Departure < curTrip.Times[pos].Departure) {
						curTrip = t
					}
				}
			}
		}
	}

	return tau, transfers, usedFP
}

func (rd *RaptorData) QueryWithTransfersScanner(
	sourceStopIdx int,
	depTimeSec int32,
	scanner *RouteScanner,
	maxCutoffSec int32,
) (tau []int32, transfers []int, usedFP map[FPKey]bool) {
	return rd.QueryWithTransfersScannerSources([]Source{{StopIdx: sourceStopIdx, Time: depTimeSec}}, depTimeSec, scanner, maxCutoffSec)
}

func (rd *RaptorData) QueryWithTransfersScannerSources(
	sources []Source,
	depTimeSec int32,
	scanner *RouteScanner,
	maxCutoffSec int32,
) (tau []int32, transfers []int, usedFP map[FPKey]bool) {
	n := len(rd.Stops)
	tau = make([]int32, n)
	transfers = make([]int, n)
	for i := range tau {
		tau[i] = Unreachable
		transfers[i] = -1
	}
	usedFP = make(map[FPKey]bool)

	marked := make([]bool, n)
	markedList := make([]int, 0, len(sources))
	for _, source := range sources {
		if source.StopIdx < 0 || source.StopIdx >= n {
			continue
		}
		if source.Time < depTimeSec {
			source.Time = depTimeSec
		}
		if source.Time >= tau[source.StopIdx] {
			continue
		}
		tau[source.StopIdx] = source.Time
		transfers[source.StopIdx] = 0
		if !marked[source.StopIdx] {
			marked[source.StopIdx] = true
			markedList = append(markedList, source.StopIdx)
		}
	}

	maxArrival := depTimeSec + maxCutoffSec

	const walkSpeed = 1.4

	footByFrom := make([][]FootPath, n)
	for i := range rd.FootPaths {
		fp := rd.FootPaths[i]
		footByFrom[fp.From] = append(footByFrom[fp.From], fp)
	}

	const maxRounds = 6

	for round := 0; round < maxRounds; round++ {
		if len(markedList) == 0 {
			break
		}

		footMarked := make([]int, 0)
		for _, sh := range markedList {
			for _, fp := range footByFrom[sh] {
				walkTime := int32(fp.DistM / walkSpeed)
				arr := tau[sh] + walkTime
				if arr >= depTimeSec && arr < tau[fp.To] && arr <= maxArrival {
					tau[fp.To] = arr
					transfers[fp.To] = transfers[sh]
					usedFP[FPKey{fp.From, fp.To}] = true
					if !marked[fp.To] {
						marked[fp.To] = true
						footMarked = append(footMarked, fp.To)
					}
				}
			}
		}
		markedList = append(markedList, footMarked...)

		type qEntry struct {
			stopPos int
			stopIdx int
		}
		Q := make(map[int]qEntry, len(markedList)*3)

		for _, sh := range markedList {
			for _, rsp := range rd.StopRoutes[sh] {
				if e, exists := Q[rsp.RouteIdx]; !exists || rsp.StopPos < e.stopPos {
					Q[rsp.RouteIdx] = qEntry{stopPos: rsp.StopPos, stopIdx: sh}
				}
			}
		}

		for _, sh := range markedList {
			marked[sh] = false
		}
		markedList = markedList[:0]

		for ri, entry := range Q {
			route := &rd.Routes[ri]
			var curTrip *RaptorTrip

			for pos := entry.stopPos; pos < len(route.Stops); pos++ {
				sh := route.Stops[pos]

				if curTrip != nil {
					arr := curTrip.Times[pos].Arrival
					if arr < depTimeSec {
						continue
					}
					if arr < tau[sh] && arr <= maxArrival {
						tau[sh] = arr
						transfers[sh] = round
						if !marked[sh] {
							marked[sh] = true
							markedList = append(markedList, sh)
						}
					}
				}

				stopTau := tau[sh]
				if stopTau == Unreachable || stopTau < depTimeSec {
					continue
				}
				if curTrip == nil || stopTau <= curTrip.Times[pos].Departure {
					t := scanner.EarliestTrip(ri, pos, stopTau)
					if t != nil && (curTrip == nil || t.Times[pos].Departure < curTrip.Times[pos].Departure) {
						curTrip = t
					}
				}
			}
		}
	}

	return tau, transfers, usedFP
}

const UnreachableBackward = int32(-1)

func (rd *RaptorData) QueryWithTransfersScannerSourcesBackward(
	sources []Source,
	arrTimeSec int32,
	scanner *RouteScanner,
	maxCutoffSec int32,
) (tau []int32, transfers []int, usedFP map[FPKey]bool) {
	n := len(rd.Stops)
	tau = make([]int32, n)
	transfers = make([]int, n)
	for i := range tau {
		tau[i] = UnreachableBackward
		transfers[i] = -1
	}
	usedFP = make(map[FPKey]bool)

	marked := make([]bool, n)
	markedList := make([]int, 0, len(sources))
	for _, source := range sources {
		if source.StopIdx < 0 || source.StopIdx >= n {
			continue
		}
		if source.Time > arrTimeSec {
			source.Time = arrTimeSec
		}
		if source.Time <= tau[source.StopIdx] {
			continue
		}
		tau[source.StopIdx] = source.Time
		transfers[source.StopIdx] = 0
		if !marked[source.StopIdx] {
			marked[source.StopIdx] = true
			markedList = append(markedList, source.StopIdx)
		}
	}

	minDeparture := arrTimeSec - maxCutoffSec

	const walkSpeed = 1.4

	// Index foot paths by To stop for fast backward lookup
	footByTo := make([][]FootPath, n)
	for i := range rd.FootPaths {
		fp := rd.FootPaths[i]
		footByTo[fp.To] = append(footByTo[fp.To], fp)
	}

	const maxRounds = 6

	for round := 0; round < maxRounds; round++ {
		if len(markedList) == 0 {
			break
		}

		// Backward Foot path phase
		footMarked := make([]int, 0)
		for _, sh := range markedList {
			for _, fp := range footByTo[sh] {
				walkTime := int32(fp.DistM / walkSpeed)
				dep := tau[sh] - walkTime
				if dep <= arrTimeSec && dep > tau[fp.From] && dep >= minDeparture {
					tau[fp.From] = dep
					transfers[fp.From] = transfers[sh]
					usedFP[FPKey{fp.From, fp.To}] = true
					if !marked[fp.From] {
						marked[fp.From] = true
						footMarked = append(footMarked, fp.From)
					}
				}
			}
		}
		markedList = append(markedList, footMarked...)

		// Collect routes Q: routeIdx -> latest stop position among marked stops
		type qEntry struct {
			stopPos int
		}
		Q := make(map[int]qEntry, len(markedList)*3)

		for _, sh := range markedList {
			for _, rsp := range rd.StopRoutes[sh] {
				if e, exists := Q[rsp.RouteIdx]; !exists || rsp.StopPos > e.stopPos {
					Q[rsp.RouteIdx] = qEntry{stopPos: rsp.StopPos}
				}
			}
		}

		for _, sh := range markedList {
			marked[sh] = false
		}
		markedList = markedList[:0]

		for ri, entry := range Q {
			route := &rd.Routes[ri]
			var curTrip *RaptorTrip

			for pos := entry.stopPos; pos >= 0; pos-- {
				sh := route.Stops[pos]

				if curTrip != nil {
					dep := curTrip.Times[pos].Departure
					if dep > arrTimeSec {
						continue
					}
					if dep > tau[sh] && dep >= minDeparture {
						tau[sh] = dep
						transfers[sh] = round
						if !marked[sh] {
							marked[sh] = true
							markedList = append(markedList, sh)
						}
					}
				}

				stopTau := tau[sh]
				if stopTau == UnreachableBackward || stopTau > arrTimeSec {
					continue
				}
				if curTrip == nil || stopTau >= curTrip.Times[pos].Arrival {
					t := scanner.LatestTrip(ri, pos, stopTau)
					if t != nil && (curTrip == nil || t.Times[pos].Arrival > curTrip.Times[pos].Arrival) {
						curTrip = t
					}
				}
			}
		}
	}

	return tau, transfers, usedFP
}

// earliestTrip finds the earliest trip on route that departs stop at position pos
// at or after minDep, restricted to active services.
func earliestTrip(route *RaptorRoute, pos int, minDep int32, activeServices map[string]bool) *RaptorTrip {
	var best *RaptorTrip
	for i := range route.Trips {
		t := &route.Trips[i]
		if !activeServices[t.ServiceID] {
			continue
		}
		dep := t.Times[pos].Departure
		if dep < minDep {
			continue
		}
		if best == nil || dep < best.Times[pos].Departure {
			best = t
		}
	}
	return best
}
