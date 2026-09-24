// Developed by Bombs King, Taipei Codefest 2026

package raptor

import "testing"

func TestRouteScannerEarliestTripMatchesLinearSearch(t *testing.T) {
	route := RaptorRoute{
		Stops: []int{0, 1},
		Trips: []RaptorTrip{
			{ServiceID: "inactive", Times: []StopTimeEntry{{Departure: 100}, {Departure: 200}}},
			{ServiceID: "active", Times: []StopTimeEntry{{Departure: 300}, {Departure: 400}}},
			{ServiceID: "active", Times: []StopTimeEntry{{Departure: 500}, {Departure: 600}}},
		},
	}
	rd := &RaptorData{Routes: []RaptorRoute{route}}
	active := map[string]bool{"active": true}
	scanner := NewRouteScanner(rd, active)

	got := scanner.EarliestTrip(0, 1, 350)
	want := earliestTrip(&rd.Routes[0], 1, 350, active)
	if got != want {
		t.Fatalf("scanner trip mismatch: got %p want %p", got, want)
	}
	if got == nil || got.Times[1].Departure != 400 {
		t.Fatalf("expected departure 400, got %#v", got)
	}
}

func TestRouteScannerSkipsInactiveTrips(t *testing.T) {
	rd := &RaptorData{Routes: []RaptorRoute{{
		Stops: []int{0},
		Trips: []RaptorTrip{
			{ServiceID: "inactive", Times: []StopTimeEntry{{Departure: 100}}},
			{ServiceID: "active", Times: []StopTimeEntry{{Departure: 300}}},
		},
	}}}
	scanner := NewRouteScanner(rd, map[string]bool{"active": true})

	got := scanner.EarliestTrip(0, 0, 0)
	if got == nil || got.ServiceID != "active" {
		t.Fatalf("expected active trip, got %#v", got)
	}
}

func TestRouteScannerReturnsNilWhenNoTripFound(t *testing.T) {
	rd := &RaptorData{Routes: []RaptorRoute{{
		Stops: []int{0},
		Trips: []RaptorTrip{
			{ServiceID: "active", Times: []StopTimeEntry{{Departure: 100}}},
		},
	}}}
	scanner := NewRouteScanner(rd, map[string]bool{"active": true})

	if got := scanner.EarliestTrip(0, 0, 200); got != nil {
		t.Fatalf("expected nil trip, got %#v", got)
	}
}
