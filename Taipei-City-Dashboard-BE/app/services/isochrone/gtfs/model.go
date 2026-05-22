// Developed by Bombs King, Taipei Codefest 2026

package gtfs

import "time"

// Feed holds all parsed data from one GTFS feed directory.
type Feed struct {
	Prefix    string // "bus:", "rail:", "train:"
	Stops     map[string]*RawStop
	Routes    map[string]*RawRoute
	Trips     map[string]*RawTrip
	StopTimes map[string][]RawStopTime // trip_id ??stop times sorted by sequence
	Shapes    map[string][]RawShapePoint
	Calendar  map[string]*ServicePattern
	CalDates  map[string][]CalDateException
	Freqs     map[string][]FreqEntry // trip_id ??frequency entries
}

type RawStop struct {
	ID            string
	Name          string
	Lat           float64
	Lon           float64
	ParentStation string
}

type RawRoute struct {
	ID        string
	ShortName string
	LongName  string
	RouteType int
}

type RawTrip struct {
	ID        string
	RouteID   string
	ServiceID string
	ShapeID   string
}
type RawShapePoint struct {
	Lat      float64
	Lon      float64
	Sequence int
	Part     int
}

// RawStopTime holds one stop_times row. Times are seconds since midnight (can exceed 86400).
type RawStopTime struct {
	StopID   string
	Sequence int
	Arrival  int32
	Dep      int32
}

type ServicePattern struct {
	Weekdays  [7]bool // index 0=Monday ??6=Sunday
	StartDate time.Time
	EndDate   time.Time
}

type CalDateException struct {
	Date time.Time
	Type int // 1=service added, 2=service removed
}

type FreqEntry struct {
	StartTime  int32 // seconds since midnight
	EndTime    int32
	HeadwaySec int32
}
