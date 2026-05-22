package gtfs

import (
	"fmt"
	"strings"
	"time"
)

type ServiceProfile string

const (
	ServiceProfileWeekday ServiceProfile = "weekday"
	ServiceProfileHoliday ServiceProfile = "holiday"
)

func ParseServiceProfile(value string) (ServiceProfile, error) {
	switch strings.TrimSpace(strings.ToLower(value)) {
	case "", "weekday", "平日":
		return ServiceProfileWeekday, nil
	case "holiday", "weekend", "假日":
		return ServiceProfileHoliday, nil
	default:
		return "", fmt.Errorf("unsupported service profile %q", value)
	}
}

func ServiceProfileFromTime(t time.Time) ServiceProfile {
	switch t.Weekday() {
	case time.Saturday, time.Sunday:
		return ServiceProfileHoliday
	default:
		return ServiceProfileWeekday
	}
}

// IsServiceActive returns true if the given service runs on date.
// Date range (start_date/end_date) is intentionally ignored — only day-of-week
// and calendar_dates exceptions are considered. This ensures all feeds are
// active regardless of their respective calendar validity windows.
func IsServiceActive(f *Feed, serviceID string, date time.Time) bool {
	weekday := int(date.Weekday()+6) % 7 // Mon=0 … Sun=6

	// Check calendar_dates exceptions first (override everything)
	for _, ex := range f.CalDates[serviceID] {
		if ex.Date.Equal(date.Truncate(24 * time.Hour)) {
			return ex.Type == 1 // 1=added, 2=removed
		}
	}

	// Try regular calendar entry — check day of week only
	if pat, ok := f.Calendar[serviceID]; ok {
		return pat.Weekdays[weekday]
	}

	// TRA embedded-date service_id format: "2024-01-04_1111010"
	if idx := strings.Index(serviceID, "_"); idx == 10 {
		dayBits := serviceID[idx+1:]
		if weekday < len(dayBits) {
			return dayBits[weekday] == '1'
		}
	}

	return false
}

func IsServiceActiveForProfile(f *Feed, serviceID string, profile ServiceProfile) bool {
	if pat, ok := f.Calendar[serviceID]; ok {
		return weekdaysMatchProfile(pat.Weekdays, profile)
	}

	if idx := strings.Index(serviceID, "_"); idx == 10 {
		dayBits := serviceID[idx+1:]
		var days [7]bool
		for i := 0; i < len(days) && i < len(dayBits); i++ {
			days[i] = dayBits[i] == '1'
		}
		return weekdaysMatchProfile(days, profile)
	}

	return false
}

func ActiveServicesForProfile(f *Feed, profile ServiceProfile) map[string]bool {
	result := make(map[string]bool)
	for sid := range f.Calendar {
		if IsServiceActiveForProfile(f, sid, profile) {
			result[sid] = true
		}
	}
	for _, trip := range f.Trips {
		if IsServiceActiveForProfile(f, trip.ServiceID, profile) {
			result[trip.ServiceID] = true
		}
	}
	return result
}

func weekdaysMatchProfile(days [7]bool, profile ServiceProfile) bool {
	switch profile {
	case ServiceProfileHoliday:
		return days[5] || days[6]
	default:
		for i := 0; i < 5; i++ {
			if days[i] {
				return true
			}
		}
		return false
	}
}
