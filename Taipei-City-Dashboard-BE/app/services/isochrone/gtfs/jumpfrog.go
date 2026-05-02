package gtfs

// JumpfrogRouteNames mirrors data/scripts/app.py. Current bus GTFS route IDs
// are provider-generated, so route_short_name is the stable split key.
var JumpfrogRouteNames = map[string]bool{
	"853跳蛙":             true,
	"939跳蛙":             true,
	"三峽-中和高中":           true,
	"三峽-內科":             true,
	"三峽-捷運台大醫院站":        true,
	"三峽-捷運府中站":          true,
	"三峽-捷運永寧站":          true,
	"三峽-臺北市信義區":         true,
	"中和-新北板橋公車站":        true,
	"中和左岸社區-捷運頂溪站":      true,
	"中和環河西路-永和仁愛路":      true,
	"中和自立路-新店":          true,
	"五股-內湖科技園區":         true,
	"北大社區-捷運頂埔站":        true,
	"合宜住宅-捷運亞東醫院站":      true,
	"台北小城-大坪林":          true,
	"雙園巴士":              true,
	"土城-南天母廣場":          true,
	"土城金城路-樹林大安路":       true,
	"捷運七張站-全球工業區":       true,
	"捷運中和站-政大附中":        true,
	"捷運忠孝復興站-三峽":        true,
	"捷運景安站-三峽臺北大學":      true,
	"捷運新店站-坪林":          true,
	"捷運蘆洲站-內湖科技園區":      true,
	"捷運頂溪站-捷運頂埔站":       true,
	"政大附中-捷運景美站":        true,
	"新店(綠中海)-捷運新店站":     true,
	"新店-汐止":             true,
	"新店北新路-政大一街":        true,
	"新店高中-三峽":           true,
	"新莊-臺北車站":           true,
	"林口-內湖科技園區":         true,
	"林口-捷運圓山站":          true,
	"林口-捷運府中站":          true,
	"林口-捷運忠孝敦化站":        true,
	"林口-板橋":             true,
	"林口-臺北車站(承德)":       true,
	"林口-臺北長庚醫院":         true,
	"林口(文化三路)-捷運圓山站":    true,
	"林口(文化北路)-捷運圓山站":    true,
	"樹林後火車站-海洋公園":       true,
	"沙崙國小(篤行路)-捷運亞東醫院站": true,
	"淡水-內湖科技園區":         true,
	"淡水-國道1號-南港車站":      true,
	"淡水新市鎮-板橋":          true,
	"湯泉-十四張-大坪林":        true,
	"湯泉-大坪林-湯泉":         true,
	"湯泉-崇光中學":           true,
	"瑞芳-內科(北客)":         true,
	"瑞芳-內科(基客)":         true,
	"瑞芳-南港":             true,
	"瑞芳-松山車站(北客)":       true,
	"瑞芳-松山車站(基客)":       true,
	"瑞芳(經東碇路)-松山車站":     true,
	"石碇高中-捷運忠孝復興站":      true,
	"石門-捷運紅樹林站":         true,
	"蘆洲-中正高中":           true,
	"蘆洲-內湖":             true,
	"蘆洲-南港":             true,
	"蘆洲中正路-士林中正路":       true,
	"萬里-內湖科技園區":         true,
	"鶯歌火車站-中正紀念堂":       true,
	"鶯歌火車站-松山機場":        true,
	"泰山-內湖":             true,
	"泰山-內湖(直達)":         true,
	"泰山-內湖科技園區":         true,
	"中原中平路口-建國中學":       true,
	"湯泉-大坪林":            true,
	"汐止-台北101":          true,
	"三重-內科":             true,
}

// SplitJumpfrog removes jumpfrog routes from a bus feed and returns them as a
// separate feed using the jumpfrog prefix.
func SplitJumpfrog(bus *Feed) *Feed {
	routeIDs := make(map[string]bool)
	for id, route := range bus.Routes {
		if JumpfrogRouteNames[route.ShortName] {
			routeIDs[id] = true
		}
	}
	return SplitRoutes(bus, routeIDs, "jumpfrog:")
}

// SplitRoutes extracts routeIDs into a new feed and removes them from src.
func SplitRoutes(src *Feed, routeIDs map[string]bool, prefix string) *Feed {
	dst := &Feed{
		Prefix:    prefix,
		Stops:     make(map[string]*RawStop),
		Routes:    make(map[string]*RawRoute),
		Trips:     make(map[string]*RawTrip),
		StopTimes: make(map[string][]RawStopTime),
		Shapes:    make(map[string][]RawShapePoint),
		Calendar:  src.Calendar,
		CalDates:  src.CalDates,
		Freqs:     make(map[string][]FreqEntry),
	}
	if len(routeIDs) == 0 {
		return dst
	}

	tripIDs := make(map[string]bool)
	for tripID, trip := range src.Trips {
		if routeIDs[trip.RouteID] {
			tripIDs[tripID] = true
			dst.Trips[tripID] = trip
		}
	}

	for routeID := range routeIDs {
		if route, ok := src.Routes[routeID]; ok {
			dst.Routes[routeID] = route
			delete(src.Routes, routeID)
		}
	}

	for tripID := range tripIDs {
		if stopTimes, ok := src.StopTimes[tripID]; ok {
			dst.StopTimes[tripID] = stopTimes
			for _, st := range stopTimes {
				if stop, ok := src.Stops[st.StopID]; ok {
					dst.Stops[st.StopID] = stop
				}
			}
			delete(src.StopTimes, tripID)
		}
		if trip, ok := dst.Trips[tripID]; ok && trip.ShapeID != "" {
			if shape, ok := src.Shapes[trip.ShapeID]; ok {
				dst.Shapes[trip.ShapeID] = shape
			}
		}
		if freqs, ok := src.Freqs[tripID]; ok {
			dst.Freqs[tripID] = freqs
			delete(src.Freqs, tripID)
		}
		delete(src.Trips, tripID)
	}

	return dst
}
