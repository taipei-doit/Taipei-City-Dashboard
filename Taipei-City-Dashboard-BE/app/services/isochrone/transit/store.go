// Developed by Bombs King, Taipei Codefest 2026

package transit

import (
	"encoding/json"
	"fmt"
	"time"

	"TaipeiCityDashboardBE/app/cache"
	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

const (
	keyStops      = "gtfs:raptor:v4:stops"
	keyStopRoutes = "gtfs:raptor:v4:stoproutes"
	keyStopIndex  = "gtfs:raptor:v4:stopindex"
	keyRouteMeta  = "gtfs:raptor:v4:routemeta" // []routeMetaEntry (ID + Stops + SegmentShapes, no Trips)
	keyRouteCount = "gtfs:raptor:v4:routecount"
	keyRouteFmt   = "gtfs:raptor:v4:route:%d" // per-route trips blob
	keyBuiltAt    = "gtfs:raptor:v4:built_at"
	routeBatchSz  = 200
)

type routeMetaEntry struct {
	ID            string
	Stops         []int
	SegmentShapes [][]raptor.Coord
}

// Save serializes RaptorData to Redis. Routes are stored in batches of routeBatchSz
// to stay within Redis value size limits for large trip datasets.
func Save(rd *raptor.RaptorData) error {
	c := cache.Redis

	// stops
	if b, err := json.Marshal(rd.Stops); err == nil {
		c.Set(keyStops, b, 0)
	} else {
		return fmt.Errorf("marshal stops: %w", err)
	}

	// stop ??routes index
	if b, err := json.Marshal(rd.StopRoutes); err == nil {
		c.Set(keyStopRoutes, b, 0)
	} else {
		return fmt.Errorf("marshal stoproutes: %w", err)
	}

	// stop id ??index map
	if b, err := json.Marshal(rd.StopIndex); err == nil {
		c.Set(keyStopIndex, b, 0)
	} else {
		return fmt.Errorf("marshal stopindex: %w", err)
	}

	// route metadata (ID + stop handles, without trips)
	metas := make([]routeMetaEntry, len(rd.Routes))
	for i, r := range rd.Routes {
		metas[i] = routeMetaEntry{
			ID:            r.ID,
			Stops:         r.Stops,
			SegmentShapes: r.SegmentShapes,
		}
	}
	if b, err := json.Marshal(metas); err == nil {
		c.Set(keyRouteMeta, b, 0)
	} else {
		return fmt.Errorf("marshal routemeta: %w", err)
	}

	// store trip data per route in individual keys
	c.Set(keyRouteCount, fmt.Sprint(len(rd.Routes)), 0)
	for i, r := range rd.Routes {
		b, err := json.Marshal(r.Trips)
		if err != nil {
			return fmt.Errorf("marshal route %d trips: %w", i, err)
		}
		c.Set(fmt.Sprintf(keyRouteFmt, i), b, 0)
	}

	c.Set(keyBuiltAt, time.Now().Format(time.RFC3339), 0)
	return nil
}

// Load deserializes RaptorData from Redis.
func Load() (*raptor.RaptorData, error) {
	c := cache.Redis
	rd := &raptor.RaptorData{}

	// stops
	b, err := c.Get(keyStops).Bytes()
	if err != nil {
		return nil, fmt.Errorf("get stops: %w", err)
	}
	if err := json.Unmarshal(b, &rd.Stops); err != nil {
		return nil, fmt.Errorf("unmarshal stops: %w", err)
	}

	// stop ??routes index
	b, err = c.Get(keyStopRoutes).Bytes()
	if err != nil {
		return nil, fmt.Errorf("get stoproutes: %w", err)
	}
	if err := json.Unmarshal(b, &rd.StopRoutes); err != nil {
		return nil, fmt.Errorf("unmarshal stoproutes: %w", err)
	}

	// stop id ??index map
	b, err = c.Get(keyStopIndex).Bytes()
	if err != nil {
		return nil, fmt.Errorf("get stopindex: %w", err)
	}
	if err := json.Unmarshal(b, &rd.StopIndex); err != nil {
		return nil, fmt.Errorf("unmarshal stopindex: %w", err)
	}

	// route metadata
	b, err = c.Get(keyRouteMeta).Bytes()
	if err != nil {
		return nil, fmt.Errorf("get routemeta: %w", err)
	}
	var metas []routeMetaEntry
	if err := json.Unmarshal(b, &metas); err != nil {
		return nil, fmt.Errorf("unmarshal routemeta: %w", err)
	}

	// route trips
	countStr, err := c.Get(keyRouteCount).Result()
	if err != nil {
		return nil, fmt.Errorf("get routecount: %w", err)
	}
	var count int
	fmt.Sscan(countStr, &count)

	rd.Routes = make([]raptor.RaptorRoute, count)
	for i := 0; i < count; i++ {
		rd.Routes[i].ID = metas[i].ID
		rd.Routes[i].Stops = metas[i].Stops
		rd.Routes[i].SegmentShapes = metas[i].SegmentShapes

		b, err = c.Get(fmt.Sprintf(keyRouteFmt, i)).Bytes()
		if err != nil {
			return nil, fmt.Errorf("get route %d: %w", i, err)
		}
		if err := json.Unmarshal(b, &rd.Routes[i].Trips); err != nil {
			return nil, fmt.Errorf("unmarshal route %d trips: %w", i, err)
		}
	}

	return rd, nil
}

// BuiltAt returns the timestamp string of when the RAPTOR data was last built.
func BuiltAt() (string, error) {
	return cache.Redis.Get(keyBuiltAt).Result()
}
