package raptor

import (
	"testing"

	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
)

func TestBuildMergesNearbySameNameBusStops(t *testing.T) {
	feed := testFeed("bus:", map[string]*gtfs.RawStop{
		"a": {ID: "a", Name: "Taipei Main", Lat: 25.04780, Lon: 121.51740},
		"b": {ID: "b", Name: "Taipei Main", Lat: 25.04790, Lon: 121.51750},
		"c": {ID: "c", Name: "Zhongshan", Lat: 25.05200, Lon: 121.52000},
	}, []gtfs.RawStopTime{
		{StopID: "a", Sequence: 1, Arrival: 28800, Dep: 28800},
		{StopID: "c", Sequence: 2, Arrival: 29100, Dep: 29100},
	}, []gtfs.RawStopTime{
		{StopID: "b", Sequence: 1, Arrival: 28800, Dep: 28800},
		{StopID: "c", Sequence: 2, Arrival: 29100, Dep: 29100},
	})

	rd, err := Build([]*gtfs.Feed{feed})
	if err != nil {
		t.Fatal(err)
	}

	if rd.StopIndex["bus:a"] != rd.StopIndex["bus:b"] {
		t.Fatalf("expected same-name nearby bus stops to merge, got %d and %d", rd.StopIndex["bus:a"], rd.StopIndex["bus:b"])
	}
	if len(rd.Stops) != 2 {
		t.Fatalf("expected 2 merged stops, got %d", len(rd.Stops))
	}
}

func TestBuildKeepsDistantSameNameBusStopsSeparate(t *testing.T) {
	feed := testFeed("bus:", map[string]*gtfs.RawStop{
		"a": {ID: "a", Name: "Same Name", Lat: 25.04780, Lon: 121.51740},
		"b": {ID: "b", Name: "Same Name", Lat: 25.14780, Lon: 121.61740},
	}, []gtfs.RawStopTime{
		{StopID: "a", Sequence: 1, Arrival: 28800, Dep: 28800},
		{StopID: "b", Sequence: 2, Arrival: 29100, Dep: 29100},
	})

	rd, err := Build([]*gtfs.Feed{feed})
	if err != nil {
		t.Fatal(err)
	}

	if rd.StopIndex["bus:a"] == rd.StopIndex["bus:b"] {
		t.Fatalf("expected distant same-name bus stops to stay separate")
	}
	if len(rd.Stops) != 2 {
		t.Fatalf("expected 2 stops, got %d", len(rd.Stops))
	}
}

func testFeed(prefix string, stops map[string]*gtfs.RawStop, trips ...[]gtfs.RawStopTime) *gtfs.Feed {
	feed := &gtfs.Feed{
		Prefix:    prefix,
		Stops:     stops,
		Routes:    map[string]*gtfs.RawRoute{"r": {ID: "r"}},
		Trips:     make(map[string]*gtfs.RawTrip),
		StopTimes: make(map[string][]gtfs.RawStopTime),
		Calendar:  make(map[string]*gtfs.ServicePattern),
		CalDates:  make(map[string][]gtfs.CalDateException),
		Freqs:     make(map[string][]gtfs.FreqEntry),
	}
	for i, stopTimes := range trips {
		tripID := string(rune('a' + i))
		feed.Trips[tripID] = &gtfs.RawTrip{ID: tripID, RouteID: "r", ServiceID: "svc"}
		feed.StopTimes[tripID] = stopTimes
	}
	return feed
}
