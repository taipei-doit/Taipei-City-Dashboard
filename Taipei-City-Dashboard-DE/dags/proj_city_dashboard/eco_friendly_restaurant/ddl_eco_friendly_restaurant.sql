-- DDL for table `eco_friendly_restaurant`
-- 來源：DAG eco_friendly_restaurant (proj_city_dashboard) 的 COL_MAP
-- 由 `_ensure_ready_table()` 首次跑 DAG 時自動建表；本檔為對應的人類可讀版本，
-- 提供上游維護者 review schema 用。
--
-- 對應 component：eco_diet_restaurants_points（環保餐廳數量，id 600）
-- 對應 city scope：taipei、metrotaipei（與新北 eco_friendly_restaurant_ntpe 透過 UNION ALL 合計）

CREATE TABLE IF NOT EXISTS public.eco_friendly_restaurant (
    data_time           timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    seq                 integer,
    restaurant_category text COLLATE pg_catalog."default",
    restaurant_name     text COLLATE pg_catalog."default",
    phone               character varying(50)  COLLATE pg_catalog."default",
    ext                 character varying(20)  COLLATE pg_catalog."default",
    mobile              character varying(50)  COLLATE pg_catalog."default",
    address             text COLLATE pg_catalog."default",
    extra_eco_actions   text COLLATE pg_catalog."default"
);
