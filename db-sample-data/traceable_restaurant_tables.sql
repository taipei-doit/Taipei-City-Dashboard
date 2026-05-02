-- =====================================================
-- 溯源餐廳 資料表定義 SQL
-- 適用 postgres-data (dashboard)
-- =====================================================

-- ===== 台北市溯源餐廳 =====

CREATE TABLE IF NOT EXISTS public.traceable_restaurant_tpe (
    ogc_fid      serial PRIMARY KEY,
    data_time    timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    name         text,
    cuisine_type text,
    star_rating  text,
    address      text,
    tel          text,
    lng          double precision,
    lat          double precision,
    wkb_geometry geometry(Point, 4326),
    _ctime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_tpe_cuisine
    ON public.traceable_restaurant_tpe (cuisine_type);
CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_tpe_star
    ON public.traceable_restaurant_tpe (star_rating);
CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_tpe_geom
    ON public.traceable_restaurant_tpe USING gist (wkb_geometry);

-- ===== 新北市溯源餐廳 =====

CREATE TABLE IF NOT EXISTS public.traceable_restaurant_ntpc (
    ogc_fid      serial PRIMARY KEY,
    data_time    timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    name         text,
    cuisine_type text,
    star_rating  text,
    address      text,
    tel          text,
    lng          double precision,
    lat          double precision,
    wkb_geometry geometry(Point, 4326),
    _ctime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime       timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_ntpc_cuisine
    ON public.traceable_restaurant_ntpc (cuisine_type);
CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_ntpc_star
    ON public.traceable_restaurant_ntpc (star_rating);
CREATE INDEX IF NOT EXISTS idx_traceable_restaurant_ntpc_geom
    ON public.traceable_restaurant_ntpc USING gist (wkb_geometry);
