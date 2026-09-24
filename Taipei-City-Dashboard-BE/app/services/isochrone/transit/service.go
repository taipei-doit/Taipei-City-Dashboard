// Developed by Bombs King, Taipei Codefest 2026

package transit

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"runtime"
	"sort"
	"strings"
	"sync/atomic"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
	"TaipeiCityDashboardBE/app/services/isochrone/isochrone"
	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
	"TaipeiCityDashboardBE/logs"
)

const (
	accessWalkRadiusM         = 800.0
	accessWalkSpeed           = 1.4
	DefaultMaxTransfers       = -1
	defaultMaxCutoffSec int32 = 7200
	transitModeBus            = "bus"
	transitModeJumpfrog       = "jumpfrog"
	transitModeRail           = "rail"
	transitModeTrain          = "train"
)

type gtfsFeedSpec struct {
	sub    string
	prefix string
}

var (
	defaultTransitModes = []string{
		transitModeBus,
		transitModeJumpfrog,
		transitModeRail,
		transitModeTrain,
	}
	allowedTransitModes = map[string]bool{
		transitModeBus:      true,
		transitModeJumpfrog: true,
		transitModeRail:     true,
		transitModeTrain:    true,
	}
	runtimeFeedSpecs = []gtfsFeedSpec{
		{sub: transitModeBus, prefix: transitModeBus + ":"},
		{sub: transitModeRail, prefix: transitModeRail + ":"},
		{sub: transitModeTrain, prefix: transitModeTrain + ":"},
	}
)

// Service holds the loaded RAPTOR data and provides isochrone queries.
type Service struct {
	rd       *raptor.RaptorData
	idx      *isochrone.IsochroneIndex
	feeds    []*gtfs.Feed // kept for compatibility and profile scanner construction
	scanners map[gtfs.ServiceProfile]*raptor.RouteScanner
}

var current atomic.Pointer[Service]

// InitService loads RAPTOR data from DB and initialises the global service.
// Call this once at application startup, after database connection.
func InitService() error {
	db, err := models.DBDashboard.DB()
	if err != nil {
		return fmt.Errorf("transit: get DBDashboard sql.DB: %w", err)
	}

	svc, err := buildFromDB(db)
	if err != nil {
		return fmt.Errorf("transit: initial build from DB failed: %w", err)
	}

	current.Store(svc)

	go watchAndReload(db)

	return nil
}

// DefaultService returns the package-level Service, or an error if not initialised.
func DefaultService() (*Service, error) {
	svc := current.Load()
	if svc == nil {
		return nil, errors.New("transit service not initialised; call InitService first")
	}
	return svc, nil
}

