// Developed by Bombs King, Taipei Codefest 2026

package gtfs

import (
	"archive/zip"
	"bytes"
	"encoding/csv"
	"fmt"
	"io"
	"math"
	"os"
	"path"
	"sort"
	"strconv"
	"strings"
	"time"
)

// LoadFeedFromZip reads a GTFS zip archive from memory and returns a Feed.
func LoadFeedFromZip(blob []byte, prefix string) (*Feed, error) {
	zr, err := zip.NewReader(bytes.NewReader(blob), int64(len(blob)))
	if err != nil {
		return nil, err
	}
	files := make(map[string]*zip.File)
	for _, f := range zr.File {
		files[path.Base(f.Name)] = f
	}

	feed := &Feed{
		Prefix:    prefix,
		Stops:     make(map[string]*RawStop),
		Routes:    make(map[string]*RawRoute),
		Trips:     make(map[string]*RawTrip),
		StopTimes: make(map[string][]RawStopTime),
		Shapes:    make(map[string][]RawShapePoint),
		Calendar:  make(map[string]*ServicePattern),
		CalDates:  make(map[string][]CalDateException),
		Freqs:     make(map[string][]FreqEntry),
	}

	parseZipFile := func(name string, required bool, parseFunc func(*csv.Reader) error) error {
		zf, ok := files[name]
		if !ok {
			if required {
				return fmt.Errorf("required file %s missing in zip", name)
			}
			return nil
		}
		rc, err := zf.Open()
		if err != nil {
			return err
		}
		defer rc.Close()
		return parseFunc(newCSVReader(rc))
	}

	if err := parseZipFile("stops.txt", true, feed.parseStops); err != nil {
		return nil, fmt.Errorf("stops: %w", err)
	}
	if err := parseZipFile("routes.txt", true, feed.parseRoutes); err != nil {
		return nil, fmt.Errorf("routes: %w", err)
	}
	if err := parseZipFile("trips.txt", true, feed.parseTrips); err != nil {
		return nil, fmt.Errorf("trips: %w", err)
	}
	if err := parseZipFile("shapes.txt", false, feed.parseShapes); err != nil {
		return nil, fmt.Errorf("shapes: %w", err)
	}
	if err := parseZipFile("calendar.txt", false, feed.parseCalendar); err != nil {
		return nil, fmt.Errorf("calendar: %w", err)
	}
	if err := parseZipFile("calendar_dates.txt", false, feed.parseCalendarDates); err != nil {
		return nil, fmt.Errorf("calendar_dates: %w", err)
	}
	if err := parseZipFile("frequencies.txt", false, feed.parseFrequencies); err != nil {
		return nil, fmt.Errorf("frequencies: %w", err)
	}
	if err := parseZipFile("stop_times.txt", true, feed.parseStopTimes); err != nil {
		return nil, fmt.Errorf("stop_times: %w", err)
	}

	interpolateStopTimes(feed)

	for _, s := range feed.Stops {
		if s.Lat == 0 && s.Lon == 0 && s.ParentStation != "" {
			if parent, ok := feed.Stops[s.ParentStation]; ok {
				s.Lat = parent.Lat
				s.Lon = parent.Lon
			}
		}
	}

	return feed, nil
}

func newCSVReader(r io.Reader) *csv.Reader {
	cr := csv.NewReader(r)
	cr.LazyQuotes = true
	cr.TrimLeadingSpace = true
	return cr
}

// LoadFeed reads a GTFS directory and returns a Feed.
func LoadFeed(dir, prefix string) (*Feed, error) {
	f := &Feed{
		Prefix:    prefix,
		Stops:     make(map[string]*RawStop),
		Routes:    make(map[string]*RawRoute),
		Trips:     make(map[string]*RawTrip),
		StopTimes: make(map[string][]RawStopTime),
		Shapes:    make(map[string][]RawShapePoint),
		Calendar:  make(map[string]*ServicePattern),
		CalDates:  make(map[string][]CalDateException),
		Freqs:     make(map[string][]FreqEntry),
	}

	if err := parseFile(dir+"/stops.txt", f.parseStops); err != nil {
		return nil, fmt.Errorf("stops: %w", err)
	}
	if err := parseFile(dir+"/routes.txt", f.parseRoutes); err != nil {
		return nil, fmt.Errorf("routes: %w", err)
	}
	if err := parseFile(dir+"/trips.txt", f.parseTrips); err != nil {
		return nil, fmt.Errorf("trips: %w", err)
	}
	if err := parseOptionalFile(dir+"/shapes.txt", f.parseShapes); err != nil {
		return nil, fmt.Errorf("shapes: %w", err)
	}
	if err := parseOptionalFile(dir+"/calendar.txt", f.parseCalendar); err != nil {
		return nil, fmt.Errorf("calendar: %w", err)
	}
	if err := parseOptionalFile(dir+"/calendar_dates.txt", f.parseCalendarDates); err != nil {
		return nil, fmt.Errorf("calendar_dates: %w", err)
	}
	if err := parseOptionalFile(dir+"/frequencies.txt", f.parseFrequencies); err != nil {
		return nil, fmt.Errorf("frequencies: %w", err)
	}
	if err := parseFile(dir+"/stop_times.txt", f.parseStopTimes); err != nil {
		return nil, fmt.Errorf("stop_times: %w", err)
	}

	interpolateStopTimes(f)

	for _, s := range f.Stops {
		if s.Lat == 0 && s.Lon == 0 && s.ParentStation != "" {
			if parent, ok := f.Stops[s.ParentStation]; ok {
				s.Lat = parent.Lat
				s.Lon = parent.Lon
			}
		}
	}

	return f, nil
}

