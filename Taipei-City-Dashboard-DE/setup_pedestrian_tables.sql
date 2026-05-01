-- 在 postgres-data (dashboard DB) 中建立行人事故相關資料表
-- 連線：localhost:5433 / dashboard DB

CREATE EXTENSION IF NOT EXISTS postgis;

-- 台北市行人事故明細（來源：內政部警政署 MOI，與新北市欄位一致）
CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_accident_taipei (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    year INTEGER,
    month INTEGER,
    hour INTEGER,
    death_count INTEGER DEFAULT 0,
    injury_count INTEGER DEFAULT 0,
    age INTEGER,
    cause_name VARCHAR(200),
    pedestrian_action VARCHAR(100),
    lng DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_acc_tpe_year
    ON public.traffic_pedestrian_accident_taipei(year);
CREATE INDEX IF NOT EXISTS idx_ped_acc_tpe_geom
    ON public.traffic_pedestrian_accident_taipei USING GIST(wkb_geometry);

-- 新北市行人事故明細
CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_accident_ntpc (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    year INTEGER,
    month INTEGER,
    hour INTEGER,
    death_count INTEGER DEFAULT 0,
    injury_count INTEGER DEFAULT 0,
    age INTEGER,
    cause_name VARCHAR(200),
    pedestrian_action VARCHAR(100),
    lng DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_acc_ntpc_year
    ON public.traffic_pedestrian_accident_ntpc(year);
CREATE INDEX IF NOT EXISTS idx_ped_acc_ntpc_geom
    ON public.traffic_pedestrian_accident_ntpc USING GIST(wkb_geometry);

-- 行人事故路口熱點（近三年聚合）
CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_hotspot (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    city VARCHAR(20),
    h3_index VARCHAR(20),
    center_lng DOUBLE PRECISION,
    center_lat DOUBLE PRECISION,
    accident_count INTEGER,
    death_count INTEGER,
    injury_count INTEGER,
    top_cause VARCHAR(200),
    top_hour INTEGER,
    near_location VARCHAR(200),
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_hotspot_city
    ON public.traffic_pedestrian_hotspot(city);
CREATE INDEX IF NOT EXISTS idx_ped_hotspot_geom
    ON public.traffic_pedestrian_hotspot USING GIST(wkb_geometry);

-- 行人事故時段統計（供 HeatmapChart 使用）
CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_hourly_stats (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    city VARCHAR(20),
    year INTEGER,
    weekday INTEGER,   -- 1=週一, 7=週日 (ISO)
    hour INTEGER,      -- 0-23
    accident_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_ped_hourly_city_year
    ON public.traffic_pedestrian_hourly_stats(city, year);

-- 行人事故年度趨勢（供 ColumnLineChart 使用）
CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_yearly_trend (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    city VARCHAR(20),
    year INTEGER,
    accident_count INTEGER,
    death_count INTEGER,
    injury_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_ped_trend_city_year
    ON public.traffic_pedestrian_yearly_trend(city, year);