func buildFromDB(db *sql.DB) (*Service, error) {
	// Get the latest DB updated_at timestamp to validate cache freshness
	var dbUpdatedAt time.Time
	_ = db.QueryRow("SELECT max(updated_at) FROM gtfs_bundle").Scan(&dbUpdatedAt)

	// 1. Try loading pre-built data from Redis first, only if the cache is valid
	if CacheIsValid(dbUpdatedAt) {
		if rd, err := Load(); err == nil && rd != nil {
			if feeds, err := LoadFeedsMeta(); err == nil && len(feeds) > 0 {
				logs.FInfo("Transit: successfully loaded pre-built RaptorData and Feeds from Redis cache")
				return &Service{
					rd:       rd,
					idx:      isochrone.NewIsochroneIndex(rd),
					feeds:    feeds,
					scanners: buildProfileScanners(rd, feeds),
				}, nil
			}
		}
	}

	// 2. Redis cache miss or invalid, fallback to rebuilding from DB ZIPs
	logs.FInfo("Transit: Redis cache stale or miss, rebuilding raptor data from SQL DB...")
	feeds := make([]*gtfs.Feed, 0, 4)
	for _, name := range []string{"bus", "rail", "train"} {
		var blob []byte
		err := db.QueryRow("SELECT archive FROM gtfs_bundle WHERE feed=$1", name).Scan(&blob)
		if err != nil {
			return nil, fmt.Errorf("query feed %s: %w", name, err)
		}
		f, err := gtfs.LoadFeedFromZip(blob, name+":")
		if err != nil {
			return nil, fmt.Errorf("load feed %s from zip: %w", name, err)
		}
		feeds = append(feeds, f)
		blob = nil   // Explicitly release binary data from memory
		runtime.GC() // Garbage collect immediately to prevent memory heap pile-up
	}
	feeds = append(feeds, gtfs.SplitJumpfrog(feeds[0])) // bus -> jumpfrog
	rd, err := raptor.Build(feeds)
	if err != nil {
		return nil, fmt.Errorf("raptor build: %w", err)
	}

	scanners := buildProfileScanners(rd, feeds)

	// 3. Prune large raw arrays/maps from feeds metadata to save heap space
	for _, f := range feeds {
		f.Stops = nil
		f.Routes = nil
		f.StopTimes = nil // This frees ~2GB of RAM
		f.Shapes = nil    // This frees ~1GB of RAM
		f.Freqs = nil
	}

	// 4. Cache the built RaptorData and pruned feeds metadata to Redis asynchronously
	go func(r *raptor.RaptorData, f []*gtfs.Feed, dbTime time.Time) {
		if err := Save(r, dbTime); err != nil {
			logs.FWarn("Transit: failed to cache RaptorData to Redis: %v", err)
			return
		}
		if err := SaveFeedsMeta(f); err != nil {
			logs.FWarn("Transit: failed to cache feeds metadata to Redis: %v", err)
			return
		}
		logs.FInfo("Transit: successfully cached built RaptorData and feeds metadata to Redis")
	}(rd, feeds, dbUpdatedAt)

	// 5. Force GC immediately to return massive temporary allocations back to OS
	runtime.GC()

	return &Service{
		rd:       rd,
		idx:      isochrone.NewIsochroneIndex(rd),
		feeds:    feeds,
		scanners: scanners,
	}, nil
}

func watchAndReload(db *sql.DB) {
	var loaded time.Time
	_ = db.QueryRow("SELECT max(updated_at) FROM gtfs_bundle").Scan(&loaded)

	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		var newest time.Time
		err := db.QueryRow("SELECT max(updated_at) FROM gtfs_bundle").Scan(&newest)
		if err != nil {
			continue
		}
		if newest.After(loaded) {
			svc, err := buildFromDB(db)
			if err != nil {
				continue
			}
			current.Store(svc)
			loaded = newest
		}
	}
}

// IsochroneRequest holds the parameters for a single isochrone query.
type IsochroneRequest struct {
	Lat            float64
	Lon            float64
	TimeType       string // "departure" or "arrival"
	DepartureTime  time.Time
	ServiceProfile string
	Cutoffs        []int32 // seconds; nil ??DefaultCutoffs
	Modes          []string
}

// NetworkRequest holds the parameters for a transit network query.
type NetworkRequest struct {
	Lat            float64
	Lon            float64
	TimeType       string // "departure" or "arrival"
	DepartureTime  time.Time
	Cutoffs        []int32 // seconds; nil ??DefaultCutoffs
	ServiceProfile string
	MaxTransfers   int // max transfers; -1 means no limit
	Modes          []string
}

// FullRequest holds the parameters for a combined isochrone + network query.
type FullRequest = NetworkRequest

// Query runs RAPTOR and returns a GeoJSON FeatureCollection as raw JSON bytes.
func (s *Service) Query(req IsochroneRequest) ([]byte, error) {
	modes := normalizeModes(req.Modes)
	depSec := timeToSec(req.DepartureTime)
	isArrival := req.TimeType == "arrival"

	sources, anchorIdx, err := s.accessSources(req.Lat, req.Lon, modes, depSec, isArrival)
	if err != nil {
		return nil, err
	}

	date := req.DepartureTime.Truncate(24 * time.Hour)
	profile, err := resolveServiceProfile(req.ServiceProfile, req.DepartureTime)
	if err != nil {
		return nil, err
	}
	cutoffs := normalizeCutoffs(req.Cutoffs)

	// 2. Check cache
	key := isoKey(originKey(req.Lat, req.Lon), depSec, date, string(profile), modes, cutoffs, req.TimeType)
	if cached, ok := cacheGet(key); ok {
		return cached, nil
	}

	scanner := s.scannerForModes(profile, modes)
	if scanner == nil {
		return nil, fmt.Errorf("transit: scanner not built for service profile %s", profile)
	}

	// 4. Run RAPTOR
	maxCutoff := maxCutoff(cutoffs)
	var tau []int32
	if isArrival {
		tau, _, _ = s.rd.QueryWithTransfersScannerSourcesBackward(sources, depSec, scanner, maxCutoff)
	} else {
		tau = s.rd.QueryWithScannerSources(sources, depSec, scanner, maxCutoff)
	}

	// 5. Generate isochrone polygons using precomputed index
	result, err := s.idx.Query(tau, depSec, cutoffs, anchorIdx, isArrival)
	if err != nil {
		return nil, err
	}

	// 6. Cache and return
	cacheSet(key, result)
	return result, nil
}

