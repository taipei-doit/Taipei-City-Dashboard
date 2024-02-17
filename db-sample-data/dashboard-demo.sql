--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1 (Debian 16.1-1.pgdg110+1)
-- Dumped by pg_dump version 16.1

-- Started on 2024-02-16 10:54:01 UTC

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 11 (class 2615 OID 19300)
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA tiger;


--
-- TOC entry 12 (class 2615 OID 19556)
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA tiger_data;


--
-- TOC entry 10 (class 2615 OID 19121)
-- Name: topology; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA topology;


--
-- TOC entry 4 (class 3079 OID 19288)
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- TOC entry 2 (class 3079 OID 18043)
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- TOC entry 5 (class 3079 OID 19301)
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- TOC entry 3 (class 3079 OID 19122)
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- TOC entry 648 (class 1255 OID 19727)
-- Name: trigger_auto_accumulate_been_used_count(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trigger_auto_accumulate_been_used_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.been_used_count = OLD.been_used_count + 1;
  RETURN NEW;
END;
$$;


--
-- TOC entry 1141 (class 1255 OID 19728)
-- Name: trigger_been_used_count_accumulator(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trigger_been_used_count_accumulator() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.been_used_count = been_used_count + 1;
  RETURN NEW;
END;
$$;


--
-- TOC entry 1396 (class 1255 OID 19729)
-- Name: trigger_set_backup_time(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trigger_set_backup_time() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
	NEW.backup_time = NOW();
	RETURN NEW;
END;
$$;


--
-- TOC entry 1094 (class 1255 OID 19730)
-- Name: trigger_set_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trigger_set_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW._mtime = NOW();
  RETURN NEW;
END;
$$;


--
-- TOC entry 1339 (class 1255 OID 19731)
-- Name: update_app_calcu_hourly_patrol_rainfall_view(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_app_calcu_hourly_patrol_rainfall_view() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
		CREATE or replace VIEW "app_calcu_hourly_patrol_rainfall_view" AS
			select  distinct on (d."station_no") d."station_no", a2."ogc_fid", d."station_name", a2."rec_time", a2."hr_acc_rain", 
				a2."this_hr", a2."last_hr", a2."_ctime" , a2."_mtime", d."wkb_geometry"
			from (
				select station_no,station_name,wkb_geometry from work_rainfall_station_location
				union
				select station_no,station_name,wkb_geometry from cwb_rainfall_station_location
				)as d
			JOIN "app_calcu_hourly_patrol_rainfall" AS a2 ON d."station_no"  = a2."station_no"
			where EXTRACT(EPOCH FROM (NOW() - a2."rec_time")) < 3600
			order by d."station_no", a2."rec_time";
	RETURN NULL;
	END;
$$;


--
-- TOC entry 284 (class 1259 OID 19732)
-- Name:  building_publand_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public." building_publand_ogc_fid_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 285 (class 1259 OID 19733)
-- Name: SOCL_export_filter_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."SOCL_export_filter_ppl_ogc_fid_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 286 (class 1259 OID 19734)
-- Name: app_calcu_daily_sentiment_voice1999_109_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_daily_sentiment_voice1999_109_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 287 (class 1259 OID 19735)
-- Name: app_calcu_hour_traffic_info_histories_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_hour_traffic_info_histories_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 288 (class 1259 OID 19736)
-- Name: app_calcu_hour_traffic_youbike_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_hour_traffic_youbike_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 289 (class 1259 OID 19737)
-- Name: app_calcu_hourly_it_5g_smart_all_pole_device_log_dev13_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_hourly_it_5g_smart_all_pole_device_log_dev13_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 290 (class 1259 OID 19738)
-- Name: app_calcu_month_traffic_info_histories_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_month_traffic_info_histories_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 291 (class 1259 OID 19739)
-- Name: app_calcu_monthly_socl_welfare_people_ppl_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_monthly_socl_welfare_people_ppl_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 292 (class 1259 OID 19740)
-- Name: app_calcu_monthly_socl_welfare_people_ppl; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_calcu_monthly_socl_welfare_people_ppl (
    district character varying,
    is_low_middle_income double precision,
    is_disabled double precision,
    is_disabled_allowance double precision,
    is_low_income double precision,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid integer DEFAULT nextval('public.app_calcu_monthly_socl_welfare_people_ppl_seq'::regclass) NOT NULL
);


--
-- TOC entry 293 (class 1259 OID 19748)
-- Name: app_calcu_patrol_rainfall_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_patrol_rainfall_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 294 (class 1259 OID 19749)
-- Name: app_calcu_sentiment_dispatch_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_sentiment_dispatch_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 295 (class 1259 OID 19750)
-- Name: app_calcu_traffic_todaywork_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_traffic_todaywork_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 296 (class 1259 OID 19751)
-- Name: app_calcu_weekly_dispatching_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_weekly_dispatching_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 297 (class 1259 OID 19752)
-- Name: app_calcu_weekly_hellotaipei_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_weekly_hellotaipei_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 298 (class 1259 OID 19753)
-- Name: app_calcu_weekly_metro_capacity_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_weekly_metro_capacity_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 299 (class 1259 OID 19754)
-- Name: app_calcu_weekly_metro_capacity_threshould_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcu_weekly_metro_capacity_threshould_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 300 (class 1259 OID 19755)
-- Name: app_calcul_weekly_hellotaipei_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_calcul_weekly_hellotaipei_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 301 (class 1259 OID 19756)
-- Name: app_traffic_lives_accident_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_traffic_lives_accident_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 302 (class 1259 OID 19757)
-- Name: app_traffic_metro_capacity_realtime_stat_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_traffic_metro_capacity_realtime_stat_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 303 (class 1259 OID 19758)
-- Name: building_age_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_age_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 304 (class 1259 OID 19759)
-- Name: building_cadastralmap_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_cadastralmap_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 305 (class 1259 OID 19760)
-- Name: building_landuse_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_landuse_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 306 (class 1259 OID 19761)
-- Name: building_license_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_license_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 307 (class 1259 OID 19762)
-- Name: building_license_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_license_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 308 (class 1259 OID 19763)
-- Name: building_permit_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_permit_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 309 (class 1259 OID 19764)
-- Name: building_permit_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_permit_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 310 (class 1259 OID 19765)
-- Name: building_publand_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_publand_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 311 (class 1259 OID 19766)
-- Name: building_publand_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_publand_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 312 (class 1259 OID 19767)
-- Name: building_renewarea_10_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewarea_10_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 313 (class 1259 OID 19768)
-- Name: building_renewarea_10_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewarea_10_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 314 (class 1259 OID 19769)
-- Name: building_renewarea_40_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewarea_40_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 315 (class 1259 OID 19770)
-- Name: building_renewarea_40_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewarea_40_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 316 (class 1259 OID 19771)
-- Name: building_renewunit_12_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_12_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 317 (class 1259 OID 19772)
-- Name: building_renewunit_12_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_12_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 318 (class 1259 OID 19773)
-- Name: building_renewunit_20_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_20_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 319 (class 1259 OID 19774)
-- Name: building_renewunit_20_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_20_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 320 (class 1259 OID 19775)
-- Name: building_renewunit_30_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_30_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 321 (class 1259 OID 19776)
-- Name: building_renewunit_30_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_renewunit_30_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 322 (class 1259 OID 19777)
-- Name: building_social_house_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_social_house_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 323 (class 1259 OID 19778)
-- Name: building_social_house_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_social_house_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 324 (class 1259 OID 19779)
-- Name: building_unsued_land_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_land_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 325 (class 1259 OID 19780)
-- Name: building_unsued_land; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.building_unsued_land (
    thekey character varying,
    thename character varying,
    thelink character varying,
    aa48 character varying,
    aa49 character varying,
    aa10 double precision,
    aa21 double precision,
    aa22 double precision,
    kcnt character varying,
    cada_text character varying,
    aa17 double precision,
    aa16 double precision,
    aa46 character varying,
    "cadastral map_key_地籍圖key值" character varying,
    "10712土地_1_土地權屬情形" character varying,
    "10712土地_1_管理機關" character varying,
    area double precision,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid integer DEFAULT nextval('public.building_unsued_land_ogc_fid_seq'::regclass) NOT NULL
);


--
-- TOC entry 326 (class 1259 OID 19788)
-- Name: building_unsued_land_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_land_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 327 (class 1259 OID 19789)
-- Name: building_unsued_nonpublic_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_nonpublic_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 328 (class 1259 OID 19790)
-- Name: building_unsued_nonpublic_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_nonpublic_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 329 (class 1259 OID 19791)
-- Name: building_unsued_public; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.building_unsued_public (
    full_key character varying,
    "建物管理機關" character varying,
    "行政區" character varying,
    "門牌" character varying,
    "建物標示" character varying,
    "建築完成日期" character varying,
    "閒置樓層_閒置樓層/該建物總樓層" character varying,
    "閒置面積㎡" character varying,
    "房屋現況" character varying,
    "原使用用途" character varying,
    "基地所有權人" character varying,
    "基地管理機關" character varying,
    "土地使用分區" character varying,
    "目前執行情形" character varying,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 330 (class 1259 OID 19798)
-- Name: building_unsued_public_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_public_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 331 (class 1259 OID 19799)
-- Name: building_unsued_public_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.building_unsued_public_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 332 (class 1259 OID 19800)
-- Name: cvil_public_opinion_evn_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cvil_public_opinion_evn_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 333 (class 1259 OID 19801)
-- Name: cvil_public_opinion_maintype_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cvil_public_opinion_maintype_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 334 (class 1259 OID 19802)
-- Name: cvil_public_opinion_subtype_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cvil_public_opinion_subtype_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 335 (class 1259 OID 19803)
-- Name: cwb_city_weather_forecast_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_city_weather_forecast_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 336 (class 1259 OID 19804)
-- Name: cwb_city_weather_forecast_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_city_weather_forecast_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 337 (class 1259 OID 19805)
-- Name: cwb_daily_weather_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_daily_weather_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 338 (class 1259 OID 19806)
-- Name: cwb_hourly_weather_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_hourly_weather_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 339 (class 1259 OID 19807)
-- Name: cwb_now_weather_auto_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_now_weather_auto_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 340 (class 1259 OID 19808)
-- Name: cwb_now_weather_auto_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_now_weather_auto_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 341 (class 1259 OID 19809)
-- Name: cwb_now_weather_bureau_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_now_weather_bureau_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 342 (class 1259 OID 19810)
-- Name: cwb_now_weather_bureau_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_now_weather_bureau_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 343 (class 1259 OID 19811)
-- Name: cwb_rainfall_station_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_rainfall_station_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 344 (class 1259 OID 19812)
-- Name: cwb_rainfall_station_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_rainfall_station_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 345 (class 1259 OID 19813)
-- Name: cwb_town_weather_forecast_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_town_weather_forecast_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 346 (class 1259 OID 19814)
-- Name: cwb_town_weather_forecast_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cwb_town_weather_forecast_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 347 (class 1259 OID 19815)
-- Name: edu_elementary_school_district_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_elementary_school_district_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 348 (class 1259 OID 19816)
-- Name: edu_elementary_school_district_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_elementary_school_district_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 349 (class 1259 OID 19817)
-- Name: edu_eleschool_dist_by_administrative_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_eleschool_dist_by_administrative_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 350 (class 1259 OID 19818)
-- Name: edu_eleschool_dist_by_administrative_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_eleschool_dist_by_administrative_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 351 (class 1259 OID 19819)
-- Name: edu_jhschool_dist_by_administrative_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_jhschool_dist_by_administrative_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 352 (class 1259 OID 19820)
-- Name: edu_jhschool_dist_by_administrative_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_jhschool_dist_by_administrative_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 353 (class 1259 OID 19821)
-- Name: edu_junior_high_school_district_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_junior_high_school_district_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 354 (class 1259 OID 19822)
-- Name: edu_junior_high_school_district_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_junior_high_school_district_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 355 (class 1259 OID 19823)
-- Name: edu_school_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_school_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 356 (class 1259 OID 19824)
-- Name: edu_school_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_school_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 357 (class 1259 OID 19825)
-- Name: edu_school_romm_status_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_school_romm_status_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 358 (class 1259 OID 19826)
-- Name: edu_school_romm_status_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edu_school_romm_status_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 359 (class 1259 OID 19827)
-- Name: eoc_accommodate_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_accommodate_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 360 (class 1259 OID 19828)
-- Name: eoc_accommodate_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_accommodate_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 361 (class 1259 OID 19829)
-- Name: eoc_disaster_case_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_disaster_case_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 362 (class 1259 OID 19830)
-- Name: eoc_disaster_case_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_disaster_case_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 363 (class 1259 OID 19831)
-- Name: eoc_leave_house_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_leave_house_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 364 (class 1259 OID 19832)
-- Name: eoc_leave_house_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.eoc_leave_house_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 365 (class 1259 OID 19833)
-- Name: ethc_building_check_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ethc_building_check_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 366 (class 1259 OID 19834)
-- Name: ethc_check_calcu_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ethc_check_calcu_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 367 (class 1259 OID 19835)
-- Name: ethc_check_summary_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ethc_check_summary_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 368 (class 1259 OID 19836)
-- Name: ethc_fire_check_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ethc_fire_check_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 369 (class 1259 OID 19837)
-- Name: fire_hydrant_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fire_hydrant_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 370 (class 1259 OID 19838)
-- Name: fire_hydrant_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fire_hydrant_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 371 (class 1259 OID 19839)
-- Name: fire_to_hospital_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fire_to_hospital_ppl_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 372 (class 1259 OID 19840)
-- Name: heal_aed_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_aed_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 373 (class 1259 OID 19841)
-- Name: heal_aed_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_aed_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 374 (class 1259 OID 19842)
-- Name: heal_clinic_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_clinic_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 375 (class 1259 OID 19843)
-- Name: heal_clinic_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_clinic_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 376 (class 1259 OID 19844)
-- Name: heal_hospital_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_hospital_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 377 (class 1259 OID 19845)
-- Name: heal_hospital_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_hospital_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 378 (class 1259 OID 19846)
-- Name: heal_suicide_evn_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heal_suicide_evn_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 379 (class 1259 OID 19847)
-- Name: it_5G_smart_pole_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."it_5G_smart_pole_ogc_fid_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 380 (class 1259 OID 19848)
-- Name: it_5g_smart_all_pole_device_log_history_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_5g_smart_all_pole_device_log_history_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 381 (class 1259 OID 19849)
-- Name: it_5g_smart_all_pole_device_log_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_5g_smart_all_pole_device_log_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 382 (class 1259 OID 19850)
-- Name: it_5g_smart_all_pole_log_history_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_5g_smart_all_pole_log_history_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 383 (class 1259 OID 19851)
-- Name: it_5g_smart_all_pole_log_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_5g_smart_all_pole_log_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 384 (class 1259 OID 19852)
-- Name: it_5g_smart_pole_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_5g_smart_pole_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 385 (class 1259 OID 19853)
-- Name: it_signal_population_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_signal_population_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 386 (class 1259 OID 19854)
-- Name: it_signal_population_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_signal_population_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 387 (class 1259 OID 19855)
-- Name: it_signal_tourist_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_signal_tourist_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 388 (class 1259 OID 19856)
-- Name: it_signal_tourist_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_signal_tourist_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 389 (class 1259 OID 19857)
-- Name: it_taipeiexpo_people_flow_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_taipeiexpo_people_flow_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 390 (class 1259 OID 19858)
-- Name: it_taipeiexpo_people_flow_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_taipeiexpo_people_flow_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 391 (class 1259 OID 19859)
-- Name: it_tpe_ticket_event_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpe_ticket_event_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 392 (class 1259 OID 19860)
-- Name: it_tpe_ticket_member_hold_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpe_ticket_member_hold_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 393 (class 1259 OID 19861)
-- Name: it_tpe_ticket_place_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpe_ticket_place_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 394 (class 1259 OID 19862)
-- Name: it_tpe_ticket_ticket_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpe_ticket_ticket_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 395 (class 1259 OID 19863)
-- Name: it_tpefree_daily_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_daily_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 396 (class 1259 OID 19864)
-- Name: it_tpefree_daily_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_daily_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 397 (class 1259 OID 19865)
-- Name: it_tpefree_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 398 (class 1259 OID 19866)
-- Name: it_tpefree_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 399 (class 1259 OID 19867)
-- Name: it_tpefree_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 400 (class 1259 OID 19868)
-- Name: it_tpefree_realtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpefree_realtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 401 (class 1259 OID 19869)
-- Name: it_tpmo_poc_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpmo_poc_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 402 (class 1259 OID 19870)
-- Name: it_tpmo_poc_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_tpmo_poc_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 403 (class 1259 OID 19871)
-- Name: it_venue_people_flow_history_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_venue_people_flow_history_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 404 (class 1259 OID 19872)
-- Name: it_venue_people_flow_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.it_venue_people_flow_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 405 (class 1259 OID 19873)
-- Name: mrtp_carweight_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.mrtp_carweight_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 406 (class 1259 OID 19874)
-- Name: mrtp_carweight_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.mrtp_carweight_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 407 (class 1259 OID 19875)
-- Name: patrol_artificial_slope_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_artificial_slope_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 408 (class 1259 OID 19876)
-- Name: patrol_artificial_slope_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_artificial_slope_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 409 (class 1259 OID 19877)
-- Name: patrol_box_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_box_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 410 (class 1259 OID 19878)
-- Name: patrol_camera_hls_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_camera_hls_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 411 (class 1259 OID 19879)
-- Name: patrol_car_theft_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_car_theft_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 412 (class 1259 OID 19880)
-- Name: patrol_criminal_case_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_criminal_case_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 413 (class 1259 OID 19881)
-- Name: patrol_criminal_case; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patrol_criminal_case (
    "破獲件數/總計[件]" integer,
    "破獲率[%]" double precision,
    "犯罪人口率[人/十萬人]" double precision,
    "嫌疑犯[人]" integer,
    "發生件數[件]" integer,
    "破獲件數/他轄[件]" character varying,
    "破獲件數/積案[件]" character varying,
    _id character varying,
    "破獲件數/當期[件]" character varying,
    "發生率[件/十萬人]" double precision,
    "實際員警人數[人]" character varying,
    "年月別" timestamp with time zone,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid integer DEFAULT nextval('public.patrol_criminal_case_ogc_fid_seq'::regclass) NOT NULL
);


--
-- TOC entry 414 (class 1259 OID 19889)
-- Name: patrol_debris_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_debris_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 415 (class 1259 OID 19890)
-- Name: patrol_debris_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_debris_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 416 (class 1259 OID 19891)
-- Name: patrol_debrisarea_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_debrisarea_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 417 (class 1259 OID 19892)
-- Name: patrol_debrisarea_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_debrisarea_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 418 (class 1259 OID 19893)
-- Name: patrol_designate_place_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_designate_place_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 419 (class 1259 OID 19894)
-- Name: patrol_designate_place_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_designate_place_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 420 (class 1259 OID 19895)
-- Name: patrol_district_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_district_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 421 (class 1259 OID 19896)
-- Name: patrol_eoc_case_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_eoc_case_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 422 (class 1259 OID 19897)
-- Name: patrol_eoc_case_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_eoc_case_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 423 (class 1259 OID 19898)
-- Name: patrol_eoc_designate_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_eoc_designate_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 424 (class 1259 OID 19899)
-- Name: patrol_eoc_designate_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_eoc_designate_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 425 (class 1259 OID 19900)
-- Name: patrol_fire_brigade_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_brigade_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 426 (class 1259 OID 19901)
-- Name: patrol_fire_brigade_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_brigade_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 427 (class 1259 OID 19902)
-- Name: patrol_fire_disqualified_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_disqualified_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 428 (class 1259 OID 19903)
-- Name: patrol_fire_disqualified_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_disqualified_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 429 (class 1259 OID 19904)
-- Name: patrol_fire_rescure_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_rescure_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 430 (class 1259 OID 19905)
-- Name: patrol_fire_rescure_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_fire_rescure_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 431 (class 1259 OID 19906)
-- Name: patrol_flood_100_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_flood_100_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 432 (class 1259 OID 19907)
-- Name: patrol_flood_130_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_flood_130_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 433 (class 1259 OID 19908)
-- Name: patrol_flood_78_8_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_flood_78_8_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 434 (class 1259 OID 19909)
-- Name: patrol_motorcycle_theft_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_motorcycle_theft_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 435 (class 1259 OID 19910)
-- Name: patrol_old_settlement_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_old_settlement_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 436 (class 1259 OID 19911)
-- Name: patrol_old_settlement_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_old_settlement_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 437 (class 1259 OID 19912)
-- Name: patrol_police_region_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_police_region_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 438 (class 1259 OID 19913)
-- Name: patrol_police_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_police_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 439 (class 1259 OID 19914)
-- Name: patrol_police_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_police_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 440 (class 1259 OID 19915)
-- Name: patrol_police_station_ogc_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_police_station_ogc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 441 (class 1259 OID 19916)
-- Name: patrol_rain_floodgate_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_floodgate_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 442 (class 1259 OID 19917)
-- Name: patrol_rain_floodgate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patrol_rain_floodgate (
    ogc_fid integer DEFAULT nextval('public.patrol_rain_floodgate_ogc_fid_seq'::regclass) NOT NULL,
    station_no character varying,
    station_name character varying,
    rec_time timestamp with time zone,
    all_pumb_lights character varying,
    pumb_num integer,
    door_num integer,
    river_basin character varying,
    warning_level character varying,
    start_pumping_level character varying,
    lng double precision,
    lat double precision,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 443 (class 1259 OID 19925)
-- Name: patrol_rain_floodgate_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_floodgate_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 444 (class 1259 OID 19926)
-- Name: patrol_rain_rainfall_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_rainfall_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 445 (class 1259 OID 19927)
-- Name: patrol_rain_rainfall_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_rainfall_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 446 (class 1259 OID 19928)
-- Name: patrol_rain_sewer_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_sewer_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 447 (class 1259 OID 19929)
-- Name: patrol_rain_sewer_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_sewer_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 448 (class 1259 OID 19930)
-- Name: patrol_rain_sewer_ogc_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_rain_sewer_ogc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 449 (class 1259 OID 19931)
-- Name: patrol_random_robber_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_random_robber_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 450 (class 1259 OID 19932)
-- Name: patrol_random_snatch_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_random_snatch_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 451 (class 1259 OID 19933)
-- Name: patrol_residential_burglary_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.patrol_residential_burglary_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 452 (class 1259 OID 19934)
-- Name: poli_traffic_violation_evn_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.poli_traffic_violation_evn_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 453 (class 1259 OID 19935)
-- Name: poli_traffic_violation_mapping_code_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.poli_traffic_violation_mapping_code_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 454 (class 1259 OID 19936)
-- Name: record_db_mtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.record_db_mtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 455 (class 1259 OID 19937)
-- Name: sentiment_councillor_109_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_councillor_109_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 456 (class 1259 OID 19938)
-- Name: sentiment_dispatching_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_dispatching_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 457 (class 1259 OID 19939)
-- Name: sentiment_hello_taipei_109_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_hello_taipei_109_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 458 (class 1259 OID 19940)
-- Name: sentiment_hello_taipei_109_test_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_hello_taipei_109_test_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 459 (class 1259 OID 19941)
-- Name: sentiment_hotnews_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_hotnews_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 460 (class 1259 OID 19942)
-- Name: sentiment_voice1999_109_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sentiment_voice1999_109_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 461 (class 1259 OID 19943)
-- Name: socl_case_study_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_case_study_ppl_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 462 (class 1259 OID 19944)
-- Name: socl_dept_epidemic_info_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_dept_epidemic_info_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 463 (class 1259 OID 19945)
-- Name: socl_domestic_violence_evn_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_domestic_violence_evn_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 464 (class 1259 OID 19946)
-- Name: socl_export_filter_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_export_filter_ppl_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 465 (class 1259 OID 19947)
-- Name: socl_order_concern_mapping_code_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_order_concern_mapping_code_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 466 (class 1259 OID 19948)
-- Name: socl_order_concern_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_order_concern_ppl_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 0
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 467 (class 1259 OID 19949)
-- Name: socl_welfare_dis_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_dis_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 468 (class 1259 OID 19950)
-- Name: socl_welfare_dis_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_dis_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 469 (class 1259 OID 19951)
-- Name: socl_welfare_dislow_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_dislow_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 470 (class 1259 OID 19952)
-- Name: socl_welfare_dislow_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_dislow_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 471 (class 1259 OID 19953)
-- Name: socl_welfare_low_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_low_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 472 (class 1259 OID 19954)
-- Name: socl_welfare_low_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_low_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 473 (class 1259 OID 19955)
-- Name: socl_welfare_midlow_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_midlow_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 474 (class 1259 OID 19956)
-- Name: socl_welfare_midlow_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_midlow_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 475 (class 1259 OID 19957)
-- Name: socl_welfare_organization_plc_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_organization_plc_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 476 (class 1259 OID 19958)
-- Name: socl_welfare_organization_plc; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socl_welfare_organization_plc (
    main_type character varying,
    sub_type character varying,
    name character varying,
    address character varying,
    lon double precision,
    lat double precision,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid integer DEFAULT nextval('public.socl_welfare_organization_plc_ogc_fid_seq'::regclass) NOT NULL
);


--
-- TOC entry 477 (class 1259 OID 19966)
-- Name: socl_welfare_organization_plc_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_organization_plc_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 478 (class 1259 OID 19967)
-- Name: socl_welfare_people_ppl_history_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_people_ppl_history_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 479 (class 1259 OID 19968)
-- Name: socl_welfare_people_ppl_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.socl_welfare_people_ppl_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 480 (class 1259 OID 19969)
-- Name: tdx_bus_live_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_bus_live_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 481 (class 1259 OID 19970)
-- Name: tdx_bus_route_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_bus_route_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 482 (class 1259 OID 19971)
-- Name: tdx_bus_route_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_bus_route_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 483 (class 1259 OID 19972)
-- Name: tdx_bus_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_bus_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 484 (class 1259 OID 19973)
-- Name: tdx_bus_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_bus_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 485 (class 1259 OID 19974)
-- Name: tdx_metro_line_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_metro_line_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 486 (class 1259 OID 19975)
-- Name: tdx_metro_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tdx_metro_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 487 (class 1259 OID 19976)
-- Name: tour_2023_lantern_festival_mapping_table_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_2023_lantern_festival_mapping_table_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 488 (class 1259 OID 19977)
-- Name: tour_2023_lantern_festival_zone_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_2023_lantern_festival_zone_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 489 (class 1259 OID 19978)
-- Name: tour_2023_latern_festival_mapping_table_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_2023_latern_festival_mapping_table_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 490 (class 1259 OID 19979)
-- Name: tour_2023_latern_festival_point_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_2023_latern_festival_point_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 491 (class 1259 OID 19980)
-- Name: tour_lantern_festival_sysmemorialhall_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tour_lantern_festival_sysmemorialhall_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 492 (class 1259 OID 19981)
-- Name: tp_building_bim_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_building_bim_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 493 (class 1259 OID 19982)
-- Name: tp_building_height_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_building_height_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 494 (class 1259 OID 19983)
-- Name: tp_cht_grid_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_cht_grid_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 495 (class 1259 OID 19984)
-- Name: tp_district_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_district_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 496 (class 1259 OID 19985)
-- Name: tp_fet_age_hr_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_fet_age_hr_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 497 (class 1259 OID 19986)
-- Name: tp_fet_hourly_popu_by_vil_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_fet_hourly_popu_by_vil_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 498 (class 1259 OID 19987)
-- Name: tp_fet_work_live_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_fet_work_live_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 499 (class 1259 OID 19988)
-- Name: tp_road_center_line_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_road_center_line_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 500 (class 1259 OID 19989)
-- Name: tp_village_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_village_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 501 (class 1259 OID 19990)
-- Name: tp_village_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tp_village_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 502 (class 1259 OID 19991)
-- Name: traffic_accident_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_accident_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 503 (class 1259 OID 19992)
-- Name: traffic_accident_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_accident_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 504 (class 1259 OID 19993)
-- Name: traffic_bus_route_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_bus_route_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 505 (class 1259 OID 19994)
-- Name: traffic_bus_route_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_bus_route_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 506 (class 1259 OID 19995)
-- Name: traffic_bus_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_bus_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 507 (class 1259 OID 19996)
-- Name: traffic_bus_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_bus_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 508 (class 1259 OID 19997)
-- Name: traffic_bus_stop_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_bus_stop_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 509 (class 1259 OID 19998)
-- Name: traffic_info_histories_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_info_histories_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 510 (class 1259 OID 19999)
-- Name: traffic_lives_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_lives_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 511 (class 1259 OID 20000)
-- Name: traffic_lives_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_lives_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 512 (class 1259 OID 20001)
-- Name: traffic_metro_capacity_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_capacity_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 513 (class 1259 OID 20002)
-- Name: traffic_metro_capacity_realtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_capacity_realtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 514 (class 1259 OID 20003)
-- Name: traffic_metro_capacity_rtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_capacity_rtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 515 (class 1259 OID 20004)
-- Name: traffic_metro_line_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_line_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 516 (class 1259 OID 20005)
-- Name: traffic_metro_line_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_line_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 517 (class 1259 OID 20006)
-- Name: traffic_metro_realtime_position_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_realtime_position_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 518 (class 1259 OID 20007)
-- Name: traffic_metro_realtime_position_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_realtime_position_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 519 (class 1259 OID 20008)
-- Name: traffic_metro_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 520 (class 1259 OID 20009)
-- Name: traffic_metro_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 521 (class 1259 OID 20010)
-- Name: traffic_metro_unusual_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_unusual_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 522 (class 1259 OID 20011)
-- Name: traffic_metro_unusual_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_metro_unusual_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 523 (class 1259 OID 20012)
-- Name: traffic_todayworks_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_todayworks_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 524 (class 1259 OID 20013)
-- Name: traffic_youbike_one_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_youbike_one_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 525 (class 1259 OID 20014)
-- Name: traffic_youbike_realtime_histories_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_youbike_realtime_histories_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 526 (class 1259 OID 20015)
-- Name: traffic_youbike_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_youbike_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 527 (class 1259 OID 20016)
-- Name: traffic_youbike_two_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traffic_youbike_two_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 528 (class 1259 OID 20017)
-- Name: tran_parking_capacity_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_parking_capacity_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 529 (class 1259 OID 20018)
-- Name: tran_parking_capacity_realtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_parking_capacity_realtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 530 (class 1259 OID 20019)
-- Name: tran_parking_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_parking_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 531 (class 1259 OID 20020)
-- Name: tran_parking_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_parking_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 532 (class 1259 OID 20021)
-- Name: tran_ubike_realtime_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_ubike_realtime_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 533 (class 1259 OID 20022)
-- Name: tran_ubike_realtime_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_ubike_realtime_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 534 (class 1259 OID 20023)
-- Name: tran_ubike_station_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_ubike_station_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 535 (class 1259 OID 20024)
-- Name: tran_ubike_station_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_ubike_station_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 536 (class 1259 OID 20025)
-- Name: tran_urban_bike_path_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_urban_bike_path_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 537 (class 1259 OID 20026)
-- Name: tran_urban_bike_path_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tran_urban_bike_path_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 538 (class 1259 OID 20027)
-- Name: tw_village_center_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tw_village_center_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 539 (class 1259 OID 20028)
-- Name: tw_village_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tw_village_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 540 (class 1259 OID 20029)
-- Name: work_eco_park_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_eco_park_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 541 (class 1259 OID 20030)
-- Name: work_eco_park_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_eco_park_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 542 (class 1259 OID 20031)
-- Name: work_floodgate_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_floodgate_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 543 (class 1259 OID 20032)
-- Name: work_floodgate_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_floodgate_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 544 (class 1259 OID 20033)
-- Name: work_garden_city_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_garden_city_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 545 (class 1259 OID 20034)
-- Name: work_garden_city_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_garden_city_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 546 (class 1259 OID 20035)
-- Name: work_goose_sanctuary_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_goose_sanctuary_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 547 (class 1259 OID 20036)
-- Name: work_goose_sanctuary_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_goose_sanctuary_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 548 (class 1259 OID 20037)
-- Name: work_nature_reserve_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_nature_reserve_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 549 (class 1259 OID 20038)
-- Name: work_nature_reserve_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_nature_reserve_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 550 (class 1259 OID 20039)
-- Name: work_park_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_park_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 551 (class 1259 OID 20040)
-- Name: work_park_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_park_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 552 (class 1259 OID 20041)
-- Name: work_pumping_station_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_pumping_station_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 553 (class 1259 OID 20042)
-- Name: work_pumping_station_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_pumping_station_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 554 (class 1259 OID 20043)
-- Name: work_rainfall_station_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_rainfall_station_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 555 (class 1259 OID 20044)
-- Name: work_rainfall_station_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_rainfall_station_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 556 (class 1259 OID 20045)
-- Name: work_riverside_bike_path_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_riverside_bike_path_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 557 (class 1259 OID 20046)
-- Name: work_riverside_bike_path_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_riverside_bike_path_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 558 (class 1259 OID 20047)
-- Name: work_riverside_park_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_riverside_park_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 559 (class 1259 OID 20048)
-- Name: work_riverside_park_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_riverside_park_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 560 (class 1259 OID 20049)
-- Name: work_school_greening_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_school_greening_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 561 (class 1259 OID 20050)
-- Name: work_school_greening_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_school_greening_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 562 (class 1259 OID 20051)
-- Name: work_sewer_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_sewer_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 563 (class 1259 OID 20052)
-- Name: work_sewer_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_sewer_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 564 (class 1259 OID 20053)
-- Name: work_sidewalk_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_sidewalk_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 565 (class 1259 OID 20054)
-- Name: work_sidewalk_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_sidewalk_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 566 (class 1259 OID 20055)
-- Name: work_soil_liquefaction_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_soil_liquefaction_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 567 (class 1259 OID 20056)
-- Name: work_soil_liquefaction_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_soil_liquefaction_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 568 (class 1259 OID 20057)
-- Name: work_street_light_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_street_light_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 569 (class 1259 OID 20058)
-- Name: work_street_light_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_street_light_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 570 (class 1259 OID 20059)
-- Name: work_street_tree_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_street_tree_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 571 (class 1259 OID 20060)
-- Name: work_street_tree_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_street_tree_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 572 (class 1259 OID 20061)
-- Name: work_underpass_location_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_underpass_location_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 573 (class 1259 OID 20062)
-- Name: work_underpass_location_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_underpass_location_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 574 (class 1259 OID 20063)
-- Name: work_urban_agricultural_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_urban_agricultural_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 575 (class 1259 OID 20064)
-- Name: work_urban_agricultural_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_urban_agricultural_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 576 (class 1259 OID 20065)
-- Name: work_urban_reserve_history_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_urban_reserve_history_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 577 (class 1259 OID 20066)
-- Name: work_urban_reserve_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.work_urban_reserve_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5001 (class 0 OID 19740)
-- Dependencies: 292
-- Data for Name: app_calcu_monthly_socl_welfare_people_ppl; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_calcu_monthly_socl_welfare_people_ppl (district, is_low_middle_income, is_disabled, is_disabled_allowance, is_low_income, _ctime, _mtime, ogc_fid) FROM stdin;
士林區	1754	13285	706	5302	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	235
大安區	753	11388	249	1895	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	236
文山區	2180	12441	697	5803	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	238
南港區	1161	6055	431	2555	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	239
松山區	560	7963	188	1701	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	240
大同區	987	6390	353	3040	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	241
中山區	920	9531	354	2474	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	242
內湖區	1415	10711	573	3215	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	243
北投區	1533	11783	634	4453	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	244
中正區	513	6415	238	1785	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	245
萬華區	2549	11303	763	6807	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	246
信義區	1242	10239	444	3208	2023-09-02 00:00:09.443476+00	2023-09-02 00:00:09.443476+00	247
\.


--
-- TOC entry 5034 (class 0 OID 19780)
-- Dependencies: 325
-- Data for Name: building_unsued_land; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.building_unsued_land (thekey, thename, thelink, aa48, aa49, aa10, aa21, aa22, kcnt, cada_text, aa17, aa16, aa46, "cadastral map_key_地籍圖key值", "10712土地_1_土地權屬情形", "10712土地_1_管理機關", area, _ctime, _mtime, ogc_fid) FROM stdin;
000502160000	段名：永昌段五小段 地號：216號	\N	0005	02160000	628	2768796.4	\N	永昌段五小段	216	55800	211000	03	永昌段五小段02160000	臺北市	警察局	628	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19335
095003790000	段名：翠山段一小段 地號：379號	\N	0950	03790000	3681	2777645	\N	翠山段一小段	379	12800	47700	15	翠山段一小段03790000	臺北市	公共運輸處	3681	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19336
027103950008	段名：大龍段一小段 地號：395-8號	\N	0271	03950008	496	2774018.4	\N	大龍段一小段	395-8	45725	170573	09	大龍段一小段03950008	臺北市	消防局	496	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19337
007506670000	段名：實踐段二小段 地號：667號	\N	0075	06670000	1305.48	2763647.1	\N	實踐段二小段	667	53000	196000	11	實踐段二小段06670000	臺北市	市場處	1305.48	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19338
089600800003	段名：立農段五小段 地號：80-3號	\N	0896	00800003	179	2779077.2	\N	立農段五小段	80-3	73500	273000	16	立農段五小段00800003	臺北市	市場處	179	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19339
089601090004	段名：立農段五小段 地號：109-4號	\N	0896	01090004	266	2779085.725	\N	立農段五小段	109-4	73500	273000	16	立農段五小段01090004	臺北市	市場處	266	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19340
089601090005	段名：立農段五小段 地號：109-5號	\N	0896	01090005	375	2779084.6	\N	立農段五小段	109-5	73500	273000	16	立農段五小段01090005	臺北市	市場處	375	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19341
089601340000	段名：立農段五小段 地號：134號	\N	0896	01340000	6	2779075.9	\N	立農段五小段	134	73500	273000	16	立農段五小段01340000	臺北市	市場處	6	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19342
089601350000	段名：立農段五小段 地號：135號	\N	0896	01350000	103	2779079.31	\N	立農段五小段	135	73500	273000	16	立農段五小段01350000	臺北市	市場處	103	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19343
089601370001	段名：立農段五小段 地號：137-1號	\N	0896	01370001	244	2779089.983	\N	立農段五小段	137-1	73500	273000	16	立農段五小段01370001	臺北市	市場處	244	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19344
089601380002	段名：立農段五小段 地號：138-2號	\N	0896	01380002	4	2779096.4	\N	立農段五小段	138-2	73500	273000	16	立農段五小段01380002	臺北市	市場處	4	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19345
089601420002	段名：立農段五小段 地號：142-2號	\N	0896	01420002	10	2779092.8	\N	立農段五小段	142-2	73500	273000	16	立農段五小段01420002	臺北市	市場處	10	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19346
021903350003	段名：仁愛段三小段 地號：335-3號	\N	0219	03350003	314	2769653.3	\N	仁愛段三小段	335-3	166000	627000	02	仁愛段三小段03350003	臺北市	大安地政事務所	314	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19347
021903350004	段名：仁愛段三小段 地號：335-4號	\N	0219	03350004	221	2769591.7	\N	仁愛段三小段	335-4	237013	907413	02	仁愛段三小段03350004	臺北市	大安地政事務所	221	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19348
021903740003	段名：仁愛段三小段 地號：374-3號	\N	0219	03740003	25	2769591.5	\N	仁愛段三小段	374-3	286000	1097000	02	仁愛段三小段03740003	臺北市	大安地政事務所	25	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19349
046000170000	段名：康寧段一小段 地號：17號	\N	0460	00170000	6932	2775493.9	\N	康寧段一小段	17	7000	25800	14	康寧段一小段00170000	臺北市	體育局	6932	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19350
046000170001	段名：康寧段一小段 地號：17-1號	\N	0460	00170001	1539	2775546.6	\N	康寧段一小段	17-1	7000	25800	14	康寧段一小段00170001	臺北市	體育局	1539	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19351
046000170003	段名：康寧段一小段 地號：17-3號	\N	0460	00170003	44	2775456.2	\N	康寧段一小段	17-3	7000	25800	14	康寧段一小段00170003	臺北市	體育局	44	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19352
046000170004	段名：康寧段一小段 地號：17-4號	\N	0460	00170004	1	2775418.8	\N	康寧段一小段	17-4	7000	25800	14	康寧段一小段00170004	臺北市	體育局	1	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19353
046000170006	段名：康寧段一小段 地號：17-6號	\N	0460	00170006	8155	2775425.956	\N	康寧段一小段	17-6	7000	25800	14	康寧段一小段00170006	臺北市	體育局	8155	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19354
046000170015	段名：康寧段一小段 地號：17-15號	\N	0460	00170015	1	2775429.4	\N	康寧段一小段	17-15	7000	25800	14	康寧段一小段00170015	臺北市	體育局	1	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19355
046000170022	段名：康寧段一小段 地號：17-22號	\N	0460	00170022	2	2775450.5	\N	康寧段一小段	17-22	40400	152000	14	康寧段一小段00170022	臺北市	體育局	2	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19356
085205630000	段名：天山段一小段 地號：563號	\N	0852	05630000	794	2779530.1	\N	天山段一小段	563	53000	199000	15	天山段一小段05630000	臺北市	財政局	794	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19357
085303370000	段名：天山段二小段 地號：337號	\N	0853	03370000	221	2779217.579	\N	天山段二小段	337	53000	199000	15	天山段二小段03370000	臺北市	財政局	221	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19358
085303380000	段名：天山段二小段 地號：338號	\N	0853	03380000	221	2779223.146	\N	天山段二小段	338	53000	199000	15	天山段二小段03380000	臺北市	財政局	221	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19359
085304070000	段名：天山段二小段 地號：407號	\N	0853	04070000	14	2779203.609	\N	天山段二小段	407	53000	199000	15	天山段二小段04070000	臺北市	財政局	14	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19360
082800240001	段名：芝山段一小段 地號：24-1號	\N	0828	00240001	366	2777865.723	\N	芝山段一小段	24-1	80400	302000	15	芝山段一小段00240001	臺北市	財政局	366	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19361
084400420000	段名：溪洲段三小段 地號：42號	\N	0844	00420000	812	2777122.8	\N	溪洲段三小段	42	8700	32600	15	溪洲段三小段00420000	臺北市	財政局	812	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19362
084400430000	段名：溪洲段三小段 地號：43號	\N	0844	00430000	815	2777115.074	\N	溪洲段三小段	43	8700	32600	15	溪洲段三小段00430000	臺北市	財政局	815	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19363
027806620000	段名：大同段二小段 地號：662號	\N	0278	06620000	389	2773163.568	\N	大同段二小段	662	62351	232391	09	大同段二小段06620000	臺北市	財政局	389	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19364
040305530000	段名：中山段四小段 地號：553號	\N	0403	05530000	182	2771921.65	\N	中山段四小段	553	100000	385000	10	中山段四小段05530000	臺北市	財政局	182	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19365
040305540000	段名：中山段四小段 地號：554號	\N	0403	05540000	119	2771921.328	\N	中山段四小段	554	100000	385000	10	中山段四小段05540000	臺北市	財政局	119	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19366
040305550000	段名：中山段四小段 地號：555號	\N	0403	05550000	119	2771921.028	\N	中山段四小段	555	100000	385000	10	中山段四小段05550000	臺北市	財政局	119	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19367
040305560000	段名：中山段四小段 地號：556號	\N	0403	05560000	186	2771920.659	\N	中山段四小段	556	100000	385000	10	中山段四小段05560000	臺北市	財政局	186	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19368
040500820013	段名：北安段一小段 地號：82-13號	\N	0405	00820013	847	2775456.7	\N	北安段一小段	82-13	49500	185000	10	北安段一小段00820013	臺北市	財政局	847	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19369
041302380000	段名：正義段四小段 地號：238號	\N	0413	02380000	1235	2771493.9	\N	正義段四小段	238	102000	390000	10	正義段四小段02380000	臺北市	財政局	1050	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19370
041304290000	段名：正義段四小段 地號：429號	\N	0413	04290000	542	2771332.1	\N	正義段四小段	429	85433	324422	10	正義段四小段04290000	臺北市	財政局	542	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19371
041304290003	段名：正義段四小段 地號：429-3號	\N	0413	04290003	334	2771327.4	\N	正義段四小段	429-3	85096	323150	10	正義段四小段04290003	臺北市	財政局	334	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19372
041803320000	段名：吉林段五小段 地號：332號	\N	0418	03320000	571	2771918.7	\N	吉林段五小段	332	131000	492000	10	吉林段五小段03320000	臺北市	財政局	571	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19373
042307250000	段名：長春段一小段 地號：725號	\N	0423	07250000	619	2771842.2	\N	長春段一小段	725	93200	357000	10	長春段一小段07250000	臺北市	財政局	619	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19374
042705010000	段名：榮星段二小段 地號：501號	\N	0427	05010000	932	2773024.626	\N	榮星段二小段	501	81400	311000	10	榮星段二小段05010000	臺北市	財政局	932	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19375
020502460000	段名：中正段二小段 地號：246號	\N	0205	02460000	47.22	2769963.066	\N	中正段二小段	246	121000	462000	03	中正段二小段02460000	臺北市	財政局	47.22	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19376
020502560000	段名：中正段二小段 地號：256號	\N	0205	02560000	502	2769946	\N	中正段二小段	256	121000	462000	03	中正段二小段02560000	臺北市	財政局	502	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19377
020502570000	段名：中正段二小段 地號：257號	\N	0205	02570000	7	2769958.3	\N	中正段二小段	257	121000	462000	03	中正段二小段02570000	臺北市	財政局	7	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19378
001503390000	段名：南海段二小段 地號：339號	\N	0015	03390000	589	2768969.1	\N	南海段二小段	339	113113	426413	03	南海段二小段03390000	臺北市	財政局	589	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19379
001503400000	段名：南海段二小段 地號：340號	\N	0015	03400000	113	2768969.3	\N	南海段二小段	340	98700	373000	03	南海段二小段03400000	臺北市	財政局	113	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19380
001503570002	段名：南海段二小段 地號：357-2號	\N	0015	03570002	41	2768971.7	\N	南海段二小段	357-2	164000	615000	03	南海段二小段03570002	臺北市	財政局	41	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19381
002001710008	段名：福和段二小段 地號：171-8號	\N	0020	01710008	478	2767670.618	\N	福和段二小段	171-8	59900	225000	03	福和段二小段01710008	臺北市	財政局	478	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19382
023103030000	段名：臨沂段一小段 地號：303號	\N	0231	03030000	157	2770502.4	\N	臨沂段一小段	303	121000	462000	03	臨沂段一小段03030000	臺北市	財政局	157	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19383
023103060000	段名：臨沂段一小段 地號：306號	\N	0231	03060000	162	2770508.5	\N	臨沂段一小段	306	121000	462000	03	臨沂段一小段03060000	臺北市	財政局	162	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19384
023103070000	段名：臨沂段一小段 地號：307號	\N	0231	03070000	156	2770510.6	\N	臨沂段一小段	307	121000	462000	03	臨沂段一小段03070000	臺北市	財政局	156	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19385
023103080000	段名：臨沂段一小段 地號：308號	\N	0231	03080000	156	2770512.6	\N	臨沂段一小段	308	121000	462000	03	臨沂段一小段03080000	臺北市	財政局	156	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19386
023103630000	段名：臨沂段一小段 地號：363號	\N	0231	03630000	144	2770606.1	\N	臨沂段一小段	363	127875	485375	03	臨沂段一小段03630000	臺北市	財政局	144	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19387
023103630001	段名：臨沂段一小段 地號：363-1號	\N	0231	03630001	68	2770599.307	\N	臨沂段一小段	363-1	121735	463654	03	臨沂段一小段03630001	臺北市	財政局	68	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19388
023103630002	段名：臨沂段一小段 地號：363-2號	\N	0231	03630002	7.62	2770596.861	\N	臨沂段一小段	363-2	121000	462000	03	臨沂段一小段03630002	臺北市	財政局	7.62	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19389
023103640000	段名：臨沂段一小段 地號：364號	\N	0231	03640000	105	2770602.3	\N	臨沂段一小段	364	128000	486000	03	臨沂段一小段03640000	臺北市	財政局	105	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19390
023103640001	段名：臨沂段一小段 地號：364-1號	\N	0231	03640001	45	2770595.201	\N	臨沂段一小段	364-1	121000	462000	03	臨沂段一小段03640001	臺北市	財政局	45	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19391
045704560000	段名：西湖段一小段 地號：456號	\N	0457	04560000	364	2775354.4	\N	西湖段一小段	456	51700	194000	14	西湖段一小段04560000	臺北市	財政局	364	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19392
046002020001	段名：康寧段一小段 地號：202-1號	\N	0460	02020001	626	2775504.045	\N	康寧段一小段	202-1	7000	25800	14	康寧段一小段02020001	臺北市	財政局	626	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19393
046304520000	段名：康寧段四小段 地號：452號	\N	0463	04520000	734	2774603.4	\N	康寧段四小段	452	67800	252011	14	康寧段四小段04520000	臺北市	財政局	734	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19394
046304520002	段名：康寧段四小段 地號：452-2號	\N	0463	04520002	431	2774679.3	\N	康寧段四小段	452-2	64942	241538	14	康寧段四小段04520002	臺北市	財政局	431	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19395
046701670000	段名：碧湖段四小段 地號：167號	\N	0467	01670000	370	2775349.5	\N	碧湖段四小段	167	33100	123000	14	碧湖段四小段01670000	臺北市	財政局	370	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19396
012703360000	段名：木柵段三小段 地號：336號	\N	0127	03360000	1004	2764602.2	\N	木柵段三小段	336	50993	188392	11	木柵段三小段03360000	臺北市	財政局	1004	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19397
015604900000	段名：博嘉段四小段 地號：490號	\N	0156	04900000	566.68	2765900.3	\N	博嘉段四小段	490	4800	17400	11	博嘉段四小段04900000	臺北市	財政局	566.68	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19398
005103790000	段名：景美段二小段 地號：379號	\N	0051	03790000	822	2765500.8	\N	景美段二小段	379	50600	188000	11	景美段二小段03790000	臺北市	財政局	822	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19399
011500040005	段名：萬芳段一小段 地號：4-5號	\N	0115	00040005	328	2766304.1	\N	萬芳段一小段	4-5	45100	167000	11	萬芳段一小段00040005	臺北市	財政局	328	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19400
006500140002	段名：興安段二小段 地號：14-2號	\N	0065	00140002	187	2765922.9	\N	興安段二小段	14-2	80400	302000	11	興安段二小段00140002	臺北市	財政局	187	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19401
006500150000	段名：興安段二小段 地號：15號	\N	0065	00150000	23	2765916.7	\N	興安段二小段	15	80400	302000	11	興安段二小段00150000	臺北市	財政局	23	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19402
006500200005	段名：興安段二小段 地號：20-5號	\N	0065	00200005	19	2765934.9	\N	興安段二小段	20-5	80400	302000	11	興安段二小段00200005	臺北市	財政局	19	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19403
006500200006	段名：興安段二小段 地號：20-6號	\N	0065	00200006	96	2765930.6	\N	興安段二小段	20-6	80400	302000	11	興安段二小段00200006	臺北市	財政局	96	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19404
006507110000	段名：興安段二小段 地號：711號	\N	0065	07110000	371	2765693.9	\N	興安段二小段	711	50750	188550	11	興安段二小段07110000	臺北市	財政局	371	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19405
006203990011	段名：興隆段三小段 地號：399-11號	\N	0062	03990011	78	2766384.8	\N	興隆段三小段	399-11	48600	181000	11	興隆段三小段03990011	臺北市	財政局	78	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19406
006205590007	段名：興隆段三小段 地號：559-7號	\N	0062	05590007	49	2766378.5	\N	興隆段三小段	559-7	48600	181000	11	興隆段三小段05590007	臺北市	財政局	49	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19407
006205590009	段名：興隆段三小段 地號：559-9號	\N	0062	05590009	20	2766387.9	\N	興隆段三小段	559-9	48600	181000	11	興隆段三小段05590009	臺北市	財政局	20	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19408
006205600000	段名：興隆段三小段 地號：560號	\N	0062	05600000	145	2766378.4	\N	興隆段三小段	560	48600	181000	11	興隆段三小段05600000	臺北市	財政局	145	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19409
006205600007	段名：興隆段三小段 地號：560-7號	\N	0062	05600007	62	2766387.7	\N	興隆段三小段	560-7	48600	181000	11	興隆段三小段05600007	臺北市	財政局	62	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19410
006205620013	段名：興隆段三小段 地號：562-13號	\N	0062	05620013	84	2766381	\N	興隆段三小段	562-13	48600	181000	11	興隆段三小段05620013	臺北市	財政局	84	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19411
006205630013	段名：興隆段三小段 地號：563-13號	\N	0062	05630013	6	2766382.3	\N	興隆段三小段	563-13	48600	181000	11	興隆段三小段05630013	臺北市	財政局	6	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19412
090402910001	段名：大業段一小段 地號：291-1號	\N	0904	02910001	724	2780741.8	\N	大業段一小段	291-1	90477	340466	16	大業段一小段02910001	臺北市	財政局	724	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19413
090702230000	段名：大業段四小段 地號：223號	\N	0907	02230000	1081	2780044.126	\N	大業段四小段	223	44500	167000	16	大業段四小段02230000	臺北市	財政局	1081	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19414
090702240001	段名：大業段四小段 地號：224-1號	\N	0907	02240001	109	2780058.567	\N	大業段四小段	224-1	44500	167000	16	大業段四小段02240001	臺北市	財政局	109	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19415
099201670000	段名：湖山段二小段 地號：167號	\N	0992	01670000	1202.1	2782525	\N	湖山段二小段	167	13100	49400	16	湖山段二小段01670000	臺北市	財政局	1202.1	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19416
090001180000	段名：新民段四小段 地號：118號	\N	0900	01180000	765	2781188.3	\N	新民段四小段	118	16900	62900	16	新民段四小段01180000	臺北市	財政局	765	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19417
060106750004	段名：西松段二小段 地號：675-4號	\N	0601	06750004	138	2771331.2	\N	西松段二小段	675-4	92600	349000	01	西松段二小段06750004	臺北市	財政局	138	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19418
060106750005	段名：西松段二小段 地號：675-5號	\N	0601	06750005	175	2771302.6	\N	西松段二小段	675-5	92600	349000	01	西松段二小段06750005	臺北市	財政局	175	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19419
064007900000	段名：吳興段三小段 地號：790號	\N	0640	07900000	94	2767954.193	\N	吳興段三小段	790	55800	211000	17	吳興段三小段07900000	臺北市	財政局	94	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19420
064007920000	段名：吳興段三小段 地號：792號	\N	0640	07920000	569	2767967.402	\N	吳興段三小段	792	55800	211000	17	吳興段三小段07920000	臺北市	財政局	569	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19421
067403610001	段名：新光段二小段 地號：361-1號	\N	0674	03610001	848	2770390.021	\N	新光段二小段	361-1	50300	193000	13	新光段二小段03610001	臺北市	財政局	848	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19422
067403610005	段名：新光段二小段 地號：361-5號	\N	0674	03610005	5	2770407.7	\N	新光段二小段	361-5	50300	193000	13	新光段二小段03610005	臺北市	財政局	5	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19423
067403610006	段名：新光段二小段 地號：361-6號	\N	0674	03610006	16	2770392.3	\N	新光段二小段	361-6	50300	193000	13	新光段二小段03610006	臺北市	財政局	16	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19424
067403830001	段名：新光段二小段 地號：383-1號	\N	0674	03830001	1171	2770369.7	\N	新光段二小段	383-1	50300	193000	13	新光段二小段03830001	臺北市	財政局	1171	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19425
067403850005	段名：新光段二小段 地號：385-5號	\N	0674	03850005	2	2770400.6	\N	新光段二小段	385-5	50300	193000	13	新光段二小段03850005	臺北市	財政局	2	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19426
067403850006	段名：新光段二小段 地號：385-6號	\N	0674	03850006	1	2770377	\N	新光段二小段	385-6	50300	193000	13	新光段二小段03850006	臺北市	財政局	1	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19427
003203050000	段名：華中段二小段 地號：305號	\N	0032	03050000	490	2768265.398	\N	華中段二小段	305	53078	200673	05	華中段二小段03050000	臺北市	財政局	490	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19428
003205420007	段名：華中段二小段 地號：542-7號	\N	0032	05420007	888	2768334.622	\N	華中段二小段	542-7	41300	156000	05	華中段二小段05420007	臺北市	財政局	888	2023-05-24 19:00:45.305729+00	2023-05-24 19:00:45.305729+00	19429
\.


--
-- TOC entry 5038 (class 0 OID 19791)
-- Dependencies: 329
-- Data for Name: building_unsued_public; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.building_unsued_public (full_key, "建物管理機關", "行政區", "門牌", "建物標示", "建築完成日期", "閒置樓層_閒置樓層/該建物總樓層", "閒置面積㎡", "房屋現況", "原使用用途", "基地所有權人", "基地管理機關", "土地使用分區", "目前執行情形", _ctime, _mtime) FROM stdin;
1	\N	萬華區	桂林路52號3樓	萬華段一小段01157建號	731205	\N	\N	\N	辦公廳舍	臺北市	\N	\N	參與都市更新計畫，目前進度權利變換分配中。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
2	\N	萬華區	桂林路52號4樓	萬華段一小段01158建號	731205	\N	\N	\N	辦公廳舍	臺北市	\N	\N	參與都市更新計畫，目前進度權利變換分配中。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
3	\N	萬華區	桂林路52號5樓	萬華段一小段01159建號	731205	\N	\N	\N	辦公廳舍	臺北市	\N	\N	參與都市更新計畫，目前進度權利變換分配中。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
4	\N	中山區	林森北路487號5樓之6	吉林段三小段04721建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
5	\N	中山區	林森北路487號4樓之10	吉林段三小段04724建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
6	\N	中山區	林森北路487號3樓之18	吉林段三小段04697建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
7	\N	中山區	林森北路487號3樓之20	吉林段三小段04698建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
8	\N	中山區	林森北路487號3樓之21	吉林段三小段04693建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
9	\N	中山區	林森北路487號5樓之1	吉林段三小段04705建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
10	\N	中山區	林森北路487號4樓之6	吉林段三小段04720建號	611117	\N	\N	\N	宿舍、眷舍	臺北市	\N	\N	併同毗鄰新興國中評估以EOD方式辦理改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
11	\N	松山區	八德路4段688號2樓	寶清段七小段01201建號	720715	\N	\N	\N	檔案室	臺北市	\N	\N	該綜合大樓經耐震能力評估後，決議拆除重建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
12	\N	松山區	八德路4段688號地下一層	寶清段七小段01202建號	720715	\N	\N	\N	停車場	臺北市	\N	\N	該綜合大樓經耐震能力評估後，決議拆除重建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
13	\N	信義區	松德路25巷58號5樓	永春段一小段02408建號	790511	\N	\N	\N	兒少庇護性團體家庭(含自立宿舍)	臺北市	\N	\N	評估辦理標租	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
14	\N	信義區	松德路25巷60號5樓	永春段一小段02414建號	790511	\N	\N	\N	兒少庇護性團體家庭(含自立宿舍)	臺北市	\N	\N	評估辦理標租	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
15	\N	中山區	長春路299號3樓	長春段一小段01114建號	640611	\N	\N	\N	辦公廳舍	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
16	\N	中山區	長春路299號4樓	長春段一小段01381建號	640611	\N	\N	\N	辦公廳舍	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
17	\N	北投區	中山路5-8號	新民段二小段E0001-000建號	550101	\N	\N	\N	辦公廳舍	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
18	\N	士林區	大東路80號	光華段三小段E0080-000建號	580428	\N	\N	\N	辦公廳舍	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
19	\N	中正區	博愛路119號	公園段二小段E0833-001建號	520601	\N	\N	\N	辦公廳舍	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
20	\N	士林區	仰德大道2段2巷50號	至善段五小段50106建號	540101	\N	\N	\N	倉庫	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
21	\N	大同區	敦煌路臨160-2號	文昌段一小段E0001-001建號	870320	\N	\N	\N	老師區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
22	\N	大同區	敦煌路臨151-1號	文昌段一小段E0001-002建號	720730	\N	\N	\N	慶昌區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
23	\N	大同區	保安街47-1號3樓	延平段一小段02730建號	871116	\N	\N	\N	延平區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
24	\N	中山區	長春路299號3樓之1	長春段一小段01582建號	640611	\N	\N	\N	長春區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
25	\N	內湖區	環山路2段68巷14號	碧湖段四小段05443建號	780110	\N	\N	\N	港華區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
26	\N	內湖區	金龍路136-1號2樓	碧湖段一小段02820建號	940519	\N	\N	\N	金龍區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
27	\N	士林區	中正路589號	福順段一小段E0012-000建號	850917	\N	\N	\N	葫東區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
28	\N	北投區	大度路3段301巷1號1樓	豐年段四小段40674建號	770129	\N	\N	\N	關渡區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
29	\N	北投區	崇仰一路7號1、2樓	奇岩段一小段10851建號	560220	\N	\N	\N	崇仰區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
30	\N	信義區	吳興街156巷6號6樓	三興段一小段05156建號	940715	\N	\N	\N	景勤區民活動中心	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
31	\N	萬華區	萬大路411號2樓	青年段一小段12432建號	880918	\N	\N	\N	萬青區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
32	\N	萬華區	萬大路臨614-1號	華中段四小段E1112-000建號	830516	\N	\N	\N	萬大第一區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
33	\N	萬華區	萬大路臨600-1號	華中段四小段E1113-000建號	901103	\N	\N	\N	萬大第二區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
34	\N	萬華區	西園路2段臨370-1號	雙園段一小段E0624-000建號	700415	\N	\N	\N	光復區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
35	\N	萬華區	環河南路2段臨5-1號	直興段二小段E0001-000建號	880101	\N	\N	\N	青山區民活動中心	臺北市	\N	\N	民政局檢討釋出，未完成媒合前，仍按區民活動中心經營管理。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
36	\N	中正區	北平東路1號4樓之2	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
37	\N	中正區	北平東路1號4樓之3	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
38	\N	中正區	北平東路1號4樓之4	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
39	\N	中正區	北平東路1號4樓之5	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
40	\N	中正區	北平東路1號4樓之12	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
41	\N	中正區	北平東路1號4樓之10	成功段三小段00077建號	570509	\N	\N	\N	辦公室	臺北市	\N	\N	無使用需求，徵詢各機關有無公務需求。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
42	\N	士林區	陽明路1段48巷3號2樓	力行段三小段E0000-001建號	600705	\N	\N	\N	宿舍	臺北市	\N	\N	基地為國有，使用受限。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
43	\N	北投區	勝利街29號	湖山段二小段E0385建號	560510	\N	\N	\N	宿舍	臺北市	\N	\N	基地為國有，使用受限。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
44	\N	士林區	陽明路1段48巷8號2樓	力行段三小段EO381建號	600110	\N	\N	\N	宿舍	臺北市	\N	\N	基地為國有，使用受限。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
45	\N	南港區	同德路100號	玉成段五小段03213建號	670626	\N	\N	\N	提供標租使用	臺北市	\N	\N	現況維管。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
46	\N	中山區	長春路75號	吉林段四小段03818建號	420101	\N	\N	\N	辦公廳舍	臺北市	\N	\N	已納入都市更新範圍，待參與都市更新改建。	2023-09-19 19:00:21.881162+00	2023-09-19 19:00:21.881162+00
\.


--
-- TOC entry 5122 (class 0 OID 19881)
-- Dependencies: 413
-- Data for Name: patrol_criminal_case; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.patrol_criminal_case ("破獲件數/總計[件]", "破獲率[%]", "犯罪人口率[人/十萬人]", "嫌疑犯[人]", "發生件數[件]", "破獲件數/他轄[件]", "破獲件數/積案[件]", _id, "破獲件數/當期[件]", "發生率[件/十萬人]", "實際員警人數[人]", "年月別", _ctime, _mtime, ogc_fid) FROM stdin;
2542	69.89	51.4	1336	3637	-	-	1	-	139.92	-	2022-01-01 00:00:00+00	2023-09-19 18:00:14.92278+00	2024-02-15 05:49:34.017761+00	30357
2847	76.99	64.25	1671	3698	-	-	2	-	142.2	-	2022-02-01 00:00:00+00	2023-09-19 18:00:14.933006+00	2024-02-15 05:49:34.017761+00	30358
3131	68.29	59.73	1555	4585	-	-	3	-	176.12	-	2022-03-01 00:00:00+00	2023-09-19 18:00:14.938244+00	2024-02-15 05:49:34.017761+00	30359
3148	73.07	59.79	1559	4308	-	-	4	-	165.23	-	2022-04-01 00:00:00+00	2023-09-19 18:00:14.943127+00	2024-02-15 05:49:34.017761+00	30360
3328	77.43	71.9	1877	4298	-	-	5	-	164.64	-	2022-05-01 00:00:00+00	2023-09-19 18:00:14.947897+00	2024-02-15 05:49:34.017761+00	30361
3379	78.51	69.65	1823	4304	-	-	6	-	164.45	-	2022-06-01 00:00:00+00	2023-09-19 18:00:14.952845+00	2024-02-15 05:49:34.017761+00	30362
3670	80.82	71.65	1881	4541	-	-	7	-	172.97	-	2022-07-01 00:00:00+00	2023-09-19 18:00:14.957895+00	2024-02-15 05:49:34.017761+00	30363
3537	75.69	73.81	1941	4673	-	-	8	-	177.7	-	2022-08-01 00:00:00+00	2023-09-19 18:00:14.962737+00	2024-02-15 05:49:34.017761+00	30364
3382	78.82	66.18	1742	4291	-	-	9	-	163.01	-	2022-09-01 00:00:00+00	2023-09-19 18:00:14.96857+00	2024-02-15 05:49:34.017761+00	30365
3014	74.57	64.11	1689	4042	-	-	10	-	153.43	-	2022-10-01 00:00:00+00	2023-09-19 18:00:14.973027+00	2024-02-15 05:49:34.017761+00	30366
3137	69.63	70.65	1863	4505	-	-	11	-	170.84	-	2022-11-01 00:00:00+00	2023-09-19 18:00:14.977989+00	2024-02-15 05:49:34.017761+00	30367
3205	65.73	64.53	1703	4876	-	-	12	-	184.75	-	2022-12-01 00:00:00+00	2023-09-19 18:00:14.982901+00	2024-02-15 05:49:34.017761+00	30368
4123	96.24	72.76	1921	4284	-	-	13	-	162.26	-	2023-01-01 00:00:00+00	2023-09-19 18:00:14.987317+00	2024-02-15 05:49:34.017761+00	30369
3030	94.25	72.3	1909	3215	-	-	14	-	121.77	-	2023-02-01 00:00:00+00	2023-09-19 18:00:14.99184+00	2024-02-15 05:49:34.017761+00	30370
2761	62.62	64.39	1700	4409	-	-	15	-	167	-	2023-03-01 00:00:00+00	2023-09-19 18:00:14.996997+00	2024-02-15 05:49:34.017761+00	30371
2745	69.95	60.11	1587	3924	-	-	16	-	148.62	-	2023-04-01 00:00:00+00	2023-09-19 18:00:15.002567+00	2024-02-15 05:49:34.017761+00	30372
2770	78.54	74.54	1968	3527	-	-	17	-	133.59	-	2023-05-01 00:00:00+00	2023-09-19 18:00:15.00915+00	2024-02-15 05:49:34.017761+00	30373
2793	75.79	77.15	2037	3685	-	-	18	-	139.57	-	2023-06-01 00:00:00+00	2023-09-19 18:00:15.01957+00	2024-02-15 05:49:34.017761+00	30374
3701	80.06	96.92	2559	4623	-	-	19	-	175.09	-	2023-07-01 00:00:00+00	2023-09-19 18:00:15.026468+00	2024-02-15 05:49:34.017761+00	30375
4109	90.63	95.54	2522	4534	-	-	20	-	171.76	-	2023-08-01 00:00:00+00	2023-09-19 18:00:15.059418+00	2024-02-15 05:49:34.017761+00	30376
\.


--
-- TOC entry 5151 (class 0 OID 19917)
-- Dependencies: 442
-- Data for Name: patrol_rain_floodgate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.patrol_rain_floodgate (ogc_fid, station_no, station_name, rec_time, all_pumb_lights, pumb_num, door_num, river_basin, warning_level, start_pumping_level, lng, lat, _ctime, _mtime) FROM stdin;
3776892	62	康樂	2023-08-22 15:02:00+00	-	5	2	基隆河	4.8	5.0	121.617475	25.066575	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776893	51	南港	2023-08-22 14:03:00+00	-	5	3	基隆河	4.5	5.2	121.612422	25.062131	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776894	78	康寧	2023-08-22 15:01:00+00	-	7	4	基隆河	7.3	7.6	121.617475	25.064339	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776895	50	南湖	2023-08-22 15:01:00+00	-	3	1	基隆河	5.2	5.5	121.610806	25.063467	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776896	49	長壽	2023-08-22 15:01:00+00	-	4	1	基隆河	3.3	4.3	121.596286	25.060864	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776897	48	成功	2023-08-22 15:01:00+00	-	4	1	基隆河	2.8	3.6	121.596189	25.058636	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776898	42	成美	2023-09-20 12:55:00+00	-	3	1	基隆河	4.0	4.3	121.583492	25.055453	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776899	15	玉成	2023-08-22 14:02:00+00	-	11	5	基隆河	1.8	2.2	121.582547	25.052339	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776900	16	南京	2023-08-22 14:02:00+00	-	3	1	基隆河	3.4	3.7	121.572244	25.050686	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776901	17	松山	2023-08-22 15:00:00+00	-	3	1	基隆河	3.1	3.4	121.570169	25.054519	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776902	47	新民權	2023-08-22 14:02:00+00	-	10	2	基隆河	1.6	1.9	121.573431	25.058611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776903	18	撫遠	2023-08-22 15:02:00+00	-	5	2	基隆河	1.9	2.2	121.568778	25.06225	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776904	46	陽光	2023-08-22 15:01:00+00	-	10	1	基隆河	2.5	2.8	121.573847	25.071375	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776905	45	港漧	2023-06-30 14:01:00+00	-	8	2	基隆河	3.22	3.3	121.572861	25.074403	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776906	44	環山	2023-08-22 15:01:00+00	-	6	2	基隆河	2.0	2.22	121.562683	25.076772	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776907	43	北安	2023-08-22 15:02:00+00	-	8	2	基隆河	2.01	2.31	121.555822	25.077814	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776908	19	濱江	2023-09-20 12:01:00+00	-	6	2	基隆河	0.6	0.9	121.549706	25.072508	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776909	20	大直	2023-09-20 12:01:00+00	-	12	6	基隆河	1.7	2.0	121.546972	25.077389	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776910	21	中山	2023-09-20 12:01:00+00	-	9	3	基隆河	1.6	1.8	121.534111	25.073978	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776911	22	建國	2023-09-20 12:01:00+00	-	9	4	基隆河	1.3	1.5	121.528911	25.072414	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776912	23	新生	2023-09-20 12:24:00+00	-	12	5	基隆河	2.7	3.0	121.528369	25.072197	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776913	76	新生二	2023-08-31 14:03:00+00	-	4	1	基隆河	2.7	3.0	121.528835	25.071711	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776914	24	圓山	2023-09-20 12:01:00+00	-	6	2	基隆河	1.0	1.2	121.527403	25.071344	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776915	26	劍潭	2023-09-20 12:02:00+00	-	5	3	基隆河	0.1	0.25	121.518283	25.081297	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776916	25	大龍	2023-09-20 12:55:00+00	-	4	3	基隆河	1.0	1.2	121.516164	25.078653	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776917	29	社子	2023-09-20 12:02:00+00	-	5	2	基隆河	0.7	1.0	121.508611	25.092756	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776918	27	士林	2023-08-29 10:40:00+00	-	10	5	基隆河	0.1	0.3	121.511178	25.096128	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776919	28	士林二	2023-09-20 12:01:00+00	-	2	6	基隆河	-0.2	0.01	121.511222	25.09611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776920	70	社基下	2023-09-20 12:56:00+00	-	13	12	基隆河	2.0	2.1	121.495556	25.105611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776921	71	社基上	2023-09-20 12:03:00+00	-	15	8	基隆河	2.0	2.1	121.495556	25.106611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776922	67	洲美二	2023-09-20 12:04:00+00	-	2	2	基隆河	0.9	1.0	121.499392	25.107058	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776923	64	洲美一	2023-09-20 12:02:00+00	-	6	5	基隆河	0.1	0.3	121.498875	25.110122	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776924	72	大業二	2023-09-20 12:03:00+00	-	1	1	基隆河	1.0	1.1	121.495342	25.113561	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776925	77	大業東	2023-09-20 12:04:00+00	-	7	2	基隆河	0.9	1.5	121.500569	25.119675	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776926	73	下八仙	2023-09-20 12:03:00+00	-	5	2	基隆河	0.9	1.0	121.490594	25.116067	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776927	74	誠正	2023-08-22 15:01:00+00	-	7	3	大坑溪	6.2	6.7	121.620692	25.054306	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776928	81	木新	2023-08-22 15:00:00+00	-	2	1	景美溪	14.0	14.5	121.565647	24.981706	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776929	36	林森	2023-09-20 10:48:00+00	-	6	3	新生大排	1.5	1.8	121.531758	25.046064	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776930	82	文林	2023-09-20 09:49:00+00	-	3	0	磺港溪	0.7	1.0	121.517902	25.102625	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776931	53	新長安	2023-08-10 17:09:00+00	+	4	1	新生大排	1.1	1.3	121.527211	25.052667	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776932	83	文林二	2023-06-12 11:16:00+00	-	4	0	磺港溪	1.8	2.1	121.517733	25.102486	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776933	38	長春	2023-09-20 11:13:00+00	-	2	3	新生大排	2.0	2.3	121.527933	25.052792	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776934	39	民生	2023-09-20 12:00:00+00	-	5	2	新生大排	1.1	1.3	121.526906	25.058272	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776935	84	洲美	2023-09-20 12:00:00+00	-	5	3	基隆河	1.8	2.2	121.512083	25.099064	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776936	40	民權	2023-09-20 11:16:00+00	-	1	1	新生大排	1.4	1.7	121.527731	25.058828	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776937	41	錦州	2023-09-20 12:55:00+00	-	5	2	新生大排	1.2	1.5	121.527794	25.061417	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776938	07	景美	2023-08-22 14:04:00+00	-	5	2	新店溪	5.8	6.8	121.534983	25.009786	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776939	63	興隆	2023-08-20 15:00:00+00	-	9	2	\N	\N	\N	\N	\N	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776940	08	古亭	2023-08-22 14:03:00+00	-	4	1	新店溪	5.3	5.8	121.523597	25.019419	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776941	09	雙園	2023-08-22 14:03:00+00	-	10	2	新店溪	1.5	1.7	121.488786	25.030931	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776942	10	貴陽	2023-09-20 12:05:00+00	-	2	1	淡水河	2.0	2.3	121.498983	25.041836	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776943	11	忠孝	2023-08-04 05:00:00+00	-	9	5	淡水河	2.0	2.3	121.50635	25.049886	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776944	12	六館	2023-09-20 12:06:00+00	-	4	2	淡水河	1.4	1.5	121.508153	25.057253	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776945	13	迪化	2023-09-14 19:45:00+00	+	11	3	淡水河	0.5	0.75	121.507772	25.080181	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776946	68	社淡上	2023-09-20 12:05:00+00	-	4	12	淡水河	2.7	2.8	121.495556	25.109611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776947	69	社淡下	2023-09-20 12:05:00+00	-	14	8	淡水河	0.5	0.7	121.495556	25.108611	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776948	14	中洲	2023-09-20 12:05:00+00	-	3	2	淡水河	0.5	0.7	121.473058	25.106197	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776949	01	萬芳	2023-09-20 12:55:00+00	-	4	1	景美溪	14.0	14.5	121.571597	24.995185	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776950	02	道南	2023-09-20 12:55:00+00	-	6	2	景美溪	13.85	14.2	121.573258	24.987883	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776951	54	老泉溪	2023-08-22 14:06:00+00	-	3	1	景美溪	13.5	14.0	121.559989	24.979156	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776952	55	無名溪	2023-08-10 14:16:00+00	-	3	1	景美溪	13.9	14.39	121.566242	24.980117	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776953	03	保儀	2023-09-20 12:55:00+00	-	2	1	景美溪	13.5	14.0	121.553811	24.9803	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776954	04	實踐	2023-08-22 15:00:00+00	-	3	3	景美溪	12.7	13.2	121.554275	24.983421	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776955	05	中港	2023-08-22 14:06:00+00	-	4	2	景美溪	11.8	12.3	121.553425	24.986499	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776956	06	埤腹	2023-08-22 15:00:00+00	-	3	3	景美溪	11.0	11.2	121.545419	24.986461	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776957	30	芝山	2023-09-20 11:44:00+00	-	5	2	雙溪	2.6	2.8	121.528161	25.101106	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776958	31	福德	2023-09-20 12:20:00+00	-	5	3	雙溪	2.0	2.25	121.528881	25.099369	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776959	32	福林	2023-09-20 08:46:00+00	-	7	6	雙溪	2.6	2.8	121.52625	25.102572	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776960	33	文昌	2023-09-20 08:42:00+00	-	3	2	雙溪	1.6	1.8	121.519675	25.100156	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776961	34	東華	2023-09-20 12:00:00+00	-	4	2	磺溪	3.3	3.8	121.522267	25.109842	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776962	35	奇岩	2023-09-20 10:47:00+00	-	4	1	磺港溪	2.4	2.8	121.503361	25.124125	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776963	65	北憲	2023-09-20 12:47:00+00	-	4	2	磺港溪	1.7	1.8	121.500808	25.117897	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776964	66	福山	2023-08-22 15:00:00+00	-	2	1	大坑溪	7.9	8.6	121.617172	25.046372	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
3776965	61	經貿	2023-08-22 13:39:00+00	-	2	1	大坑溪	7.5	8.23	121.620889	25.056294	2023-09-20 05:00:14.300246+00	2023-09-20 05:00:14.300246+00
\.


--
-- TOC entry 5185 (class 0 OID 19958)
-- Dependencies: 476
-- Data for Name: socl_welfare_organization_plc; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.socl_welfare_organization_plc (main_type, sub_type, name, address, lon, lat, _ctime, _mtime, ogc_fid) FROM stdin;
銀髮族服務	長期照護型	臺北市政府社會局附設臺北市東明住宿長照機構(委託財團法人台北市私立愛愛院經營管理)	臺北市南港區東明里南港路二段60巷17號2樓	121.60446167	25.05466652	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11009
銀髮族服務	長期照護型	臺北市兆如老人安養護中心	臺北市文山區政大二街129號	121.58419037	24.98931503	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11010
銀髮族服務	長期照護型	臺北市政府社會局附設臺北市廣智住宿長照機構(委託財團法人天主教失智老人社會福利基金會經營管理)	臺北市信義區大仁里福德街１	121.58127594	25.0371933	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11011
銀髮族服務	長期照護型	臺北市至善老人安養護中心	臺北市士林區永福里1鄰仰德大道二段2巷50號	121.54301453	25.10202217	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11012
銀髮族服務	長期照護型	臺北市私立華安老人長期照護中心	臺北市大安區光復南路116巷1、3、5號5樓及3號6樓	121.55654907	25.04299355	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11013
銀髮族服務	長期照護型	財團法人臺北市私立恆安老人長期照顧中心(長期照護型)	臺北市萬華區水源路187號	121.51077271	25.02360153	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11014
銀髮族服務	養護型	臺北市私立晨欣老人長期照顧中心(養護型)	臺北市中山區中山北路二段96巷19號3樓	121.52197266	25.05989265	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11015
銀髮族服務	養護型	臺北市私立怡靜老人長期照顧中心(養護型)	臺北市北投區致遠二路96巷3弄1、3號1樓	121.51274872	25.11644936	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11016
銀髮族服務	養護型	臺北市私立中山老人長期照顧中心(養護型)	臺北市萬華區峨眉街124、124之1號1樓	121.50235748	25.04452133	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11017
銀髮族服務	養護型	臺北市私立群仁老人長期照顧中心(養護型)	臺北市中山區民族東路512巷14號3~5樓	121.54194641	25.06735992	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11018
銀髮族服務	養護型	臺北市私立福成老人長期照顧中心(養護型)	臺北市中山區松江路374、380、382號4樓	121.53273773	25.06795311	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11019
銀髮族服務	養護型	臺北市私立福喜老人長期照顧中心(養護型)	臺北市中山區松江路374、380、382號7樓	121.53273773	25.06795311	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11020
銀髮族服務	養護型	臺北市私立龍江老人長期照顧中心(養護型)	臺北市中山區長安東路一段63號4樓	121.52721405	25.04865265	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11021
銀髮族服務	養護型	臺北市私立大園老人長期照顧中心(養護型)	臺北市中正區新生南路一段124之3號1~4樓	121.53248596	25.03775406	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11022
銀髮族服務	養護型	臺北市私立仁泰老人長期照顧中心(養護型)	臺北市中正區連雲街3號1、3樓、3之4號及新生南路1段124之3號5樓	121.53230286	25.03763771	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11023
銀髮族服務	養護型	臺北市私立明德老人長期照顧中心(養護型)	臺北市中正區詔安街220巷2、4號1樓	121.50917053	25.02619934	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11024
銀髮族服務	養護型	臺北市私立博愛長期照顧中心(養護型)	臺北市中正區汀州路三段56號2樓	121.53092194	25.01579475	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11025
銀髮族服務	養護型	臺北市私立文德老人長期照顧中心(養護型)	臺北市內湖區陽光街70-2、70-3、72、72-1號1樓	121.57635498	25.07274628	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11026
銀髮族服務	養護型	臺北市私立祥家老人養護所	臺北市內湖區內湖路二段253巷1弄1、3號1-2樓	121.58998108	25.08249664	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11027
銀髮族服務	養護型	臺北市私立湖濱老人長期照顧中心(養護型)	臺北市內湖區內湖路二段179巷58、60號1樓	121.58660126	25.08285332	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11028
銀髮族服務	養護型	臺北市私立童音老人長期照顧中心(養護型)	臺北市內湖區民權東路六段280巷19弄1、3、5、7號1樓	121.60499573	25.0715847	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11029
銀髮族服務	養護型	臺北市私立瑞安老人長期照顧中心(養護型)	臺北市內湖區成功路三段88、90、92號2樓、76巷9號2樓	121.59078217	25.08038139	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11030
銀髮族服務	養護型	臺北市私立銀髮族老人養護所	臺北市內湖區成功路二段488號2~5樓、490號2~4樓	121.58968353	25.07325363	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11031
銀髮族服務	養護型	臺北市私立建民老人長期照顧中心(養護型)	臺北市北投區建民路22、24、26、26之1號1樓	121.52160645	25.1136837	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11032
銀髮族服務	養護型	臺北市私立倚青園老人長期照顧中心(養護型)	臺北市北投區義理街63巷4弄7、11之1~3號1樓	121.51560974	25.11821747	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11033
銀髮族服務	養護型	臺北市私立高德老人長期照顧中心(養護型)	臺北市北投區磺港路156號1~3樓	121.50298309	25.12865257	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11034
銀髮族服務	養護型	臺北市私立崇順老人養護所	臺北市北投區知行路52巷1號及54號1~2樓	121.46742249	25.11811638	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11035
銀髮族服務	養護型	臺北市私立尊暉老人長期照顧中心(養護型)	臺北市北投區石牌路二段343巷17號1~2樓	121.52346802	25.12265968	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11036
銀髮族服務	養護型	臺北市私立陽明山老人長期照顧中心(養護型)	臺北市北投區紗帽路116號	121.54716492	25.15086746	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11037
銀髮族服務	養護型	臺北市私立聖心老人養護所	臺北市北投區稻香路321號1樓	121.48655701	25.1429348	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11038
銀髮族服務	養護型	臺北市私立賢暉老人長期照顧中心(養護型)	臺北市北投區石牌路二段315巷34弄14、16號1樓	121.52238464	25.12383652	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11039
銀髮族服務	養護型	財團法人臺灣基督教道生院附設臺北市私立道生院老人長期照顧中心(養護型)	臺北市北投區中和街錫安巷112號1-2樓及地下1樓	121.50085449	25.14749146	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11040
銀髮族服務	養護型	臺北市私立豪門老人長期照顧中心(養護型)	臺北市北投區大業路452巷2號6~9樓	121.49714661	25.1315155	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11041
銀髮族服務	養護型	臺北市私立貴族老人長期照顧中心(養護型)	臺北市北投區大業路452巷2號2~5樓	121.49714661	25.1315155	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11042
銀髮族服務	養護型	臺北市私立奇里岸老人長期照顧中心(養護型)	臺北市北投區西安街二段245號1.2樓	121.50823975	25.12014771	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11043
銀髮族服務	養護型	臺北市私立安安老人長期照顧中心(養護型)	臺北市北投區公舘路194、196號1樓	121.50726318	25.1280632	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11044
銀髮族服務	養護型	臺北市私立軒儀老人長期照顧中心(養護型)	臺北市萬華區和平西路三段384號1樓	121.4912796	25.03534126	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11045
銀髮族服務	養護型	臺北市私立葉爸爸老人長期照顧中心(養護型)	臺北市萬華區西園路二段243之14號1~4樓	121.49354553	25.02655029	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11046
銀髮族服務	養護型	臺北市私立葉媽媽老人長期照顧中心(養護型)	臺北市萬華區西園路二段243之13號1~4樓	121.49354553	25.02655029	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11047
銀髮族服務	養護型	臺北市私立建順老人長期照顧中心(養護型)	臺北市大同區甘州街55號3樓	121.5128479	25.05978012	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11048
銀髮族服務	養護型	臺北市文山老人養護中心	臺北市文山區興隆路二段95巷8號3樓	121.54688263	24.9999733	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11049
銀髮族服務	養護型	臺北市私立安安老人長期照顧中心(養護型)	臺北市北投區公舘路194、196號1樓	121.50195313	25.12042046	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11050
銀髮族服務	養護型	臺北市私立上美老人長期照顧中心(養護型)	臺北市士林區重慶北路四段162號1-4樓	121.51216888	25.0841217	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11051
銀髮族服務	養護型	臺北市私立天玉老人長期照顧中心(長期照護型)	臺北市士林區天玉街38巷18弄18號1-6樓	121.53032684	25.12012482	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11052
銀髮族服務	養護型	臺北市私立永青老人長期照顧中心(養護型)	臺北市士林區中山北路六段427巷8號1~4樓	121.52654266	25.11425209	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11053
銀髮族服務	養護型	臺北市私立松園老人長期照顧中心(養護型)	臺北市士林區德行東路61巷1、2、3號1、2樓	121.52713776	25.10788536	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11054
銀髮族服務	養護型	臺北市私立柏安老人養護所	臺北市士林區中山北路六段290巷52、54號1樓	121.52733612	25.10889626	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11055
銀髮族服務	養護型	臺北市私立祇福老人養護所	臺北市士林區忠誠路二段10巷11、13號1~2樓	121.52907562	25.10870934	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11056
銀髮族服務	養護型	臺北市私立祐心老人長期照顧中心(養護型)	臺北市士林區至誠路一段305巷3弄14號1-2樓	121.53173828	25.1014595	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11057
銀髮族服務	養護型	臺北市私立荷園老人長期照顧中心(養護型)	臺北市士林區葫蘆街33號2~3樓	121.50971985	25.07997704	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11058
銀髮族服務	養護型	臺北市私立璞園老人長期照顧中心(養護型)	臺北市士林區葫蘆街33號4、5、6樓	121.50971985	25.07997704	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11059
銀髮族服務	養護型	臺北市私立仁家老人長期照顧中心(養護型)	臺北市大同區甘州街55號5~6樓	121.5128479	25.05978012	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11060
銀髮族服務	養護型	臺北市私立永安老人養護所	臺北市大同區重慶北路三段284號2~4樓、286號1~4樓	121.51359558	25.07314873	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11061
銀髮族服務	養護型	臺北市私立建興老人長期照顧中心(養護型)	臺北市大同區甘州街55號2樓	121.5128479	25.05978012	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11062
銀髮族服務	養護型	臺北市私立晉安老人長期照顧中心(養護型)	臺北市大同區重慶北路三段175、177號1~4樓	121.51359558	25.07275963	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11063
銀髮族服務	養護型	臺北市私立祥安尊榮老人長期照顧中心(養護型)	臺北市大同區延平北路三段4號2樓	121.51104736	25.06343269	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11064
銀髮族服務	養護型	臺北市私立祥寶尊榮老人長期照顧中心(養護型)	臺北市大同區太原路97巷4、6號	121.51672363	25.0520649	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11065
銀髮族服務	養護型	臺北市私立敦煌老人長期照顧中心(養護型)	臺北市大同區敦煌路80巷3號及3-1號1樓	121.51746368	25.07487679	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11066
銀髮族服務	養護型	臺北市私立德寶老人養護所	臺北市大同區長安西路78巷4弄11號1~4樓	121.51855469	25.05000877	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11067
銀髮族服務	養護型	臺北市私立慧光老人養護所	臺北市大同區寧夏路32號5樓	121.51516724	25.05598068	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11068
銀髮族服務	養護型	臺北市私立上上老人養護所	臺北市大安區復興南路一段279巷14、16號1樓	121.54529572	25.035532	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11069
銀髮族服務	養護型	臺北市私立天恩老人長期照顧中心(養護型)	臺北市大安區新生南路三段7-4號、9-4號、9-5號	121.53501129	25.0255127	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11070
銀髮族服務	養護型	臺北市私立健全老人長期照顧中心(養護型)	臺北市大安區金山南路二段152號2、3、4、5、6樓	121.52611542	25.02870369	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11071
銀髮族服務	養護型	臺北市私立康寧老人長期照顧中心(養護型)	臺北市大安區仁愛路四段300巷20弄15號2樓、17號2樓	121.55350494	25.03634071	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11072
銀髮族服務	養護型	臺北市私立新常安老人長期照顧中心(養護型)	臺北市大安區安居街46巷14號1~3樓及臺北市大安區和平東路3段228巷39號2樓	121.55361938	25.02067757	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11073
銀髮族服務	養護型	臺北市私立嘉恩老人長期照顧中心(養護型)	臺北市大安區安居街27號4、6樓及29號4、5樓	121.55461884	25.02058411	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11074
銀髮族服務	養護型	臺北市私立仁群老人長期照顧中心(養護型)	臺北市中山區民族東路512巷14號1~2樓、16號2樓	121.54194641	25.06735992	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11075
銀髮族服務	養護型	臺北市私立松青園老人養護所	臺北市中山區民生西路30號2樓、2樓之1~4	121.52163696	25.05763626	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11076
銀髮族服務	養護型	臺北市私立松湛園老人養護所	臺北市中山區錦州街4巷1號2樓、2樓之1	121.52354431	25.05995941	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11077
銀髮族服務	養護型	臺北市私立法泉老人長期照顧中心(養護型)	臺北市中山區八德路二段251號2樓	121.54103851	25.046978	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11078
銀髮族服務	養護型	臺北市私立三園老人長期照顧中心(養護型)	臺北市文山區車前路12號3-4樓	121.54091644	24.99147224	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11079
銀髮族服務	養護型	臺北市私立心慈老人養護所	臺北市文山區辛亥路五段120-1號1~4樓	121.55229187	24.99760628	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11080
銀髮族服務	養護型	臺北市私立吉祥老人長期照顧中心(養護型)	臺北市文山區木柵路三段85巷8弄4-1、4-2號1樓及2、2-1、2-2、4、4-1、4-2號2樓	121.56678009	24.98968887	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11081
銀髮族服務	養護型	臺北市私立美安老人長期照顧中心(養護型)	臺北市文山區溪口街1巷5號	121.54077148	24.99481392	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11082
銀髮族服務	養護型	臺北市私立景安老人長期照顧中心(養護型)	臺北市文山區景仁里溪口街1巷5號1~2樓	121.54077148	24.99481392	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11083
銀髮族服務	養護型	臺北市私立景興老人長期照顧中心(養護型)	臺北市文山區景興路222號3樓	121.54328156	24.99110413	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11084
銀髮族服務	養護型	臺北市私立慈安老人長期照顧中心(養護型)	臺北市文山區興隆路一段2、4號1~4樓	121.54180908	25.00139236	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11085
銀髮族服務	養護型	臺北市私立萬芳老人長期照顧中心(養護型)	臺北市文山區萬和街8號3樓	121.56772614	25.00200844	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11086
銀髮族服務	養護型	臺北市私立慧華老人長期照顧中心(養護型)	臺北市文山區興隆路二段154巷11號1樓	121.55169678	25.00085831	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11087
銀髮族服務	養護型	臺北市私立慧誠老人長期照顧中心(養護型)	臺北市文山區木柵路二段163、165號1~5樓	121.56045532	24.98859215	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11088
銀髮族服務	養護型	臺北市私立蓮馨老人長期照顧中心(養護型)	臺北市文山區萬和街6號8樓	121.56735992	25.00193787	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11089
銀髮族服務	養護型	臺北市私立精英國際老人長期照顧中心(養護型)	臺北市北投區關渡路60之1、62之1號1樓	121.46882629	25.11966324	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11090
銀髮族服務	養護型	臺北市私立北投老人長期照顧中心(養護型)	臺北市北投區公舘路231巷20號1樓	121.5092392	25.12672234	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11091
銀髮族服務	養護型	臺北市私立北投老人長期照顧中心(養護型)	臺北市北投區公舘路231巷20號1樓	121.50924683	25.12665367	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11092
銀髮族服務	養護型	臺北市私立全泰老人長期照顧中心(養護型)	臺北市北投區行義路105號1~2樓	121.52842712	25.12771606	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11093
銀髮族服務	養護型	臺北市私立同德老人長期照顧中心(養護型)	臺北市北投區明德路306號1-7樓	121.52225494	25.11522484	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11094
銀髮族服務	養護型	臺北市私立義行老人長期照顧中心(養護型)	臺北市北投區石牌路二段357巷1號4~6樓	121.52487183	25.12366486	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11095
銀髮族服務	養護型	臺北市私立榮祥老人長期照顧中心(養護型)	臺北市北投區文林北路166巷5弄2號1~2樓、4號1樓	121.51622772	25.10718346	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11096
銀髮族服務	養護型	臺北市私立全民老人長期照顧中心(養護型)	臺北市北投區石牌路二段317號1~2樓	121.52329254	25.12182045	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11097
銀髮族服務	養護型	臺北市私立行義老人長期照顧中心(養護型)	臺北市北投區石牌路二段357巷1號1~3樓	121.52487183	25.12366486	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11098
銀髮族服務	養護型	臺北市私立全家老人長期照顧中心(養護型)	臺北市北投區行義路96巷1號1~2樓	121.52892303	25.12663078	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11099
銀髮族服務	養護型	臺北市私立全寶老人長期照顧中心(養護型)	臺北市北投區石牌路二段315巷16弄2、2-1號1樓	121.52196503	25.12274551	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11100
銀髮族服務	養護型	臺北市私立榮健老人長期照顧中心(養護型)	臺北市北投區文林北路94巷5弄13號1~2樓、15號2樓	121.51776886	25.10647392	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11101
銀髮族服務	養護型	臺北市私立仁仁老人長期照顧中心(養護型)	臺北市松山區南京東路五段356號2樓	121.56969452	25.05106735	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11102
銀髮族服務	養護型	臺北市私立台大老人長期照顧中心(養護型)	臺北市松山區敦化南路一段7號4樓之1	121.54930115	25.04692078	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11103
銀髮族服務	養護型	臺北市私立康壯老人長期照顧中心(養護型)	臺北市松山區八德路四段203、205號1、2樓	121.559021	25.04846382	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11104
銀髮族服務	養護型	臺北市私立群英老人長期照顧中心(養護型)	臺北市松山區敦化南路一段7號4樓	121.54930115	25.04692078	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11105
銀髮族服務	養護型	臺北市私立倚青苑老人養護所	臺北市信義區中坡北路21號1~2樓、23號2樓	121.58084106	25.04490471	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11106
銀髮族服務	養護型	臺北市私立康庭老人養護所	臺北市信義區信義路六段15巷16號1樓	121.57540894	25.03523827	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11107
銀髮族服務	養護型	臺北市私立福安老人長期照顧中心(養護型)	臺北市南港區玉成街140巷21、23號2樓	121.58300018	25.04468727	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11108
銀髮族服務	養護型	財團法人臺北市私立愛愛院	臺北市萬華區糖?里大理街175巷27號	121.49556732	25.03454208	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11109
銀髮族服務	養護型	財團法人臺北市私立愛愛院	臺北市萬華區糖?里大理街175巷27號	121.49555969	25.03454781	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11110
銀髮族服務	失智照顧型	財團法人台北市中國基督教靈糧堂世界佈道會士林靈糧堂附設臺北私立天母社區式服務類長期照顧服務服務機構	臺北市士林區德行東路338巷12之1號	121.54025269	25.10856056	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11111
銀髮族服務	失智照顧型	委託經營管理臺北市北投奇岩樂活大樓(北投老人服務中心)	臺北市北投區奇岩里三合街一段119號	121.50392914	25.12655258	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11112
銀髮族服務	失智照顧型	財團法人天主教失智老人社會福利基金會附設臺北市私立聖若瑟失智老人養護中心	臺北市萬華區德昌街125巷11號1~4樓、13號1樓	121.49700928	25.0240097	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11113
銀髮族服務	安養機構	臺北市政府社會局老人自費安養中心	臺北市文山區忠順里興隆路四段109巷30弄6號	121.56217957	24.98660851	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11114
銀髮族服務	安養機構	臺北市立浩然敬老院	臺北市北投區知行路75號	121.46777344	25.11834908	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11115
銀髮族服務	老人公寓/住宅	臺北市陽明老人公寓	臺北市士林區格致路7號3-6樓	121.54611969	25.13634491	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11116
銀髮族服務	老人公寓/住宅	臺北市大龍老人住宅	臺北市大同區民族西路105號4-9樓	121.5171051	25.06881142	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11117
銀髮族服務	老人公寓/住宅	臺北市朱崙老人公寓	臺北市中山區龍江路15號4-7樓	121.54055023	25.04742241	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11118
銀髮族服務	老人公寓/住宅	臺北市中山老人住宅暨服務中心	臺北市中山區新生北路二段101巷2號1-6樓	121.52846527	25.05727005	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11119
銀髮族服務	團體家屋	財團法人私立廣恩老人養護中心附設臺北市私立陽明山社區長照機構	臺北市士林區陽明里15鄰仁民路15號	121.54348755	25.13361931	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11120
銀髮族服務	日間照顧中心	臺北榮民總醫院附設遊詣居社區長照機構	臺北市北投區石牌路二段322號1樓	121.52296448	25.12080193	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11121
銀髮族服務	日間照顧中心	臺北市大同老人服務暨日間照顧中心	臺北市大同區重慶里重慶北路三段347號3樓	121.51407623	25.07478523	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11122
銀髮族服務	日間照顧中心	渥康國際股份有限公司附設臺北市私立康禾社區長照機構	臺北市松山區中正里26鄰南京東路三段２８５號3樓	121.5458374	25.05200577	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11123
銀髮族服務	日間照顧中心	臺北市復華長青多元服務中心	臺北市中山區遼寧街185巷11號	121.54276276	25.05342674	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11124
銀髮族服務	日間照顧中心	臺北市中正區多元照顧中心(小規模多機能)	臺北市中正區羅斯福路二段5號2樓	121.52108765	25.02924538	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11125
銀髮族服務	日間照顧中心	臺北市西松老人日間照顧中心(小規模多機能服務)	臺北市松山區南京東路五段251巷46弄5號1-3樓	121.56482697	25.05335236	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11126
銀髮族服務	日間照顧中心	臺北市士林老人服務暨日間照顧中心	臺北市士林區忠誠路二段53巷7號5樓及6樓	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11127
銀髮族服務	日間照顧中心	臺北市政府社會局委託經營管理臺北市大安老人服務暨日間照顧中心(小規模多機能)	臺北市大安區四維路76巷12號1-5樓	121.54721832	25.02786064	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11128
銀髮族服務	日間照顧中心	臺北市中正老人服務暨日間照顧中心	臺北市中正區貴陽街一段60號	121.50904083	25.03892899	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11129
銀髮族服務	日間照顧中心	臺北市立聯合醫院陽明院區得憶齋失智失能日間照顧中心	臺北市士林區雨聲街105號	121.53156281	25.10519791	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11130
銀髮族服務	日間照顧中心	臺北市松山老人服務暨日間照顧中心	臺北市松山區健康路317號1樓	121.56661224	25.05447006	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11131
銀髮族服務	日間照顧中心	臺北市政府社會局「委託辦理臺北市大安區老人日間照顧服務」	臺北市大安區新生南路三段52-5號5樓	121.53395844	25.02114677	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11132
銀髮族服務	日間照顧中心	臺北市政府委託經營管理信義老人服務暨日間照顧中心(廣慈B標)	臺北市信義區福德街尚未有明確地址	121.58127594	25.0371933	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11133
銀髮族服務	日間照顧中心	臺北市政府委託經營管理臺北市瑞光社區長照機構	臺北市內湖區瑞光路尚未有明確地址	121.56655121	25.08001518	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11134
銀髮族服務	日間照顧中心	臺北市大同昌吉老人社區長照機構	臺北市大同區昌吉街52號9-10樓	121.51634216	25.06581688	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11135
銀髮族服務	日間照顧中心	臺北市私立新生社區長照機構	臺北市大安區新生南路三段52-5號5樓	121.53395844	25.02114677	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11136
銀髮族服務	日間照顧中心	臺北市立聯合醫院附設仁愛護理之家日間照護仁鶴軒	臺北市大安區仁愛路四段10號5樓	121.54530334	25.03754616	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11137
銀髮族服務	日間照顧中心	臺北市私立安歆松江社區長照機構	臺北市中山區松江路50號3樓A室	121.53273773	25.04824448	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11138
銀髮族服務	日間照顧中心	臺北市私立雲朵社區長照機構	臺北市中正區杭州南路一段63號4樓之1	121.52592468	25.04044151	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11139
銀髮族服務	日間照顧中心	臺北市西湖老人日間照顧中心	臺北市內湖區內湖路一段285號6樓	121.56659698	25.08241653	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11140
銀髮族服務	日間照顧中心	臺北市興隆老人日間照顧中心	臺北市文山區興隆路四段105巷47號B棟2樓	121.56312561	24.98828125	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11141
銀髮族服務	日間照顧中心	臺北市興隆老人日間照顧中心	臺北市文山區興隆路四段105巷47號B棟2樓	121.56312561	24.98828125	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11142
銀髮族服務	日間照顧中心	臺北市私立頤福社區長照機構	臺北市北投區裕民六路120號3樓	121.51763153	25.11454582	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11143
銀髮族服務	日間照顧中心	臺北市信義老人服務暨日間照顧中心	臺北市信義區興雅里松隆路36號4、5樓	121.56754303	25.04339409	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11144
銀髮族服務	日間照顧中心	臺北市南港老人服務暨日間照顧中心	臺北市南港區重陽路187巷5號2樓	121.59870148	25.05772591	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11145
銀髮族服務	日間照顧中心	臺北市萬華龍山老人服務暨日間照顧中心	臺北市萬華區梧州街36號2樓、2樓之2、3樓、3樓之1	121.49748993	25.03737068	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11146
銀髮族服務	小規模多機能	社團法人中華民國士林靈糧堂社會福利協會附設臺北市私立內湖社區長照機構	臺北市內湖區康樂街136巷15弄1、3、5號1樓	121.61862183	25.07226944	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11147
銀髮族服務	老人服務中心	臺北市政府社會局委託經營管理臺北市內湖老人服務中心	臺北市內湖區康樂街110巷16弄20號5、6樓	121.61838531	25.07037354	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11148
銀髮族服務	老人服務中心	臺北市政府社會局委託經營管理臺北市文山老人服務中心	臺北市文山區萬壽路27號6樓	121.57657623	24.98863983	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11149
銀髮族服務	老人服務中心	臺北市政府社會局委託經營管理臺北市萬華老人服務中心	臺北市萬華區西寧南路4號A棟3樓	121.50704193	25.04793739	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11150
銀髮族服務	老人服務中心	臺北市政府社會局委託辦理臺北市中正國宅銀髮族服務中心	臺北市萬華區青年路52號1樓之2	121.50349426	25.02539635	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11151
銀髮族服務	石頭湯社區整合照顧服務	內湖區社區整合照顧服務中心	臺北市內湖區明湖里康寧路三段99巷6弄12號1樓	121.61032867	25.07165337	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11152
銀髮族服務	石頭湯社區整合照顧服務	文山區社區整合照顧服務中心	臺北市文山區木新里保儀路115號	121.56761932	24.98573112	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11153
銀髮族服務	石頭湯社區整合照顧服務	北投區社區整合照顧服務中心	臺北市北投區關渡里知行路245巷14號1樓	121.46643066	25.12083626	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11154
銀髮族服務	石頭湯社區整合照顧服務	松山區社區整合照顧服務中心	臺北市松山區民福里復興北路451號1樓	121.54444122	25.06399155	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11155
銀髮族服務	石頭湯社區整合照顧服務	信義區社區整合照顧服務中心	臺北市信義區黎平里和平東路三段341巷10號	121.55724335	25.02124214	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11156
銀髮族服務	石頭湯社區整合照顧服務	南港區社區整合照顧服務中心	臺北市南港區萬福里同德路85巷6號1樓	121.58552551	25.04639244	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11157
銀髮族服務	石頭湯社區整合照顧服務	萬華區社區整合照顧服務中心	臺北市萬華區忠德里德昌街180號	121.49555206	25.02378845	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11158
銀髮族服務	石頭湯社區整合照顧服務	士林區社區整合照顧服務中心	臺北市士林區福志里幸福街5巷25號1樓	121.52803802	25.09728241	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11159
銀髮族服務	石頭湯社區整合照顧服務	大同區社區整合照顧服務中心	臺北市大同區揚雅里昌吉街61巷41號1樓	121.51489258	25.06703949	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11160
銀髮族服務	石頭湯社區整合照顧服務	大安區社區整合照顧服務中心	臺北市大安區法治里通化街192號1樓	121.55292511	25.02616882	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11161
銀髮族服務	石頭湯社區整合照顧服務	中山區社區整合照顧服務中心	臺北市中山區江山里合江街73巷4號1樓	121.53985596	25.05870819	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11162
銀髮族服務	石頭湯社區整合照顧服務	中正區社區整合照顧服務中心	臺北市中正區新營里愛國東路110巷16號	121.52105713	25.03215218	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11163
銀髮族服務	家庭照顧者服務中心	北區家庭照顧者支持中心(士林靈糧堂承辦)	臺北市士林區忠誠路二段53巷7號5樓	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11164
銀髮族服務	家庭照顧者服務中心	東區家庭照顧者支持中心(健順養護中心承辦)	臺北市中山區吉林路312號4樓	121.53016663	25.06193161	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11165
銀髮族服務	家庭照顧者服務中心	西區家庭照顧者支持中心(台北市立心慈善基金會承辦)	臺北市萬華區萬大路329巷1之1號1樓	121.50053406	25.02407074	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11166
銀髮族服務	家庭照顧者服務中心	南區家庭照顧者支持中心(婦女新知承辦)	臺北市中正區重慶南路三段2號3樓304室	121.51516724	25.02960968	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11167
銀髮族服務	社區照顧關懷據點	臺北市北投老人服務據點	臺北市北投區中央北路一段12號3、4樓	121.50099945	25.13391304	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11168
銀髮族服務	長青學苑	臺北醫學大學進修推廣處	臺北市大安區基隆路二段172-1號13樓	121.55477142	25.02655983	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11169
銀髮族服務	長青學苑	臺北市中山社區大學	臺北市中山區新生北路三段55號	121.52857971	25.06537628	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11170
銀髮族服務	長青學苑	臺北市士林社區大學	臺北市士林區承德路四段177號（百齡高中）	121.5230484	25.08701706	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11171
銀髮族服務	長青學苑	臺北市松山社區大學	臺北市松山區八德路四段101號	121.5610733	25.04870796	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11172
銀髮族服務	長青學苑	臺北市信義社區大學	臺北市信義區松仁路158巷1號	121.56793213	25.02861404	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11173
銀髮族服務	長青學苑	國立臺灣戲曲學院	臺北市內湖區內湖路二段177號	121.586586	25.0814724	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11174
銀髮族服務	長青學苑	臺北市中正社區大學	臺北市中正區濟南路一段6號	121.52183533	25.04241371	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11175
銀髮族服務	長青學苑	臺北市立大學	臺北市中正區愛國西路1號	121.51358032	25.03556442	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11176
銀髮族服務	長青學苑	淡江大學進修推廣處	臺北市大安區金華街199巷5號	121.52857971	25.03101158	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11177
銀髮族服務	長青學苑	臺北市大同社區大學	臺北市大同區長安西路37-1號	121.5196991	25.05036736	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11178
銀髮族服務	長青學苑	臺北市萬華社區大學	臺北市萬華區南寧路46號	121.50460052	25.03606415	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11179
銀髮族服務	長青學苑	臺北市文山社區大學	臺北市文山區景中街27號	121.54294586	24.9930191	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11180
銀髮族服務	長青學苑	臺北市大安社區大學	臺北市大安區杭州南路二段1號(金甌女中)	121.52423859	25.03493118	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11181
銀髮族服務	長青學苑	臺北市內湖社區大學	臺北市內湖區文德路240號3樓	121.58873749	25.0788002	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11182
身障機構	住宿機構	臺北市私立文山創世清寒植物人安養院	臺北市文山區萬和街8號五樓	121.56772614	25.00200844	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11183
身障機構	住宿機構	崇愛發展中心	新北市中和區正行里7鄰圓通路143-1號	121.498909	24.99508858	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11184
身障機構	住宿機構	崇愛發展中心	新北市中和區正行里7鄰圓通路143-1號	121.498909	24.99508858	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11185
身障機構	住宿機構	臺北市三玉啟能中心	臺北市士林區忠誠路二段53巷7號3、4、7樓	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11186
身障機構	住宿機構	臺北市永福之家	臺北市士林區永福里5鄰莊頂路2號	121.54947662	25.11076546	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11187
身障機構	住宿機構	臺北市私立世美家園	臺北市文山區萬芳路51號	121.56383514	24.99812317	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11188
身障機構	住宿機構	臺北市私立彩虹村家園	臺北市北投區泉源路華南巷18號一樓	121.50702667	25.14027596	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11189
身障機構	住宿機構	臺北市私立陽明養護中心	臺北市北投區公舘路209巷18號	121.5087738	25.1275177	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11190
身障機構	住宿機構	臺北市私立陽明養護中心	臺北市北投區公舘路209巷18號	121.5087738	25.1275177	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11191
身障機構	住宿機構	臺北市私立永愛發展中心	臺北市信義區信義路五段150巷316號五樓	121.56960297	25.02690887	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11192
身障機構	住宿機構	臺北市南港養護中心	臺北市南港區松河街550號一樓	121.59855652	25.05801392	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11193
身障機構	住宿機構	臺北市東明扶愛家園	臺北市南港區南港路二段38巷8弄1號	121.60428619	25.05506134	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11194
身障機構	住宿機構	臺北市東明扶愛家園	臺北市南港區南港路二段38巷8弄1號	121.60427856	25.05506134	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11195
身障機構	住宿機構	臺北市一壽照顧中心	臺北市文山區樟新里5鄰一壽街22號三、四樓	121.55627441	24.97971535	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11196
身障機構	住宿機構	臺北市立陽明教養院(華岡院區)	臺北市士林區陽明里8鄰凱旋路61巷4弄9號	121.54120636	25.13517189	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11197
身障機構	住宿機構	臺北市廣愛家園	臺北市信義區大仁里福德街84巷	121.58076477	25.03858566	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11198
身障機構	住宿機構	臺北市私立聖安娜之家	臺北市士林區中山北路七段181巷1號	121.5322113	25.12449646	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11199
身障機構	住宿機構	臺北市大龍養護中心	臺北市大同區民族西路105號1-3樓	121.5171051	25.06881142	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11200
身障機構	住宿機構	臺北市私立育成和平發展中心	臺北市大安區臥龍街280號	121.55869293	25.01689339	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11201
身障機構	住宿機構	臺北市弘愛服務中心	臺北市中正區濟南路二段46號四樓	121.53089905	25.04035187	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11202
身障機構	住宿機構	臺北市私立創世清寒植物人安養院	臺北市中正區北平東路28號2樓	121.52537537	25.04586029	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11203
身障機構	住宿機構	臺北市金龍發展中心	臺北市內湖區金龍路136-1號	121.59009552	25.0857563	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11204
身障機構	住宿機構	臺北市興隆照顧中心	臺北市文山區興隆路四段105巷45號2樓	121.56251526	24.98816681	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11205
身障機構	住宿機構	臺北市興隆照顧中心	臺北市文山區興隆路四段105巷45號2樓	121.56251526	24.98816681	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11206
身障機構	社區居住	士林社區居住家園(德蘭家)	臺北市士林區0鄰中山北路七段146巷7、7-1號1樓	121.53314209	25.12323761	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11207
身障機構	社區居住	金南社區居住家園	臺北市大安區金山南路二段135號三樓	121.5267334	25.02968597	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11208
身障機構	社區居住	景仁社區居住(景仁家)	臺北市文山區羅斯福路六段276巷11號二樓	121.53927612	24.99145126	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11209
身障機構	社區居住	景仁社區居住(愛國家)	臺北市中正區愛國東路62號五樓	121.51902771	25.03349495	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11210
身障機構	社區居住	士林社區居住家園(聖露薏絲家)	臺北市士林區中山北路七段191巷9號1樓	121.53173065	25.12537384	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11211
身障機構	社區居住	建成社區居住家園	臺北市大同區承德路二段33號4、5樓	121.51842499	25.05458832	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11212
身障機構	社區居住	臺北市文林社區居住家園	臺北市北投區文林北路75巷51號/53號/63號	121.51718903	25.10387039	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11213
身障機構	社區居住	臺北市松德社區居住家園	臺北市信義區松德路25巷58號三樓	121.57752228	25.03782082	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11214
身障機構	社區居住	臺北市萬大社區居住家園	臺北市萬華區萬大路411、413號	121.50067902	25.03209686	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11215
身障機構	團體家庭	臺北市健軍團體家庭	臺北市中正區富水里4鄰汀州路三段60巷2弄6號	121.53071594	25.01549721	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11216
身障機構	團體家庭	臺北市興隆團體家庭	臺北市文山區木柵路二段138巷33號3樓	121.56230927	24.9880352	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11217
身障機構	團體家庭	臺北市三興團體家庭	臺北市信義區景勤里5鄰吳興街156巷6號3樓	121.56117249	25.0290184	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11218
身障機構	團體家庭	臺北市興隆團體家庭	臺北市文山區木柵路二段138巷33號3樓	121.56230927	24.9880352	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11219
身障機構	團體家庭	臺北市私立心路社區家園	臺北市文山區興旺里22鄰福興路63巷4弄29號一樓	121.5490036	25.00467873	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11220
身障機構	共融式遊戲場	立農公園	臺北市北投區承德路七段與吉利街口	121.51067352	25.11059761	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11367
身障機構	日間服務機構	臺北市私立陽光重建中心	臺北市中山區南京東路三段91號三樓	121.53896332	25.05215836	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11221
身障機構	日間服務機構	臺北市永明發展中心(兼辦早療服務)	臺北市北投區永明里4鄰石牌路二段115號四至六樓	121.51758575	25.11827469	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11222
身障機構	日間服務機構	臺北市私立心路兒童發展中心(兼辦早療服務)	臺北市中山區復興北路232號	121.54392242	25.0572319	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11223
身障機構	日間服務機構	臺北市城中發展中心	臺北市中正區汀州路二段172號	121.52207184	25.02377129	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11224
身障機構	日間服務機構	臺北市南海發展中心	臺北市中正區延平南路207號1-2樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11225
身障機構	日間服務機構	臺北市南海發展中心	臺北市中正區延平南路207號1-2樓	121.50766754	25.03288651	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11226
身障機構	日間服務機構	臺北市私立婦幼家園(兼辦早療服務)	臺北市內湖區民權東路六段180巷42弄6號	121.59233093	25.06734657	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11227
身障機構	日間服務機構	臺北市萬芳啟能中心	臺北市文山區萬美街一段51號1樓	121.56848145	25.00230408	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11228
身障機構	日間服務機構	臺北市萬芳發展中心(兼辦早療服務)	臺北市文山區萬美街一段55號二樓	121.56811523	25.00234032	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11229
身障機構	日間服務機構	臺北市私立至德聽語中心(提供早療服務)	臺北市中正區0鄰中華路一段77號三樓	121.50778198	25.03894234	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11230
身障機構	日間服務機構	臺北市私立育成裕民發展中心	臺北市北投區裕民一路41巷2弄18號	121.5185318	25.11671829	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11231
身障機構	日間服務機構	臺北市稻香發展中心	臺北市北投區稻香里0鄰稻香路81號2樓	121.48936462	25.14090347	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11232
身障機構	日間服務機構	臺北市私立自立社區學園	臺北市士林區德行西路93巷7號地下一樓之1	121.52088165	25.10487366	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11233
身障機構	日間服務機構	臺北市大同發展中心(兼辦早療服務)	臺北市大同區昌吉街52號六-七樓	121.51634216	25.06581688	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11234
身障機構	日間服務機構	臺北市博愛發展中心	臺北市中山區敬業三路160號	121.556633	25.07952881	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11235
身障機構	日間服務機構	臺北市慈祐發展中心	臺北市松山區八德路四段688號3-4樓	121.57688141	25.04985809	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11236
身障機構	日間服務機構	臺北市恆愛發展中心	臺北市信義區松隆路36號六樓	121.56754303	25.04339409	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11237
身障機構	日間服務機構	臺北市私立第一兒童發展中心(兼辦早療服務)	臺北市信義區信義路五段150巷316號一樓	121.56960297	25.02690887	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11238
身障機構	日間服務機構	臺北市私立育仁兒童發展中心(兼辦早療服務)	臺北市萬華區萬大路387巷15號	121.49967194	25.0221405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11239
身障機構	日間服務機構	臺北市私立育仁啟能中心	臺北市萬華區柳州街41號四樓	121.50538635	25.03847122	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11240
身障機構	社區日間作業設施	內湖工坊	臺北市內湖區江南街71巷60號	121.5791626	25.07430649	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11241
身障機構	社區日間作業設施	萬華視障生活重建中心暨社區工坊	臺北市萬華區0鄰梧州街36號4樓	121.49748993	25.03737068	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11242
身障機構	社區日間作業設施	士林工坊	臺北市士林區忠誠路二段53巷7號9樓A	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11243
身障機構	社區日間作業設施	奇岩工坊	臺北市北投區三合街一段119號7樓	121.50392914	25.12655258	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11244
身障機構	社區日間作業設施	奇岩工坊	臺北市北投區三合街一段119號7樓	121.50392914	25.12655258	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11245
身障機構	社區日間作業設施	文山工坊	臺北市文山區興隆路四段105巷47號1樓(興隆公宅2區)	121.56312561	24.98828125	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11246
身障機構	社區日間作業設施	文山工坊	臺北市文山區興隆路四段105巷47號1樓(興隆公宅2區)	121.56312561	24.98828125	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11247
身障機構	社區日間作業設施	北投工坊	臺北市北投區石牌路二段99巷9號四樓	121.51663971	25.11792564	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11248
身障機構	社區日間作業設施	肯納行義坊	臺北市北投區行義路129號	121.52828217	25.12879944	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11249
身障機構	社區日間作業設施	聖文生樂活工坊	臺北市北投區石牌路二段90巷20號2樓	121.51741791	25.11698341	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11250
身障機構	社區日間作業設施	民生工坊	臺北市松山區敦化北路199巷5號三樓	121.55152893	25.05699539	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11251
身障機構	社區日間作業設施	健康工坊_A處	臺北市松山區健康路399號6樓	121.56886292	25.05460167	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11252
身障機構	社區日間作業設施	星扶工坊	臺北市松山區八德路四段306號四樓	121.56736755	25.04899979	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11253
身障機構	社區日間作業設施	信義工坊	臺北市信義區信義路五段15號三樓	121.56689453	25.03314972	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11254
身障機構	社區日間作業設施	心朋友工作坊	臺北市信義區和平東路三段391巷20弄16號	121.55817413	25.02076912	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11255
身障機構	社區日間作業設施	台北工坊	臺北市信義區信義路四段415號七樓	121.55923462	25.03330421	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11256
身障機構	社區日間作業設施	南港工坊(舊址，已停辦)	臺北市南港區南港路一段173號五樓	121.61297607	25.05520248	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11257
身障機構	社區日間作業設施	委託經營管理身心障礙者社區日間作業設施-瑞光工坊	臺北市內湖區瑞光路162號2樓之2	121.57926178	25.07343483	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11258
身障機構	社區日間作業設施	松山工坊	臺北市松山區新聚里3鄰南京東路五段356號6F-2	121.56969452	25.05106735	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11259
身障機構	社區日間作業設施	南港工坊	臺北市南港區八德路四段768-1號	121.57996368	25.05030441	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11260
身障機構	社區日間作業設施	南港工坊	臺北市南港區八德路四段768-1號	121.57996368	25.05030441	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11261
身障機構	社區日間作業設施	健康工坊_B處	臺北市松山區健康路399號6樓	121.56886292	25.05460167	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11262
身障機構	社區日間作業設施	委託經營管理身心障礙者社區日間作業設施-瑞光工坊	臺北市內湖區瑞光路162號2樓之2	121.57926178	25.07343483	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11263
身障機構	社區日間作業設施	委託經營管理身心障礙者社區日間作業設施-明倫工坊	臺北市大同區承德路三段285之5號	121.51941681	25.07311821	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11264
身障機構	社區日間作業設施	建成工坊	臺北市大同區承德路二段33號6樓	121.51842499	25.05458832	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11265
身障機構	社區日間作業設施	士林工坊(舊名，已停用)	臺北市士林區中山北路六段248號五樓	121.52549744	25.10923576	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11266
身障機構	社區日間作業設施	育成蘭興站	臺北市士林區磺溪街88巷5號一樓	121.52371979	25.10851097	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11267
身障機構	社區日間作業設施	心願工坊	臺北市大同區昌吉街52號八樓	121.51634216	25.06581688	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11268
身障機構	社區日間作業設施	大安工坊	臺北市大安區瑞安街73號三樓	121.54110718	25.02832413	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11269
身障機構	社區日間作業設施	天生我才大安站	臺北市大安區敦化南路二段200巷16號五樓	121.54759216	25.02278519	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11270
身障機構	社區日間作業設施	中山工坊	臺北市中山區建國北路二段260、262號3樓	121.53770447	25.06095505	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11271
身障機構	社區日間作業設施	古亭工坊	臺北市中正區羅斯福路二段150號	121.52320862	25.02566338	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11272
身障機構	社區日間作業設施	夢想工坊	臺北市中正區南昌路二段192號五樓之3	121.52384186	25.02423477	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11273
身障機構	社區日間作業設施	星兒工坊	臺北市中正區寧波西街62號三樓	121.51712799	25.03038788	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11274
身障機構	社區日間作業設施	肯納和平坊	臺北市中正區和平西路二段6號四樓	121.51416779	25.02775192	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11275
身障機構	身障社區長照機構（日間照顧）	財團法人廣青文教基金會附設臺北市私立士林身障社區長照機構(日間照顧)	臺北市士林區後港街189號一樓	121.52096558	25.08804512	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11276
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人喜憨兒社會福利基金會經營管理中山身障社區長照機構（日間照顧）	臺北市中山區長安西路5弄2號四樓	121.52077484	25.05050468	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11277
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人喜憨兒社會福利基金會經營管理中山身障社區長照機構（日間照顧）	臺北市中山區長安西路5弄2號四樓	121.52132416	25.04980659	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11278
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人伊甸社會福利基金會經營管理臺北市民生身障社區長照機構（日間照顧）	臺北市松山區民生東路五段163之1號七樓	121.56258392	25.05905724	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11279
身障機構	身障社區長照機構（日間照顧）	財團法人喜憨兒社會福利基金會附設臺北市私立松山身障社區長照機構(日間照顧)	臺北市松山區南京東路五段356號六樓之2	121.56969452	25.05106735	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11280
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人中華民國唐氏症基金會經營管理信義身障社區長照機構（日間照顧）	臺北市信義區信義路五段15號五樓	121.56689453	25.03314972	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11281
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人臺北市喜樂家族社會福利基金會經營管理大龍峒身障社區長照機構（日間照顧）	臺北市大同區老師里0鄰重慶北路三段320號3、4樓（社福大樓）	121.51358795	25.07470131	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11282
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人天主教白永恩神父社會福利基金會經營管理稻香身障社區長照機構（日間照顧）	臺北市北投區稻香里0鄰稻香路81號3樓之1	121.48936462	25.14090347	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11283
身障機構	身障社區長照機構（日間照顧）	臺北市政府社會局委託財團法人中華民國唐氏症基金會經營管理景新身障社區長照機構（日間照顧）	臺北市文山區景行里景後街151號4樓	121.54191589	24.98999786	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11284
身障機構	精神障礙者會所	星辰會所	臺北市士林區三玉里忠誠路二段53巷7號9樓	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11285
身障機構	精神障礙者會所	真福之家_公辦民營	臺北市大同區承德路二段33號3樓	121.51842499	25.05458832	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11286
身障機構	精神障礙者會所	興隆會所	臺北市文山區木柵路二段138巷33號1樓	121.56230927	24.9880352	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11287
身障機構	精神障礙者會所	興隆會所	臺北市文山區木柵路二段138巷33號1樓	121.56230927	24.9880352	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11288
身障機構	精神障礙者會所	真福之家_方案委託	臺北市松山區敦化北路145巷10之2號1樓	121.55015564	25.05389595	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11289
身障機構	精神障礙者會所	向陽會所	臺北市萬華區青年路152巷20號、22號1樓	121.50184631	25.02095222	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11290
身障機構	精神障礙者會所	臺北市精神障礙者會所-向陽會所	臺北市萬華區日祥里1鄰青年路152巷2號	121.50217438	25.02130318	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11291
身障機構	身心障礙者資源中心	臺北市士林、北投區身心障礙者資源中心	臺北市北投區奇岩里0鄰三合街一段119號7樓	121.50392914	25.12655258	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11292
身障機構	身心障礙者資源中心	臺北市士林、北投區身心障礙者資源中心	臺北市北投區奇岩里0鄰三合街一段119號7樓	121.50392914	25.12655258	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11293
身障機構	身心障礙者資源中心	臺北市大同、中山區身心障礙者資源中心	臺北市中山區長安西路5巷2號	121.52077484	25.05050659	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11294
身障機構	身心障礙者資源中心	臺北市中正、萬華區身心障礙者資源中心	臺北市中正區南門里延平南路207號3樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11295
身障機構	身心障礙者資源中心	臺北市中正、萬華區身心障礙者資源中心	臺北市中正區南門里延平南路207號3樓	121.50766754	25.03288651	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11296
身障機構	身心障礙者資源中心	大安、文山區身心障礙者資源中心	臺北市文山區辛亥路五段94號一樓	121.55312347	24.9984436	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11297
身障機構	身心障礙者資源中心	臺北市內湖、松山區身心障礙者資源中心	臺北市內湖區瑞光路162號2樓之3	121.57926178	25.07343483	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11298
身障機構	身心障礙者資源中心	臺北市內湖、松山區身心障礙者資源中心	臺北市內湖區瑞光路162號2樓之3	121.57926178	25.07343483	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11299
身障機構	身心障礙者資源中心	臺北市信義、南港區身心障礙者資源中心	臺北市信義區廣居里3鄰忠孝東路五段242號7樓	121.57232666	25.040802	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11300
身障機構	福利服務中心	臺北市私立活泉之家	臺北市文山區萬美街一段55號三樓	121.56811523	25.00234032	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11301
身障機構	福利服務中心	臺北市身心障礙者自立生活支持服務中心	臺北市大同區重慶北路三段347號3樓之2	121.51407623	25.07478523	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11302
身障機構	福利服務中心	臺北市身心障礙者自立生活支持服務中心	臺北市大同區重慶北路三段347號3樓之2	121.51407623	25.07478523	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11303
身障機構	福利服務中心	臺北市私立八德服務中心	臺北市松山區八德路三段155巷4弄35號	121.55560303	25.04892731	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11304
身障機構	輔具服務中心	臺北市合宜輔具中心(財團法人第一社會福利基金會承辦)	臺北市中山區玉門街1號	121.52050018	25.07036209	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11305
身障機構	輔具服務中心	臺北市西區輔具中心 (財團法人伊甸社會福利基金會承辦)	臺北市中山區長安西路2號5巷2號2樓	121.52077484	25.05050468	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11306
身障機構	輔具服務中心	臺北市西區輔具中心 (財團法人伊甸社會福利基金會承辦)	臺北市中山區長安西路2號5巷2號2樓	121.5203476	25.04982758	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11307
身障機構	輔具服務中心	臺北市南區輔具中心 (財團法人第一社會福利基金會承辦)	臺北市信義區信義路五段150巷310號	121.56950378	25.0270462	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11308
身障機構	身心障礙者社區日間活動據點	財團法人台北市私立雙連視障關懷基金會	臺北市中山區中山北路二段111號11樓	121.52317047	25.06012344	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11309
身障機構	身心障礙者社區日間活動據點	財團法人喜憨兒社會福利基金會	臺北市松山區民生東路五段163-1號7樓	121.56258392	25.05905724	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11310
身障機構	身心障礙者社區日間活動據點	財團法人中華民國自閉症基金會	臺北市士林區中山北路五段841號4樓之2	121.5253067	25.10217667	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11311
身障機構	身心障礙者社區日間活動據點	中華視障人福利協會	臺北市中山區撫順街6號6樓	121.52156067	25.06368637	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11312
身障機構	身心障礙者社區日間活動據點	財團法人心路社會福利基金會	臺北市文山區萬和街8號1樓(臺北社區生活支持中心)	121.56772614	25.00200844	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11313
身障機構	身心障礙者社區日間活動據點	中華民國腦性麻痺協會	臺北市北投區大業路166號5樓	121.49906921	25.12528992	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11314
身障機構	身心障礙者社區日間活動據點	社團法人台北生命勵樂活輔健會	臺北市松山區塔悠路臺北市觀山自行車租借站（塔悠路與民權東路交叉口，民權高架橋下，基六號疏散門進入，左轉直走往大直橋方向，約250公尺之高速公路橋下方彩色貨櫃屋）	121.56828308	25.06192589	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11315
身障機構	身心障礙者社區日間活動據點	台北市康復之友協會	臺北市松山區八德路四段604號2樓之3	121.57272339	25.04980087	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11316
身障機構	身心障礙者社區日間活動據點	財團法人伊甸社會福利基金會(附設台北市私立恩望身心障礙者人力資源服務中心)	臺北市南港區忠孝東路六段85號3樓	121.58466339	25.04817581	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11317
身障機構	身心障礙者社區日間活動據點	社團法人臺北市視障者家長協會	臺北市松山區敦化北路155巷76號4樓	121.55147552	25.0543232	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11318
身障機構	身心障礙者社區日間活動據點	台北市瞽者福利協進會	臺北市萬華區廣州街152巷10號3樓(新富民區民活動中心)	121.5005188	25.03620529	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11319
身障機構	共融式遊戲場	福志公園	臺北市士林區福林路251巷4弄	121.53466034	25.0984745	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11320
身障機構	共融式遊戲場	眷村文化公園	臺北市信義區莊敬路與松勤路交口,信義國小西側	121.56114197	25.03233337	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11321
身障機構	共融式遊戲場	福志公園	臺北市士林區福林路251巷4弄	121.53466034	25.0984726	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11322
身障機構	共融式遊戲場	士林4號廣場	臺北市士林區福林路與雨農路交叉口	121.53025055	25.09458733	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11323
身障機構	共融式遊戲場	士林4號廣場	臺北市士林區福林路與雨農路交叉口	121.53025055	25.09458733	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11324
身障機構	共融式遊戲場	兒童新樂園(機械式)	臺北市士林區承德路五段55號	121.51416779	25.09683609	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11325
身障機構	共融式遊戲場	兒童新樂園(非機械式)	臺北市士林區承德路五段55號	121.51416779	25.09683609	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11326
身障機構	共融式遊戲場	樹德公園	臺北市大同區大龍街129號	121.51611328	25.06715202	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11327
身障機構	共融式遊戲場	樹德公園	臺北市大同區大龍街129號	121.51611328	25.06715202	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11328
身障機構	共融式遊戲場	景化公園	臺北市大同區伊寧街9巷(景化街巷弄中)	121.5131073	25.06513214	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11329
身障機構	共融式遊戲場	朝陽公園	臺北市大同區重慶北路二段64巷口	121.51343536	25.05578804	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11330
身障機構	共融式遊戲場	建成公園	臺北市大同區承德路二段臺北市大同區承德路二段35號旁	121.51843262	25.0547924	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11331
身障機構	共融式遊戲場	眷村文化公園	臺北市信義區莊敬路與松勤路交口,信義國小西側	121.56114197	25.03233337	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11332
身障機構	共融式遊戲場	象山公園	臺北市信義區信義路五段150巷旁	121.57032013	25.02561569	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11333
身障機構	共融式遊戲場	聯成公園	臺北市南港區忠孝東路六段250巷1弄	121.58903503	25.04843712	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11334
身障機構	共融式遊戲場	玉成公園	臺北市南港區中坡南路55號	121.58575439	25.04187012	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11335
身障機構	共融式遊戲場	四分綠地	臺北市南港區研究院路二段182巷58弄旁	121.61441803	25.0363636	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11336
身障機構	共融式遊戲場	中研公園	臺北市南港區研究院路二段12巷58弄	121.6138916	25.04714584	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11337
身障機構	共融式遊戲場	山水綠生態公園	臺北市南港區南深路37號	121.62039948	25.03647423	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11338
身障機構	共融式遊戲場	山水綠生態公園	臺北市南港區南深路37號	121.62039948	25.03647614	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11339
身障機構	共融式遊戲場	和平青草公園	臺北市萬華區艋舺大道與號西園路二段交叉口	121.50521851	25.03445435	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11340
身障機構	共融式遊戲場	和平青草公園	臺北市萬華區艋舺大道與號西園路二段交叉口	121.50521851	25.03445435	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11341
身障機構	共融式遊戲場	建成公園	臺北市大同區承德路二段臺北市大同區承德路二段35號旁	121.51843262	25.05479431	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11342
身障機構	共融式遊戲場	大安國小	臺北市大安區臥龍街129號	121.54964447	25.01951027	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11343
身障機構	共融式遊戲場	和平實驗小學	臺北市大安區敦南街76巷28號	121.54666901	25.02072525	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11344
身障機構	共融式遊戲場	和平實驗小學	臺北市大安區敦南街76巷28號	121.54666901	25.02072525	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11345
身障機構	共融式遊戲場	建安國小	臺北市大安區大安路二段99號	121.54615021	25.02939034	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11346
身障機構	共融式遊戲場	古亭國小	臺北市大安區羅斯福路三段201號	121.52848816	25.02066994	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11347
身障機構	共融式遊戲場	明水公園	臺北市中山區北安路538巷1弄	121.54827118	25.07998466	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11348
身障機構	共融式遊戲場	永盛公園	臺北市中山區中山北路二段93巷26,40號間	121.52429199	25.05919838	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11349
身障機構	共融式遊戲場	大佳河濱公園	臺北市中山區濱江街　	121.53036499	25.07175255	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11350
身障機構	共融式遊戲場	中安公園	臺北市中山區中山北路二段65巷2弄內	121.52474213	25.05659676	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11351
身障機構	共融式遊戲場	花博公園美術園區	臺北市中山區民族東路以北中山北路以東(原民族公園)	121.52336121	25.06830025	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11352
身障機構	共融式遊戲場	花博公園美術園區	臺北市中山區民族東路以北中山北路以東(原民族公園)	121.52336121	25.06829834	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11353
身障機構	共融式遊戲場	石潭公園	臺北市內湖區成功路二段東側	121.59127045	25.06021118	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11354
身障機構	共融式遊戲場	大港墘公園	臺北市內湖區瑞光路393巷旁	121.57296753	25.07869911	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11355
身障機構	共融式遊戲場	碧湖公園	臺北市內湖區內湖路二段175號，國立臺灣戲曲學院旁	121.58579254	25.08116722	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11356
身障機構	共融式遊戲場	碧湖公園	臺北市內湖區內湖路二段175號，國立臺灣戲曲學院旁	121.58579254	25.08116913	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11357
身障機構	共融式遊戲場	潭美國小	臺北市內湖區新明路22號	121.59078979	25.06095314	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11358
身障機構	共融式遊戲場	萬芳4號公園	臺北市文山區萬和街1號對面	121.56757355	25.00131416	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11359
身障機構	共融式遊戲場	興隆公園	臺北市文山區興隆路二段154巷與仙岩路交口	121.55167389	25.00101662	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11360
身障機構	共融式遊戲場	興隆公園	臺北市文山區興隆路二段154巷與仙岩路交口	121.55167389	25.00101662	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11361
身障機構	共融式遊戲場	景華公園	臺北市文山區景興路與景華街交口	121.54488373	24.99845695	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11362
身障機構	共融式遊戲場	景華公園	臺北市文山區景興路與景華街交口	121.54488373	24.99845695	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11363
身障機構	共融式遊戲場	道南河濱公園	臺北市文山區恆光街景美恆光橋下游右側	121.5667038	24.98355865	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11364
身障機構	共融式遊戲場	榮華公園	臺北市北投區明德路150巷17-1號	121.52153778	25.11068535	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11365
身障機構	共融式遊戲場	石牌公園	臺北市北投區石牌路一段39巷內	121.50989532	25.118536	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11366
身障機構	共融式遊戲場	立農公園	臺北市北投區承德路七段與吉利街口	121.51073456	25.11044312	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11368
身障機構	共融式遊戲場	磺港公園	臺北市北投區磺港路與大興街交叉口	121.50196075	25.13333893	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11369
身障機構	共融式遊戲場	磺港公園	臺北市北投區磺港路與大興街交叉口	121.50196075	25.13333893	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11370
身障機構	共融式遊戲場	文林國小	臺北市北投區文林北路155號	121.51473999	25.10593414	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11371
身障機構	共融式遊戲場	榮富公園	臺北市北投區榮華三路及磺溪旁(過天母橋)	121.52153015	25.11384583	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11372
身障機構	共融式遊戲場	三民公園	臺北市松山區三民路、撫遠街298號	121.56399536	25.05328369	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11373
兒童與少年服務	兒童及少年安置機構	財團法人台北市私立體惠育幼院	臺北市士林區中山北路七段141巷43號	121.53018951	25.12454033	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11374
兒童與少年服務	兒童及少年安置機構	財團法人台北市愛慈社會福利基金會附設恩典之家寶寶照護中心	臺北市中正區公園路20巷12號4樓	121.5165863	25.04507828	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11375
兒童與少年服務	兒童及少年安置機構	臺北市私立義光育幼院	臺北市萬華區和平西路三段382巷11弄17號	121.49207306	25.03457069	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11376
兒童與少年服務	兒童及少年安置機構	財團法人台北市私立非拉鐵非兒少之家	臺北市士林區愛富二街7號	121.54443359	25.13857269	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11377
兒童與少年服務	兒童及少年安置機構	財團法人忠義社會福利事業基金會附設台北市私立忠義育幼院	臺北市文山區景興路85巷12號	121.54556274	24.99618721	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11378
兒童與少年服務	兒童及少年安置機構	財團法人基督教聖道兒少福利基金會附屬台北市私立聖道兒童之家	臺北市北投區承德路七段388號1樓	121.50209045	25.11964607	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11379
兒童與少年服務	兒童及少年安置機構	臺北市選擇家園(臺北市少年緊急短期安置庇護家園)	臺北市內湖區康樂街16號(內湖東湖郵局第6-151號信箱)	121.61789703	25.06816483	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11380
兒童與少年服務	兒童及少年安置機構	財團法人忠義社會福利事業基金會心棧家園	臺北市文山區萬和街6號11樓之1	121.56735992	25.00193787	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11381
兒童與少年服務	兒童及少年安置機構	財團法人基督教臺北市私立伯大尼兒少家園	臺北市文山區保儀路129號	121.56707001	24.98495674	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11382
兒童與少年服務	兒童及少年安置機構	臺北市向晴家園	臺北市文山區順興里003鄰興隆路四段145巷9弄15號	121.56182098	24.9857502	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11383
兒童與少年服務	兒童及少年安置機構	臺北市綠洲家園	新北市深坑區北深路２段155號	121.61414337	25.00211525	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11384
兒童與少年服務	兒童及少年安置機構	財團法人臺北市私立華興育幼院	臺北市士林區仰德大道一段101號	121.53820801	25.10460472	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11385
兒童與少年服務	兒童及少年安置機構	財團法人中華文化社會福利事業基金會台北兒童福利中心	臺北市信義區虎林街120巷270號	121.5708847	25.04220772	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11386
兒童與少年服務	兒童及少年安置機構	財團法人台灣關愛基金會附設台北市私立關愛之子家園	臺北市南港區南港路一段173號4樓	121.61297607	25.05520248	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11387
兒童與少年服務	兒童及少年安置機構	臺北市培立家園(大同區)	臺北市大同區光能里5鄰承德路二段33號11-12樓	121.51842499	25.05458832	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11388
兒童與少年服務	兒童及少年安置機構	臺北市培立家園	臺北市北投區中和街399-8號	121.49840546	25.14273262	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11389
兒童與少年服務	兒童及少年安置機構	臺北市希望家園	臺北市中山區松江路362巷22號	121.5322113	25.06189728	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11390
兒童與少年服務	青少年自立住宅	臺北市青少年自立住宅(得力住宅)	臺北市文山區木柵路二段138巷33號4樓之8	121.56230927	24.9880352	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11391
兒童與少年服務	兒童福利服務中心	臺北市福安兒童服務中心	臺北市中正區汀州路一段123號	121.50945282	25.02817535	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11392
兒童與少年服務	兒童福利服務中心	臺北市萬華兒童服務中心	臺北市萬華區東園街19號3樓、8樓	121.4956665	25.02791405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11393
兒童與少年服務	少年福利服務中心	臺北市北區少年服務中心	臺北市北投區中央北路一段12號5樓	121.50099945	25.13391304	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11394
兒童與少年服務	少年福利服務中心	臺北市中山、大同區少年服務中心	臺北市中山區聚盛里林森北路381號4樓	121.52565765	25.05848885	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11395
兒童與少年服務	少年福利服務中心	臺北市南區少年服務中心	臺北市大安區延吉街246巷10號4樓	121.555336	25.0353241	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11396
兒童與少年服務	少年福利服務中心	臺北市東區少年服務中心	臺北市松山區敦化北路199巷5號3樓	121.55152893	25.05699539	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11397
兒童與少年服務	少年福利服務中心	臺北市南港、信義區少年服務中心	臺北市信義區信義路六段12巷21號1樓	121.57520294	25.03305435	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11398
兒童與少年服務	少年福利服務中心	臺北市西區少年服務中心	臺北市萬華區東園街19號1樓	121.4956665	25.02791405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11399
兒童與少年服務	兒童及少年收出養服務資源中心	臺北市兒童及少年收出養服務資源中心	臺北市中正區延平南路207號5樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11400
兒童與少年服務	親職教育輔導中心	臺北市親職教育輔導中心	臺北市中正區延平南路207號5樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11401
兒童與少年服務	早期療育社區資源中心	大安、文山早期療育社區資源中心（萬隆東營區）	臺北市文山區興隆路二段88號5樓	121.5490799	25.00047112	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11402
兒童與少年服務	早期療育社區資源中心	財團法人天主教白永恩神父社會福利基金會附設臺北市私立聖文生兒童發展中心	臺北市北投區石牌路二段90巷20號	121.51741791	25.11698341	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11403
兒童與少年服務	早期療育社區資源中心	大安、文山區早療社區資源中心-財團法人心路社會福利基金會	臺北市大安區辛亥路一段40號2樓	121.53017426	25.02003098	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11404
兒童與少年服務	早期療育社區資源中心	大同、中山區早療社區資源中心-財團法人天主教光仁社會福利基金會	臺北市中山區林森北路77號4樓	121.52485657	25.04954529	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11405
兒童與少年服務	早期療育社區資源中心	松山、內湖區早療社區資源中心-財團法人伊甸社會福利基金會	臺北市內湖區民權東路六段90巷16弄1號3樓	121.5854187	25.06788063	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11406
兒童與少年服務	早期療育社區資源中心	士林、北投區早療社區資源中心-財團法人育成社會福利基金會	臺北市北投區中央北路一段6號4樓之2	121.50121307	25.13376808	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11407
兒童與少年服務	早期療育社區資源中心	信義、南港區早療社區資源中心-財團法人第一社會福利基金會	臺北市信義區莊敬路418號5樓	121.56639862	25.02712059	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11408
兒童與少年服務	早期療育社區資源中心	中正、萬華區早療社區資源中心-財團法人中華民國發展遲緩兒童基金會	臺北市萬華區西園路一段150號3樓	121.49941254	25.03749847	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11409
兒童與少年服務	友善兒童少年福利服務據點	財團法人基督教救世軍-友善兒少福利服務據點	臺北市內湖區內湖路一段285巷63弄7號1樓	121.56732941	25.08409309	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11410
兒童與少年服務	友善兒童少年福利服務據點	大橋友善兒童少年福利服務據點	臺北市大同區迪化街二段67號	121.50945282	25.06493759	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11411
兒童與少年服務	友善兒童少年福利服務據點	財團法人台北市中國基督教靈糧世界佈道會士林靈糧堂	臺北市北投區1鄰大業路大業路721號2樓	121.50223541	25.13728714	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11412
兒童與少年服務	友善兒童少年福利服務據點	社團法人臺北市基督教大內之光協會	臺北市內湖區康寧路一段128號	121.59368134	25.07933044	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11413
兒童與少年服務	友善兒童少年福利服務據點	社團法人中華社區厝邊頭尾營造協會「拉他們一把」社區弱勢家庭服務計畫	臺北市中山區建國北路一段33巷45號	121.53987885	25.04782104	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11414
兒童與少年服務	友善兒童少年福利服務據點	財團法人台北市基督教勵友中心-新興友善兒童少年福利服務據點	臺北市中山區雙城街43巷2號	121.52490997	25.06742096	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11415
兒童與少年服務	友善兒童少年福利服務據點	社團法人台北市原住民關懷協會-Lokah Laqi中山區友善兒少福利服務據點	臺北市中山區中山北路二段137巷18-12號B1	121.52423859	25.06165314	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11416
兒童與少年服務	友善兒童少年福利服務據點	「小星光陪讀班」友善兒童少年福利服務據點計畫	臺北市中正區杭州南路一段15-1號B1	121.52674866	25.04314613	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11417
兒童與少年服務	友善兒童少年福利服務據點	社團法人中華青少年純潔運動協會務-純潔古亭據點	臺北市中正區水源路臨28號	121.52282715	25.01967812	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11418
兒童與少年服務	友善兒童少年福利服務據點	南機場學苑-友善兒少福利服務據點	臺北市中正區中華路二段315巷18號 (據點)	121.5070343	25.02846336	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11419
兒童與少年服務	友善兒童少年福利服務據點	迎曦學園-接觸點友善兒童少年福利服務據點	臺北市內湖區內湖路二段355巷19號 1樓(據點)	121.59236145	25.08438301	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11420
兒童與少年服務	友善兒童少年福利服務據點	天使之家創造希望、迎向多元	臺北市內湖區成功路二段242號1樓	121.5901413	25.06586647	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11421
兒童與少年服務	友善兒童少年福利服務據點	社團法人台北市基督教萬芳浸信會-萬芳地區兒少服務計畫	臺北市文山區萬美街一段19巷5號1樓	121.5694046	25.00199318	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11422
兒童與少年服務	友善兒童少年福利服務據點	臺北市樂服社區關懷協會-友善兒少福利服務據點	臺北市文山區羅斯福路五段176巷26號	121.53729248	25.0043335	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11423
兒童與少年服務	友善兒童少年福利服務據點	臺北市文山區 明興社區發展協會-明興白屋童趣練功坊	臺北市文山區明興里秀明路一段17號2樓	121.56394196	24.98950005	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11424
兒童與少年服務	友善兒童少年福利服務據點	順興有福「童」享兒少服務據點	臺北市文山區興隆路四段165巷11號1樓	121.56249237	24.98421478	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11425
兒童與少年服務	友善兒童少年福利服務據點	愛鄰木柵舊社區兒少據點	臺北市文山區木柵路三段77號6樓	121.56716919	24.98875618	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11426
兒童與少年服務	友善兒童少年福利服務據點	社團法人台灣社區 鴻羽關懷協會-兒少夢想力學苑	臺北市萬華區萬大路322巷39號3樓	121.49914551	25.0245533	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11427
兒童與少年服務	友善兒童少年福利服務據點	牧人學堂(銀河班) 友善兒童少年福利服務據點	臺北市大同區寧夏路139號2樓	121.51441193	25.06093025	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11428
兒童與少年服務	友善兒童少年福利服務據點	台北市朱厝崙社區發展協會	臺北市中山區龍江路45巷6號	121.5411377	25.04913521	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11429
兒童與少年服務	友善兒童少年福利服務據點	社團法人中華民國我願意全人關懷協會- I Do友善兒童少年福利服務據點	臺北市南港區同德路85巷12號1樓	121.58542633	25.04656601	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11430
兒童與少年服務	友善兒童少年福利服務據點	臺北市南港區久如社區發展協會-久如社區友善兒少服務據點(國高中)	臺北市南港區研究院路二段208號1樓	121.61710358	25.03666878	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11431
兒童與少年服務	友善兒童少年福利服務據點	財團法人伊甸社會福利基金會	臺北市松山區八德路三段155巷4弄35號1樓	121.55560303	25.04892731	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11432
兒童與少年服務	友善兒童少年福利服務據點	財團法人味全文化教育基金會	臺北市中山區松江路125號4樓	121.53325653	25.05302811	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11433
兒童與少年服務	友善兒童少年福利服務據點	臺灣兒少玩心教育協會	臺北市文山區興隆路四段145巷9弄3號1樓	121.56201172	24.98526382	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11434
兒童與少年服務	友善兒童少年福利服務據點	社團法人台北市基督教活水江河全人關懷協會-社區兒童少年關懷服務據點計畫	臺北市信義區松信路163號地下室	121.5721283	25.04297829	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11435
兒童與少年服務	友善兒童少年福利服務據點	臺北市南港區久如社區發展協會(國小)	臺北市南港區研究院路二段169號1樓	121.61737823	25.0374794	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11436
兒童與少年服務	友善兒童少年福利服務據點	財團法人台北市立心慈善基金會「小荳荳關懷園地」社區兒童照顧	臺北市萬華區東園街19號3樓	121.4956665	25.02791405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11437
兒童與少年服務	友善兒童少年福利服務據點	社團法人台灣社區實踐協會-萬華青年次分區兒少友善據點	臺北市萬華區萬大路137巷16號	121.50132751	25.02901459	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11438
兒童與少年服務	友善兒童少年福利服務據點	社團法人中華青少年純潔運動協會-萬華社區兒少關懷據點	臺北市萬華區寶興街80巷25號	121.49385834	25.02557373	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11439
兒童與少年服務	友善兒童少年福利服務據點	立心青春痘關懷園地社區少年照顧計畫	臺北市萬華區東園街19號8樓	121.4956665	25.02791405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11440
兒童與少年服務	友善兒童少年福利服務據點	社團法人臺灣好學協會-好學空間友善兒少福利據點	臺北市中山區松江路360號5樓	121.53298187	25.0618763	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11441
兒童與少年服務	友善兒童少年福利服務據點	社團法人 中華牧人關懷協會-星光班	臺北市大同區重慶北路二段57巷4號1樓	121.514534	25.05554962	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11442
兒童與少年服務	友善兒童少年福利服務據點	616幸福工作站	臺北市松山區民生東路五段36巷8弄7號1樓	121.55944824	25.05732727	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11443
兒童與少年服務	兒少活動小站	台北市彩虹全人關懷發展協會-彩虹小棧-兒少活動小站	臺北市內湖區文德路208巷16號B1	121.58349609	25.07766533	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11444
兒童與少年服務	兒少活動小站	財團法人台北市中國基督教靈糧世界佈道會台北靈糧堂-快樂學習列車	臺北市大同區承德路三段93號	121.51856995	25.06630516	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11445
兒童與少年服務	兒少活動小站	社團法人中華牧人關懷協會-星光小屋-兒少活動小站	臺北市文山區福興路78巷20弄2號1樓	121.55102539	25.00422859	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11446
兒童與少年服務	兒少活動小站	社團法人國際奔享體驗教育協會-吉利真光-兒少活動小站	臺北市北投區石牌路一段39巷80弄41號1樓	121.51094055	25.11594009	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11447
兒童與少年服務	兒少活動小站	社團法人台灣基督教展翔天地全人發展協會-小太陽歡樂園地活動小站	臺北市中正區汀州路三段101號2樓	121.52953339	25.01712608	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11448
兒童與少年服務	兒少活動小站	財團法人新北市基督教新希望教會-「花盛開福中」新希望教會福中萬花塢活動小站	臺北市士林區福港街129巷10弄12號1樓	121.51851654	25.08764839	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11449
兒童與少年服務	兒少活動小站	社團法人臺灣翔愛公益慈善協會-翻轉吧~孩子-兒少活動小站	臺北市士林區美崙街53號	121.52238464	25.09703255	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11450
兒童與少年服務	兒少活動小站	社團法人台北市文山區明興社區發展協會-明興巷弄兒少活動小站	臺北市文山區興隆路四段61號	121.55999756	24.98944283	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11451
兒童與少年服務	兒少活動小站	社團法人台灣守護有祢生命關懷協會-守護有祢兒童少年活動八禱活動小站	臺北市北投區奇岩里公舘路376巷2弄9號1樓	121.5039444	25.12334824	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11452
兒童與少年服務	兒少活動小站	社團法人台北市歐伊寇斯OIKOS社區關懷協會-小星光兒童少年活動小站	臺北市中正區杭州南路一段15-1號B1	121.52674866	25.04314613	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11453
兒童與少年服務	兒少活動小站	臺北市大安區古莊 社區發展協會-古莊兒童少年活動小站	臺北市大安區浦城街13巷20號	121.52778625	25.02440071	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11454
兒童與少年服務	兒少活動小站	社團法人中華民國基督教榮耀福音協會-勇士總動員-兒少活動小站	臺北市中山區成功里明水路636號	121.55134583	25.08284378	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11455
兒童與少年服務	兒少活動小站	臺北市南港區久如社區發展協會-活動小站	臺北市南港區九如里研究院路二段208號1樓	121.61710358	25.03666878	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11456
兒童與少年服務	兒少活動小站	財團法人基督教中華循理會內湖教會-社區弱勢兒少課業輔導暨品格成長營活動小站	臺北市內湖區環山路三段12號1樓	121.57907104	25.08468819	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11457
兒童與少年服務	兒少活動小站	社團法人臺北市放心窩社會互助協會-放心窩在社子島兒少活動小站	臺北市士林區延平北路八段93巷2號	121.48377228	25.10573959	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11458
兒童與少年服務	兒少活動小站	臺北市南港區聯成社區發展協會-歡樂窩.自在窩.安心窩-聯成兒少小站	臺北市南港區東新街77巷29號1樓	121.58834076	25.04766464	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11459
兒童與少年服務	兒少活動小站	財團法人台北市敦安社會福利基金會-「敦」親睦鄰「安」你心	臺北市中正區羅斯福路一段36號4樓	121.519104	25.03123856	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11460
兒童與少年服務	兒少活動小站	社團法人台北市士林全人關懷協會-士林兒少v小站	臺北市士林區文林路421巷30號2樓	121.52322388	25.09421349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11461
兒童與少年服務	兒少活動小站	社團法人臺北市放心窩社會互助協會-放心窩在「放心窩」活動小站	臺北市大同區迪化街二段172巷11號1樓	121.50994873	25.06722832	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11462
兒童與少年服務	兒少活動小站	中華民國愛之語全人關懷教育協會-古亭兒童少年活動小站	臺北市中正區羅斯福路二段44號2樓	121.52152252	25.02796173	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11463
兒童與少年服務	兒少活動小站	社團法人臺北市臻佶祥社會服務協會-書屋花甲的咖啡夢想	臺北市中正區中華路二段307巷82號1樓	121.5056076	25.02884865	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11464
婦女服務	婦女館	臺北市婦女館	臺北市萬華區艋舺大道101號3樓	121.50138092	25.03347778	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11465
婦女服務	婦女暨家庭服務中心	士林婦女暨家庭服務中心	臺北市士林區基河路140號	121.52230835	25.08888054	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11466
婦女服務	婦女暨家庭服務中心	臺北市文山婦女支持培力中心	臺北市文山區興安里0鄰興隆路二段88號5樓	121.5490799	25.00047112	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11467
婦女服務	婦女暨家庭服務中心	臺北市松山南港婦女支持培力中心	臺北市松山區南京東路五段251巷46弄5號7樓	121.56482697	25.05335236	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11468
婦女服務	婦女暨家庭服務中心	臺北市大同士林婦女支持培力中心	臺北市大同區迪化街一段21號7樓	121.51032257	25.05449867	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11469
婦女服務	婦女暨家庭服務中心	臺北市新移民家庭服務中心	臺北市大同區迪化街一段21號7樓	121.51032257	25.05449867	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11470
婦女服務	婦女暨家庭服務中心	臺北市大安婦女支持培力中心	臺北市大安區延吉街246巷10號5樓	121.555336	25.0353241	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11471
婦女服務	婦女暨家庭服務中心	臺北市大直婦女支持培力中心	臺北市中山區大直街1號2樓	121.54698181	25.08029556	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11472
婦女服務	婦女暨家庭服務中心	臺北市內湖婦女支持培力中心	臺北市內湖區康樂街110巷16弄20號7樓	121.61838531	25.07037354	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11473
婦女服務	婦女暨家庭服務中心	臺北市文山婦女支持培力中心（景新）	臺北市文山區景行里17鄰景後街151號3樓	121.54191589	24.98999786	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11474
婦女服務	婦女暨家庭服務中心	臺北市北投婦女支持培力中心	臺北市北投區長安里1鄰中央北路一段12號6樓	121.50099945	25.13391304	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11475
婦女服務	婦女暨家庭服務中心	臺北市松德婦女暨家庭服務中心	臺北市信義區松德路25巷60號1樓	121.57752991	25.03779411	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11476
婦女服務	婦女暨家庭服務中心	臺北市萬華婦女支持培力中心	臺北市萬華區東園街19號4樓	121.4956665	25.02791405	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11477
婦女服務	婦女暨家庭服務中心	臺北市西區單親家庭服務中心	臺北市大同區迪化街一段21號7樓	121.51032257	25.05449867	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11478
婦女服務	婦女暨家庭服務中心	臺北市東區單親家庭服務中心	臺北市松山區南京東路五段251巷46弄5號7樓	121.56482697	25.05335236	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11479
婦女服務	婦女暨家庭服務中心	臺北市中正婦女支持培力中心	臺北市中正區南門里12鄰延平南路207號4樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11480
婦女服務	婦女暨家庭服務中心	臺北市信義婦女支持培力中心	臺北市信義區大仁里27鄰大道路116號8樓	121.58288574	25.03861618	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11481
婦女服務	新移民社區關懷據點	臺北市北區新移民社區關懷據點	臺北市士林區蘭雅里8鄰中山北路六段290巷7弄5號1樓	121.5262146	25.11043358	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11482
婦女服務	新移民社區關懷據點	臺北市西區新移民社區關懷據點	臺北市中正區延平南路270號4樓	121.50717926	25.03229904	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11483
婦女服務	新移民社區關懷據點	臺北市東區新移民社區關懷據點	臺北市南港區向陽路252號1樓	121.59337616	25.05799294	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11484
婦女服務	新移民社區關懷據點	臺北市南區新移民社區關懷據點	臺北市文山區萬祥里5鄰羅斯福路五段211巷23號1樓	121.53981018	25.00259972	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11485
婦女服務	新移民社區關懷據點	臺北市北區新移民社區關懷據點	臺北市北投區清江里清江路177巷12號1樓	121.50223541	25.12792397	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11486
貧困危機家庭服務	平價住宅	延吉平宅	臺北市大安區延吉街236巷17號	121.55516052	25.03639793	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11487
貧困危機家庭服務	平價住宅	安康平宅	臺北市文山區興隆路四段103號3樓	121.56060028	24.98800468	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11488
貧困危機家庭服務	平價住宅	大同之家	臺北市北投區東昇路12巷4號	121.52305603	25.14614296	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11489
貧困危機家庭服務	平價住宅	福民平宅	臺北市萬華區西園路二段320巷57號	121.49098969	25.02757835	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11490
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局士林社會福利服務中心	臺北市士林區基河路140號1樓	121.52230835	25.08888054	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11491
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局大同社會福利服務中心	臺北市大同區昌吉街57號6樓	121.51514435	25.06601906	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11492
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局大安社會福利服務中心	臺北市大安區四維路198巷30弄5號2樓之9	121.54590607	25.02657509	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11493
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局中山社會福利服務中心	臺北市中山區合江街137號3樓	121.53932953	25.06165504	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11494
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局中正社會福利服務中心	臺北市中正區延平南路207號6樓	121.50766754	25.0328846	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11495
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局內湖社會福利服務中心	臺北市內湖區星雲街161巷3號4樓	121.59613037	25.0811367	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11496
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局文山社會福利服務中心	臺北市文山區興隆路二段160號6樓	121.55140686	25.00157356	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11497
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局北投社會福利服務中心	臺北市北投區新市街30號5樓	121.50241089	25.13248253	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11498
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局松山社會福利服務中心	臺北市松山區民生東路五段163之1號9樓	121.56258392	25.05905724	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11499
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局信義社會福利服務中心	臺北市信義區松隆路36號5樓	121.56754303	25.04339409	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11500
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局南港社會福利服務中心	臺北市南港區市民大道八段367號3樓	121.60793304	25.05376053	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11501
貧困危機家庭服務	社會福利服務中心	臺北市政府社會局萬華社會福利服務中心	臺北市萬華區梧州街36號5樓	121.49748993	25.03737068	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11502
貧困危機家庭服務	培力基地	轉角培力基地	臺北市中正區南陽街23巷1號	121.51654816	25.04381371	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11503
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」樟林社區據點	臺北市文山區光輝路87巷3號2樓	121.55719757	24.98562622	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11504
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」榮光社區據點	臺北市北投區石牌路一段166巷43弄15號1樓	121.51500702	25.11403084	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11505
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」奇岩社區據點	臺北市北投區公舘路315號1樓	121.50579071	25.1240406	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11506
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」吉慶社區據點	臺北市北投區實踐街34號3樓	121.50863647	25.11506462	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11507
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」立賢社區據點	臺北市北投區承德路七段232巷16號3樓	121.50737	25.11572647	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11508
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」立群社區據點	臺北市北投區尊賢街251巷18號1樓	121.5056839	25.11770058	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11509
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」秀山社區據點	臺北市北投區秀山里中和街502巷2弄15號1樓	121.4949646	25.14557076	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11510
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」清江社區據點	臺北市北投區清江里崇仁路一段83號5樓之1 	121.50174713	25.12591171	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11511
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」復建社區據點	臺北市松山區光復南路6巷26弄3號	121.55704498	25.04741478	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11512
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」雙和社區據點	臺北市信義區吳興街284巷24弄12號	121.56310272	25.02431679	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11513
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」永安社區據點	臺北市信義區忠孝東路五段236巷10弄10號3樓	121.5714035	25.04012871	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11514
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」舊莊社區據點	臺北市南港區舊莊街一段145巷6弄39號	121.62221527	25.03961754	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11515
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」好厝邊社區據點	臺北市南港區研究院路二段12巷57弄38號1樓	121.61360168	25.04813957	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11516
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」鴻福社區據點	臺北市南港區鴻福里成福路82號	121.58655548	25.04385185	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11517
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」久如社區據點	臺北市南港區研究院路二段208號	121.61710358	25.03666878	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11518
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」華江社區據點	臺北市萬華區華江里長順街14巷1弄2號	121.48970795	25.03133774	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11519
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」保德社區據點	臺北市萬華區東園街154巷9弄2號	121.49708557	25.02282715	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11520
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」孝德社區據點	臺北市萬華區德昌街185巷68號	121.49302673	25.0224247	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11521
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」馬場町社區據點	臺北市萬華區水源路195號4樓之4 	121.50919342	25.02322769	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11522
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」青年社區據點	臺北市萬華區新和里中華路二段416巷11之2號	121.50418854	25.02662277	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11523
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」朱厝崙社區據點	臺北市中山區龍江路12號	121.54027557	25.04766655	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11524
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」新力行社區據點	臺北市中山區長安東路二段163-1號	121.54016113	25.0484333	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11525
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」中原社區據點	臺北市中山區新生北路二段77巷1-1號2樓	121.5280838	25.05690002	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11526
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」泰和社區據點	臺北市信義區泰和里松仁路308巷60號	121.57008362	25.0212841	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11527
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」大道社區據點	臺北市信義區大道里忠孝東路五段790巷23弄12號2樓	121.58282471	25.0428009	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11528
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」安康社區據點	臺北市信義區安康里虎林街232巷63號	121.57596588	25.03573227	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11529
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」國慶社區據點	臺北市大同區重慶北路三段136巷20號	121.51289368	25.06767082	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11530
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」淡水河邊社區據點	臺北市大同區延平北路三段124號	121.51083374	25.0675602	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11531
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」林泉社區據點	臺北市北投區林泉里中心街27巷17號1樓	121.51035309	25.13833237	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11532
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」學府社區據點	臺北市大安區學府里羅斯福路四段119巷68弄15號	121.53972626	25.00936127	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11533
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」岩山社區據點	臺北市士林區岩山里芝玉路一段197巷1號	121.53339386	25.10755539	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11534
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」明勝社區據點	臺北市士林區明勝里承德路四段12巷57號3樓	121.51957703	25.08098221	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11535
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」灣仔社區據點	臺北市內湖區民權東路六段180巷72弄6號10樓之1	121.59210205	25.06613922	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11536
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」聯成社區據點	臺北市南港區聯成里東新街77巷29號1樓	121.58834076	25.04766464	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11537
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」幸福永和社區據點	臺北市北投區永和里行義路96巷25號3樓	121.52900696	25.12726212	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11538
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」忠駝社區據點	臺北市信義區西村里基隆路一段364巷24號7樓	121.55903625	25.03491211	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11539
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」我愛石牌社區據點	臺北市北投區石牌里明德路89號4樓	121.51880646	25.10899734	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11540
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」新忠社區據點	臺北市萬華區新忠里西藏路125巷15號3樓	121.50246429	25.02822685	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11541
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」挹翠社區據點	臺北市信義區六合里紫雲街23號1樓	121.57436371	25.01861191	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11542
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」松友社區據點	臺北市信義區松友里信義路六段76巷2弄22號	121.57613373	25.03439522	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11543
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」富洲社區據點	臺北市士林區延平北路八段86號	121.48439026	25.1058197	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11544
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」福佳社區據點	臺北市士林區美崙街49巷19號1樓	121.52204132	25.09667206	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11545
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」溪山社區據點	臺北市士林區至善路三段87號	121.5670166	25.11364174	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11546
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」幸福名山社區據點	臺北市士林區雨聲街53巷6號7樓	121.52832031	25.1026001	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11547
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」慶安社區據點	臺北市大同區重慶北路三段383巷3號4樓	121.514328	25.0759716	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11548
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」圓環社區據點	臺北市大同區重慶北路一段83巷37號6樓	121.51546478	25.05294609	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11549
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」錦華社區據點	臺北市大安區羅斯福路二段35巷19弄6號	121.52294922	25.02820969	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11550
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」安東社區據點	臺北市大安區安東街28號1樓	121.54244995	25.04427338	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11551
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」古風社區據點	臺北市大安區泰順街60巷2-1號	121.53092194	25.02227592	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11552
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」欣龍陣社區據點	臺北市大安區瑞安街65-1號4樓	121.54161072	25.02877426	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11553
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」新民炤社區據點	臺北市大安區建國南路一段286巷35號1樓	121.53580475	25.03619957	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11554
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」古莊社區據點	臺北市大安區羅斯福路二段81巷16弄1-2號2樓	121.52474213	25.02535057	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11555
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」大直社區據點	臺北市中山區北安路573巷6號	121.54754639	25.08128738	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11556
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」文祥社區據點	臺北市中正區金山南路一段100號1樓	121.52740479	25.03572273	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11557
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」南機場社區據點	臺北市中正區中華路二段303巷14號	121.50532532	25.02950668	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11558
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」新永昌社區據點	臺北市中正區汀州路一段232號4樓	121.51004791	25.02744102	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11559
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」新營社區據點	臺北市中正區寧波東街16巷2號	121.52065277	25.03236198	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11560
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」白石湖社區據點	臺北市內湖區碧山路40-3號	121.58834839	25.10344887	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11561
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」碧湖社區據點	臺北市內湖區內湖路三段294號	121.58493042	25.08917046	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11562
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」忠順社區據點	臺北市文山區興隆路四段145巷30號1樓	121.56311798	24.9851799	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11563
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」順興社區據點	臺北市文山區興隆路四段165巷12號2樓	121.56257629	24.98407173	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11564
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」明興社區據點	臺北市文山區木柵路二段109巷34號2樓	121.56375885	24.99076462	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11565
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」景慶社區據點	臺北市文山區景福街147-1號1樓	121.53639221	24.99567032	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11566
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」硫磺谷社區據點	臺北市北投區豐年里中央北路二段17號4樓	121.49612427	25.13641167	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11567
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」振華社區據點	臺北市北投區振華里裕民一路40巷29號3樓	121.51780701	25.11546516	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11568
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」永寬社區據點	臺北市中正區永昌里寧波西街181巷-8號1樓	121.51040649	25.02660179	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11569
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」中正新城社區據點	臺北市萬華區忠貞里青年路66號4樓之3	121.50273132	25.02424431	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11570
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」萬大社區據點	臺北市萬華區萬大路387巷39號3樓	121.49986267	25.02173424	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11571
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」住安社區據點	臺北市大安區住安里信義路四段60-12號1樓	121.54562378	25.03313446	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11572
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」愛在大學里社區據點	臺北市大安區大學里新生南路三段68之4號	121.53366089	25.01968575	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11573
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」芝山岩社區據點	臺北市士林區雨聲街8巷1-1號2樓	121.52948761	25.1014576	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11574
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」康福社區據點	臺北市士林區承德路四段40巷73號2樓	121.52111816	25.08145523	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11575
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」德行繽紛社區據點	臺北市士林區德行里福國路58號1樓	121.52336884	25.10216522	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11576
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」紫雲社區據點	臺北市內湖區紫雲里康寧路一段206號	121.59539795	25.07849312	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11577
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」大湖居安社區據點	臺北市內湖區大湖里大湖山莊街219巷29號	121.59983826	25.08901978	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11578
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」萬和社區據點	臺北市文山區溪洲街12號5樓之10	121.534729	25.00635529	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11579
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」德芳社區據點	臺北市文山區興邦里興隆路二段153巷6弄5號	121.54814148	25.001297	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11580
社區服務、NPO	「咱ㄟ社區」服務據點	「咱ㄟ社區」中央社區據點	臺北市北投區中央里光明路56號1樓	121.49977875	25.1327076	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11581
社區服務、NPO	NPO培力基地	台北NPO聚落	臺北市中正區龍光里13鄰重慶南路三段2號	121.51516724	25.02960968	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11582
社區服務、NPO	志願服務推廣中心	臺北市志願服務推廣中心	臺北市信義區信義路五段5段15號5樓	121.56689453	25.03314781	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11583
保護性服務	男士成長暨家庭服務中心	臺北市男士成長暨家庭服務中心-城男舊事心驛站	臺北市松山區敦化北路199巷5號3樓	121.55152893	25.05699539	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11584
保護性服務	親子會面中心	同心園臺北市親子會面中心	臺北市中正區新生南路一段54巷5弄2號	121.5321579	25.04141235	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11585
保護性服務	家庭暴力暨性侵害防治中心-分區辦公室	分區辦公室-臺北市政府駐地方法院處理家庭暴力暨家事事件聯合服務中心	臺北市士林區忠誠路二段53巷7號	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11586
保護性服務	家庭暴力暨性侵害防治中心-分區辦公室	分區辦公室-財團法人天主教善牧社會福利基金會(兒童少年保護及監護個案家庭處遇服務方案)	臺北市士林區忠誠路二段53巷7號	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11587
保護性服務	家庭暴力暨性侵害防治中心-分區辦公室	分區辦公室-台北市婦女救援基金會/目睹家暴兒少輔導方案	臺北市士林區忠誠路二段53巷7號8樓	121.53237915	25.11142349	2023-09-18 07:43:15.420088+00	2023-09-18 07:43:15.420088+00	11588
\.


--
-- TOC entry 4777 (class 0 OID 18361)
-- Dependencies: 223
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- TOC entry 4781 (class 0 OID 19307)
-- Dependencies: 234
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: -
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- TOC entry 4782 (class 0 OID 19639)
-- Dependencies: 279
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: -
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- TOC entry 4783 (class 0 OID 19649)
-- Dependencies: 281
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: -
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- TOC entry 4784 (class 0 OID 19659)
-- Dependencies: 283
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: -
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- TOC entry 4779 (class 0 OID 19124)
-- Dependencies: 228
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: -
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- TOC entry 4780 (class 0 OID 19136)
-- Dependencies: 229
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: -
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- TOC entry 5292 (class 0 OID 0)
-- Dependencies: 284
-- Name:  building_publand_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public." building_publand_ogc_fid_seq"', 1, true);


--
-- TOC entry 5293 (class 0 OID 0)
-- Dependencies: 285
-- Name: SOCL_export_filter_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."SOCL_export_filter_ppl_ogc_fid_seq"', 1, true);


--
-- TOC entry 5294 (class 0 OID 0)
-- Dependencies: 286
-- Name: app_calcu_daily_sentiment_voice1999_109_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_daily_sentiment_voice1999_109_ogc_fid_seq', 67090, true);


--
-- TOC entry 5295 (class 0 OID 0)
-- Dependencies: 287
-- Name: app_calcu_hour_traffic_info_histories_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_hour_traffic_info_histories_ogc_fid_seq', 15701, true);


--
-- TOC entry 5296 (class 0 OID 0)
-- Dependencies: 288
-- Name: app_calcu_hour_traffic_youbike_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_hour_traffic_youbike_ogc_fid_seq', 22724, true);


--
-- TOC entry 5297 (class 0 OID 0)
-- Dependencies: 289
-- Name: app_calcu_hourly_it_5g_smart_all_pole_device_log_dev13_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_hourly_it_5g_smart_all_pole_device_log_dev13_seq', 4172815, true);


--
-- TOC entry 5298 (class 0 OID 0)
-- Dependencies: 290
-- Name: app_calcu_month_traffic_info_histories_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_month_traffic_info_histories_ogc_fid_seq', 1128, true);


--
-- TOC entry 5299 (class 0 OID 0)
-- Dependencies: 291
-- Name: app_calcu_monthly_socl_welfare_people_ppl_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_monthly_socl_welfare_people_ppl_seq', 247, true);


--
-- TOC entry 5300 (class 0 OID 0)
-- Dependencies: 293
-- Name: app_calcu_patrol_rainfall_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_patrol_rainfall_ogc_fid_seq', 612676, true);


--
-- TOC entry 5301 (class 0 OID 0)
-- Dependencies: 294
-- Name: app_calcu_sentiment_dispatch_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_sentiment_dispatch_ogc_fid_seq', 1, true);


--
-- TOC entry 5302 (class 0 OID 0)
-- Dependencies: 295
-- Name: app_calcu_traffic_todaywork_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_traffic_todaywork_ogc_fid_seq', 4690, true);


--
-- TOC entry 5303 (class 0 OID 0)
-- Dependencies: 296
-- Name: app_calcu_weekly_dispatching_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_weekly_dispatching_ogc_fid_seq', 8615, true);


--
-- TOC entry 5304 (class 0 OID 0)
-- Dependencies: 297
-- Name: app_calcu_weekly_hellotaipei_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_weekly_hellotaipei_ogc_fid_seq', 35582, true);


--
-- TOC entry 5305 (class 0 OID 0)
-- Dependencies: 298
-- Name: app_calcu_weekly_metro_capacity_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_weekly_metro_capacity_ogc_fid_seq', 1, true);


--
-- TOC entry 5306 (class 0 OID 0)
-- Dependencies: 299
-- Name: app_calcu_weekly_metro_capacity_threshould_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcu_weekly_metro_capacity_threshould_ogc_fid_seq', 1937419, true);


--
-- TOC entry 5307 (class 0 OID 0)
-- Dependencies: 300
-- Name: app_calcul_weekly_hellotaipei_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_calcul_weekly_hellotaipei_ogc_fid_seq', 50276, true);


--
-- TOC entry 5308 (class 0 OID 0)
-- Dependencies: 301
-- Name: app_traffic_lives_accident_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_traffic_lives_accident_ogc_fid_seq', 223, true);


--
-- TOC entry 5309 (class 0 OID 0)
-- Dependencies: 302
-- Name: app_traffic_metro_capacity_realtime_stat_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_traffic_metro_capacity_realtime_stat_ogc_fid_seq', 391928384, true);


--
-- TOC entry 5310 (class 0 OID 0)
-- Dependencies: 303
-- Name: building_age_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_age_ogc_fid_seq', 258569, true);


--
-- TOC entry 5311 (class 0 OID 0)
-- Dependencies: 304
-- Name: building_cadastralmap_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_cadastralmap_ogc_fid_seq', 3438485, true);


--
-- TOC entry 5312 (class 0 OID 0)
-- Dependencies: 305
-- Name: building_landuse_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_landuse_ogc_fid_seq', 1, true);


--
-- TOC entry 5313 (class 0 OID 0)
-- Dependencies: 306
-- Name: building_license_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_license_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5314 (class 0 OID 0)
-- Dependencies: 307
-- Name: building_license_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_license_ogc_fid_seq', 1, true);


--
-- TOC entry 5315 (class 0 OID 0)
-- Dependencies: 308
-- Name: building_permit_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_permit_history_ogc_fid_seq', 14018365, true);


--
-- TOC entry 5316 (class 0 OID 0)
-- Dependencies: 309
-- Name: building_permit_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_permit_ogc_fid_seq', 869836, true);


--
-- TOC entry 5317 (class 0 OID 0)
-- Dependencies: 310
-- Name: building_publand_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_publand_history_ogc_fid_seq', 1259841, true);


--
-- TOC entry 5318 (class 0 OID 0)
-- Dependencies: 311
-- Name: building_publand_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_publand_ogc_fid_seq', 31804304, true);


--
-- TOC entry 5319 (class 0 OID 0)
-- Dependencies: 312
-- Name: building_renewarea_10_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewarea_10_history_ogc_fid_seq', 136717, true);


--
-- TOC entry 5320 (class 0 OID 0)
-- Dependencies: 313
-- Name: building_renewarea_10_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewarea_10_ogc_fid_seq', 131927, true);


--
-- TOC entry 5321 (class 0 OID 0)
-- Dependencies: 314
-- Name: building_renewarea_40_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewarea_40_history_ogc_fid_seq', 33825, true);


--
-- TOC entry 5322 (class 0 OID 0)
-- Dependencies: 315
-- Name: building_renewarea_40_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewarea_40_ogc_fid_seq', 33105, true);


--
-- TOC entry 5323 (class 0 OID 0)
-- Dependencies: 316
-- Name: building_renewunit_12_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_12_history_ogc_fid_seq', 407217, true);


--
-- TOC entry 5324 (class 0 OID 0)
-- Dependencies: 317
-- Name: building_renewunit_12_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_12_ogc_fid_seq', 392433, true);


--
-- TOC entry 5325 (class 0 OID 0)
-- Dependencies: 318
-- Name: building_renewunit_20_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_20_history_ogc_fid_seq', 16936, true);


--
-- TOC entry 5326 (class 0 OID 0)
-- Dependencies: 319
-- Name: building_renewunit_20_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_20_ogc_fid_seq', 4088, true);


--
-- TOC entry 5327 (class 0 OID 0)
-- Dependencies: 320
-- Name: building_renewunit_30_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_30_history_ogc_fid_seq', 51238740, true);


--
-- TOC entry 5328 (class 0 OID 0)
-- Dependencies: 321
-- Name: building_renewunit_30_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_renewunit_30_ogc_fid_seq', 51190290, true);


--
-- TOC entry 5329 (class 0 OID 0)
-- Dependencies: 322
-- Name: building_social_house_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_social_house_history_ogc_fid_seq', 46646, true);


--
-- TOC entry 5330 (class 0 OID 0)
-- Dependencies: 323
-- Name: building_social_house_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_social_house_ogc_fid_seq', 41822, true);


--
-- TOC entry 5331 (class 0 OID 0)
-- Dependencies: 326
-- Name: building_unsued_land_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_land_history_ogc_fid_seq', 19384, true);


--
-- TOC entry 5332 (class 0 OID 0)
-- Dependencies: 324
-- Name: building_unsued_land_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_land_ogc_fid_seq', 19429, true);


--
-- TOC entry 5333 (class 0 OID 0)
-- Dependencies: 327
-- Name: building_unsued_nonpublic_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_nonpublic_history_ogc_fid_seq', 2464, true);


--
-- TOC entry 5334 (class 0 OID 0)
-- Dependencies: 328
-- Name: building_unsued_nonpublic_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_nonpublic_ogc_fid_seq', 2452, true);


--
-- TOC entry 5335 (class 0 OID 0)
-- Dependencies: 330
-- Name: building_unsued_public_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_public_history_ogc_fid_seq', 20418, true);


--
-- TOC entry 5336 (class 0 OID 0)
-- Dependencies: 331
-- Name: building_unsued_public_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.building_unsued_public_ogc_fid_seq', 19, true);


--
-- TOC entry 5337 (class 0 OID 0)
-- Dependencies: 332
-- Name: cvil_public_opinion_evn_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cvil_public_opinion_evn_ogc_fid_seq', 8501, true);


--
-- TOC entry 5338 (class 0 OID 0)
-- Dependencies: 333
-- Name: cvil_public_opinion_maintype_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cvil_public_opinion_maintype_ogc_fid_seq', 8, true);


--
-- TOC entry 5339 (class 0 OID 0)
-- Dependencies: 334
-- Name: cvil_public_opinion_subtype_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cvil_public_opinion_subtype_ogc_fid_seq', 41, true);


--
-- TOC entry 5340 (class 0 OID 0)
-- Dependencies: 335
-- Name: cwb_city_weather_forecast_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_city_weather_forecast_history_ogc_fid_seq', 234168, true);


--
-- TOC entry 5341 (class 0 OID 0)
-- Dependencies: 336
-- Name: cwb_city_weather_forecast_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_city_weather_forecast_ogc_fid_seq', 234168, true);


--
-- TOC entry 5342 (class 0 OID 0)
-- Dependencies: 337
-- Name: cwb_daily_weather_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_daily_weather_ogc_fid_seq', 653280, true);


--
-- TOC entry 5343 (class 0 OID 0)
-- Dependencies: 338
-- Name: cwb_hourly_weather_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_hourly_weather_ogc_fid_seq', 15256546, true);


--
-- TOC entry 5344 (class 0 OID 0)
-- Dependencies: 339
-- Name: cwb_now_weather_auto_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_now_weather_auto_station_history_ogc_fid_seq', 2533563, true);


--
-- TOC entry 5345 (class 0 OID 0)
-- Dependencies: 340
-- Name: cwb_now_weather_auto_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_now_weather_auto_station_ogc_fid_seq', 2533563, true);


--
-- TOC entry 5346 (class 0 OID 0)
-- Dependencies: 341
-- Name: cwb_now_weather_bureau_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_now_weather_bureau_station_history_ogc_fid_seq', 1387607, true);


--
-- TOC entry 5347 (class 0 OID 0)
-- Dependencies: 342
-- Name: cwb_now_weather_bureau_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_now_weather_bureau_station_ogc_fid_seq', 1387607, true);


--
-- TOC entry 5348 (class 0 OID 0)
-- Dependencies: 343
-- Name: cwb_rainfall_station_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_rainfall_station_location_history_ogc_fid_seq', 25222, true);


--
-- TOC entry 5349 (class 0 OID 0)
-- Dependencies: 344
-- Name: cwb_rainfall_station_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_rainfall_station_location_ogc_fid_seq', 25222, true);


--
-- TOC entry 5350 (class 0 OID 0)
-- Dependencies: 345
-- Name: cwb_town_weather_forecast_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_town_weather_forecast_history_ogc_fid_seq', 258050, true);


--
-- TOC entry 5351 (class 0 OID 0)
-- Dependencies: 346
-- Name: cwb_town_weather_forecast_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cwb_town_weather_forecast_ogc_fid_seq', 241344, true);


--
-- TOC entry 5352 (class 0 OID 0)
-- Dependencies: 347
-- Name: edu_elementary_school_district_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_elementary_school_district_history_ogc_fid_seq', 1584, true);


--
-- TOC entry 5353 (class 0 OID 0)
-- Dependencies: 348
-- Name: edu_elementary_school_district_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_elementary_school_district_ogc_fid_seq', 1584, true);


--
-- TOC entry 5354 (class 0 OID 0)
-- Dependencies: 349
-- Name: edu_eleschool_dist_by_administrative_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_eleschool_dist_by_administrative_history_ogc_fid_seq', 6147, true);


--
-- TOC entry 5355 (class 0 OID 0)
-- Dependencies: 350
-- Name: edu_eleschool_dist_by_administrative_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_eleschool_dist_by_administrative_ogc_fid_seq', 6147, true);


--
-- TOC entry 5356 (class 0 OID 0)
-- Dependencies: 351
-- Name: edu_jhschool_dist_by_administrative_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_jhschool_dist_by_administrative_history_ogc_fid_seq', 5380, true);


--
-- TOC entry 5357 (class 0 OID 0)
-- Dependencies: 352
-- Name: edu_jhschool_dist_by_administrative_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_jhschool_dist_by_administrative_ogc_fid_seq', 5380, true);


--
-- TOC entry 5358 (class 0 OID 0)
-- Dependencies: 353
-- Name: edu_junior_high_school_district_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_junior_high_school_district_history_ogc_fid_seq', 891, true);


--
-- TOC entry 5359 (class 0 OID 0)
-- Dependencies: 354
-- Name: edu_junior_high_school_district_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_junior_high_school_district_ogc_fid_seq', 891, true);


--
-- TOC entry 5360 (class 0 OID 0)
-- Dependencies: 355
-- Name: edu_school_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_school_history_ogc_fid_seq', 5704, true);


--
-- TOC entry 5361 (class 0 OID 0)
-- Dependencies: 356
-- Name: edu_school_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_school_ogc_fid_seq', 5704, true);


--
-- TOC entry 5362 (class 0 OID 0)
-- Dependencies: 357
-- Name: edu_school_romm_status_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_school_romm_status_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5363 (class 0 OID 0)
-- Dependencies: 358
-- Name: edu_school_romm_status_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edu_school_romm_status_ogc_fid_seq', 1, true);


--
-- TOC entry 5364 (class 0 OID 0)
-- Dependencies: 359
-- Name: eoc_accommodate_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_accommodate_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5365 (class 0 OID 0)
-- Dependencies: 360
-- Name: eoc_accommodate_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_accommodate_ogc_fid_seq', 1, true);


--
-- TOC entry 5366 (class 0 OID 0)
-- Dependencies: 361
-- Name: eoc_disaster_case_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_disaster_case_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5367 (class 0 OID 0)
-- Dependencies: 362
-- Name: eoc_disaster_case_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_disaster_case_ogc_fid_seq', 1, true);


--
-- TOC entry 5368 (class 0 OID 0)
-- Dependencies: 363
-- Name: eoc_leave_house_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_leave_house_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5369 (class 0 OID 0)
-- Dependencies: 364
-- Name: eoc_leave_house_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.eoc_leave_house_ogc_fid_seq', 1, true);


--
-- TOC entry 5370 (class 0 OID 0)
-- Dependencies: 365
-- Name: ethc_building_check_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ethc_building_check_ogc_fid_seq', 25135, true);


--
-- TOC entry 5371 (class 0 OID 0)
-- Dependencies: 366
-- Name: ethc_check_calcu_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ethc_check_calcu_ogc_fid_seq', 9685, true);


--
-- TOC entry 5372 (class 0 OID 0)
-- Dependencies: 367
-- Name: ethc_check_summary_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ethc_check_summary_ogc_fid_seq', 651, true);


--
-- TOC entry 5373 (class 0 OID 0)
-- Dependencies: 368
-- Name: ethc_fire_check_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ethc_fire_check_ogc_fid_seq', 9385, true);


--
-- TOC entry 5374 (class 0 OID 0)
-- Dependencies: 369
-- Name: fire_hydrant_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.fire_hydrant_location_history_ogc_fid_seq', 29966, true);


--
-- TOC entry 5375 (class 0 OID 0)
-- Dependencies: 370
-- Name: fire_hydrant_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.fire_hydrant_location_ogc_fid_seq', 1, true);


--
-- TOC entry 5376 (class 0 OID 0)
-- Dependencies: 371
-- Name: fire_to_hospital_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.fire_to_hospital_ppl_ogc_fid_seq', 2519111, true);


--
-- TOC entry 5377 (class 0 OID 0)
-- Dependencies: 372
-- Name: heal_aed_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_aed_history_ogc_fid_seq', 25751, true);


--
-- TOC entry 5378 (class 0 OID 0)
-- Dependencies: 373
-- Name: heal_aed_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_aed_ogc_fid_seq', 25751, true);


--
-- TOC entry 5379 (class 0 OID 0)
-- Dependencies: 374
-- Name: heal_clinic_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_clinic_history_ogc_fid_seq', 39851, true);


--
-- TOC entry 5380 (class 0 OID 0)
-- Dependencies: 375
-- Name: heal_clinic_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_clinic_ogc_fid_seq', 39851, true);


--
-- TOC entry 5381 (class 0 OID 0)
-- Dependencies: 376
-- Name: heal_hospital_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_hospital_history_ogc_fid_seq', 380, true);


--
-- TOC entry 5382 (class 0 OID 0)
-- Dependencies: 377
-- Name: heal_hospital_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_hospital_ogc_fid_seq', 380, true);


--
-- TOC entry 5383 (class 0 OID 0)
-- Dependencies: 378
-- Name: heal_suicide_evn_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.heal_suicide_evn_ogc_fid_seq', 7091, true);


--
-- TOC entry 5384 (class 0 OID 0)
-- Dependencies: 379
-- Name: it_5G_smart_pole_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."it_5G_smart_pole_ogc_fid_seq"', 1, true);


--
-- TOC entry 5385 (class 0 OID 0)
-- Dependencies: 380
-- Name: it_5g_smart_all_pole_device_log_history_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_5g_smart_all_pole_device_log_history_seq', 6783542, true);


--
-- TOC entry 5386 (class 0 OID 0)
-- Dependencies: 381
-- Name: it_5g_smart_all_pole_device_log_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_5g_smart_all_pole_device_log_ogc_fid_seq', 9384108, true);


--
-- TOC entry 5387 (class 0 OID 0)
-- Dependencies: 382
-- Name: it_5g_smart_all_pole_log_history_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_5g_smart_all_pole_log_history_seq', 644, true);


--
-- TOC entry 5388 (class 0 OID 0)
-- Dependencies: 383
-- Name: it_5g_smart_all_pole_log_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_5g_smart_all_pole_log_seq', 644, true);


--
-- TOC entry 5389 (class 0 OID 0)
-- Dependencies: 384
-- Name: it_5g_smart_pole_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_5g_smart_pole_ogc_fid_seq', 6893026, true);


--
-- TOC entry 5390 (class 0 OID 0)
-- Dependencies: 385
-- Name: it_signal_population_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_signal_population_history_ogc_fid_seq', 6078536, true);


--
-- TOC entry 5391 (class 0 OID 0)
-- Dependencies: 386
-- Name: it_signal_population_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_signal_population_ogc_fid_seq', 6078536, true);


--
-- TOC entry 5392 (class 0 OID 0)
-- Dependencies: 387
-- Name: it_signal_tourist_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_signal_tourist_history_ogc_fid_seq', 16738, true);


--
-- TOC entry 5393 (class 0 OID 0)
-- Dependencies: 388
-- Name: it_signal_tourist_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_signal_tourist_ogc_fid_seq', 16720, true);


--
-- TOC entry 5394 (class 0 OID 0)
-- Dependencies: 389
-- Name: it_taipeiexpo_people_flow_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_taipeiexpo_people_flow_history_ogc_fid_seq', 4314, true);


--
-- TOC entry 5395 (class 0 OID 0)
-- Dependencies: 390
-- Name: it_taipeiexpo_people_flow_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_taipeiexpo_people_flow_ogc_fid_seq', 4314, true);


--
-- TOC entry 5396 (class 0 OID 0)
-- Dependencies: 391
-- Name: it_tpe_ticket_event_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpe_ticket_event_ogc_fid_seq', 26437, true);


--
-- TOC entry 5397 (class 0 OID 0)
-- Dependencies: 392
-- Name: it_tpe_ticket_member_hold_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpe_ticket_member_hold_ogc_fid_seq', 110050, true);


--
-- TOC entry 5398 (class 0 OID 0)
-- Dependencies: 393
-- Name: it_tpe_ticket_place_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpe_ticket_place_ogc_fid_seq', 10702, true);


--
-- TOC entry 5399 (class 0 OID 0)
-- Dependencies: 394
-- Name: it_tpe_ticket_ticket_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpe_ticket_ticket_ogc_fid_seq', 12670, true);


--
-- TOC entry 5400 (class 0 OID 0)
-- Dependencies: 395
-- Name: it_tpefree_daily_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_daily_history_ogc_fid_seq', 6478334, true);


--
-- TOC entry 5401 (class 0 OID 0)
-- Dependencies: 396
-- Name: it_tpefree_daily_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_daily_ogc_fid_seq', 100814877, true);


--
-- TOC entry 5402 (class 0 OID 0)
-- Dependencies: 397
-- Name: it_tpefree_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_location_history_ogc_fid_seq', 3802, true);


--
-- TOC entry 5403 (class 0 OID 0)
-- Dependencies: 398
-- Name: it_tpefree_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_location_ogc_fid_seq', 4142, true);


--
-- TOC entry 5404 (class 0 OID 0)
-- Dependencies: 399
-- Name: it_tpefree_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_realtime_history_ogc_fid_seq', 50558539, true);


--
-- TOC entry 5405 (class 0 OID 0)
-- Dependencies: 400
-- Name: it_tpefree_realtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpefree_realtime_ogc_fid_seq', 92942265, true);


--
-- TOC entry 5406 (class 0 OID 0)
-- Dependencies: 401
-- Name: it_tpmo_poc_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpmo_poc_location_history_ogc_fid_seq', 31968, true);


--
-- TOC entry 5407 (class 0 OID 0)
-- Dependencies: 402
-- Name: it_tpmo_poc_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_tpmo_poc_location_ogc_fid_seq', 31968, true);


--
-- TOC entry 5408 (class 0 OID 0)
-- Dependencies: 403
-- Name: it_venue_people_flow_history_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_venue_people_flow_history_seq', 647366, true);


--
-- TOC entry 5409 (class 0 OID 0)
-- Dependencies: 404
-- Name: it_venue_people_flow_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.it_venue_people_flow_ogc_fid_seq', 1, true);


--
-- TOC entry 5410 (class 0 OID 0)
-- Dependencies: 405
-- Name: mrtp_carweight_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.mrtp_carweight_history_ogc_fid_seq', 7475523, true);


--
-- TOC entry 5411 (class 0 OID 0)
-- Dependencies: 406
-- Name: mrtp_carweight_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.mrtp_carweight_ogc_fid_seq', 7475523, true);


--
-- TOC entry 5412 (class 0 OID 0)
-- Dependencies: 407
-- Name: patrol_artificial_slope_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_artificial_slope_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5413 (class 0 OID 0)
-- Dependencies: 408
-- Name: patrol_artificial_slope_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_artificial_slope_ogc_fid_seq', 383867, true);


--
-- TOC entry 5414 (class 0 OID 0)
-- Dependencies: 409
-- Name: patrol_box_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_box_ogc_fid_seq', 18491, true);


--
-- TOC entry 5415 (class 0 OID 0)
-- Dependencies: 410
-- Name: patrol_camera_hls_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_camera_hls_ogc_fid_seq', 1717, true);


--
-- TOC entry 5416 (class 0 OID 0)
-- Dependencies: 411
-- Name: patrol_car_theft_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_car_theft_ogc_fid_seq', 518, true);


--
-- TOC entry 5417 (class 0 OID 0)
-- Dependencies: 412
-- Name: patrol_criminal_case_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_criminal_case_ogc_fid_seq', 30376, true);


--
-- TOC entry 5418 (class 0 OID 0)
-- Dependencies: 414
-- Name: patrol_debris_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_debris_history_ogc_fid_seq', 24204, true);


--
-- TOC entry 5419 (class 0 OID 0)
-- Dependencies: 415
-- Name: patrol_debris_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_debris_ogc_fid_seq', 1726, true);


--
-- TOC entry 5420 (class 0 OID 0)
-- Dependencies: 416
-- Name: patrol_debrisarea_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_debrisarea_history_ogc_fid_seq', 20521, true);


--
-- TOC entry 5421 (class 0 OID 0)
-- Dependencies: 417
-- Name: patrol_debrisarea_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_debrisarea_ogc_fid_seq', 22384, true);


--
-- TOC entry 5422 (class 0 OID 0)
-- Dependencies: 418
-- Name: patrol_designate_place_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_designate_place_history_ogc_fid_seq', 103170, true);


--
-- TOC entry 5423 (class 0 OID 0)
-- Dependencies: 419
-- Name: patrol_designate_place_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_designate_place_ogc_fid_seq', 103748, true);


--
-- TOC entry 5424 (class 0 OID 0)
-- Dependencies: 420
-- Name: patrol_district_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_district_ogc_fid_seq', 90, true);


--
-- TOC entry 5425 (class 0 OID 0)
-- Dependencies: 421
-- Name: patrol_eoc_case_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_eoc_case_history_ogc_fid_seq', 10132, true);


--
-- TOC entry 5426 (class 0 OID 0)
-- Dependencies: 422
-- Name: patrol_eoc_case_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_eoc_case_ogc_fid_seq', 9321, true);


--
-- TOC entry 5427 (class 0 OID 0)
-- Dependencies: 423
-- Name: patrol_eoc_designate_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_eoc_designate_history_ogc_fid_seq', 1066, true);


--
-- TOC entry 5428 (class 0 OID 0)
-- Dependencies: 424
-- Name: patrol_eoc_designate_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_eoc_designate_ogc_fid_seq', 1066, true);


--
-- TOC entry 5429 (class 0 OID 0)
-- Dependencies: 425
-- Name: patrol_fire_brigade_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_brigade_history_ogc_fid_seq', 19090, true);


--
-- TOC entry 5430 (class 0 OID 0)
-- Dependencies: 426
-- Name: patrol_fire_brigade_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_brigade_ogc_fid_seq', 19136, true);


--
-- TOC entry 5431 (class 0 OID 0)
-- Dependencies: 427
-- Name: patrol_fire_disqualified_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_disqualified_history_ogc_fid_seq', 7815, true);


--
-- TOC entry 5432 (class 0 OID 0)
-- Dependencies: 428
-- Name: patrol_fire_disqualified_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_disqualified_ogc_fid_seq', 7778, true);


--
-- TOC entry 5433 (class 0 OID 0)
-- Dependencies: 429
-- Name: patrol_fire_rescure_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_rescure_history_ogc_fid_seq', 416367, true);


--
-- TOC entry 5434 (class 0 OID 0)
-- Dependencies: 430
-- Name: patrol_fire_rescure_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_fire_rescure_ogc_fid_seq', 415225, true);


--
-- TOC entry 5435 (class 0 OID 0)
-- Dependencies: 431
-- Name: patrol_flood_100_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_flood_100_ogc_fid_seq', 3, true);


--
-- TOC entry 5436 (class 0 OID 0)
-- Dependencies: 432
-- Name: patrol_flood_130_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_flood_130_ogc_fid_seq', 3, true);


--
-- TOC entry 5437 (class 0 OID 0)
-- Dependencies: 433
-- Name: patrol_flood_78_8_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_flood_78_8_ogc_fid_seq', 3, true);


--
-- TOC entry 5438 (class 0 OID 0)
-- Dependencies: 434
-- Name: patrol_motorcycle_theft_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_motorcycle_theft_ogc_fid_seq', 702, true);


--
-- TOC entry 5439 (class 0 OID 0)
-- Dependencies: 435
-- Name: patrol_old_settlement_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_old_settlement_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5440 (class 0 OID 0)
-- Dependencies: 436
-- Name: patrol_old_settlement_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_old_settlement_ogc_fid_seq', 340, true);


--
-- TOC entry 5441 (class 0 OID 0)
-- Dependencies: 437
-- Name: patrol_police_region_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_police_region_ogc_fid_seq', 90, true);


--
-- TOC entry 5442 (class 0 OID 0)
-- Dependencies: 438
-- Name: patrol_police_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_police_station_history_ogc_fid_seq', 15488, true);


--
-- TOC entry 5443 (class 0 OID 0)
-- Dependencies: 439
-- Name: patrol_police_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_police_station_ogc_fid_seq', 215783, true);


--
-- TOC entry 5444 (class 0 OID 0)
-- Dependencies: 440
-- Name: patrol_police_station_ogc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_police_station_ogc_id_seq', 1, true);


--
-- TOC entry 5445 (class 0 OID 0)
-- Dependencies: 443
-- Name: patrol_rain_floodgate_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_floodgate_history_ogc_fid_seq', 3784767, true);


--
-- TOC entry 5446 (class 0 OID 0)
-- Dependencies: 441
-- Name: patrol_rain_floodgate_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_floodgate_ogc_fid_seq', 3776990, true);


--
-- TOC entry 5447 (class 0 OID 0)
-- Dependencies: 444
-- Name: patrol_rain_rainfall_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_rainfall_history_ogc_fid_seq', 15653401, true);


--
-- TOC entry 5448 (class 0 OID 0)
-- Dependencies: 445
-- Name: patrol_rain_rainfall_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_rainfall_ogc_fid_seq', 13849310, true);


--
-- TOC entry 5449 (class 0 OID 0)
-- Dependencies: 446
-- Name: patrol_rain_sewer_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_sewer_history_ogc_fid_seq', 8206620, true);


--
-- TOC entry 5450 (class 0 OID 0)
-- Dependencies: 447
-- Name: patrol_rain_sewer_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_sewer_ogc_fid_seq', 7905081, true);


--
-- TOC entry 5451 (class 0 OID 0)
-- Dependencies: 448
-- Name: patrol_rain_sewer_ogc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_rain_sewer_ogc_id_seq', 1, true);


--
-- TOC entry 5452 (class 0 OID 0)
-- Dependencies: 449
-- Name: patrol_random_robber_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_random_robber_ogc_fid_seq', 20, true);


--
-- TOC entry 5453 (class 0 OID 0)
-- Dependencies: 450
-- Name: patrol_random_snatch_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_random_snatch_ogc_fid_seq', 31, true);


--
-- TOC entry 5454 (class 0 OID 0)
-- Dependencies: 451
-- Name: patrol_residential_burglary_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.patrol_residential_burglary_ogc_fid_seq', 3231, true);


--
-- TOC entry 5455 (class 0 OID 0)
-- Dependencies: 452
-- Name: poli_traffic_violation_evn_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.poli_traffic_violation_evn_ogc_fid_seq', 1331036, true);


--
-- TOC entry 5456 (class 0 OID 0)
-- Dependencies: 453
-- Name: poli_traffic_violation_mapping_code_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.poli_traffic_violation_mapping_code_ogc_fid_seq', 6, true);


--
-- TOC entry 5457 (class 0 OID 0)
-- Dependencies: 454
-- Name: record_db_mtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.record_db_mtime_ogc_fid_seq', 227, true);


--
-- TOC entry 5458 (class 0 OID 0)
-- Dependencies: 455
-- Name: sentiment_councillor_109_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_councillor_109_ogc_fid_seq', 8645017, true);


--
-- TOC entry 5459 (class 0 OID 0)
-- Dependencies: 456
-- Name: sentiment_dispatching_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_dispatching_ogc_fid_seq', 2354258, true);


--
-- TOC entry 5460 (class 0 OID 0)
-- Dependencies: 457
-- Name: sentiment_hello_taipei_109_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_hello_taipei_109_ogc_fid_seq', 841010535, true);


--
-- TOC entry 5461 (class 0 OID 0)
-- Dependencies: 458
-- Name: sentiment_hello_taipei_109_test_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_hello_taipei_109_test_ogc_fid_seq', 9601315, true);


--
-- TOC entry 5462 (class 0 OID 0)
-- Dependencies: 459
-- Name: sentiment_hotnews_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_hotnews_ogc_fid_seq', 2147485712, true);


--
-- TOC entry 5463 (class 0 OID 0)
-- Dependencies: 460
-- Name: sentiment_voice1999_109_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sentiment_voice1999_109_ogc_fid_seq', 38542042, true);


--
-- TOC entry 5464 (class 0 OID 0)
-- Dependencies: 461
-- Name: socl_case_study_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_case_study_ppl_ogc_fid_seq', 210, true);


--
-- TOC entry 5465 (class 0 OID 0)
-- Dependencies: 462
-- Name: socl_dept_epidemic_info_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_dept_epidemic_info_ogc_fid_seq', 15600, true);


--
-- TOC entry 5466 (class 0 OID 0)
-- Dependencies: 463
-- Name: socl_domestic_violence_evn_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_domestic_violence_evn_ogc_fid_seq', 28494, true);


--
-- TOC entry 5467 (class 0 OID 0)
-- Dependencies: 464
-- Name: socl_export_filter_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_export_filter_ppl_ogc_fid_seq', 1186, true);


--
-- TOC entry 5468 (class 0 OID 0)
-- Dependencies: 465
-- Name: socl_order_concern_mapping_code_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_order_concern_mapping_code_ogc_fid_seq', 42, true);


--
-- TOC entry 5469 (class 0 OID 0)
-- Dependencies: 466
-- Name: socl_order_concern_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_order_concern_ppl_ogc_fid_seq', 270588, true);


--
-- TOC entry 5470 (class 0 OID 0)
-- Dependencies: 467
-- Name: socl_welfare_dis_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_dis_history_ogc_fid_seq', 2232259, true);


--
-- TOC entry 5471 (class 0 OID 0)
-- Dependencies: 468
-- Name: socl_welfare_dis_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_dis_ogc_fid_seq', 9490987, true);


--
-- TOC entry 5472 (class 0 OID 0)
-- Dependencies: 469
-- Name: socl_welfare_dislow_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_dislow_history_ogc_fid_seq', 90324, true);


--
-- TOC entry 5473 (class 0 OID 0)
-- Dependencies: 470
-- Name: socl_welfare_dislow_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_dislow_ogc_fid_seq', 158138, true);


--
-- TOC entry 5474 (class 0 OID 0)
-- Dependencies: 471
-- Name: socl_welfare_low_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_low_history_ogc_fid_seq', 711436, true);


--
-- TOC entry 5475 (class 0 OID 0)
-- Dependencies: 472
-- Name: socl_welfare_low_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_low_ogc_fid_seq', 1254473, true);


--
-- TOC entry 5476 (class 0 OID 0)
-- Dependencies: 473
-- Name: socl_welfare_midlow_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_midlow_history_ogc_fid_seq', 248365, true);


--
-- TOC entry 5477 (class 0 OID 0)
-- Dependencies: 474
-- Name: socl_welfare_midlow_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_midlow_ogc_fid_seq', 432236, true);


--
-- TOC entry 5478 (class 0 OID 0)
-- Dependencies: 477
-- Name: socl_welfare_organization_plc_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_organization_plc_history_ogc_fid_seq', 15277, true);


--
-- TOC entry 5479 (class 0 OID 0)
-- Dependencies: 475
-- Name: socl_welfare_organization_plc_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_organization_plc_ogc_fid_seq', 11588, true);


--
-- TOC entry 5480 (class 0 OID 0)
-- Dependencies: 478
-- Name: socl_welfare_people_ppl_history_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_people_ppl_history_seq', 2906301, true);


--
-- TOC entry 5481 (class 0 OID 0)
-- Dependencies: 479
-- Name: socl_welfare_people_ppl_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socl_welfare_people_ppl_ogc_fid_seq', 3626525, true);


--
-- TOC entry 5482 (class 0 OID 0)
-- Dependencies: 480
-- Name: tdx_bus_live_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_bus_live_ogc_fid_seq', 413748703, true);


--
-- TOC entry 5483 (class 0 OID 0)
-- Dependencies: 481
-- Name: tdx_bus_route_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_bus_route_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5484 (class 0 OID 0)
-- Dependencies: 482
-- Name: tdx_bus_route_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_bus_route_ogc_fid_seq', 764, true);


--
-- TOC entry 5485 (class 0 OID 0)
-- Dependencies: 483
-- Name: tdx_bus_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_bus_station_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5486 (class 0 OID 0)
-- Dependencies: 484
-- Name: tdx_bus_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_bus_station_ogc_fid_seq', 1, true);


--
-- TOC entry 5487 (class 0 OID 0)
-- Dependencies: 485
-- Name: tdx_metro_line_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_metro_line_ogc_fid_seq', 1, true);


--
-- TOC entry 5488 (class 0 OID 0)
-- Dependencies: 486
-- Name: tdx_metro_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tdx_metro_station_ogc_fid_seq', 1, true);


--
-- TOC entry 5489 (class 0 OID 0)
-- Dependencies: 487
-- Name: tour_2023_lantern_festival_mapping_table_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tour_2023_lantern_festival_mapping_table_ogc_fid_seq', 9873, true);


--
-- TOC entry 5490 (class 0 OID 0)
-- Dependencies: 488
-- Name: tour_2023_lantern_festival_zone_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tour_2023_lantern_festival_zone_ogc_fid_seq', 1289, true);


--
-- TOC entry 5491 (class 0 OID 0)
-- Dependencies: 489
-- Name: tour_2023_latern_festival_mapping_table_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tour_2023_latern_festival_mapping_table_ogc_fid_seq', 1036, true);


--
-- TOC entry 5492 (class 0 OID 0)
-- Dependencies: 490
-- Name: tour_2023_latern_festival_point_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tour_2023_latern_festival_point_ogc_fid_seq', 463, true);


--
-- TOC entry 5493 (class 0 OID 0)
-- Dependencies: 491
-- Name: tour_lantern_festival_sysmemorialhall_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tour_lantern_festival_sysmemorialhall_ogc_fid_seq', 21940, true);


--
-- TOC entry 5494 (class 0 OID 0)
-- Dependencies: 492
-- Name: tp_building_bim_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_building_bim_ogc_fid_seq', 124557, true);


--
-- TOC entry 5495 (class 0 OID 0)
-- Dependencies: 493
-- Name: tp_building_height_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_building_height_ogc_fid_seq', 373532, true);


--
-- TOC entry 5496 (class 0 OID 0)
-- Dependencies: 494
-- Name: tp_cht_grid_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_cht_grid_ogc_fid_seq', 1, true);


--
-- TOC entry 5497 (class 0 OID 0)
-- Dependencies: 495
-- Name: tp_district_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_district_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5498 (class 0 OID 0)
-- Dependencies: 496
-- Name: tp_fet_age_hr_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_fet_age_hr_ogc_fid_seq', 76311, true);


--
-- TOC entry 5499 (class 0 OID 0)
-- Dependencies: 497
-- Name: tp_fet_hourly_popu_by_vil_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_fet_hourly_popu_by_vil_ogc_fid_seq', 2147052, true);


--
-- TOC entry 5500 (class 0 OID 0)
-- Dependencies: 498
-- Name: tp_fet_work_live_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_fet_work_live_ogc_fid_seq', 3329, true);


--
-- TOC entry 5501 (class 0 OID 0)
-- Dependencies: 499
-- Name: tp_road_center_line_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_road_center_line_ogc_fid_seq', 42483, true);


--
-- TOC entry 5502 (class 0 OID 0)
-- Dependencies: 500
-- Name: tp_village_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_village_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5503 (class 0 OID 0)
-- Dependencies: 501
-- Name: tp_village_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tp_village_ogc_fid_seq', 7752, true);


--
-- TOC entry 5504 (class 0 OID 0)
-- Dependencies: 502
-- Name: traffic_accident_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_accident_location_ogc_fid_seq', 14617253, true);


--
-- TOC entry 5505 (class 0 OID 0)
-- Dependencies: 503
-- Name: traffic_accident_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_accident_ogc_fid_seq', 626605, true);


--
-- TOC entry 5506 (class 0 OID 0)
-- Dependencies: 504
-- Name: traffic_bus_route_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_bus_route_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5507 (class 0 OID 0)
-- Dependencies: 505
-- Name: traffic_bus_route_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_bus_route_ogc_fid_seq', 382, true);


--
-- TOC entry 5508 (class 0 OID 0)
-- Dependencies: 506
-- Name: traffic_bus_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_bus_station_history_ogc_fid_seq', 281151, true);


--
-- TOC entry 5509 (class 0 OID 0)
-- Dependencies: 507
-- Name: traffic_bus_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_bus_station_ogc_fid_seq', 191699, true);


--
-- TOC entry 5510 (class 0 OID 0)
-- Dependencies: 508
-- Name: traffic_bus_stop_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_bus_stop_ogc_fid_seq', 14574913, true);


--
-- TOC entry 5511 (class 0 OID 0)
-- Dependencies: 509
-- Name: traffic_info_histories_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_info_histories_ogc_fid_seq', 1, true);


--
-- TOC entry 5512 (class 0 OID 0)
-- Dependencies: 510
-- Name: traffic_lives_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_lives_history_ogc_fid_seq', 39323006, true);


--
-- TOC entry 5513 (class 0 OID 0)
-- Dependencies: 511
-- Name: traffic_lives_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_lives_ogc_fid_seq', 39327120, true);


--
-- TOC entry 5514 (class 0 OID 0)
-- Dependencies: 512
-- Name: traffic_metro_capacity_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_capacity_realtime_history_ogc_fid_seq', 14664414, true);


--
-- TOC entry 5515 (class 0 OID 0)
-- Dependencies: 513
-- Name: traffic_metro_capacity_realtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_capacity_realtime_ogc_fid_seq', 15176475, true);


--
-- TOC entry 5516 (class 0 OID 0)
-- Dependencies: 514
-- Name: traffic_metro_capacity_rtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_capacity_rtime_ogc_fid_seq', 622005, true);


--
-- TOC entry 5517 (class 0 OID 0)
-- Dependencies: 515
-- Name: traffic_metro_line_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_line_history_ogc_fid_seq', 89, true);


--
-- TOC entry 5518 (class 0 OID 0)
-- Dependencies: 516
-- Name: traffic_metro_line_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_line_ogc_fid_seq', 59, true);


--
-- TOC entry 5519 (class 0 OID 0)
-- Dependencies: 517
-- Name: traffic_metro_realtime_position_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_realtime_position_history_ogc_fid_seq', 57265982, true);


--
-- TOC entry 5520 (class 0 OID 0)
-- Dependencies: 518
-- Name: traffic_metro_realtime_position_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_realtime_position_ogc_fid_seq', 56605498, true);


--
-- TOC entry 5521 (class 0 OID 0)
-- Dependencies: 519
-- Name: traffic_metro_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_station_history_ogc_fid_seq', 4995, true);


--
-- TOC entry 5522 (class 0 OID 0)
-- Dependencies: 520
-- Name: traffic_metro_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_station_ogc_fid_seq', 1620, true);


--
-- TOC entry 5523 (class 0 OID 0)
-- Dependencies: 521
-- Name: traffic_metro_unusual_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_unusual_history_ogc_fid_seq', 21399, true);


--
-- TOC entry 5524 (class 0 OID 0)
-- Dependencies: 522
-- Name: traffic_metro_unusual_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_metro_unusual_ogc_fid_seq', 40, true);


--
-- TOC entry 5525 (class 0 OID 0)
-- Dependencies: 523
-- Name: traffic_todayworks_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_todayworks_history_ogc_fid_seq', 1773800, true);


--
-- TOC entry 5526 (class 0 OID 0)
-- Dependencies: 524
-- Name: traffic_youbike_one_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_youbike_one_realtime_history_ogc_fid_seq', 17226614, true);


--
-- TOC entry 5527 (class 0 OID 0)
-- Dependencies: 525
-- Name: traffic_youbike_realtime_histories_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_youbike_realtime_histories_ogc_fid_seq', 3422686, true);


--
-- TOC entry 5528 (class 0 OID 0)
-- Dependencies: 526
-- Name: traffic_youbike_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_youbike_station_ogc_fid_seq', 9444, true);


--
-- TOC entry 5529 (class 0 OID 0)
-- Dependencies: 527
-- Name: traffic_youbike_two_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traffic_youbike_two_realtime_history_ogc_fid_seq', 17768215, true);


--
-- TOC entry 5530 (class 0 OID 0)
-- Dependencies: 528
-- Name: tran_parking_capacity_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_parking_capacity_realtime_history_ogc_fid_seq', 82499677, true);


--
-- TOC entry 5531 (class 0 OID 0)
-- Dependencies: 529
-- Name: tran_parking_capacity_realtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_parking_capacity_realtime_ogc_fid_seq', 82499677, true);


--
-- TOC entry 5532 (class 0 OID 0)
-- Dependencies: 530
-- Name: tran_parking_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_parking_history_ogc_fid_seq', 72536, true);


--
-- TOC entry 5533 (class 0 OID 0)
-- Dependencies: 531
-- Name: tran_parking_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_parking_ogc_fid_seq', 73972, true);


--
-- TOC entry 5534 (class 0 OID 0)
-- Dependencies: 532
-- Name: tran_ubike_realtime_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_ubike_realtime_history_ogc_fid_seq', 54669867, true);


--
-- TOC entry 5535 (class 0 OID 0)
-- Dependencies: 533
-- Name: tran_ubike_realtime_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_ubike_realtime_ogc_fid_seq', 54669867, true);


--
-- TOC entry 5536 (class 0 OID 0)
-- Dependencies: 534
-- Name: tran_ubike_station_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_ubike_station_history_ogc_fid_seq', 27533, true);


--
-- TOC entry 5537 (class 0 OID 0)
-- Dependencies: 535
-- Name: tran_ubike_station_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_ubike_station_ogc_fid_seq', 27533, true);


--
-- TOC entry 5538 (class 0 OID 0)
-- Dependencies: 536
-- Name: tran_urban_bike_path_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_urban_bike_path_history_ogc_fid_seq', 8516, true);


--
-- TOC entry 5539 (class 0 OID 0)
-- Dependencies: 537
-- Name: tran_urban_bike_path_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tran_urban_bike_path_ogc_fid_seq', 8516, true);


--
-- TOC entry 5540 (class 0 OID 0)
-- Dependencies: 538
-- Name: tw_village_center_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tw_village_center_ogc_fid_seq', 7965, true);


--
-- TOC entry 5541 (class 0 OID 0)
-- Dependencies: 539
-- Name: tw_village_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tw_village_ogc_fid_seq', 7965, true);


--
-- TOC entry 5542 (class 0 OID 0)
-- Dependencies: 540
-- Name: work_eco_park_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_eco_park_history_ogc_fid_seq', 184, true);


--
-- TOC entry 5543 (class 0 OID 0)
-- Dependencies: 541
-- Name: work_eco_park_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_eco_park_ogc_fid_seq', 184, true);


--
-- TOC entry 5544 (class 0 OID 0)
-- Dependencies: 542
-- Name: work_floodgate_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_floodgate_location_history_ogc_fid_seq', 817, true);


--
-- TOC entry 5545 (class 0 OID 0)
-- Dependencies: 543
-- Name: work_floodgate_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_floodgate_location_ogc_fid_seq', 1, true);


--
-- TOC entry 5546 (class 0 OID 0)
-- Dependencies: 544
-- Name: work_garden_city_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_garden_city_history_ogc_fid_seq', 6796, true);


--
-- TOC entry 5547 (class 0 OID 0)
-- Dependencies: 545
-- Name: work_garden_city_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_garden_city_ogc_fid_seq', 6796, true);


--
-- TOC entry 5548 (class 0 OID 0)
-- Dependencies: 546
-- Name: work_goose_sanctuary_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_goose_sanctuary_history_ogc_fid_seq', 9, true);


--
-- TOC entry 5549 (class 0 OID 0)
-- Dependencies: 547
-- Name: work_goose_sanctuary_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_goose_sanctuary_ogc_fid_seq', 9, true);


--
-- TOC entry 5550 (class 0 OID 0)
-- Dependencies: 548
-- Name: work_nature_reserve_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_nature_reserve_history_ogc_fid_seq', 12, true);


--
-- TOC entry 5551 (class 0 OID 0)
-- Dependencies: 549
-- Name: work_nature_reserve_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_nature_reserve_ogc_fid_seq', 12, true);


--
-- TOC entry 5552 (class 0 OID 0)
-- Dependencies: 550
-- Name: work_park_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_park_history_ogc_fid_seq', 7632, true);


--
-- TOC entry 5553 (class 0 OID 0)
-- Dependencies: 551
-- Name: work_park_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_park_ogc_fid_seq', 7632, true);


--
-- TOC entry 5554 (class 0 OID 0)
-- Dependencies: 552
-- Name: work_pumping_station_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_pumping_station_location_history_ogc_fid_seq', 88, true);


--
-- TOC entry 5555 (class 0 OID 0)
-- Dependencies: 553
-- Name: work_pumping_station_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_pumping_station_location_ogc_fid_seq', 1, true);


--
-- TOC entry 5556 (class 0 OID 0)
-- Dependencies: 554
-- Name: work_rainfall_station_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_rainfall_station_location_history_ogc_fid_seq', 164, true);


--
-- TOC entry 5557 (class 0 OID 0)
-- Dependencies: 555
-- Name: work_rainfall_station_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_rainfall_station_location_ogc_fid_seq', 164, true);


--
-- TOC entry 5558 (class 0 OID 0)
-- Dependencies: 556
-- Name: work_riverside_bike_path_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_riverside_bike_path_history_ogc_fid_seq', 741, true);


--
-- TOC entry 5559 (class 0 OID 0)
-- Dependencies: 557
-- Name: work_riverside_bike_path_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_riverside_bike_path_ogc_fid_seq', 749, true);


--
-- TOC entry 5560 (class 0 OID 0)
-- Dependencies: 558
-- Name: work_riverside_park_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_riverside_park_history_ogc_fid_seq', 742962, true);


--
-- TOC entry 5561 (class 0 OID 0)
-- Dependencies: 559
-- Name: work_riverside_park_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_riverside_park_ogc_fid_seq', 742962, true);


--
-- TOC entry 5562 (class 0 OID 0)
-- Dependencies: 560
-- Name: work_school_greening_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_school_greening_history_ogc_fid_seq', 270, true);


--
-- TOC entry 5563 (class 0 OID 0)
-- Dependencies: 561
-- Name: work_school_greening_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_school_greening_ogc_fid_seq', 270, true);


--
-- TOC entry 5564 (class 0 OID 0)
-- Dependencies: 562
-- Name: work_sewer_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_sewer_location_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5565 (class 0 OID 0)
-- Dependencies: 563
-- Name: work_sewer_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_sewer_location_ogc_fid_seq', 1, true);


--
-- TOC entry 5566 (class 0 OID 0)
-- Dependencies: 564
-- Name: work_sidewalk_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_sidewalk_history_ogc_fid_seq', 122105, true);


--
-- TOC entry 5567 (class 0 OID 0)
-- Dependencies: 565
-- Name: work_sidewalk_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_sidewalk_ogc_fid_seq', 122105, true);


--
-- TOC entry 5568 (class 0 OID 0)
-- Dependencies: 566
-- Name: work_soil_liquefaction_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_soil_liquefaction_history_ogc_fid_seq', 1088, true);


--
-- TOC entry 5569 (class 0 OID 0)
-- Dependencies: 567
-- Name: work_soil_liquefaction_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_soil_liquefaction_ogc_fid_seq', 1088, true);


--
-- TOC entry 5570 (class 0 OID 0)
-- Dependencies: 568
-- Name: work_street_light_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_street_light_history_ogc_fid_seq', 34997771, true);


--
-- TOC entry 5571 (class 0 OID 0)
-- Dependencies: 569
-- Name: work_street_light_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_street_light_ogc_fid_seq', 34997771, true);


--
-- TOC entry 5572 (class 0 OID 0)
-- Dependencies: 570
-- Name: work_street_tree_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_street_tree_history_ogc_fid_seq', 1035349, true);


--
-- TOC entry 5573 (class 0 OID 0)
-- Dependencies: 571
-- Name: work_street_tree_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_street_tree_ogc_fid_seq', 1075704, true);


--
-- TOC entry 5574 (class 0 OID 0)
-- Dependencies: 572
-- Name: work_underpass_location_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_underpass_location_history_ogc_fid_seq', 1, true);


--
-- TOC entry 5575 (class 0 OID 0)
-- Dependencies: 573
-- Name: work_underpass_location_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_underpass_location_ogc_fid_seq', 1, true);


--
-- TOC entry 5576 (class 0 OID 0)
-- Dependencies: 574
-- Name: work_urban_agricultural_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_urban_agricultural_history_ogc_fid_seq', 441, true);


--
-- TOC entry 5577 (class 0 OID 0)
-- Dependencies: 575
-- Name: work_urban_agricultural_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_urban_agricultural_ogc_fid_seq', 441, true);


--
-- TOC entry 5578 (class 0 OID 0)
-- Dependencies: 576
-- Name: work_urban_reserve_history_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_urban_reserve_history_ogc_fid_seq', 4086, true);


--
-- TOC entry 5579 (class 0 OID 0)
-- Dependencies: 577
-- Name: work_urban_reserve_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.work_urban_reserve_ogc_fid_seq', 4086, true);


--
-- TOC entry 5580 (class 0 OID 0)
-- Dependencies: 227
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: -
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- TOC entry 4831 (class 2606 OID 20068)
-- Name: app_calcu_monthly_socl_welfare_people_ppl app_calcu_monthly_socl_welfare_people_ppl_seq_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_calcu_monthly_socl_welfare_people_ppl
    ADD CONSTRAINT app_calcu_monthly_socl_welfare_people_ppl_seq_pkey PRIMARY KEY (ogc_fid);


--
-- TOC entry 4833 (class 2606 OID 20070)
-- Name: building_unsued_land building_unsued_land_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_unsued_land
    ADD CONSTRAINT building_unsued_land_pkey PRIMARY KEY (ogc_fid);


--
-- TOC entry 4835 (class 2606 OID 20072)
-- Name: patrol_criminal_case patrol_criminal_case_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patrol_criminal_case
    ADD CONSTRAINT patrol_criminal_case_pkey PRIMARY KEY (ogc_fid);


--
-- TOC entry 4837 (class 2606 OID 20074)
-- Name: patrol_rain_floodgate patrol_rain_floodgate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patrol_rain_floodgate
    ADD CONSTRAINT patrol_rain_floodgate_pkey PRIMARY KEY (ogc_fid);


--
-- TOC entry 4839 (class 2606 OID 20076)
-- Name: socl_welfare_organization_plc socl_welfare_organization_plc_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socl_welfare_organization_plc
    ADD CONSTRAINT socl_welfare_organization_plc_pkey PRIMARY KEY (ogc_fid);


--
-- TOC entry 4840 (class 2620 OID 20077)
-- Name: app_calcu_monthly_socl_welfare_people_ppl auto_app_calcu_monthly_socl_welfare_people_ppl_mtime; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER auto_app_calcu_monthly_socl_welfare_people_ppl_mtime BEFORE INSERT OR UPDATE ON public.app_calcu_monthly_socl_welfare_people_ppl FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- TOC entry 4841 (class 2620 OID 20078)
-- Name: building_unsued_land auto_building_unsued_land_mtime; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER auto_building_unsued_land_mtime BEFORE INSERT OR UPDATE ON public.building_unsued_land FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- TOC entry 4842 (class 2620 OID 20079)
-- Name: building_unsued_public auto_building_unsued_public_mtime; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER auto_building_unsued_public_mtime BEFORE INSERT OR UPDATE ON public.building_unsued_public FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- TOC entry 4843 (class 2620 OID 20080)
-- Name: patrol_criminal_case auto_patrol_criminal_case_mtime; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER auto_patrol_criminal_case_mtime BEFORE INSERT OR UPDATE ON public.patrol_criminal_case FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- TOC entry 4844 (class 2620 OID 20081)
-- Name: socl_welfare_organization_plc auto_socl_welfare_organization_plc_mtime; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER auto_socl_welfare_organization_plc_mtime BEFORE INSERT OR UPDATE ON public.socl_welfare_organization_plc FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


-- Completed on 2024-02-16 10:54:03 UTC

--
-- PostgreSQL database dump complete
--

