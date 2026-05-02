package raptor

import "math"

const Unreachable = int32(math.MaxInt32)

// RaptorData holds the preprocessed transit network ready for RAPTOR queries.
type RaptorData struct {
	Stops      []RaptorStop
	Routes     []RaptorRoute
	StopRoutes [][]RouteStopPos // for each stop: which routes serve it and at which position
	StopIndex  map[string]int   // prefixed stop_id ("bus:Stop_X") → stop handle
	FootPaths  []FootPath       // precomputed nearby-stop pairs for walking transfers
}

// FootPath represents a walking transfer between two stops.
type FootPath struct {
	From  int
	To    int
	DistM float64 // distance in metres
}

type Source struct {
	StopIdx int
	Time    int32
}

type RaptorStop struct {
	ID   string
	Name string
	Lat  float64
	Lon  float64
}

// RaptorRoute represents one GTFS route direction as an ordered stop sequence.
// Each route in RAPTOR terms corresponds to a (route_id, direction) pair —
// or simply to all trips sharing the same stop sequence.
type RaptorRoute struct {
	ID            string
	Stops         []int        // ordered stop handles
	Trips         []RaptorTrip // sorted by departure time at Stops[0]
	SegmentShapes [][]Coord    // shape geometry for each adjacent stop pair
}

type Coord struct {
	Lon  float64
	Lat  float64
	Part int
}

type RaptorTrip struct {
	ServiceID string
	Times     []StopTimeEntry // index matches Route.Stops
}

type StopTimeEntry struct {
	Arrival   int32 // seconds since midnight
	Departure int32
}

// RouteStopPos records that a route passes through a stop at a given position.
type RouteStopPos struct {
	RouteIdx int
	StopPos  int
}