// Network runs RAPTOR and returns a GeoJSON FeatureCollection of reachable
// transit network elements (stops, route segments, walking transfers).
func (s *Service) Network(req NetworkRequest) ([]byte, error) {
	modes := normalizeModes(req.Modes)
	depSec := timeToSec(req.DepartureTime)
	isArrival := req.TimeType == "arrival"

	sources, _, err := s.accessSources(req.Lat, req.Lon, modes, depSec, isArrival)
	if err != nil {
		return nil, err
	}

	date := req.DepartureTime.Truncate(24 * time.Hour)
	profile, err := resolveServiceProfile(req.ServiceProfile, req.DepartureTime)
	if err != nil {
		return nil, err
	}
	cutoffs := normalizeCutoffs(req.Cutoffs)

	// Check cache
	key := netKey(originKey(req.Lat, req.Lon), depSec, date, string(profile), modes, cutoffs, req.MaxTransfers, req.TimeType)
	if cached, ok := cacheGet(key); ok {
		return cached, nil
	}

	scanner := s.scannerForModes(profile, modes)
	if scanner == nil {
		return nil, fmt.Errorf("transit: scanner not built for service profile %s", profile)
	}

	// Run RAPTOR with transfer tracking
	maxCutoff := maxCutoff(cutoffs)
	var tau []int32
	var transfers []int
	var usedFP map[raptor.FPKey]bool

	if isArrival {
		tau, transfers, usedFP = s.rd.QueryWithTransfersScannerSourcesBackward(sources, depSec, scanner, maxCutoff)
	} else {
		tau, transfers, usedFP = s.rd.QueryWithTransfersScannerSources(sources, depSec, scanner, maxCutoff)
	}

	// Generate network GeoJSON
	result, err := isochrone.GenerateNetwork(s.rd, tau, transfers, usedFP, depSec, cutoffs, req.MaxTransfers, "", isArrival)
	if err != nil {
		return nil, err
	}

	cacheSet(key, result)
	return result, nil
}

