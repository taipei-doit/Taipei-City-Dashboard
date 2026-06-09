// Developed by Bombs King, Taipei Codefest 2026

package transit

import (
	"errors"

	"TaipeiCityDashboardBE/app/services/isochrone/gtfs"
	"TaipeiCityDashboardBE/app/services/isochrone/raptor"
)

// GTFSFeedSource provides GTFS-derived data for the transit service.
// TODO: Implement this with SQL-backed GTFS queries instead of reading local files.
type GTFSFeedSource interface {
	LoadCalendarFeeds() ([]*gtfs.Feed, error)
	BuildRaptorData() ([]*gtfs.Feed, *raptor.RaptorData, error)
}

type sqlGTFSFeedSource struct{}

func newGTFSFeedSource() GTFSFeedSource {
	return sqlGTFSFeedSource{}
}

func (sqlGTFSFeedSource) LoadCalendarFeeds() ([]*gtfs.Feed, error) {
	return nil, errors.New("TODO: load GTFS calendar feeds from SQL")
}

func (sqlGTFSFeedSource) BuildRaptorData() ([]*gtfs.Feed, *raptor.RaptorData, error) {
	return nil, nil, errors.New("TODO: build RAPTOR data from SQL GTFS tables")
}
