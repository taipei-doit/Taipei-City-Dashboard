BEGIN;

ALTER TABLE IF EXISTS public.urbn_landuse_master_plan
    ALTER COLUMN area_code TYPE varchar(50),
    ALTER COLUMN area_short_name TYPE varchar(50);

ALTER TABLE IF EXISTS public.urbn_landuse_master_plan_history
    ALTER COLUMN area_code TYPE varchar(50),
    ALTER COLUMN area_short_name TYPE varchar(50);

CREATE SEQUENCE IF NOT EXISTS public.patrol_bike_theft_ogc_fid_seq;

CREATE TABLE IF NOT EXISTS public.patrol_bike_theft (
    case_id varchar NULL,
    type varchar NULL,
    date varchar NULL,
    time varchar NULL,
    location varchar NULL,
    address varchar NULL,
    wkb_geometry public.geometry(Point, 4326) NULL,
    begin_when timestamptz NULL,
    epoch_time float8 NULL,
    _ctime timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
    _mtime timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
    ogc_fid integer DEFAULT nextval('public.patrol_bike_theft_ogc_fid_seq'::regclass) NOT NULL
);

ALTER SEQUENCE public.patrol_bike_theft_ogc_fid_seq
    OWNED BY public.patrol_bike_theft.ogc_fid;

CREATE INDEX IF NOT EXISTS patrol_bike_theft_wkb_geometry_geom_idx
    ON public.patrol_bike_theft USING gist (wkb_geometry);

DROP TRIGGER IF EXISTS auto_patrol_bike_theft_mtime ON public.patrol_bike_theft;
CREATE TRIGGER auto_patrol_bike_theft_mtime
    BEFORE INSERT OR UPDATE ON public.patrol_bike_theft
    FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

ALTER TABLE IF EXISTS public.patrol_bike_theft OWNER TO airflow;
ALTER SEQUENCE IF EXISTS public.patrol_bike_theft_ogc_fid_seq OWNER TO airflow;

COMMIT;
