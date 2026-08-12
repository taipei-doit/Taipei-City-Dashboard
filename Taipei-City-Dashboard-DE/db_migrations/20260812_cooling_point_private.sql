BEGIN;

-- 臺北市民間涼適點（環保局）。DAG proj_city_dashboard/cooling_point_private 寫入。
-- 來源：https://data.taipei/dataset/detail?id=a1b59e2f-057a-41e2-ae09-482ba5af7d58
--
-- 這份 DDL 是必要的、不能省：job_config 的 load_behavior 是 replace，
-- save_geodataframe_to_postgresql() 會先 TRUNCATE 再 append，
-- 表不存在時第一次執行就會直接失敗。DAG 上線前必須先跑這支。
--
-- 欄位型別由 utils/generate_sql_to_create_DB_table.py 產生，與其他 ready data 表一致
-- （ogc_fid 主鍵 + _ctime/_mtime + mtime trigger）。
--
-- 電話類欄位（localcall/ext/mobile）與 id 一律存字串：來源 CSV 的電話有前導零，
-- ETL 端以 dtype=str 讀取避免掉零，這裡的型別要跟著是 varchar 才不會又被轉回數值。

CREATE SEQUENCE IF NOT EXISTS public.cooling_point_private_tpe_ogc_fid_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

-- 序列一旦 OWNED BY 資料表欄位，Postgres 就禁止單獨改它的 owner
-- (0A000 feature_not_supported)；此時 owner 會隨下方 ALTER TABLE ... OWNER 一併變更。
DO $$
BEGIN
    ALTER TABLE IF EXISTS public.cooling_point_private_tpe_ogc_fid_seq OWNER to airflow;
EXCEPTION WHEN feature_not_supported THEN
    NULL;
END $$;
GRANT ALL ON TABLE public.cooling_point_private_tpe_ogc_fid_seq TO airflow WITH GRANT OPTION;

CREATE TABLE IF NOT EXISTS public.cooling_point_private_tpe
(
    data_time       timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    id              character varying(10) COLLATE pg_catalog."default",
    location_type   character varying(10) COLLATE pg_catalog."default",
    name            text COLLATE pg_catalog."default",
    area            character varying(10) COLLATE pg_catalog."default",
    address         text COLLATE pg_catalog."default",
    longitude       double precision,
    latitude        double precision,
    localcall       character varying(50) COLLATE pg_catalog."default",
    ext             character varying(20) COLLATE pg_catalog."default",
    mobile          character varying(50) COLLATE pg_catalog."default",
    contact_other   text COLLATE pg_catalog."default",
    open_time       text COLLATE pg_catalog."default",
    fan             character varying(5) COLLATE pg_catalog."default",
    aircon          character varying(5) COLLATE pg_catalog."default",
    toilet          character varying(5) COLLATE pg_catalog."default",
    seat            character varying(5) COLLATE pg_catalog."default",
    water_facility  character varying(5) COLLATE pg_catalog."default",
    accessible_seat character varying(5) COLLATE pg_catalog."default",
    features        text COLLATE pg_catalog."default",
    note            text COLLATE pg_catalog."default",
    wkb_geometry    geometry(Point,4326),
    _ctime          timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime          timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid         integer NOT NULL DEFAULT nextval('cooling_point_private_tpe_ogc_fid_seq'::regclass),
    CONSTRAINT cooling_point_private_tpe_pkey PRIMARY KEY (ogc_fid)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cooling_point_private_tpe OWNER to airflow;
GRANT ALL ON TABLE public.cooling_point_private_tpe TO airflow WITH GRANT OPTION;

-- 冪等：先 DROP 再 CREATE，避免表已存在時 trigger 重複建立而失敗
DROP TRIGGER IF EXISTS cooling_point_private_tpe_mtime ON public.cooling_point_private_tpe;
CREATE TRIGGER cooling_point_private_tpe_mtime
    BEFORE INSERT OR UPDATE
    ON public.cooling_point_private_tpe
    FOR EACH ROW
    EXECUTE PROCEDURE public.trigger_set_timestamp();

COMMIT;
