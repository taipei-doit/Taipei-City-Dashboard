// Developed by Bombs King, Taipei Codefest 2026

package transit

import (
	"fmt"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/cache"
)

const isoTTL = time.Hour
const resultCacheVersion = "v6"

// isoKey builds a deterministic Redis key for an isochrone query result.
// depTimeSec is quantised to 15-minute buckets so nearby queries share cache.
func isoKey(origin string, depTimeSec int32, date time.Time, profile string, modes []string, cutoffs []int32, timeType string) string {
	bucket := depTimeSec / 900
	return fmt.Sprintf("gtfs:iso:%s:%s:%d:%s:%s:%s:%s:%s", resultCacheVersion, origin, bucket, date.Format("20060102"), profile, modesKey(modes), cutoffsKey(cutoffs), timeType)
}

// netKey builds a deterministic Redis key for a network query result.
func netKey(origin string, depTimeSec int32, date time.Time, profile string, modes []string, cutoffs []int32, maxTransfers int, timeType string) string {
	bucket := depTimeSec / 900
	return fmt.Sprintf("gtfs:net:%s:%s:%d:%s:%s:%s:%s:%d:%s", resultCacheVersion, origin, bucket, date.Format("20060102"), profile, modesKey(modes), cutoffsKey(cutoffs), maxTransfers, timeType)
}

func fullKey(origin string, depTimeSec int32, date time.Time, profile string, modes []string, cutoffs []int32, maxTransfers int, timeType string) string {
	bucket := depTimeSec / 900
	return fmt.Sprintf("gtfs:full:%s:%s:%d:%s:%s:%s:%s:%d:%s", resultCacheVersion, origin, bucket, date.Format("20060102"), profile, modesKey(modes), cutoffsKey(cutoffs), maxTransfers, timeType)
}

func modesKey(modes []string) string {
	if len(modes) == 0 {
		return "all"
	}
	return strings.Join(modes, ",")
}

func cutoffsKey(cutoffs []int32) string {
	if len(cutoffs) == 0 {
		return "default"
	}
	parts := make([]string, len(cutoffs))
	for i, cutoff := range cutoffs {
		parts[i] = fmt.Sprint(cutoff)
	}
	return strings.Join(parts, ",")
}

func cacheGet(key string) ([]byte, bool) {
	b, err := cache.Redis.Get(key).Bytes()
	if err != nil {
		return nil, false
	}
	return b, true
}

func cacheSet(key string, val []byte) {
	cache.Redis.Set(key, val, isoTTL)
}
