-- Run this once before the first DAG execution.
-- Both DAGs use TRUNCATE-based load (current+history / replace) which requires
-- the destination tables to already exist.

-- ============================================================
-- mrt_a11y_alert (current+history)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.mrtp_a11y_alert (
    line          text,
    station       text,
    publish_time  timestamptz,
    description   text,
    status        text,
    data_time     timestamptz
);

CREATE TABLE IF NOT EXISTS public.mrtp_a11y_alert_history
    (LIKE public.mrtp_a11y_alert);

CREATE INDEX IF NOT EXISTS mrtp_a11y_alert_status_idx
    ON public.mrtp_a11y_alert (status);
CREATE INDEX IF NOT EXISTS mrtp_a11y_alert_history_data_time_idx
    ON public.mrtp_a11y_alert_history (data_time);
CREATE INDEX IF NOT EXISTS mrtp_a11y_alert_history_line_idx
    ON public.mrtp_a11y_alert_history (line);

-- ============================================================
-- mrt_a11y_elevator (replace, master data with geometry)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS public.mrtp_a11y_elevator (
    station         text,
    exit_no         text,
    facility_name   text,
    facility_type   text,
    lng             double precision,
    lat             double precision,
    wkb_geometry    geometry(Point, 4326),
    data_time       timestamptz
);

CREATE INDEX IF NOT EXISTS mrtp_a11y_elevator_geom_idx
    ON public.mrtp_a11y_elevator USING GIST (wkb_geometry);
CREATE INDEX IF NOT EXISTS mrtp_a11y_elevator_station_idx
    ON public.mrtp_a11y_elevator (station);
