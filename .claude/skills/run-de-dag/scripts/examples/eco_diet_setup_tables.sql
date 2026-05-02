-- Run this once before the first DAG execution.
-- All 4 DAGs use TRUNCATE-based load (replace / current+history) which requires
-- the destination tables to already exist.
--
-- Execute via:
--   docker compose -f Taipei-City-Dashboard-DE/docker/develop/docker-compose.yaml \
--     exec -T postgres-data psql -U airflow -d dashboard_db \
--     -f /path/to/eco_diet_setup_tables.sql

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- eco_restaurant  (replace)  — C1 / C2 / C3 環保餐廳
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eco_restaurant (
    id              serial          PRIMARY KEY,
    source_dataset  varchar(20)     NOT NULL,
    seq_no          varchar(20),
    name            text            NOT NULL,
    address         text            NOT NULL,
    city            varchar(10)     NOT NULL,
    district        varchar(20),
    tel             text,
    env_actions     text[],
    lng             double precision,
    lat             double precision,
    wkb_geometry    geometry(Point, 4326),
    data_time       timestamptz     NOT NULL,
    CONSTRAINT eco_restaurant_unique UNIQUE (source_dataset, seq_no)
);

CREATE INDEX IF NOT EXISTS idx_eco_restaurant_city_district
    ON public.eco_restaurant (city, district);
CREATE INDEX IF NOT EXISTS idx_eco_restaurant_geom
    ON public.eco_restaurant USING GIST (wkb_geometry);
CREATE INDEX IF NOT EXISTS idx_eco_restaurant_actions
    ON public.eco_restaurant USING GIN (env_actions);

-- ============================================================
-- green_store  (replace)  — C4 綠色商店
-- ============================================================
CREATE TABLE IF NOT EXISTS public.green_store (
    id              serial          PRIMARY KEY,
    source_dataset  varchar(20)     NOT NULL,
    store_code      varchar(20),
    name            text            NOT NULL,
    address         text            NOT NULL,
    city            varchar(10)     NOT NULL,
    district        varchar(20),
    tel             text,
    store_type      varchar(30),
    lng             double precision,
    lat             double precision,
    wkb_geometry    geometry(Point, 4326),
    data_time       timestamptz     NOT NULL,
    CONSTRAINT green_store_unique UNIQUE (source_dataset, store_code)
);

CREATE INDEX IF NOT EXISTS idx_green_store_geom
    ON public.green_store USING GIST (wkb_geometry);
CREATE INDEX IF NOT EXISTS idx_green_store_type
    ON public.green_store (store_type);

-- ============================================================
-- food_bank  (replace)  — C7 實物銀行
-- ============================================================
CREATE TABLE IF NOT EXISTS public.food_bank (
    id              serial          PRIMARY KEY,
    source_dataset  varchar(20)     NOT NULL,
    seq_no          varchar(20),
    name            text            NOT NULL,
    org_type        varchar(40),
    city            varchar(10)     NOT NULL,
    district        varchar(20),
    district_code   varchar(20),
    postal_code     varchar(10),
    address         text            NOT NULL,
    tel             text,
    lng             double precision,
    lat             double precision,
    wkb_geometry    geometry(Point, 4326),
    data_time       timestamptz     NOT NULL,
    CONSTRAINT food_bank_unique UNIQUE (source_dataset, seq_no)
);

CREATE INDEX IF NOT EXISTS idx_food_bank_geom
    ON public.food_bank USING GIST (wkb_geometry);

-- ============================================================
-- gov_open_waste_yearly  (current+history)  — C5 廚餘量年趨勢
-- ============================================================
CREATE TABLE IF NOT EXISTS public.gov_open_waste_yearly (
    id                   serial      PRIMARY KEY,
    data_year            integer     NOT NULL,
    county               varchar(20) NOT NULL,
    garbage_generated    numeric(14, 2),
    garbage_clearance    numeric(14, 2),
    garbage_recycled     numeric(14, 2),
    food_wastes_recycled numeric(14, 2),
    data_time            timestamptz NOT NULL,
    CONSTRAINT gov_open_waste_yearly_unique UNIQUE (data_year, county)
);

CREATE TABLE IF NOT EXISTS public.gov_open_waste_yearly_history
    (LIKE public.gov_open_waste_yearly INCLUDING ALL);

CREATE INDEX IF NOT EXISTS idx_gov_open_waste_yearly_year_county
    ON public.gov_open_waste_yearly (data_year, county);
CREATE INDEX IF NOT EXISTS idx_gov_open_waste_yearly_history_year
    ON public.gov_open_waste_yearly_history (data_year);
