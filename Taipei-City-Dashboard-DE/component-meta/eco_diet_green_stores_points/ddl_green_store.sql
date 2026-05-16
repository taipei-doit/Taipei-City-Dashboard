-- ============================================================
-- DDL: green_store (臺北市綠色商店)
-- ============================================================
-- schema    : public
-- table     : green_store
-- source    : data.taipei page_id 1756cb64-0066-444a-a323-9f3b5a961045
-- DAG       : proj_city_dashboard/green_store
-- 建表方式  : DAG 首次執行時由 utils.generate_sql_to_create_DB_table.generate_sql_to_create_db_table()
--             依照 ETL 函式內 COL_MAP 自動建立;本檔為等價人類可讀版本,可重複套用。
-- 時間欄位  : data_time (DEFAULT CURRENT_TIMESTAMP,ETL 寫入時間)
-- primary key / 索引 : 無 (load_behavior=replace,每月整批覆寫)
-- 地理欄位  : 無 (本次不做地理編碼;未來若補 lng/lat 再 ALTER TABLE)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.green_store (
    data_time      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    seq            INTEGER,
    store_name     TEXT COLLATE pg_catalog."default",
    address        TEXT COLLATE pg_catalog."default",
    store_code     CHARACTER VARYING(20) COLLATE pg_catalog."default",
    contact_person TEXT COLLATE pg_catalog."default",
    contact_phone  CHARACTER VARYING(50) COLLATE pg_catalog."default",
    extension      CHARACTER VARYING(20) COLLATE pg_catalog."default",
    mobile         CHARACTER VARYING(20) COLLATE pg_catalog."default",
    store_type     CHARACTER VARYING(50) COLLATE pg_catalog."default"
);
