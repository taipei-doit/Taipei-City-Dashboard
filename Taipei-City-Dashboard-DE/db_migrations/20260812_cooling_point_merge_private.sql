BEGIN;

-- 臺北市民間涼適點併入既有的 cooling_point_tpe。
-- DAG proj_city_dashboard/cooling_point 改為一次抓兩個資料集：
--   市府 https://data.taipei/dataset/detail?id=a98a3e0e-a36f-43fa-82f8-b09a3011a47a (494 筆)
--   民間 https://data.taipei/dataset/detail?id=a1b59e2f-057a-41e2-ae09-482ba5af7d58 ( 28 筆)
-- 兩份資料的 名稱/地址 零重疊，直接合併不會產生重複點位。
--
-- cooling_point_tpe 是早期手動建立、未進版控的表，因此下面一律用 IF NOT EXISTS /
-- ALTER ... USING 寫法，不假設現有欄位型別，重跑也安全。

-- 1) 來源別。兩個資料集的「編號」各自從 1 開始，併表後 id 不再唯一，
--    要指涉單一點位請用 (provider, id) 或 ogc_fid。
ALTER TABLE public.cooling_point_tpe
    ADD COLUMN IF NOT EXISTS provider character varying(10) COLLATE pg_catalog."default";

-- 2) id 與電話類欄位一律存字串。
--    ETL 端改用 dtype=str 讀 CSV（否則 pandas 會把 手機/分機 推斷成 float64，
--    寫進來變成 972867232.0）；欄位型別要跟著是 varchar 才不會又被轉回數值。
ALTER TABLE public.cooling_point_tpe
    ALTER COLUMN id        TYPE character varying(10) USING id::varchar,
    ALTER COLUMN localcall TYPE character varying(50) USING localcall::varchar,
    ALTER COLUMN ext       TYPE character varying(20) USING ext::varchar,
    ALTER COLUMN mobile    TYPE character varying(50) USING mobile::varchar;

-- 3) 放寬設施欄位寬度。
--    這幾欄不是只有 Y/N，市府那份實際出現 'Y\n(部分區域)'（8 字元）這種值，
--    原本若是 varchar(5) 會在寫入時被 Postgres 擋下來。
ALTER TABLE public.cooling_point_tpe
    ALTER COLUMN fan             TYPE character varying(20) USING fan::varchar,
    ALTER COLUMN aircon          TYPE character varying(20) USING aircon::varchar,
    ALTER COLUMN toilet          TYPE character varying(20) USING toilet::varchar,
    ALTER COLUMN seat            TYPE character varying(20) USING seat::varchar,
    ALTER COLUMN water_facility  TYPE character varying(20) USING water_facility::varchar,
    ALTER COLUMN accessible_seat TYPE character varying(20) USING accessible_seat::varchar;

COMMIT;
