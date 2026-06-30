// Developed by Bombs King, Taipei Codefest 2026

package transit

import (
	"bytes"
	"encoding/gob"
	"encoding/json"
	"fmt"
	"time"

	"TaipeiCityDashboardBE/app/cache"
	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

const (
	keyRaptorGob   = "gtfs:raptor:v4:gob"
	keyBuiltAt     = "gtfs:raptor:v4:built_at"
	keyFeedsMeta   = "gtfs:raptor:v4:feedsmeta"
	keyDbUpdatedAt = "gtfs:raptor:v4:db_updated_at"
)

// Save serializes RaptorData to Redis using gob.
func Save(rd *raptor.RaptorData, dbUpdatedAt time.Time) error {
	c := cache.Redis

	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	if err := enc.Encode(rd); err != nil {
		return fmt.Errorf("gob encode RaptorData: %w", err)
	}

	if err := c.Set(keyRaptorGob, buf.Bytes(), 0).Err(); err != nil {
		return fmt.Errorf("redis set RaptorData gob: %w", err)
	}

	c.Set(keyBuiltAt, time.Now().Format(time.RFC3339), 0)
	c.Set(keyDbUpdatedAt, dbUpdatedAt.Format(time.RFC3339), 0)
	return nil
}

// Load deserializes RaptorData from Redis using gob.
func Load() (*raptor.RaptorData, error) {
	c := cache.Redis

	b, err := c.Get(keyRaptorGob).Bytes()
	if err != nil {
		return nil, fmt.Errorf("redis get RaptorData gob: %w", err)
	}

	rd := &raptor.RaptorData{}
	dec := gob.NewDecoder(bytes.NewReader(b))
	if err := dec.Decode(rd); err != nil {
		return nil, fmt.Errorf("gob decode RaptorData: %w", err)
	}

	return rd, nil
}

// BuiltAt returns the timestamp string of when the RAPTOR data was last built.
func BuiltAt() (string, error) {
	return cache.Redis.Get(keyBuiltAt).Result()
}

// SaveFeedsMeta serializes pruned feeds to Redis.
func SaveFeedsMeta(feeds []*gtfs.Feed) error {
	b, err := json.Marshal(feeds)
	if err != nil {
		return fmt.Errorf("marshal feeds meta: %w", err)
	}
	return cache.Redis.Set(keyFeedsMeta, b, 0).Err()
}

// LoadFeedsMeta deserializes pruned feeds from Redis.
func LoadFeedsMeta() ([]*gtfs.Feed, error) {
	b, err := cache.Redis.Get(keyFeedsMeta).Bytes()
	if err != nil {
		return nil, fmt.Errorf("get feeds meta: %w", err)
	}
	var feeds []*gtfs.Feed
	if err := json.Unmarshal(b, &feeds); err != nil {
		return nil, fmt.Errorf("unmarshal feeds meta: %w", err)
	}
	return feeds, nil
}

// CacheIsValid checks if the cached RaptorData in Redis is still valid
// by comparing its cached DB updated_at timestamp with the actual database timestamp.
func CacheIsValid(dbUpdatedAt time.Time) bool {
	cachedStr, err := cache.Redis.Get(keyDbUpdatedAt).Result()
	if err != nil {
		return false
	}
	return cachedStr == dbUpdatedAt.Format(time.RFC3339)
}
