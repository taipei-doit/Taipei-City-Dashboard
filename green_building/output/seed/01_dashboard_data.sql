-- ===========================================================================
-- green_building / 01_dashboard_data.sql
-- 目標 DB: dashboard
-- 說明：建立綠建築事實表 public.green_buildings 並從 CSV 載入。
--
-- 資料 CSV: green_building/green_geocoded.csv（共 1394 筆，valid='1' 共 680 筆）
--   臺北市 valid='1': 約 356、新北市 valid='1': 約 324
--
-- 因 CSV 由 docker 容器外提供，請依 README 步驟先 docker cp 進容器再執行 \copy。
-- ===========================================================================

DROP TABLE IF EXISTS public.green_buildings;

CREATE TABLE public.green_buildings (
    id              SERIAL        PRIMARY KEY,
    building_no     INTEGER,
    building_name   VARCHAR(300),
    building_desc   TEXT,
    cert_version    VARCHAR(100),
    cert_level      VARCHAR(50),
    rank            INTEGER,
    valid_until     VARCHAR(50),
    valid           VARCHAR(5),
    cert_type       VARCHAR(50),
    designer        VARCHAR(200),
    city            VARCHAR(50),    -- CSV 中的「行政區」欄位（如「臺北市」/「新北市」）
    district        VARCHAR(50),    -- CSV 中的「ditrict」欄位（如「大安區」）
    lot_number      TEXT,
    building_use    VARCHAR(100),
    lon             NUMERIC,
    lat             NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_green_buildings_valid    ON public.green_buildings(valid);
CREATE INDEX IF NOT EXISTS idx_green_buildings_city     ON public.green_buildings(city);
CREATE INDEX IF NOT EXISTS idx_green_buildings_district ON public.green_buildings(district);
CREATE INDEX IF NOT EXISTS idx_green_buildings_rank     ON public.green_buildings(rank);
