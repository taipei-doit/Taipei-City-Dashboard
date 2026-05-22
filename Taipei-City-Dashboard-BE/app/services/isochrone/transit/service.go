package transit

import (
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"sort"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
	"TaipeiCityDashboardBE/app/services/isochrone/isochrone"
	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
	"TaipeiCityDashboardBE/global"
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

var defaultService *Service

// InitService loads RAPTOR data from Redis and initialises the global service.
// Call this once at application startup, after ConnectToRedis.
func InitService() error {
	rd, err := Load()
	var feeds []*gtfs.Feed
	if err != nil {
		feeds, rd, err = buildRaptorFromGTFS()
		if err != nil {
			return fmt.Errorf("transit: build raptor data: %w", err)
		}
		if err := Save(rd); err != nil {
			return fmt.Errorf("transit: save raptor data: %w", err)
		}
	} else {
		// Re-load GTFS feeds (calendar only; stop_times not needed at runtime)
		feeds, err = loadCalendarFeeds()
		if err != nil {
			return fmt.Errorf("transit: load calendar feeds: %w", err)
		}
	}

	defaultService = &Service{
		rd:       rd,
		idx:      isochrone.NewIsochroneIndex(rd),
		feeds:    feeds,
		scanners: buildProfileScanners(rd, feeds),
	}
	return nil
}

// DefaultService returns the package-level Service, or an error if not initialised.
func DefaultService() (*Service, error) {
	if defaultService == nil {
		return nil, errors.New("transit service not initialised; call InitService first")
	}
	return defaultService, nil
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

// loadCalendarFeeds loads only trips + calendar files (no stop_times) for runtime use.
func loadCalendarFeeds() ([]*gtfs.Feed, error) {
	dir := global.GTFSDir
	var feeds []*gtfs.Feed
	for _, sp := range runtimeFeedSpecs {
		f, err := gtfs.LoadCalendarOnly(dir+"/"+sp.sub, sp.prefix)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", sp.sub, err)
		}
		feeds = append(feeds, f)
	}
	return feeds, nil
}

func buildRaptorFromGTFS() ([]*gtfs.Feed, *raptor.RaptorData, error) {
	dir := global.GTFSDir
	busFeed, err := gtfs.LoadFeed(dir+"/"+transitModeBus, transitModeBus+":")
	if err != nil {
		return nil, nil, fmt.Errorf("bus: %w", err)
	}
	jumpfrogFeed := gtfs.SplitJumpfrog(busFeed)

	railFeed, err := gtfs.LoadFeed(dir+"/"+transitModeRail, transitModeRail+":")
	if err != nil {
		return nil, nil, fmt.Errorf("rail: %w", err)
	}
	trainFeed, err := gtfs.LoadFeed(dir+"/"+transitModeTrain, transitModeTrain+":")
	if err != nil {
		return nil, nil, fmt.Errorf("train: %w", err)
	}

	feeds := []*gtfs.Feed{busFeed, jumpfrogFeed, railFeed, trainFeed}
	rd, err := raptor.Build(feeds)
	if err != nil {
		return nil, nil, err
	}
	return feeds, rd, nil
}
