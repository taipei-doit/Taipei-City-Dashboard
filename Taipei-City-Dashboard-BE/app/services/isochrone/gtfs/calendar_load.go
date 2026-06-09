// Developed by Bombs King, Taipei Codefest 2026

package gtfs

import "fmt"

// LoadCalendarOnly parses only the files needed for service-date filtering:
// trips.txt, calendar.txt, and calendar_dates.txt.
// This is much faster than LoadFeed and is intended for server-startup use.
func LoadCalendarOnly(dir, prefix string) (*Feed, error) {
	f := &Feed{
		Prefix:    prefix,
		Stops:     make(map[string]*RawStop),
		Routes:    make(map[string]*RawRoute),
		Trips:     make(map[string]*RawTrip),
		StopTimes: make(map[string][]RawStopTime),
		Calendar:  make(map[string]*ServicePattern),
		CalDates:  make(map[string][]CalDateException),
		Freqs:     make(map[string][]FreqEntry),
	}

	if err := f.parseTrips(dir + "/trips.txt"); err != nil {
		return nil, fmt.Errorf("trips: %w", err)
	}
	if err := f.parseCalendar(dir + "/calendar.txt"); err != nil {
		return nil, fmt.Errorf("calendar: %w", err)
	}
	if err := f.parseCalendarDates(dir + "/calendar_dates.txt"); err != nil {
		return nil, fmt.Errorf("calendar_dates: %w", err)
	}
	return f, nil
}
