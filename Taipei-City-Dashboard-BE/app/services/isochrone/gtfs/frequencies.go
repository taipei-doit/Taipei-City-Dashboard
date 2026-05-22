// Developed by Bombs King, Taipei Codefest 2026

package gtfs

// ExpandFrequencies generates concrete stop-time sequences for trips defined
// in frequencies.txt. Each frequency entry produces one trip per headway
// interval between start_time and end_time.
//
// Returns a slice of (tripID, serviceID, routeID, []RawStopTime) tuples
// ready to be merged into the RAPTOR builder.
type ExpandedTrip struct {
	TripID    string
	ServiceID string
	RouteID   string
	ShapeID   string
	StopTimes []RawStopTime
}

func ExpandFrequencies(f *Feed) []ExpandedTrip {
	var out []ExpandedTrip

	for tripID, entries := range f.Freqs {
		template, ok := f.StopTimes[tripID]
		if !ok || len(template) == 0 {
			continue
		}
		trip, ok := f.Trips[tripID]
		if !ok {
			continue
		}

		// Compute time offset of each stop relative to the first stop's departure.
		baseDep := template[0].Dep
		offsets := make([]struct{ arrOff, depOff int32 }, len(template))
		for i, st := range template {
			offsets[i].arrOff = st.Arrival - baseDep
			offsets[i].depOff = st.Dep - baseDep
		}

		for _, fe := range entries {
			if fe.HeadwaySec <= 0 {
				continue
			}
			seq := 0
			for tripStart := fe.StartTime; tripStart < fe.EndTime; tripStart += fe.HeadwaySec {
				newTimes := make([]RawStopTime, len(template))
				for i, st := range template {
					newTimes[i] = RawStopTime{
						StopID:   st.StopID,
						Sequence: st.Sequence,
						Arrival:  tripStart + offsets[i].arrOff,
						Dep:      tripStart + offsets[i].depOff,
					}
				}
				syntheticID := tripID + ":freq:" + itoa(int(tripStart)) + ":" + itoa(seq)
				out = append(out, ExpandedTrip{
					TripID:    syntheticID,
					ServiceID: trip.ServiceID,
					RouteID:   trip.RouteID,
					ShapeID:   trip.ShapeID,
					StopTimes: newTimes,
				})
				seq++
			}
		}
	}
	return out
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	buf := [20]byte{}
	pos := len(buf)
	for n > 0 {
		pos--
		buf[pos] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		pos--
		buf[pos] = '-'
	}
	return string(buf[pos:])
}
