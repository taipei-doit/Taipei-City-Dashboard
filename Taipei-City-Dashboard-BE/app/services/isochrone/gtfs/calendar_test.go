// Developed by Bombs King, Taipei Codefest 2026

package gtfs

import (
	"testing"
	"time"
)

func TestActiveServicesForProfile(t *testing.T) {
	feed := &Feed{
		Calendar: map[string]*ServicePattern{
			"bus_monday": {
				Weekdays: [7]bool{true, false, false, false, false, false, false},
			},
			"rail_holiday": {
				Weekdays: [7]bool{false, false, false, false, false, true, true},
			},
		},
		Trips: map[string]*RawTrip{
			"train_all": {ID: "train_all", ServiceID: "2024-01-04_1111111"},
			"train_sun": {ID: "train_sun", ServiceID: "2024-01-07_0000001"},
		},
	}

	weekday := ActiveServicesForProfile(feed, ServiceProfileWeekday)
	if !weekday["bus_monday"] {
		t.Fatalf("expected weekday bus service")
	}
	if !weekday["2024-01-04_1111111"] {
		t.Fatalf("expected embedded all-days train service in weekday profile")
	}
	if weekday["rail_holiday"] || weekday["2024-01-07_0000001"] {
		t.Fatalf("unexpected holiday-only service in weekday profile: %#v", weekday)
	}

	holiday := ActiveServicesForProfile(feed, ServiceProfileHoliday)
	if !holiday["rail_holiday"] {
		t.Fatalf("expected holiday rail service")
	}
	if !holiday["2024-01-04_1111111"] || !holiday["2024-01-07_0000001"] {
		t.Fatalf("expected embedded train services in holiday profile: %#v", holiday)
	}
	if holiday["bus_monday"] {
		t.Fatalf("unexpected weekday-only bus service in holiday profile")
	}
}

func TestParseServiceProfile(t *testing.T) {
	cases := map[string]ServiceProfile{
		"":        ServiceProfileWeekday,
		"weekday": ServiceProfileWeekday,
		"平日":      ServiceProfileWeekday,
		"holiday": ServiceProfileHoliday,
		"weekend": ServiceProfileHoliday,
		"假日":      ServiceProfileHoliday,
	}
	for input, want := range cases {
		got, err := ParseServiceProfile(input)
		if err != nil {
			t.Fatalf("ParseServiceProfile(%q): %v", input, err)
		}
		if got != want {
			t.Fatalf("ParseServiceProfile(%q)=%q, want %q", input, got, want)
		}
	}
}

func TestServiceProfileFromTime(t *testing.T) {
	weekday := time.Date(2026, 5, 1, 0, 0, 0, 0, time.UTC)
	holiday := time.Date(2026, 5, 2, 0, 0, 0, 0, time.UTC)
	if ServiceProfileFromTime(weekday) != ServiceProfileWeekday {
		t.Fatalf("expected Friday to be weekday")
	}
	if ServiceProfileFromTime(holiday) != ServiceProfileHoliday {
		t.Fatalf("expected Saturday to be holiday")
	}
}
