-- =====================================================
-- 環保餐廳 資料表定義 SQL
-- 適用 postgres-data (dashboard)
-- =====================================================

-- ===== 台北市環保餐廳 =====

CREATE TABLE IF NOT EXISTS public.green_restaurant_tpe (
    ogc_fid      serial PRIMARY KEY,
    data_time    timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    district     text,
    name         text,
    category     text,
    tel          text,
    address      text,
    eco_grade    text,
    activities   text,
    eco_actions  text,
    lng          double precision,
    lat          double precision,
    wkb_geometry geometry(Point, 4326),
    _ctime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_green_restaurant_tpe_district
    ON public.green_restaurant_tpe (district);
CREATE INDEX IF NOT EXISTS idx_green_restaurant_tpe_geom
    ON public.green_restaurant_tpe USING gist (wkb_geometry);

-- ===== 新北市環保餐廳 =====

CREATE TABLE IF NOT EXISTS public.green_restaurant_ntpc (
    ogc_fid      serial PRIMARY KEY,
    data_time    timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    district     text,
    name         text,
    category     text,
    tel          text,
    address      text,
    eco_grade    text,
    activities   text,
    eco_actions  text,
    lng          double precision,
    lat          double precision,
    wkb_geometry geometry(Point, 4326),
    _ctime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_green_restaurant_ntpc_district
    ON public.green_restaurant_ntpc (district);
CREATE INDEX IF NOT EXISTS idx_green_restaurant_ntpc_geom
    ON public.green_restaurant_ntpc USING gist (wkb_geometry);
