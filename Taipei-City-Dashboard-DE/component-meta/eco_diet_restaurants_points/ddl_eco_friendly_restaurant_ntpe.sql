-- DDL for table `eco_friendly_restaurant_ntpe`
-- 來源：DAG eco_friendly_restaurant_ntpe (proj_new_taipei_city_dashboard) 的 COL_MAP
-- 由 `_ensure_ready_table()` 首次跑 DAG 時自動建表；本檔為對應的人類可讀版本，
-- 提供上游維護者 review schema 用。
--
-- 對應 component：eco_diet_restaurants_points（環保餐廳數量，id 600）
-- 對應 city scope：metrotaipei（與北市 eco_friendly_restaurant 透過 UNION ALL 合計）
--
-- 欄位命名與北市版 eco_friendly_restaurant 雙北 align（seq / restaurant_category /
-- restaurant_name / phone / address）；額外保留 NTPC 原始 city / countycode 兩欄位，
-- 北市版則有 ext / mobile / extra_eco_actions 三欄位是 NTPC 沒有的。

CREATE TABLE IF NOT EXISTS public.eco_friendly_restaurant_ntpe (
    data_time           timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    seq                 integer,
    restaurant_category text COLLATE pg_catalog."default",
    city                character varying(20) COLLATE pg_catalog."default",
    countycode          character varying(20) COLLATE pg_catalog."default",
    restaurant_name     text COLLATE pg_catalog."default",
    phone               character varying(50) COLLATE pg_catalog."default",
    address             text COLLATE pg_catalog."default"
);
