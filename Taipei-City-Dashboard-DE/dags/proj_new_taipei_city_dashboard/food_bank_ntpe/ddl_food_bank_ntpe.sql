-- ============================================================
-- 範例資料表 DDL (hw.md §3)
-- schema  : public
-- table   : food_bank_ntpe
-- 用途    : 新北市實物銀行分行及領用站一覽表 (社會局, 每年 1/7 月更新)
-- 對應 DAG: Taipei-City-Dashboard-DE/dags/proj_new_taipei_city_dashboard/food_bank_ntpe/
-- 對應前端 component: food_bank_points (實物銀行數量)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.food_bank_ntpe (
    data_time   timestamp with time zone DEFAULT CURRENT_TIMESTAMP,  -- ETL 寫入時的資料時間戳
    seq         integer,                                              -- 來源序號 (no)
    title       text                  COLLATE pg_catalog."default",   -- 分行/領用站名稱
    county_code character varying(10) COLLATE pg_catalog."default",   -- 縣市代碼
    county      character varying(10) COLLATE pg_catalog."default",   -- 縣市
    area_code   character varying(10) COLLATE pg_catalog."default",   -- 行政區代碼
    area        character varying(10) COLLATE pg_catalog."default",   -- 行政區
    postal_code character varying(10) COLLATE pg_catalog."default",   -- 郵遞區號
    address     text                  COLLATE pg_catalog."default",   -- 地址
    phone       character varying(50) COLLATE pg_catalog."default"    -- 連絡電話
);

-- 註: is_geometry=0, 無 geometry / lng / lat (本批次不交付地圖)
-- 註: 來源資料無業務唯一鍵, DAG load_behavior=replace, 故不設 primary key
-- 註: data_time 由 ETL 寫入時以當下時間戳記填入 (來源不含時間欄位)