func parseFile(path string, parseFunc func(*csv.Reader) error) error {
	fh, err := os.Open(path)
	if err != nil {
		return err
	}
	defer fh.Close()
	return parseFunc(newCSVReader(fh))
}

func parseOptionalFile(path string, parseFunc func(*csv.Reader) error) error {
	fh, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	defer fh.Close()
	return parseFunc(newCSVReader(fh))
}

// readHeader reads the first row and returns a map of field name → column index.
// Strips UTF-8 BOM from the first field if present.
func readHeader(r *csv.Reader) (map[string]int, error) {
	row, err := r.Read()
	if err != nil {
		return nil, err
	}
	m := make(map[string]int, len(row))
	for i, h := range row {
		h = strings.TrimPrefix(h, "\xef\xbb\xbf") // UTF-8 BOM
		h = strings.TrimSpace(h)
		m[h] = i
	}
	return m, nil
}

func col(row []string, idx map[string]int, key string) string {
	i, ok := idx[key]
	if !ok || i >= len(row) {
		return ""
	}
	return strings.TrimSpace(row[i])
}

func parseFloat(s string) float64 {
	v, _ := strconv.ParseFloat(strings.TrimSpace(s), 64)
	return v
}

func parseInt(s string) int {
	v, _ := strconv.Atoi(strings.TrimSpace(s))
	return v
}

func parseInt32(s string) int32 {
	v, _ := strconv.ParseInt(strings.TrimSpace(s), 10, 32)
	return int32(v)
}

// parseGTFSTime converts "HH:MM:SS" (hours may be ≥ 24) to seconds since midnight.
func parseGTFSTime(s string) int32 {
	s = strings.TrimSpace(s)
	parts := strings.SplitN(s, ":", 3)
	if len(parts) != 3 {
		return 0
	}
	h, _ := strconv.ParseInt(parts[0], 10, 32)
	m, _ := strconv.ParseInt(parts[1], 10, 32)
	sec, _ := strconv.ParseInt(parts[2], 10, 32)
	total := h*3600 + m*60 + sec
	if total > math.MaxInt32 {
		return math.MaxInt32
	}
	if total < math.MinInt32 {
		return math.MinInt32
	}
	return int32(total)
}

func parseDate(s string) (time.Time, error) {
	return time.ParseInLocation("20060102", strings.TrimSpace(s), time.UTC)
}

func (f *Feed) parseStops(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		id := col(row, idx, "stop_id")
		if id == "" {
			continue
		}
		lat := parseFloat(col(row, idx, "stop_lat"))
		lon := parseFloat(col(row, idx, "stop_lon"))
		// Filter out stops with clearly invalid coordinates
		if math.IsNaN(lat) || math.IsNaN(lon) {
			lat, lon = 0, 0
		}
		f.Stops[id] = &RawStop{
			ID:            id,
			Name:          col(row, idx, "stop_name"),
			Lat:           lat,
			Lon:           lon,
			ParentStation: col(row, idx, "parent_station"),
		}
	}
	return nil
}

func (f *Feed) parseRoutes(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		id := col(row, idx, "route_id")
		if id == "" {
			continue
		}
		f.Routes[id] = &RawRoute{
			ID:        id,
			ShortName: col(row, idx, "route_short_name"),
			LongName:  col(row, idx, "route_long_name"),
			RouteType: parseInt(col(row, idx, "route_type")),
		}
	}
	return nil
}

func (f *Feed) parseTrips(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		id := col(row, idx, "trip_id")
		if id == "" {
			continue
		}
		f.Trips[id] = &RawTrip{
			ID:        id,
			RouteID:   col(row, idx, "route_id"),
			ServiceID: col(row, idx, "service_id"),
			ShapeID:   col(row, idx, "shape_id"),
		}
	}
	return nil
}

