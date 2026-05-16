-- ============================================================
-- 範例資料表 DDL (hw.md §3)
-- schema  : public
-- table   : food_bank_contacts
-- 用途    : 臺北市政府實物銀行據點聯絡資訊 (社會局, 每年 1/7 月更新)
-- 對應 DAG: Taipei-City-Dashboard-DE/dags/proj_city_dashboard/food_bank_contacts/
-- 對應前端 component: food_bank_points (實物銀行數量)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.food_bank_contacts (
    data_time        timestamp with time zone DEFAULT CURRENT_TIMESTAMP,  -- ETL 寫入時的資料時間戳 (來自來源 data_time)
    seq              integer,                                              -- 來源序號
    institution_type character varying(20) COLLATE pg_catalog."default",   -- 機構類型
    institution_name text                  COLLATE pg_catalog."default",   -- 機構名稱
    district_code    character varying(10) COLLATE pg_catalog."default",   -- 行政區代碼
    address          text                  COLLATE pg_catalog."default"    -- 地址
);

-- 註: is_geometry=0, 無 geometry / lng / lat (本批次不交付地圖)
-- 註: 來源資料無業務唯一鍵, DAG load_behavior=replace, 故不設 primary key
-- 註: data_time 由 ETL 從來源 data_time 欄位轉成 timestamptz 寫入
