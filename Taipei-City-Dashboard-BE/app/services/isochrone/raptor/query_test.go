// Developed by Bombs King, Taipei Codefest 2026

package raptor

import "testing"

func TestQueryRejectsArrivalsBeforeDeparture(t *testing.T) {
	rd := &RaptorData{
		Stops: []RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Impossible", Lat: 25.0488, Lon: 121.5184},
		},
		Routes: []RaptorRoute{{
			ID:    "bus:r",
			Stops: []int{0, 1},
			Trips: []RaptorTrip{{
				ServiceID: "svc",
				Times: []StopTimeEntry{
					{Arrival: 28800, Departure: 28800},
					{Arrival: 60, Departure: 60},
				},
			}},
		}},
		StopRoutes: [][]RouteStopPos{
			{{RouteIdx: 0, StopPos: 0}},
			{{RouteIdx: 0, StopPos: 1}},
		},
	}

	tau := rd.Query(0, 28800, map[string]bool{"svc": true}, 900)
	if tau[1] != Unreachable {
		t.Fatalf("expected pre-departure arrival to be rejected, got %d", tau[1])
	}
}

func TestQueryBackward(t *testing.T) {
	rd := &RaptorData{
		Stops: []RaptorStop{
			{ID: "s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "s1", Name: "Destination", Lat: 25.0488, Lon: 121.5184},
		},
		Routes: []RaptorRoute{{
			ID:    "bus:r",
			Stops: []int{0, 1},
			Trips: []RaptorTrip{{
				ServiceID: "svc",
				Times: []StopTimeEntry{
					{Arrival: 28000, Departure: 28100}, // s0
					{Arrival: 28700, Departure: 28800}, // s1
				},
			}},
		}},
		StopRoutes: [][]RouteStopPos{
			{{RouteIdx: 0, StopPos: 0}},
			{{RouteIdx: 0, StopPos: 1}},
		},
	}

	active := map[string]bool{"svc": true}
	scanner := NewRouteScanner(rd, active)
	sources := []Source{{StopIdx: 1, Time: 28800}} // Arrive at s1 by 08:00:00

	tau, _, _ := rd.QueryWithTransfersScannerSourcesBackward(sources, 28800, scanner, 3600)

	if tau[1] != 28800 {
		t.Errorf("expected destination tau to be 28800, got %d", tau[1])
	}
	if tau[0] != 28100 {
		t.Errorf("expected origin tau to be 28100 (latest departure), got %d", tau[0])
	}
}
