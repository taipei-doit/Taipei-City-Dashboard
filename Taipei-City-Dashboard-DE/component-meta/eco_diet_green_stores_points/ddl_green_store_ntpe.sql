-- ============================================================
-- DDL: green_store_ntpe (新北市綠色商店)
-- ============================================================
-- schema    : public
-- table     : green_store_ntpe
-- source    : data.ntpc rid 6ccd0274-0c09-43b0-98fc-4d5222a71e8b
-- DAG       : proj_new_taipei_city_dashboard/green_store_ntpe
-- 建表方式  : DAG 首次執行時由 utils.generate_sql_to_create_DB_table.generate_sql_to_create_db_table()
--             依照 ETL 函式內 COL_MAP 自動建立;本檔為等價人類可讀版本,可重複套用。
-- 時間欄位  : data_time (DEFAULT CURRENT_TIMESTAMP,ETL 寫入時間)
-- primary key / 索引 : 無 (load_behavior=replace,每月整批覆寫)
-- 地理欄位  : 無 (本次不做地理編碼)
-- 備註      : source 已自帶 city 欄位 (固定為 '新北市') 與 county_code (固定 65000)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.green_store_ntpe (
    data_time     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    seq           INTEGER,
    store_name    TEXT COLLATE pg_catalog."default",
    address       TEXT COLLATE pg_catalog."default",
    store_code    CHARACTER VARYING(20) COLLATE pg_catalog."default",
    contact_phone CHARACTER VARYING(50) COLLATE pg_catalog."default",
    store_type    CHARACTER VARYING(50) COLLATE pg_catalog."default",
    city          CHARACTER VARYING(10) COLLATE pg_catalog."default",
    county_code   CHARACTER VARYING(10) COLLATE pg_catalog."default"
);
