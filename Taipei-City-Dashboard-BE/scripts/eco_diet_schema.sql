-- 市民綠色飲食行為流程儀表板 — 4 張表 schema
-- 對齊 DE plan §5.2 / §6.2 / §6.5.2 / §6.6.2
-- 本機 dev 版：略過 wkb_geometry（PostGIS）— GeoServer 層由 DE 處理；BE API 只用 lng/lat。

-- ─── 1. eco_restaurant (DE plan §5.2) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS eco_restaurant (
    id              SERIAL PRIMARY KEY,
    source_dataset  VARCHAR(20)              NOT NULL,
    seq_no          VARCHAR(20),
    name            TEXT                     NOT NULL,
    address         TEXT                     NOT NULL,
    city            VARCHAR(10)              NOT NULL,
    district        VARCHAR(20),
    tel             TEXT,
    env_actions     TEXT[],                  -- DE plan §5.2: nullable; ETL §5.3 一律 populate ([] for ntpe)
    lng             DOUBLE PRECISION,
    lat             DOUBLE PRECISION,
    data_time       TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT eco_restaurant_unique UNIQUE (source_dataset, seq_no)
);
CREATE INDEX IF NOT EXISTS idx_eco_restaurant_city_district
    ON eco_restaurant (city, district);
CREATE INDEX IF NOT EXISTS idx_eco_restaurant_actions
    ON eco_restaurant USING GIN (env_actions);

-- ─── 2. green_store (DE plan §6.2) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS green_store (
    id              SERIAL PRIMARY KEY,
    source_dataset  VARCHAR(20)              NOT NULL,
    store_code      VARCHAR(20),
    name            TEXT                     NOT NULL,
    address         TEXT                     NOT NULL,
    city            VARCHAR(10)              NOT NULL,
    district        VARCHAR(20),
    tel             TEXT,
    store_type      VARCHAR(30),
    lng             DOUBLE PRECISION,
    lat             DOUBLE PRECISION,
    data_time       TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT green_store_unique UNIQUE (source_dataset, store_code)
);
CREATE INDEX IF NOT EXISTS idx_green_store_type
    ON green_store (store_type);
CREATE INDEX IF NOT EXISTS idx_green_store_city_district
    ON green_store (city, district);

-- ─── 3. food_bank (DE plan §6.5.2) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS food_bank (
    id              SERIAL PRIMARY KEY,
    source_dataset  VARCHAR(20)              NOT NULL,
    seq_no          VARCHAR(20),
    name            TEXT                     NOT NULL,
    org_type        VARCHAR(40),
    city            VARCHAR(10)              NOT NULL,
    district        VARCHAR(20),
    district_code   VARCHAR(20),
    postal_code     VARCHAR(10),
    address         TEXT                     NOT NULL,
    tel             TEXT,
    lng             DOUBLE PRECISION,
    lat             DOUBLE PRECISION,
    data_time       TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT food_bank_unique UNIQUE (source_dataset, seq_no)
);
CREATE INDEX IF NOT EXISTS idx_food_bank_city_district
    ON food_bank (city, district);

-- ─── 4. gov_open_waste_yearly (DE plan §6.6.2) ───────────────────────
CREATE TABLE IF NOT EXISTS gov_open_waste_yearly (
    id                    SERIAL PRIMARY KEY,
    data_year             INTEGER                  NOT NULL,
    county                VARCHAR(20)              NOT NULL,
    garbage_generated     NUMERIC(14, 2),
    garbage_clearance     NUMERIC(14, 2),
    garbage_recycled      NUMERIC(14, 2),
    food_wastes_recycled  NUMERIC(14, 2),
    data_time             TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT gov_open_waste_yearly_unique UNIQUE (data_year, county)
);
CREATE INDEX IF NOT EXISTS idx_gov_open_waste_yearly_county
    ON gov_open_waste_yearly (county, data_year);