func (f *Feed) parseShapes(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		id := col(row, idx, "shape_id")
		if id == "" {
			continue
		}
		f.Shapes[id] = append(f.Shapes[id], RawShapePoint{
			Lat:      parseFloat(col(row, idx, "shape_pt_lat")),
			Lon:      parseFloat(col(row, idx, "shape_pt_lon")),
			Sequence: parseInt(col(row, idx, "shape_pt_sequence")),
		})
	}
	for id := range f.Shapes {
		sort.Slice(f.Shapes[id], func(i, j int) bool {
			return f.Shapes[id][i].Sequence < f.Shapes[id][j].Sequence
		})
	}
	return nil
}

func (f *Feed) parseCalendar(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	dayKeys := []string{"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		sid := col(row, idx, "service_id")
		if sid == "" {
			continue
		}
		start, err := parseDate(col(row, idx, "start_date"))
		if err != nil {
			continue
		}
		end, err := parseDate(col(row, idx, "end_date"))
		if err != nil {
			continue
		}
		var days [7]bool
		for i, k := range dayKeys {
			days[i] = col(row, idx, k) == "1"
		}
		f.Calendar[sid] = &ServicePattern{
			Weekdays:  days,
			StartDate: start,
			EndDate:   end,
		}
	}
	return nil
}

func (f *Feed) parseCalendarDates(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		sid := col(row, idx, "service_id")
		if sid == "" {
			continue
		}
		d, err := parseDate(col(row, idx, "date"))
		if err != nil {
			continue
		}
		et := parseInt(col(row, idx, "exception_type"))
		f.CalDates[sid] = append(f.CalDates[sid], CalDateException{Date: d, Type: et})
	}
	return nil
}

func (f *Feed) parseFrequencies(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		tid := col(row, idx, "trip_id")
		if tid == "" {
			continue
		}
		f.Freqs[tid] = append(f.Freqs[tid], FreqEntry{
			StartTime:  parseGTFSTime(col(row, idx, "start_time")),
			EndTime:    parseGTFSTime(col(row, idx, "end_time")),
			HeadwaySec: parseInt32(col(row, idx, "headway_secs")),
		})
	}
	return nil
}

func (f *Feed) parseStopTimes(r *csv.Reader) error {
	idx, err := readHeader(r)
	if err != nil {
		return err
	}

	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		tid := col(row, idx, "trip_id")
		sid := col(row, idx, "stop_id")
		if tid == "" || sid == "" {
			continue
		}
		seq := parseInt(col(row, idx, "stop_sequence"))
		arr := parseGTFSTime(col(row, idx, "arrival_time"))
		dep := parseGTFSTime(col(row, idx, "departure_time"))
		if dep == 0 {
			dep = arr
		}
		f.StopTimes[tid] = append(f.StopTimes[tid], RawStopTime{
			StopID:   sid,
			Sequence: seq,
			Arrival:  arr,
			Dep:      dep,
		})
	}

	// Sort each trip's stop times by sequence
	for tid := range f.StopTimes {
		sts := f.StopTimes[tid]
		sort.Slice(sts, func(i, j int) bool {
			return sts[i].Sequence < sts[j].Sequence
		})
		f.StopTimes[tid] = sts
	}
	return nil
}

// interpolateStopTimes fills in missing (zero) arrival/departure times by
// linear interpolation between the nearest timepoint stops with actual times.
func interpolateStopTimes(f *Feed) {
	for _, sts := range f.StopTimes {
		if len(sts) < 2 {
			continue
		}

		// Find timepoint indices (stops with actual non-zero times)
		var tpIdx []int
		for i, st := range sts {
			if st.Arrival > 0 || st.Dep > 0 {
				tpIdx = append(tpIdx, i)
			}
		}
		if len(tpIdx) < 2 {
			continue
		}

		// Interpolate between each pair of timepoints
		for seg := 0; seg < len(tpIdx)-1; seg++ {
			from := tpIdx[seg]
			to := tpIdx[seg+1]
			fromTime := sts[from].Dep
			toTime := sts[to].Arrival
			if fromTime == 0 {
				fromTime = sts[from].Arrival
			}
			if toTime == 0 {
				toTime = sts[to].Dep
			}
			if fromTime == 0 || toTime == 0 {
				continue
			}
			nBetween := to - from
			if nBetween <= 1 {
				continue
			}
			for i := from + 1; i < to; i++ {
				frac := float64(i-from) / float64(nBetween)
				t := fromTime + int32(float64(toTime-fromTime)*frac)
				sts[i].Arrival = t
				sts[i].Dep = t
			}
		}
	}
}