// Full runs one RAPTOR query and returns isochrone polygons plus network
// features in a single GeoJSON FeatureCollection.
func (s *Service) Full(req FullRequest) ([]byte, error) {
	modes := normalizeModes(req.Modes)
	depSec := timeToSec(req.DepartureTime)
	isArrival := req.TimeType == "arrival"

	sources, anchorIdx, err := s.accessSources(req.Lat, req.Lon, modes, depSec, isArrival)
	if err != nil {
		return nil, err
	}

	date := req.DepartureTime.Truncate(24 * time.Hour)
	profile, err := resolveServiceProfile(req.ServiceProfile, req.DepartureTime)
	if err != nil {
		return nil, err
	}
	cutoffs := normalizeCutoffs(req.Cutoffs)

	key := fullKey(originKey(req.Lat, req.Lon), depSec, date, string(profile), modes, cutoffs, req.MaxTransfers, req.TimeType)
	if cached, ok := cacheGet(key); ok {
		return cached, nil
	}

	scanner := s.scannerForModes(profile, modes)
	if scanner == nil {
		return nil, fmt.Errorf("transit: scanner not built for service profile %s", profile)
	}

	var tau []int32
	var transfers []int
	var usedFP map[raptor.FPKey]bool

	if isArrival {
		tau, transfers, usedFP = s.rd.QueryWithTransfersScannerSourcesBackward(sources, depSec, scanner, maxCutoff(cutoffs))
	} else {
		tau, transfers, usedFP = s.rd.QueryWithTransfersScannerSources(sources, depSec, scanner, maxCutoff(cutoffs))
	}

	isoJSON, err := s.idx.Query(tau, depSec, cutoffs, anchorIdx, isArrival)
	if err != nil {
		return nil, err
	}
	netJSON, err := isochrone.GenerateNetwork(s.rd, tau, transfers, usedFP, depSec, cutoffs, req.MaxTransfers, "", isArrival)
	if err != nil {
		return nil, err
	}

	var isoFC isochrone.FeatureCollection
	if err := json.Unmarshal(isoJSON, &isoFC); err != nil {
		return nil, fmt.Errorf("unmarshal isochrone: %w", err)
	}
	var netFC isochrone.FeatureCollection
	if err := json.Unmarshal(netJSON, &netFC); err != nil {
		return nil, fmt.Errorf("unmarshal network: %w", err)
	}

	for i := range isoFC.Features {
		if isoFC.Features[i].Properties == nil {
			isoFC.Features[i].Properties = make(map[string]interface{})
		}
		isoFC.Features[i].Properties["layer"] = "isochrone"
	}
	for i := range netFC.Features {
		if netFC.Features[i].Properties == nil {
			netFC.Features[i].Properties = make(map[string]interface{})
		}
		netFC.Features[i].Properties["layer"] = "network"
	}

	features := append(isoFC.Features, netFC.Features...)
	result, err := json.Marshal(isochrone.FeatureCollection{Type: "FeatureCollection", Features: features})
	if err != nil {
		return nil, fmt.Errorf("marshal full result: %w", err)
	}

	cacheSet(key, result)
	return result, nil
}

func (s *Service) buildActiveServices(date time.Time) map[string]bool {
	active := make(map[string]bool)
	for _, f := range s.feeds {
		for sid := range f.Calendar {
			if gtfs.IsServiceActive(f, sid, date) {
				active[sid] = true
			}
		}
		for sid := range f.CalDates {
			if gtfs.IsServiceActive(f, sid, date) {
				active[sid] = true
			}
		}
	}
	for _, f := range s.feeds {
		for _, trip := range f.Trips {
			if gtfs.IsServiceActive(f, trip.ServiceID, date) {
				active[trip.ServiceID] = true
			}
		}
	}
	return active
}

func normalizeCutoffs(cutoffs []int32) []int32 {
	if len(cutoffs) == 0 {
		result := make([]int32, len(isochrone.DefaultCutoffs))
		copy(result, isochrone.DefaultCutoffs)
		return result
	}
	result := make([]int32, 0, len(cutoffs))
	for _, cutoff := range cutoffs {
		if cutoff > 0 {
			result = append(result, cutoff)
		}
	}
	if len(result) == 0 {
		return normalizeCutoffs(nil)
	}
	return result
}

func normalizeModes(modes []string) []string {
	if len(modes) == 0 {
		return append([]string(nil), defaultTransitModes...)
	}
	set := make(map[string]bool)
	for _, mode := range modes {
		mode = strings.TrimSpace(strings.ToLower(mode))
		if allowedTransitModes[mode] {
			set[mode] = true
		}
	}
	if len(set) == 0 {
		return append([]string(nil), defaultTransitModes...)
	}
	result := make([]string, 0, len(set))
	for mode := range set {
		result = append(result, mode)
	}
	sort.Strings(result)
	return result
}

func maxCutoff(cutoffs []int32) int32 {
	maxValue := defaultMaxCutoffSec
	for _, cutoff := range cutoffs {
		if cutoff > maxValue {
			maxValue = cutoff
		}
	}
	return maxValue
}

func buildProfileScanners(rd *raptor.RaptorData, feeds []*gtfs.Feed) map[gtfs.ServiceProfile]*raptor.RouteScanner {
	profiles := []gtfs.ServiceProfile{gtfs.ServiceProfileWeekday, gtfs.ServiceProfileHoliday}
	scanners := make(map[gtfs.ServiceProfile]*raptor.RouteScanner, len(profiles))
	for _, profile := range profiles {
		active := make(map[string]bool)
		for _, feed := range feeds {
			for serviceID := range gtfs.ActiveServicesForProfile(feed, profile) {
				active[serviceID] = true
			}
		}
		scanners[profile] = raptor.NewRouteScanner(rd, active)
	}
	return scanners
}

