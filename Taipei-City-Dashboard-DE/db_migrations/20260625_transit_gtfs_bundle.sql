BEGIN;

-- GTFS feeds for the transit-isochrone backend, stored as zipped blobs.
-- One row per feed (bus | rail | train); `archive` is that feed's .txt files zipped.
-- Written by DAG proj_city_dashboard/transit_gtfs; read by the BE (LoadFeedFromZip).
CREATE TABLE IF NOT EXISTS public.gtfs_bundle (
    feed       varchar PRIMARY KEY,
    archive    bytea NOT NULL,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE IF EXISTS public.gtfs_bundle OWNER TO airflow;

COMMIT;
