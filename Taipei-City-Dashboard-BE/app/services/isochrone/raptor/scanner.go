// Developed by Bombs King, Taipei Codefest 2026

package raptor

import (
	"sort"
	"sync"
)

type RouteScanner struct {
	rd          *RaptorData
	activeTrips [][]int

	mu    sync.RWMutex
	cache map[routePosTypeKey][]tripTime
}

type routePosTypeKey struct {
	routeIdx int
	stopPos  int
	isDep    bool
}

type tripTime struct {
	time int32
	trip *RaptorTrip
}

func NewRouteScanner(rd *RaptorData, activeServices map[string]bool) *RouteScanner {
	return NewRouteScannerWithRouteFilter(rd, activeServices, nil)
}

func NewRouteScannerWithRouteFilter(rd *RaptorData, activeServices map[string]bool, allowRoute func(routeID string) bool) *RouteScanner {
	activeTrips := make([][]int, len(rd.Routes))
	for routeIdx := range rd.Routes {
		route := &rd.Routes[routeIdx]
		if allowRoute != nil && !allowRoute(route.ID) {
			continue
		}
		for tripIdx := range route.Trips {
			if activeServices[route.Trips[tripIdx].ServiceID] {
				activeTrips[routeIdx] = append(activeTrips[routeIdx], tripIdx)
			}
		}
	}

	return &RouteScanner{
		rd:          rd,
		activeTrips: activeTrips,
		cache:       make(map[routePosTypeKey][]tripTime),
	}
}

func (s *RouteScanner) WithRouteFilter(allowRoute func(routeID string) bool) *RouteScanner {
	if allowRoute == nil {
		return s
	}
	activeTrips := make([][]int, len(s.rd.Routes))
	for routeIdx := range s.rd.Routes {
		if !allowRoute(s.rd.Routes[routeIdx].ID) {
			continue
		}
		activeTrips[routeIdx] = append(activeTrips[routeIdx], s.activeTrips[routeIdx]...)
	}
	return &RouteScanner{
		rd:          s.rd,
		activeTrips: activeTrips,
		cache:       make(map[routePosTypeKey][]tripTime),
	}
}

func (s *RouteScanner) EarliestTrip(routeIdx, stopPos int, minDep int32) *RaptorTrip {
	trips := s.tripsAt(routeIdx, stopPos, true)
	i := sort.Search(len(trips), func(i int) bool {
		return trips[i].time >= minDep
	})
	if i >= len(trips) {
		return nil
	}
	return trips[i].trip
}

func (s *RouteScanner) LatestTrip(routeIdx, stopPos int, maxArr int32) *RaptorTrip {
	trips := s.tripsAt(routeIdx, stopPos, false)
	// trips are sorted by arrival time ASC
	// We want the last trip where arrival <= maxArr
	i := sort.Search(len(trips), func(i int) bool {
		return trips[i].time > maxArr
	})
	if i == 0 {
		return nil
	}
	return trips[i-1].trip
}

func (s *RouteScanner) tripsAt(routeIdx, stopPos int, isDep bool) []tripTime {
	key := routePosTypeKey{routeIdx: routeIdx, stopPos: stopPos, isDep: isDep}

	s.mu.RLock()
	if trips, ok := s.cache[key]; ok {
		s.mu.RUnlock()
		return trips
	}
	s.mu.RUnlock()

	s.mu.Lock()
	defer s.mu.Unlock()
	if trips, ok := s.cache[key]; ok {
		return trips
	}

	route := &s.rd.Routes[routeIdx]
	trips := make([]tripTime, 0, len(s.activeTrips[routeIdx]))
	for _, tripIdx := range s.activeTrips[routeIdx] {
		trip := &route.Trips[tripIdx]
		if stopPos < 0 || stopPos >= len(trip.Times) {
			continue
		}
		var t int32
		if isDep {
			t = trip.Times[stopPos].Departure
		} else {
			t = trip.Times[stopPos].Arrival
		}
		trips = append(trips, tripTime{
			time: t,
			trip: trip,
		})
	}
	sort.Slice(trips, func(i, j int) bool {
		return trips[i].time < trips[j].time
	})
	s.cache[key] = trips
	return trips
}