func resolveServiceProfile(value string, depTime time.Time) (gtfs.ServiceProfile, error) {
	if value != "" {
		return gtfs.ParseServiceProfile(value)
	}
	return gtfs.ServiceProfileFromTime(depTime), nil
}

func (s *Service) scannerForModes(profile gtfs.ServiceProfile, modes []string) *raptor.RouteScanner {
	scanner := s.scanners[profile]
	if scanner == nil {
		return nil
	}
	modeSet := modeSet(modes)
	if isAllModes(modeSet) {
		return scanner
	}
	return scanner.WithRouteFilter(func(routeID string) bool {
		return modeSet[extractTransitType(routeID)]
	})
}

// nearestStop finds the stop closest to (lat, lon) by great-circle distance.
func (s *Service) nearestStop(lat, lon float64, modes []string) (int, error) {
	if len(s.rd.Stops) == 0 {
		return 0, errors.New("no stops loaded")
	}
	modeSet := modeSet(modes)
	best := -1
	bestD := math.MaxFloat64
	for i, stop := range s.rd.Stops {
		if !modeSet[extractTransitType(stop.ID)] {
			continue
		}
		d := haversine(lat, lon, stop.Lat, stop.Lon)
		if d < bestD {
			bestD = d
			best = i
		}
	}
	if best < 0 {
		return 0, errors.New("no stop found for selected modes")
	}
	return best, nil
}

func (s *Service) accessSources(lat, lon float64, modes []string, timeSec int32, isArrival bool) ([]raptor.Source, int, error) {
	if len(s.rd.Stops) == 0 {
		return nil, -1, errors.New("no stops loaded")
	}
	modeSet := modeSet(modes)
	sources := make([]raptor.Source, 0)
	best := -1
	bestD := math.MaxFloat64

	for i, stop := range s.rd.Stops {
		if !modeSet[extractTransitType(stop.ID)] {
			continue
		}
		d := haversine(lat, lon, stop.Lat, stop.Lon)
		if d < bestD {
			bestD = d
			best = i
		}
		if d <= accessWalkRadiusM {
			var t int32
			if isArrival {
				t = timeSec - int32(d/accessWalkSpeed)
			} else {
				t = timeSec + int32(d/accessWalkSpeed)
			}
			sources = append(sources, raptor.Source{
				StopIdx: i,
				Time:    t,
			})
		}
	}

	if best < 0 {
		return nil, -1, errors.New("no stop found for selected modes")
	}
	if len(sources) == 0 {
		var t int32
		if isArrival {
			t = timeSec - int32(bestD/accessWalkSpeed)
		} else {
			t = timeSec + int32(bestD/accessWalkSpeed)
		}
		sources = append(sources, raptor.Source{
			StopIdx: best,
			Time:    t,
		})
	}
	return sources, best, nil
}

func originKey(lat, lon float64) string {
	return fmt.Sprintf("%.5f,%.5f", lat, lon)
}

func modeSet(modes []string) map[string]bool {
	set := make(map[string]bool, len(modes))
	for _, mode := range modes {
		set[mode] = true
	}
	return set
}

func isAllModes(modes map[string]bool) bool {
	for _, mode := range defaultTransitModes {
		if !modes[mode] {
			return false
		}
	}
	return true
}

func extractTransitType(id string) string {
	if idx := strings.Index(id, ":"); idx >= 0 {
		return id[:idx]
	}
	return "unknown"
}

// haversine returns the great-circle distance in metres between two WGS-84 points.
func haversine(lat1, lon1, lat2, lon2 float64) float64 {
	const r = 6371000
	dLat := (lat2 - lat1) * math.Pi / 180
	dLon := (lon2 - lon1) * math.Pi / 180
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(lat1*math.Pi/180)*math.Cos(lat2*math.Pi/180)*
			math.Sin(dLon/2)*math.Sin(dLon/2)
	return r * 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
}

// timeToSec converts a time.Time to seconds since midnight (local).
func timeToSec(t time.Time) int32 {
	h, m, sec := t.Clock()
	return int32(h*3600 + m*60 + sec)
}
