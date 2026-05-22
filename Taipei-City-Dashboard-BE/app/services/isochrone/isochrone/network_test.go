package isochrone

import (
	"encoding/json"
	"testing"

	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

func TestGenerateNetworkIgnoresArrivalsBeforeDeparture(t *testing.T) {
	rd := &raptor.RaptorData{
		Stops: []raptor.RaptorStop{
			{ID: "bus:s0", Name: "Origin", Lat: 25.0478, Lon: 121.5174},
			{ID: "bus:s1", Name: "Invalid Early", Lat: 25.0488, Lon: 121.5184},
		},
		Routes: []raptor.RaptorRoute{{
			ID:    "bus:r",
			Stops: []int{0, 1},
		}},
	}

	data, err := GenerateNetwork(rd, []int32{28800, 60}, []int{0, 0}, make(map[raptor.FPKey]bool), 28800, []int32{900}, -1, "", false)
	if err != nil {
		t.Fatalf("GenerateNetwork returned error: %v", err)
	}

	var fc FeatureCollection
	if err := json.Unmarshal(data, &fc); err != nil {
		t.Fatalf("unmarshal network: %v", err)
	}
	for _, f := range fc.Features {
		if f.Properties["stop_id"] == "bus:s1" {
			t.Fatalf("pre-departure stop should not be included: %#v", f.Properties)
		}
	}
}
