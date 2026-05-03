--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

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
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO postgres;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO postgres;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_chatlog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ai_chatlog (
    id bigint NOT NULL,
    session_id character varying(100) NOT NULL,
    user_id character varying(100),
    provider character varying(50) DEFAULT 'twcc'::character varying NOT NULL,
    model character varying(100),
    question text NOT NULL,
    answer text,
    tool_used boolean DEFAULT false,
    tools jsonb,
    input_tokens bigint DEFAULT 0,
    output_tokens bigint DEFAULT 0,
    total_tokens bigint DEFAULT 0,
    latency_ms bigint,
    status character varying(30) DEFAULT 'success'::character varying NOT NULL,
    error_code character varying(100),
    error_message text,
    ip_address character varying(45) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ai_chatlog OWNER TO postgres;

--
-- Name: ai_chatlog_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ai_chatlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_chatlog_id_seq OWNER TO postgres;

--
-- Name: ai_chatlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ai_chatlog_id_seq OWNED BY public.ai_chatlog.id;


--
-- Name: auth_user_group_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_group_roles (
    auth_user_id bigint NOT NULL,
    group_id bigint NOT NULL,
    role_id bigint NOT NULL
);


ALTER TABLE public.auth_user_group_roles OWNER TO postgres;

--
-- Name: auth_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_users (
    id bigint NOT NULL,
    name character varying,
    email character varying,
    password character varying,
    idno character varying,
    uuid character varying,
    tp_account character varying,
    member_type character varying,
    verify_level character varying,
    is_admin boolean DEFAULT false,
    is_active boolean DEFAULT true,
    is_whitelist boolean DEFAULT false,
    is_blacked boolean DEFAULT false,
    expired_at timestamp with time zone,
    created_at timestamp with time zone,
    login_at timestamp with time zone,
    CONSTRAINT chk_auth_users_email CHECK (((email)::text ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'::text))
);


ALTER TABLE public.auth_users OWNER TO postgres;

--
-- Name: auth_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_users_id_seq OWNER TO postgres;

--
-- Name: auth_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_users_id_seq OWNED BY public.auth_users.id;


--
-- Name: chat_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_logs (
    id bigint NOT NULL,
    session text,
    question text,
    answer text,
    ip_address character varying(45) NOT NULL,
    user_id bigint,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.chat_logs OWNER TO postgres;

--
-- Name: chat_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_logs_id_seq OWNER TO postgres;

--
-- Name: chat_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_logs_id_seq OWNED BY public.chat_logs.id;


--
-- Name: component_charts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.component_charts (
    index character varying NOT NULL,
    color character varying[],
    types character varying[],
    unit character varying,
    stacked boolean DEFAULT true NOT NULL
);


ALTER TABLE public.component_charts OWNER TO postgres;

--
-- Name: component_maps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.component_maps (
    id bigint NOT NULL,
    index character varying NOT NULL,
    title character varying NOT NULL,
    type character varying NOT NULL,
    source character varying NOT NULL,
    size character varying,
    icon character varying,
    paint json,
    property json
);


ALTER TABLE public.component_maps OWNER TO postgres;

--
-- Name: component_maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.component_maps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.component_maps_id_seq OWNER TO postgres;

--
-- Name: component_maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.component_maps_id_seq OWNED BY public.component_maps.id;


--
-- Name: components; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.components (
    id bigint NOT NULL,
    index character varying NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.components OWNER TO postgres;

--
-- Name: components_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.components_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.components_id_seq OWNER TO postgres;

--
-- Name: components_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.components_id_seq OWNED BY public.components.id;


--
-- Name: contributors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contributors (
    id bigint NOT NULL,
    user_id character varying NOT NULL,
    user_name character varying NOT NULL,
    image text,
    link text NOT NULL,
    identity character varying,
    description text,
    include boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.contributors OWNER TO postgres;

--
-- Name: contributors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contributors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contributors_id_seq OWNER TO postgres;

--
-- Name: contributors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contributors_id_seq OWNED BY public.contributors.id;


--
-- Name: dashboard_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dashboard_groups (
    dashboard_id bigint NOT NULL,
    group_id bigint NOT NULL
);


ALTER TABLE public.dashboard_groups OWNER TO postgres;

--
-- Name: dashboards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dashboards (
    id bigint NOT NULL,
    index character varying NOT NULL,
    name character varying NOT NULL,
    components integer[],
    icon text,
    updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.dashboards OWNER TO postgres;

--
-- Name: dashboards_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dashboards_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dashboards_id_seq OWNER TO postgres;

--
-- Name: dashboards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dashboards_id_seq OWNED BY public.dashboards.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    id bigint NOT NULL,
    name character varying,
    is_personal boolean DEFAULT false,
    create_by bigint
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.groups_id_seq OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: incidents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.incidents (
    id bigint NOT NULL,
    type text,
    description text,
    distance numeric,
    latitude numeric,
    longitude numeric,
    place text,
    "time" timestamp with time zone,
    status text
);


ALTER TABLE public.incidents OWNER TO postgres;

--
-- Name: incidents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.incidents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.incidents_id_seq OWNER TO postgres;

--
-- Name: incidents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.incidents_id_seq OWNED BY public.incidents.id;


--
-- Name: issues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issues (
    id bigint NOT NULL,
    title character varying NOT NULL,
    user_name character varying NOT NULL,
    user_id character varying NOT NULL,
    context text,
    description text NOT NULL,
    decision_desc text,
    status character varying NOT NULL,
    updated_by character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.issues OWNER TO postgres;

--
-- Name: issues_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issues_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.issues_id_seq OWNER TO postgres;

--
-- Name: issues_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issues_id_seq OWNED BY public.issues.id;


--
-- Name: query_charts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.query_charts (
    index character varying,
    history_config json,
    map_config_ids integer[],
    map_filter json,
    time_from character varying,
    time_to character varying,
    update_freq integer,
    update_freq_unit character varying,
    source character varying,
    short_desc text,
    long_desc text,
    use_case text,
    links text[],
    contributors text[],
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    query_type character varying,
    query_chart text,
    query_history text,
    city text
);


ALTER TABLE public.query_charts OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id bigint NOT NULL,
    name character varying,
    access_control boolean DEFAULT false,
    modify boolean DEFAULT false,
    read boolean DEFAULT false
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: view_points; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.view_points (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    center_x numeric,
    center_y numeric,
    zoom numeric,
    pitch numeric,
    bearing numeric,
    name text,
    point_type text
);


ALTER TABLE public.view_points OWNER TO postgres;

--
-- Name: view_points_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.view_points_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.view_points_id_seq OWNER TO postgres;

--
-- Name: view_points_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.view_points_id_seq OWNED BY public.view_points.id;


--
-- Name: ai_chatlog id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_chatlog ALTER COLUMN id SET DEFAULT nextval('public.ai_chatlog_id_seq'::regclass);


--
-- Name: auth_users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_users ALTER COLUMN id SET DEFAULT nextval('public.auth_users_id_seq'::regclass);


--
-- Name: chat_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_logs ALTER COLUMN id SET DEFAULT nextval('public.chat_logs_id_seq'::regclass);


--
-- Name: component_maps id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component_maps ALTER COLUMN id SET DEFAULT nextval('public.component_maps_id_seq'::regclass);


--
-- Name: components id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.components ALTER COLUMN id SET DEFAULT nextval('public.components_id_seq'::regclass);


--
-- Name: contributors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contributors ALTER COLUMN id SET DEFAULT nextval('public.contributors_id_seq'::regclass);


--
-- Name: dashboards id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards ALTER COLUMN id SET DEFAULT nextval('public.dashboards_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: incidents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.incidents ALTER COLUMN id SET DEFAULT nextval('public.incidents_id_seq'::regclass);


--
-- Name: issues id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues ALTER COLUMN id SET DEFAULT nextval('public.issues_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: view_points id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.view_points ALTER COLUMN id SET DEFAULT nextval('public.view_points_id_seq'::regclass);


--
-- Data for Name: ai_chatlog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ai_chatlog (id, session_id, user_id, provider, model, question, answer, tool_used, tools, input_tokens, output_tokens, total_tokens, latency_ms, status, error_code, error_message, ip_address, created_at) FROM stdin;
\.


--
-- Data for Name: auth_user_group_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_group_roles (auth_user_id, group_id, role_id) FROM stdin;
1	4	1
1	1	1
1	2	1
1	3	1
\.


--
-- Data for Name: auth_users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_users (id, name, email, password, idno, uuid, tp_account, member_type, verify_level, is_admin, is_active, is_whitelist, is_blacked, expired_at, created_at, login_at) FROM stdin;
1	root	holdtensec.cs12@nycu.edu.tw	03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4	\N	\N	\N	\N	\N	t	t	t	f	\N	2026-05-02 11:37:29.747827+00	2026-05-02 20:42:03.631518+00
\.


--
-- Data for Name: chat_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_logs (id, session, question, answer, ip_address, user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: component_charts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.component_charts (index, color, types, unit, stacked) FROM stdin;
youbike_availability	{#9DC56E,#356340,#9DC56E}	{GuageChart,BarPercentChart}	輛	t
ebus_percent	{#9DC56E,#356340,#9DC56E}	{IconPercentChart,BarPercentChart}	輛	t
city_age_distribution	{#24B0DD,#56B96D,#F8CF58,#F5AD4A,#E170A6,#ED6A45,#AF4137,#10294A}	{DistrictChart,ColumnChart}	仟人	t
dependency_aging	{#67baca,#fbf3ac}	{ColumnLineChart,TimelineSeparateChart}	%	t
aging_kpi	{#F65658,#F49F36,#F5C860,#9AC17C,#4CB495,#569C9A,#60819C,#2F8AB1}	{TextUnitChart}	\N	t
aging_workforce_trend	{#24B0DD,#56B96D,#F8CF58,#F5AD4A,#E170A6,#ED6A45,#AF4137,#10294A}	{BarPercentChart,RadarChart,ColumnChart}	%	t
bike_network	{#a0b8e8,#b7ff98}	{DonutChart,BarChart}	公里	t
bike_map	{#a0b8e8,#b7ff98}	{MapLegend}	條	t
green_buildings	{#C8E6C9,#A1887F,#90A4AE,#FBC02D,#78A75A,#E8F5E9,#A5D6A7,#81C784,#66BB6A,#4CAF50,#43A047,#388E3C,#2E7D32,#1B5E20}	{DistrictChart,BarPercentChart,ColumnChart}	棟	t
reuse_energy_capacity_metrotaipei	{#4cb495,#f5c860,#5b8def}	{ColumnChart}	瓩 (kW)	t
reuse_energy_mix_taipei	{#4cb495,#f5c860,#5b8def,#848c94}	{DonutChart,BarChart}	瓩 (kW)	t
reuse_energy_trend_taipei	{#4cb495,#f5c860,#5b8def}	{TimelineStackedChart}	瓩 (kW)	t
reuse_energy_trend_column_taipei	{#4cb495,#f5c860,#5b8def}	{ColumnChart}	瓩 (kW)	t
vehicle_type_count_taipei	{#9b6b3e,#4cb495,#f5c860}	{ColumnChart}	輛	t
vehicle_fuel_mix_taipei	{#9b6b3e,#4cb495,#f5c860,#848c94}	{DonutChart,BarChart}	輛	t
vehicle_fuel_trend_taipei	{#9b6b3e,#4cb495,#f5c860}	{TimelineStackedChart}	輛	t
green_buildings_district	{#E8F5E9,#C8E6C9,#A5D6A7,#81C784,#66BB6A,#4CAF50,#43A047,#388E3C,#2E7D32,#1B5E20}	{DistrictChart}	棟	t
green_buildings_rank	{#C8E6C9,#A1887F,#90A4AE,#FBC02D,#78A75A}	{BarPercentChart}	棟	t
green_land_vegetation	{#81C784,#43A047,#1B5E20,#AED581,#C5E1A5}	{ColumnChart}	株/盆	f
green_land_summary	{#A5D6A7,#F9A825,#66BB6A}	{TextUnitChart}		f
bus_mrt_density	{#064e3b,#065f46,#047857,#059669,#10b981,#34d399,#6ee7b7,#a7f3d0,#d1fae5,#ecfdf5,#f0fdf4,#f8fdf8}	{DistrictChart,MapLegend}	站	t
ev_stations	{#4CAF93,#5BB8A0,#6DC1AC,#7ECAB8,#90D3C5,#A2DCD1,#B4E5DE,#C6EEEA,#D8F7F6,#EAF9F8,#C8E6C9,#A5D6A7}	{DistrictChart,PolarAreaChart,MapLegend}	支	t
youbike_density	{#1a3a8f,#2952b3,#3a6ad4,#5b8df5,#7aa8f7,#99c0f9,#b3d4fb,#c6e0fb,#d9ecfd,#e8f0fe,#f0f6ff,#f8fbff}	{DistrictChart,MapLegend}	站	t
metrotaipei_village_population_density	{#000000}	{MapLegend}	人/km²	t
\.


--
-- Data for Name: component_maps; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.component_maps (id, index, title, type, source, size, icon, paint, property) FROM stdin;
70	youbike_realtime	youbike站點	symbol	geojson	\N	youbike	{}	[{"key":"sna","name":"場站名稱"},{"key":"sno","name":"場站ID"},{"key":"available_return_bikes","name":"可還車位"},{"key":"available_rent_general_bikes","name":"剩餘車輛"}]
99	youbike_realtime_metrotaipei	youbike站點	symbol	geojson	\N	youbike	{}	[{"key":"sna","name":"場站名稱"},{"key":"sno","name":"場站ID"},{"key":"available_return_bikes","name":"可還車位"},{"key":"available_rent_general_bikes","name":"剩餘車輛"}]
100	bike_network_tpe	自行車路網	line	geojson	\N	\N	{"line-color":["match",["get","direction"],"雙向","#097138","單向","#007BFF","#808080"]}	[\r\n  {"key": "data_time", "name": "數據時間"},\r\n  {"key": "route_name", "name": "路線名稱"},\r\n  {"key": "city_code", "name": "城市代碼"},\r\n  {"key": "city", "name": "城市"},\r\n  {"key": "road_section_start", "name": "起點路段"},\r\n  {"key": "road_section_end", "name": "終點路段"},\r\n  {"key": "direction", "name": "方向"},\r\n  {"key": "cycling_length", "name": "自行車道長度"},\r\n  {"key": "finished_time", "name": "完工時間"},\r\n  {"key": "update_time", "name": "更新時間"}\r\n]
101	bike_network_metrotaipei	自行車路網	line	geojson	\N	\N	{"line-color":["match",["get","direction"],"雙向","#097138","單向","#007BFF","#808080"]}	[\r\n  {"key": "data_time", "name": "數據時間"},\r\n  {"key": "route_name", "name": "路線名稱"},\r\n  {"key": "city_code", "name": "城市代碼"},\r\n  {"key": "city", "name": "城市"},\r\n  {"key": "road_section_start", "name": "起點路段"},\r\n  {"key": "road_section_end", "name": "終點路段"},\r\n  {"key": "direction", "name": "方向"},\r\n  {"key": "cycling_length", "name": "自行車道長度"},\r\n  {"key": "finished_time", "name": "完工時間"},\r\n  {"key": "update_time", "name": "更新時間"}\r\n]
11	green_buildings_district	綠建築認可建築	circle	geojson	\N	\N	{"circle-color": "#4CAF50",\n    "circle-radius": 5,\n    "circle-opacity": 0.8,\n    "circle-stroke-color": "#ffffff",\n    "circle-stroke-width": 1,\n    "filter": ["all", ["==", ["get", "valid"], "1"], ["!=", ["get", "rank"], 5]]}	[{"key":"建築物名稱","name":"建築物名稱"},\n    {"key":"認可等級","name":"認可等級"},\n    {"key":"rank","name":"等級分數"},\n    {"key":"建築物概要","name":"建築物概要"},\n    {"key":"認可版本","name":"認可版本"},\n    {"key":"認可類別","name":"認可類別"},\n    {"key":"有效期間","name":"有效期間"},\n    {"key":"建築物使用類別","name":"建築物使用類別"},\n    {"key":"設計人","name":"設計人"},\n    {"key":"ditrict","name":"行政區"}]
12	green_buildings_district	鑽石級綠建築	symbol	geojson	\N	leaf-icon	{"layout": {"icon-image": "leaf-icon",\n                "icon-size": 1.2,\n                "icon-allow-overlap": true},\n    "filter": ["all", ["==", ["get", "valid"], "1"], ["==", ["get", "rank"], 5]]}	[{"key":"建築物名稱","name":"建築物名稱"},\n    {"key":"認可等級","name":"認可等級"},\n    {"key":"rank","name":"等級分數"},\n    {"key":"建築物概要","name":"建築物概要"},\n    {"key":"有效期間","name":"有效期間"},\n    {"key":"ditrict","name":"行政區"}]
13	metrotaipei_boundary	雙北範圍底色	fill	geojson	\N	\N	{"fill-color": "#e8f0fe", "fill-opacity": 0.6}	[{"key":"name","name":"區域名稱"}]
16	metrotaipei_boundary	雙北範圍底色	fill	geojson	\N	\N	{"fill-color": "#e8f0fe", "fill-opacity": 0.6}	[{"key":"name","name":"區域名稱"}]
17	youbike_density	YouBike 服務密度	fill	geojson	\N	\N	{"fill-color": ["interpolate", ["linear"], ["get", "density"], 1, "#c6e0fb", 5, "#5b8df5", 15, "#1a3a8f"], "fill-opacity": 0.8}	[{"key":"grid_id","name":"格網ID"},{"key":"density","name":"站點密度"},{"key":"district","name":"行政區"}]
14	bus_mrt_density	大眾運輸覆蓋率	fill	geojson	\N	\N	{"fill-color": ["interpolate", ["linear"], ["get", "density"], 1, "#d1fae5", 50, "#10b981", 200, "#064e3b"], "fill-opacity": 0.8}	[{"key":"grid_id","name":"格網ID"},{"key":"density","name":"站點密度"},{"key":"district","name":"行政區"}]
15	ev_stations	電動車充電站	symbol	geojson	\N	\N	{"layout": {"icon-image": ["case", [">=", ["/", ["to-number", ["coalesce", ["get", "available"], 0]], ["max", ["to-number", ["coalesce", ["get", "total_charging_points"], 0]], 1]], 0.5], "green-charger", [">=", ["/", ["to-number", ["coalesce", ["get", "available"], 0]], ["max", ["to-number", ["coalesce", ["get", "total_charging_points"], 0]], 1]], 0.3], "orange-charger", "red-charger"], "icon-size": 1.1, "icon-allow-overlap": true}}	[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"operator_name","name":"營運業者"},{"key":"total_charging_points","name":"充電槍數"},{"key":"available","name":"空閒槍數"},{"key":"connector_types","name":"充電規格"},{"key":"charge_rate","name":"充電費率"},{"key":"parking_rate","name":"停車費率"},{"key":"service_time","name":"服務時間"},{"key":"address","name":"地址"}]
18	metrotaipei_village_population_density	村里人口密度	fill	geojson	\N	\N	{"fill-color": "#000000", "fill-opacity": 0}	[\n    {"key":"county",          "name":"縣市"},\n    {"key":"town",            "name":"鄉鎮市區"},\n    {"key":"village",         "name":"村里"},\n    {"key":"population",      "name":"人口數（人）"},\n    {"key":"households",      "name":"戶數"},\n    {"key":"area_km2",        "name":"面積（km²）"},\n    {"key":"density_per_km2", "name":"人口密度（人/km²）"}\n  ]
\.


--
-- Data for Name: components; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.components (id, index, name) FROM stdin;
60	youbike_availability	YouBike使用情況
213	bike_network	自行車道路統計資料
212	ebus_percent	電動巴士比例
214	dependency_aging	扶養比及老化指數
216	city_age_distribution	全市年齡分區
218	aging_kpi	長照指標
215	aging_workforce_trend	高齡就業人口之年增結構
217	bike_map	自行車道路網圖資
911	reuse_energy_capacity_metrotaipei	再生能源裝置容量 - 雙北比較
912	reuse_energy_mix_taipei	再生能源裝置容量 - 能源占比
913	reuse_energy_trend_taipei	再生能源裝置容量 - 年趨勢
914	reuse_energy_trend_column_taipei	再生能源裝置容量 - 年趨勢（縱向長條）
901	vehicle_type_count_taipei	新領牌車輛 - 各車種輛數
902	vehicle_fuel_mix_taipei	新領牌車輛 - 燃料類別占比
903	vehicle_fuel_trend_taipei	新領牌車輛 - 燃料類別月趨勢
921	green_buildings_district	綠建築（行政區圖·子查詢）
922	green_buildings_rank	綠建築（等級堆疊·子查詢）
923	green_buildings	綠建築
932	green_land_vegetation	樹木植栽培育量
936	green_land_summary	綠美化關鍵指標
1	bus_mrt_density	公車捷運站密度
2	ev_stations	電動車充電站分布
3	youbike_density	YouBike服務密度
941	metrotaipei_village_population_density	村里人口密度
\.


--
-- Data for Name: contributors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contributors (id, user_id, user_name, image, link, identity, description, include, created_at, updated_at) FROM stdin;
1	doit	臺北市政府資訊局	doit.png	https://doit.gov.taipei/	\N	\N	f	2024-05-09 01:58:47.164185+00	2024-05-09 01:58:47.164185+00
2	ntpc	新北市政府資訊中心	ntpc.png	https://www.imc.ntpc.gov.tw/	\N	\N	f	2024-05-09 01:58:47.164185+00	2024-05-09 01:58:47.164185+00
\.


--
-- Data for Name: dashboard_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dashboard_groups (dashboard_id, group_id) FROM stdin;
106	2
356	2
355	3
359	3
358	3
360	4
905	2
906	3
361	4
\.


--
-- Data for Name: dashboards; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dashboards (id, index, name, components, icon, updated_at, created_at) FROM stdin;
356	ltc_care_tpe	長照關懷	{214,215,216,218}	elderly	2025-02-26 08:43:42.86017+00	2024-03-21 09:38:37.66+00
355	ltc_care_newtpe	長照關懷	{214,215,216,218}	elderly	2025-02-27 06:42:21.705931+00	2024-03-21 09:38:37.66+00
358	practical_transportation_newtpe	務實交通	{60,212,213}	directions_car	2025-03-12 08:00:38.75842+00	2024-03-21 09:38:37.66+00
1	09a25cd9cb7d	收藏組件	\N	favorite	2025-03-14 07:34:22.247753+00	2025-03-14 07:34:22.247753+00
2	3245d9eace5f	我的新儀表板	{215,218,216,213,212,214,60,146}	star	2025-03-14 14:55:11.732116+00	2025-03-14 14:55:11.732116+00
360	7029d8dff48c	收藏組件	\N	favorite	2026-05-02 11:37:29.771406+00	2026-05-02 11:37:29.771406+00
905	sustainable_env_taipei	永續環境	{215,218,216,213,212,214,60,146,901,902,903,911,912,913,914,923,932,936}	eco	2026-05-03 07:42:00+00	2026-05-02 19:02:57.568905+00
906	sustainable_env_metrotaipei	永續環境	{215,218,216,213,212,214,60,146,901,902,903,911,912,913,914,923,932,936}	eco	2026-05-03 07:42:00+00	2026-05-02 19:02:57.568905+00
361	6eef4be33009	我的新儀表板	{1,2,3}	star	2026-05-02 20:30:17.321977+00	2026-05-02 20:06:13.545916+00
106	map-layers-taipei	圖資資訊	{217,941}	public	2026-05-02 22:42:55.398733+00	2024-03-21 10:04:24.928533+00
359	map-layers-metrotaipei	圖資資訊	{217,941}	public	2026-05-02 22:42:55.405189+00	2024-03-21 10:04:24.928533+00
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.groups (id, name, is_personal, create_by) FROM stdin;
1	public	f	\N
2	taipei	f	\N
3	metrotaipei	f	\N
4	user: 1's personal group	t	1
\.


--
-- Data for Name: incidents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.incidents (id, type, description, distance, latitude, longitude, place, "time", status) FROM stdin;
\.


--
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issues (id, title, user_name, user_id, context, description, decision_desc, status, updated_by, created_at, updated_at) FROM stdin;
4	test	Drew	1	test	test	測試	不處理	doit	2024-03-15 07:33:39.695288+00	2024-07-26 06:37:55.038985+00
\.


--
-- Data for Name: query_charts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.query_charts (index, history_config, map_config_ids, map_filter, time_from, time_to, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, city) FROM stdin;
aging_kpi	\N	{}	{}	static	\N	0	\N	主計處	此圖顯示雙北長照關懷各項指標。	此圖表呈現雙北長照關懷相關指標，包括 扶老比、扶幼比、扶養比 及 老化指數。扶老比代表每百名勞動人口需扶養的老年人口數，扶幼比則是需扶養的兒童人口數，而扶養比則合計這兩者，反映整體社會負擔程度。老化指數則比較老年人口與兒童人口比例，顯示人口結構的高齡化趨勢。這些數據可用於評估長照需求，並規劃資源分配與政策方向，以因應人口老化帶來的挑戰。	在制定長照政策時，政府可運用 扶老比、扶幼比、扶養比 及 老化指數 來評估未來照護需求。例如，某城市發現扶老比上升且老化指數超過 100，代表老年人口已多於兒童，預示長照需求將持續增加。政府可據此增設長照機構、強化居家照護服務，並鼓勵社區共融計畫，以減輕勞動人口的扶養壓力，確保高齡者獲得適切照顧。	{https://data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1,https://data.ntpc.gov.tw/datasets/8308ab58-62d1-424e-8314-24b65b7ab492}	{doit,ntpc}	2023-12-20 05:56:00+00	2024-06-12 06:02:41.642+00	three_d	select y_axis,icon ,round(avg(data))data  \r\nfrom(\r\nselect '扶老比' as y_axis, percent30 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '扶幼比' as y_axis, percent31 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '扶養比' as y_axis, percent32 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '老化指數' as y_axis, percent33 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '扶老比' as y_axis, avg(percent30) as data ,'%' as icon \r\nfrom public.city_age_distribution_newtaipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計'\r\nunion all\r\nselect '扶幼比' as y_axis, avg(percent31) as data ,'%' as icon \r\nfrom public.city_age_distribution_newtaipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_newtaipei ) and 統計類型='計'\r\nunion all\r\nselect '扶養比' as y_axis, avg(percent32) as data ,'%' as icon \r\nfrom public.city_age_distribution_newtaipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計'\r\nunion all\r\nselect '老化指數' as y_axis, avg(percent33) as data ,'%' as icon \r\nfrom public.city_age_distribution_newtaipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計'\r\n)d\r\ngroup by y_axis,icon	\N	metrotaipei
aging_kpi	\N	{}	{}	static	\N	0	\N	主計處	此圖顯示臺北長照關懷各項指標。	此圖表呈現臺北長照關懷相關指標，包括 扶老比、扶幼比、扶養比 及 老化指數。扶老比代表每百名勞動人口需扶養的老年人口數，扶幼比則是需扶養的兒童人口數，而扶養比則合計這兩者，反映整體社會負擔程度。老化指數則比較老年人口與兒童人口比例，顯示人口結構的高齡化趨勢。這些數據可用於評估長照需求，並規劃資源分配與政策方向，以因應人口老化帶來的挑戰。	在制定長照政策時，政府可運用 扶老比、扶幼比、扶養比 及 老化指數 來評估未來照護需求。例如，某城市發現扶老比上升且老化指數超過 100，代表老年人口已多於兒童，預示長照需求將持續增加。政府可據此增設長照機構、強化居家照護服務，並鼓勵社區共融計畫，以減輕勞動人口的扶養壓力，確保高齡者獲得適切照顧。	{https://data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1}	{doit}	2023-12-20 05:56:00+00	2024-06-12 06:02:41.642+00	three_d	select y_axis,icon ,round(avg(data))data  \r\nfrom(\r\nselect '扶老比' as y_axis, percent30 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '扶幼比' as y_axis, percent31 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '扶養比' as y_axis, percent32 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\nunion all\r\nselect '老化指數' as y_axis, percent33 as data ,'%' as icon \r\nfrom public.city_age_distribution_taipei \r\nwhere 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'\r\n)d\r\ngroup by y_axis,icon	\N	taipei
aging_workforce_trend	\N	\N	\N	static	\N	\N	\N	主計處	顯示雙北就業人口之年齡結構時間數列統計資料	雙北地區人口年齡分配按月別時間數列統計資料，記錄臺北市與新北市各年齡層人口數的月度變化，涵蓋從0歲至65歲以上等多個年齡區間。該資料反映雙北地區人口在不同年齡層之分布情形，具備連續性與時間性，可作為分析區域人口結構、行政規劃及社會資源配置的重要參考。透過長期追蹤，亦能協助了解人口構成在不同時間點的變化狀況與組成比例，有助於支持各項人口相關研究與實務應用。	適用於跨域分析或探討都市群體共通趨勢，涵蓋臺北市與新北市兩地，常見於區域整體發展、通勤流動、就業市場整合、住宅與交通規劃等議題。亦可用於比較兩市人口結構差異、公共資源分布或整合性施政評估。例如：雙北地區勞動參與率變化、雙北通勤族群結構分析、雙北教育資源均衡程度探討等。	{https://data.taipei/dataset/detail?id=df320c78-f66b-4504-92b4-cf2a2eb46f1b,https://data.ntpc.gov.tw/datasets/c285509a-7fb2-434f-8542-0b4986c337a8}	{doit,ntpc}	2024-11-28 05:56:00+00	2024-12-10 02:59:39.341+00	three_d	select x_axis,y_axis,round(avg(percentage)) as data\r\nfrom (select year as x_axis,'1.非高齡就業人口' as y_axis,sum(percentage) as percentage  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure not in ('就業人口','就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲','就業人口按年齡別/65歲以上')\r\ngroup by year \r\nunion all \r\nselect year as x_axis,'2.中高齡就業人口' as y_axis,percentage as data  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲')\r\nunion all \r\nselect year as x_axis,'3.高齡就業人口' as y_axis,percentage as data  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/65歲以上')\r\nunion all \r\nselect year as x_axis,'1.非高齡就業人口' as y_axis,sum(percentage) as data  from employment_age_structure_new_tpe\r\nwhere  gender ='總計' and age_structure not in ('就業人口','就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲','就業人口按年齡別/65歲以上')\r\ngroup by year \r\nunion all \r\nselect year as x_axis,'2.中高齡就業人口' as y_axis,percentage as data  from employment_age_structure_new_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲')\r\nunion all \r\nselect year as x_axis,'3.高齡就業人口' as y_axis,percentage as data  from employment_age_structure_new_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/65歲以上'))d\r\nwhere x_axis >'2016'\r\ngroup by x_axis,y_axis \r\norder by 1,2	\N	metrotaipei
aging_workforce_trend	\N	\N	\N	static	\N	\N	\N	主計處	顯示臺北就業人口之年齡結構時間數列統計資料	臺北市人口年齡分配按月別時間數列統計資料，提供各年齡層人口數的定期統計結果，依月別呈現，涵蓋從幼年、青壯年至高齡等不同年齡區間。此資料可作為觀察人口結構組成的重要依據，反映各年齡層在人口總數中的分布情形。透過持續的月別紀錄，可供相關單位進行人口結構分析、資源分配規劃及政策評估等多元應用。資料內容具體、連續，適合用於進行長期與跨時比較之研究分析。	適用於聚焦單一行政區之人口、就業、教育、社會福利、都市規劃等議題。多用於市政層級的政策分析、市內人口結構觀察、社會服務配置研究，以及針對臺北市特定區域（如中正區、大安區等）的細部分析。例如：臺北市高齡人口比例變化、臺北市各區幼兒園分布狀況等。	{https://data.taipei/dataset/detail?id=df320c78-f66b-4504-92b4-cf2a2eb46f1b}	{doit}	2024-11-28 05:56:00+00	2025-03-19 10:25:55.340887+00	three_d	select x_axis,y_axis,round(avg(percentage)) as data\r\nfrom (select year as x_axis,'1.非高齡就業人口' as y_axis,sum(percentage) as percentage  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure not in ('就業人口','就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲','就業人口按年齡別/65歲以上')\r\ngroup by year \r\nunion all \r\nselect year as x_axis,'2.中高齡就業人口' as y_axis,percentage as data  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/45-49歲','就業人口按年齡別/50-54歲','就業人口按年齡別/55-59歲','就業人口按年齡別/60-64歲')\r\nunion all \r\nselect year as x_axis,'3.高齡就業人口' as y_axis,percentage as data  from employment_age_structure_tpe\r\nwhere  gender ='總計' and age_structure  in ('就業人口按年齡別/65歲以上')\r\n)d\r\nwhere x_axis >'2016'\r\ngroup by x_axis,y_axis \r\norder by 1,2	\N	taipei
bike_map	\N	{100,101}	{}	static	\N	\N	\N	交通局交工處	顯示雙北當前自行車路網分布。	顯示雙北當前自行車路網分布。雙北擁有完善的自行車路網，主要包括河濱自行車道和市區自行車道。河濱自行車道沿淡水河、基隆河、新店溪和景美溪等河岸建設，提供連續且風景優美的騎行路線。市區自行車道則遍布於主要道路，如敦化南北路、成功路、承德路、松隆路、松德路、和平西路、民生東路、北安路、金湖路、八德路、大道路、光復南路和永吉路等，方便市民在城市中安全騎行。此外，雙北政府持續推動「自行車道願景計畫」，以串聯既有路網、銜接跨市及河濱自行車道，並優化現有自行車道，提升騎行環境的便利性與安全性。	使用於地圖分析、交通規劃與旅遊建議，雙北的自行車路網可與其他圖資套疊，提供更深入的洞察。透過將自行車道與人口密度、交通流量或公車捷運路線交叉比對，可優化城市規劃，提高自行車友善程度。對於旅遊應用，可將自行車道與景點、商圈、飯店位置結合，推薦最佳騎行路線，提升遊憩體驗。此外，政府與企業可藉由數據分析發掘需求熱點，進一步優化自行車基礎設施與共享單車系統。	{https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24top=30&%24format=JSON,https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/NewTaipei?%24top=30&%24format=JSON}	{doit,ntpc}	2023-12-20 05:56:00+00	2024-01-11 06:26:02.069+00	map_legend	SELECT unnest(array['自行車路網']) as name, 'line' as type	\N	metrotaipei
bike_map	\N	{100}	{}	static	\N	\N	\N	交通局交工處	顯示臺北當前自行車路網分布。	顯示臺北市當前自行車路網分布。臺北市擁有完善的自行車路網，主要由河濱自行車道與市區自行車道組成。河濱自行車道沿淡水河、基隆河、新店溪與景美溪等河岸規劃，提供連續、寬敞且景觀良好的騎行空間，深受市民與遊客喜愛。市區自行車道則分布於市內多條主要幹道，包括敦化南北路、承德路、松隆路、松德路、和平西路、民生東路、八德路、光復南路、永吉路等，串聯重要商圈、學區與轉運點，提升日常通勤與短程移動的便利性。臺北市政府持續推動「自行車道願景計畫」，整合市區與河濱車道系統、銜接捷運與轉乘據點，並優化既有路線與設施，致力打造友善、安全的騎乘環境。	使用於地圖分析、交通規劃與旅遊建議，雙北的自行車路網可與其他圖資套疊，提供更深入的洞察。透過將自行車道與人口密度、交通流量或公車捷運路線交叉比對，可優化城市規劃，提高自行車友善程度。對於旅遊應用，可將自行車道與景點、商圈、飯店位置結合，推薦最佳騎行路線，提升遊憩體驗。此外，政府與企業可藉由數據分析發掘需求熱點，進一步優化自行車基礎設施與共享單車系統。	{https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24top=30&%24format=JSON}	{doit}	2023-12-20 05:56:00+00	2024-01-11 06:26:02.069+00	map_legend	SELECT unnest(array['自行車路網']) as name, 'line' as type	\N	taipei
bike_network	\N	{100,101}	{"mode":"byParam","byParam":{"xParam":"direction"}}	static	\N	\N	\N	交通局交工處	顯示雙北當前自行車路網分布。	顯示雙北當前自行車路網分布。雙北擁有完善的自行車路網，主要包括河濱自行車道和市區自行車道。河濱自行車道沿淡水河、基隆河、新店溪和景美溪等河岸建設，提供連續且風景優美的騎行路線。市區自行車道則遍布於主要道路，如敦化南北路、成功路、承德路、松隆路、松德路、和平西路、民生東路、北安路、金湖路、八德路、大道路、光復南路和永吉路等，方便市民在城市中安全騎行。此外，雙北政府持續推動「自行車道願景計畫」，以串聯既有路網、銜接跨市及河濱自行車道，並優化現有自行車道，提升騎行環境的便利性與安全性。	使用於地圖分析、交通規劃與旅遊建議，雙北的自行車路網可與其他圖資套疊，提供更深入的洞察。透過將自行車道與人口密度、交通流量或公車捷運路線交叉比對，可優化城市規劃，提高自行車友善程度。對於旅遊應用，可將自行車道與景點、商圈、飯店位置結合，推薦最佳騎行路線，提升遊憩體驗。此外，政府與企業可藉由數據分析發掘需求熱點，進一步優化自行車基礎設施與共享單車系統。	{https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24top=30&%24format=JSON,https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/NewTaipei?%24top=30&%24format=JSON}	{doit,ntpc}	2023-12-20 05:56:00+00	2024-01-11 06:26:02.069+00	two_d	select x_axis,sum(data)data from (select  direction as x_axis ,round(sum(cycling_length)/1000) as data\r\nfrom public.bike_network_tpe  \r\ngroup by direction\r\nunion all\r\nselect  direction as x_axis ,round(sum(cycling_length)/1000) as data\r\nfrom public.bike_network_new_tpe  \r\ngroup by direction\r\n)d\r\nwhere x_axis !=''\r\ngroup by x_axis	\N	metrotaipei
bike_network	\N	{100}	{"mode":"byParam","byParam":{"xParam":"direction"}}	static	\N	\N	\N	交通局交工處	顯示臺北市當前自行車路網分布。	顯示臺北市當前自行車路網分布。臺北市擁有完善的自行車路網，主要包括河濱自行車道和市區自行車道。河濱自行車道沿淡水河、基隆河、新店溪和景美溪等河岸建設，提供連續且風景優美的騎行路線。市區自行車道則遍布於主要道路，如敦化南北路、成功路、承德路、松隆路、松德路、和平西路、民生東路、北安路、金湖路、八德路、大道路、光復南路和永吉路等，方便市民在城市中安全騎行。此外，臺北市政府持續推動「自行車道願景計畫」，以串聯既有路網、銜接跨市及河濱自行車道，並優化現有自行車道，提升騎行環境的便利性與安全性。	使用於地圖分析、交通規劃與旅遊建議，臺北市的自行車路網可與其他圖資套疊，提供更深入的洞察。透過將自行車道與人口密度、交通流量或公車捷運路線交叉比對，可優化城市規劃，提高自行車友善程度。對於旅遊應用，可將自行車道與景點、商圈、飯店位置結合，推薦最佳騎行路線，提升遊憩體驗。此外，政府與企業可藉由數據分析發掘需求熱點，進一步優化自行車基礎設施與共享單車系統。	{https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24top=30&%24format=JSON}	{doit}	2023-12-20 05:56:00+00	2024-01-11 06:26:02.069+00	two_d	select  direction as x_axis ,round(sum(cycling_length)/1000) as data\r\nfrom public.bike_network_tpe  \r\nwhere direction !=''\r\ngroup by direction	\N	taipei
city_age_distribution	\N	\N	\N	static	\N	\N	\N	主計處	顯示雙北年齡分區	顯示雙北地區年齡分區，將人口依年齡群體劃分至不同城市區域。此分區有助於了解臺北市與新北市在人口結構上的差異與分布情形，包括各行政區的老化程度、青壯年與幼年人口比例，為政策制定者、城市規劃者及研究人員提供精確的分析依據。透過此資料，可進行跨區域的公共資源配置、社區規劃與長期照護服務設計，確保雙北地區在教育、交通、醫療與社福等層面能因應不同年齡層需求，促進整體都市發展的均衡與永續。	使用於城市規劃、社會政策制定及人口統計分析，雙北地區年齡分區數據可協助政府與研究機構掌握人口結構的變化情形。此指標適用於評估各年齡層在臺北市與新北市的區域分布，有助於規劃教育資源配置、醫療設施布建及長照服務佈點。除此之外，企業亦可依據此數據進行市場分析，針對不同年齡族群設計產品與服務，強化區域經營策略的精準度與效益。此資料為雙北區域在政策與產業發展上的重要基礎依據。	{https://data.taipei/dataset/detail?id=1e0c58e9-6aa5-4acb-a5a1-f60bacad60f3,https://data.ntpc.gov.tw/datasets/8308ab58-62d1-424e-8314-24b65b7ab492}	{doit,ntpc}	2024-11-28 05:56:00+00	2025-03-20 01:33:28.634747+00	three_d	select x_axis,y_axis,round(sum(data)/1000) data\r\nfrom(select 區域別 as x_axis,'0_14歲人口數' as y_axis,percent24 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\nunion all\r\nselect 區域別 as x_axis,'15_64歲人口數' as y_axis,percent26 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\nunion all\r\nselect 區域別 as x_axis,'65歲以上人口數' as y_axis,percent28 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\nunion all\r\nselect 區域別 as x_axis,'0_14歲人口數' as y_axis,percent24 as data\r\nfrom \r\npublic.city_age_distribution_newtaipei \r\nwhere 區域別 not in ('總計','新北市') and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_newtaipei)\r\nunion all\r\nselect 區域別 as x_axis,'15_64歲人口數' as y_axis,percent26 as data\r\nfrom \r\npublic.city_age_distribution_newtaipei \r\nwhere 區域別 not in ('總計','新北市') and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_newtaipei)  \r\nunion all\r\nselect 區域別 as x_axis,'65歲以上人口數' as y_axis,percent28 as data\r\nfrom \r\npublic.city_age_distribution_newtaipei \r\nwhere 區域別 not in ('總計','新北市') and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_newtaipei)\r\n)d\r\ngroup by x_axis,y_axis\r\n	\N	metrotaipei
city_age_distribution	\N	\N	\N	static	\N	\N	\N	主計處	顯示臺北市年齡分區	顯示臺北市年齡分區，將市民人口依年齡群體劃分至不同行政區域。此分區有助於掌握各區人口結構分布，包括幼年人口、青壯年人口與高齡人口比例，為政策制定者、城市規劃單位及研究人員提供重要的分析依據。透過此資料，可進行公共資源配置、社區照護設計及設施規劃，確保臺北市在教育、醫療、交通與長照等方面的發展，能更貼近各年齡層居民的實際需求，促進人口結構與城市功能的平衡發展。	使用於城市規劃、社會政策制定及人口統計分析，臺北市年齡分區數據可協助市府機關與研究單位掌握市內人口結構的變化。此指標適用於評估各年齡層在不同行政區的分布情形，有助於規劃教育資源、醫療設施及長照服務的佈局與優化。此外，企業亦可依據此資料進行在地市場分析，針對不同年齡族群設計產品與服務，提升區域經營策略的精準度與實效性，強化對臺北市多元人口需求的回應。\n\n\n\n\n\n\n\n\n	{https://data.taipei/dataset/detail?id=1e0c58e9-6aa5-4acb-a5a1-f60bacad60f3}	{doit}	2024-11-28 05:56:00+00	2025-02-21 07:52:55.450103+00	three_d	select x_axis,y_axis,round(sum(data)/1000) data\r\nfrom(select 區域別 as x_axis,'0_14歲人口數' as y_axis,percent24 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\nunion all\r\nselect 區域別 as x_axis,'15_64歲人口數' as y_axis,percent26 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\nunion all\r\nselect 區域別 as x_axis,'65歲以上人口數' as y_axis,percent28 as data\r\nfrom \r\npublic.city_age_distribution_taipei \r\nwhere 區域別 != '總計' and 年份=(select max(年份)\r\nfrom \r\npublic.city_age_distribution_taipei)\r\n)d\r\ngroup by x_axis,y_axis\r\n	\N	taipei
dependency_aging	\N	\N	\N	static	\N	\N	\N	主計處	顯示雙北扶養比及老化指數時間數列統計資料	顯示雙北扶養比及老化指數時間數列統計資料。雙北政府主計處提供了扶養比和老化指數資料，詳細記錄了各年齡段人口比例的變化情況。這些資料有助於分析雙北人口結構的演變，評估青壯年人口對幼年和老年人口的扶養負擔，以及社會老化程度。透過這些統計資料，政策制定者和研究人員可以深入了解人口趨勢，為未來的社會福利和經濟發展規劃提供參考。	使用於人口結構分析、社會福利規劃與經濟發展評估，雙北的扶養比與老化指數數據提供決策參考。政府機構可透過這些統計資料評估勞動力供給與社會扶養負擔，進而調整退休政策與醫療資源配置。企業可運用數據研判市場趨勢，規劃銀髮族產品與服務。學術研究則可透過時間序列分析，探討人口老化對經濟與社會的影響，為未來城市發展與人口政策提供科學依據。\r\n	{https://data.taipei/dataset/detail?id=aafb15dc-5508-4091-bd48-a708e60f6698,https://data.ntpc.gov.tw/datasets/8308ab58-62d1-424e-8314-24b65b7ab492}	{doit,ntpc}	2024-11-28 05:56:00+00	2024-12-10 02:59:39.341+00	time	select \r\nx_axis,y_axis,round(avg(data)) data\r\nfrom (\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'扶養比' as y_axis,total_dependency_ratio as data  \r\nfrom \r\ndependency_ratio_and_aging_index_tpe\r\nunion all\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'老化指數' as y_axis ,aging_index \r\nfrom \r\ndependency_ratio_and_aging_index_tpe\r\nunion all\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'扶養比' as y_axis,total_dependency_ratio  \r\nfrom \r\ndependency_ratio_and_aging_index_new_tpe\r\nunion all\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'老化指數' as y_axis ,aging_index \r\nfrom \r\ndependency_ratio_and_aging_index_new_tpe\r\n)d\r\nwhere x_axis >'2013-01-01 00:00:00.000'\r\ngroup by x_axis,y_axis\r\norder by 1\r\n	\N	metrotaipei
dependency_aging	\N	\N	\N	static	\N	\N	\N	主計處	顯示臺北市扶養比及老化指數時間數列統計資料	顯示臺北市扶養比及老化指數時間數列統計資料。臺北市政府主計處提供了扶養比和老化指數資料，詳細記錄了各年齡段人口比例的變化情況。這些資料有助於分析臺北市人口結構的演變，評估青壯年人口對幼年和老年人口的扶養負擔，以及社會老化程度。透過這些統計資料，政策制定者和研究人員可以深入了解人口趨勢，為未來的社會福利和經濟發展規劃提供參考。	使用於人口結構分析、社會福利規劃與經濟發展評估，臺北市的扶養比與老化指數數據提供決策參考。政府機構可透過這些統計資料評估勞動力供給與社會扶養負擔，進而調整退休政策與醫療資源配置。企業可運用數據研判市場趨勢，規劃銀髮族產品與服務。學術研究則可透過時間序列分析，探討人口老化對經濟與社會的影響，為未來城市發展與人口政策提供科學依據。\r\n	{https://data.taipei/dataset/detail?id=aafb15dc-5508-4091-bd48-a708e60f6698}	{doit}	2024-11-28 05:56:00+00	2025-02-25 01:43:21.031142+00	time	select \r\nx_axis,y_axis,round(avg(data)) data\r\nfrom (\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'扶養比' as y_axis,total_dependency_ratio as data  \r\nfrom \r\ndependency_ratio_and_aging_index_tpe\r\nunion all\r\nselect TO_TIMESTAMP(end_of_year , 'YYYY-MM-DD HH24:MI:SS.MS') AT TIME ZONE 'Asia/Taipei' AS x_axis,\r\n'老化指數' as y_axis ,aging_index \r\nfrom \r\ndependency_ratio_and_aging_index_tpe\r\n)d\r\nwhere x_axis >'2013-01-01 00:00:00.000'\r\ngroup by x_axis,y_axis\r\norder by 1\r\n	\N	taipei
ebus_percent	\N	\N	\N	static	\N	\N	\N	交通局	顯示雙北電動公車比例	此圖顯示雙北地區電動公車的比例，呈現臺北市與新北市公車車隊中電動車所占比重，以及近年來電動公車數量的成長情形。圖表比較傳統燃油公車與電動公車的比例變化，並標示雙北兩市政府推動電動化政策、補助措施及其帶來的環保效益。透過這些數據，可評估雙北地區電動公車的普及程度，及其對減碳、空氣品質改善的實質貢獻，進一步作為規劃大臺北地區公共運輸電動化策略的重要依據，推動都會區交通體系朝向低碳永續發展。	可用於評估雙北地區公共運輸電動化進程，透過此圖顯示臺北市與新北市公車系統中電動公車的占比及成長趨勢。圖表比較傳統燃油公車與電動公車的比例變化，並標示雙北兩市推動相關政策、補助措施及其所帶來的環保效益。透過這些數據，可評估雙北地區電動公車的普及率，以及其在減碳排放與空氣品質改善上的具體貢獻，進而作為制定更完善的都會區公共運輸電動化策略的重要依據，推動雙北朝向低碳永續城市目標發展。	{https://tdx.transportdata.tw/api/basic/v2/Bus/Vehicle/City/Taipei?%24top=30&%24format=JSON,https://tdx.transportdata.tw/api/basic/v2/Bus/Vehicle/City/NewTaipei?%24top=30&%24format=JSON}	{doit,ntpc}	2025-02-15 05:56:00+00	2024-02-15 02:59:39.341+00	percent	select '電動公車數量' as x_axis,y_axis,sum(data) data from \r\n(select '電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_new_tpe\r\nwhere plate_numb like 'E%'\r\nunion all\r\nselect '非電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_new_tpe\r\nwhere plate_numb not like 'E%'\r\nunion all\r\nselect '電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_tpe\r\nwhere plate_numb like 'E%'\r\nunion all\r\nselect '非電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_tpe)d\r\ngroup by \r\ny_axis\r\n	\N	metrotaipei
ebus_percent	\N	\N	\N	static	\N	\N	\N	交通局	顯示臺北電動公車比例	此圖顯示臺北市電動公車的比例，呈現全市公車車隊中電動車所占比重，以及近年來電動公車數量的成長情形。圖表比較傳統燃油公車與電動公車的比例變化，並標示臺北市政府推動電動化政策、補助措施及其帶來的環保效益。透過這些數據，可評估臺北市電動公車的普及程度，及其在減碳與空氣品質改善上的貢獻，有助於進一步規劃更完善的公共運輸電動化策略，推動城市交通朝向低碳永續目標邁進。	可用於評估臺北市公共運輸電動化的進程，透過此圖顯示電動公車在市區公車總數中的占比及其成長趨勢。圖表呈現傳統燃油公車與電動公車的比例變化，並標示臺北市政府推動的政策措施、補助方案及相關環保效益等影響因素。透過這些數據，可分析臺北市電動公車的普及程度及其在減碳排放與空氣品質改善方面的貢獻，有助於進一步規劃更完善的公共運輸電動化策略，推動臺北朝向低碳與永續發展的城市目標邁進。	{https://tdx.transportdata.tw/api/basic/v2/Bus/Vehicle/City/Taipei?%24top=30&%24format=JSON}	{doit}	2025-02-15 05:56:00+00	2025-02-20 09:11:21.620625+00	percent	select '電動公車數量' as x_axis,y_axis,sum(data) data from \r\n(\r\nselect '電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_tpe\r\nwhere plate_numb like 'E%'\r\nunion all\r\nselect '非電動巴士' as y_axis,count(*) as  data\r\nfrom public.bus_info_tpe)d\r\ngroup by \r\ny_axis	\N	taipei
youbike_availability	\N	{99}	\N	current	\N	10	minute	交通局	顯示當前雙北共享單車YouBike的使用情況。	顯示雙北地區（臺北市與新北市）當前共享單車 YouBike 的使用情況，格式為可借車輛數／全區車位數。資料來源為兩市交通局公開資料，每5分鐘更新一次，提供即時的車輛可用資訊與站點使用狀況，有助於掌握整體運行效率與民眾使用情形，亦可作為交通管理與營運調度的參考依據。	藉由顯示雙北地區 YouBike 的使用情況，以及觀察可借車輛數約為車柱總數的一半，可大致掌握目前停放於站點與使用中車輛的整體分布情形。使用者亦可透過地圖模式查詢雙北各站點的即時資訊，包括可借車輛數、可還空位數及站點位置，方便規劃路線與掌握使用狀況，提升共享單車的便利性與使用效率。	{https://tdx.transportdata.tw/api-service/swagger/basic/2cc9b888-a592-496f-99de-9ab35b7fb70d#/Bike/BikeApi_Availability_2181,https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/NewTaipei?%24top=30&%24format=JSON}	{doit,ntpc}	2023-12-20 05:56:00+00	2024-03-19 06:08:17.99+00	percent	select x_axis,y_axis,sum(data)data\r\nfrom (select '在站車輛' as x_axis, \r\nunnest(ARRAY['可借車輛', '空位']) as y_axis, \r\nunnest(ARRAY[SUM(available_rent_general_bikes), SUM(available_return_bikes)]) as data\r\nfrom tran_ubike_realtime_new_tpe\r\nunion all \r\nselect '在站車輛' as x_axis, \r\nunnest(ARRAY['可借車輛', '空位']) as y_axis, \r\nunnest(ARRAY[SUM(available_rent_general_bikes), SUM(available_return_bikes)]) as data\r\nfrom tran_ubike_realtime)d\r\ngroup by x_axis,y_axis	\N	metrotaipei
youbike_availability	\N	{70}	\N	current	\N	10	minute	交通局	顯示當前臺北市共享單車YouBike的使用情況。	顯示臺北市當前共享單車 YouBike 的使用情況，格式為可借車輛數／全市車位數。資料來源為臺北市政府交通局公開資料，每5分鐘更新一次，反映即時的使用狀況與車輛調度情形，可作為交通監測與市民使用參考依據。	藉由臺北市 YouBike 使用情況的顯示，以及全市可借車輛數約為車柱總數的一半，可大致掌握目前停放於站點與正在使用中的車輛數量。使用者可透過地圖模式查詢臺北市各站點的即時資訊，包括可借車輛數、可還空位數及站點位置，方便即時掌握使用狀況，提升共享單車的使用效率與便利性。	{https://tdx.transportdata.tw/api-service/swagger/basic/2cc9b888-a592-496f-99de-9ab35b7fb70d#/Bike/BikeApi_Availability_2181}	{doit}	2023-12-20 05:56:00+00	2024-03-19 06:08:17.99+00	percent	select '在站車輛' as x_axis, \r\nunnest(ARRAY['可借車輛', '空位']) as y_axis, \r\nunnest(ARRAY[SUM(available_rent_general_bikes), SUM(available_return_bikes)]) as data\r\nfrom tran_ubike_realtime	\N	taipei
reuse_energy_trend_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	臺北市再生能源裝置容量逐年趨勢。	依民國 101 年起累計裝置容量逐年呈現；以堆疊面積觀察整體成長與結構變化。	觀察臺北市再生能源裝置容量的成長路徑與結構演進。	{https://www.moeaea.gov.tw/}	{doit}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	time	SELECT iso_date AS x_axis,\n       energy_type AS y_axis,\n       SUM(capacity_kw) AS data\nFROM public.reuse_energy_capacity\nWHERE city = '台北市' AND period_sort LIKE '%-00'\nGROUP BY iso_date, energy_type\nORDER BY iso_date, energy_type	\N	taipei
reuse_energy_trend_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	雙北再生能源裝置容量逐年趨勢。	雙北合計：臺北市與新北市同年加總；以堆疊面積觀察整體成長與結構變化。	評估雙北作為大區之綠能成長路徑。	{https://www.moeaea.gov.tw/,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	time	SELECT iso_date AS x_axis,\n       energy_type AS y_axis,\n       SUM(capacity_kw) AS data\nFROM public.reuse_energy_capacity\nWHERE period_sort LIKE '%-00'\nGROUP BY iso_date, energy_type\nORDER BY iso_date, energy_type	\N	metrotaipei
reuse_energy_trend_column_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	臺北市再生能源裝置容量逐年堆疊長條。	與年趨勢折線堆疊圖相同年度資料；以縱向堆疊長條呈現。11502 未納入。	以長條圖比對各年度裝置容量結構。	{https://www.moeaea.gov.tw/}	{doit}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	three_d	SELECT p.period_label AS x_axis,\n       e.energy_type AS y_axis,\n       COALESCE(m.capacity_kw, 0) AS data\nFROM\n  (SELECT DISTINCT period_sort, period_label\n   FROM public.reuse_energy_capacity\n   WHERE city = '台北市' AND period_sort LIKE '%-00'\n  ) AS p\n  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)\n  LEFT JOIN public.reuse_energy_capacity m\n    ON m.period_sort = p.period_sort\n   AND m.city = '台北市'\n   AND m.energy_type = e.energy_type\nORDER BY p.period_sort,\n         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)	\N	taipei
reuse_energy_capacity_metrotaipei	\N	{}	\N	static	\N	1	year	經濟部能源署	雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。	並列臺北市與新北市三類再生能源裝置容量，以堆疊縱向長條圖呈現；臺北市風力為 0。	比較雙北綠能發展結構，輔助再生能源政策評估。	{https://www.moeaea.gov.tw/}	{doit}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	three_d	SELECT\n  CASE c.city WHEN '台北市' THEN '臺北市' ELSE c.city END AS x_axis,\n  e.energy_type AS y_axis,\n  COALESCE(SUM(m.capacity_kw), 0) AS data\nFROM\n  (VALUES ('台北市'),('新北市')) AS c(city)\n  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)\n  LEFT JOIN public.reuse_energy_capacity m\n    ON  m.city        = c.city\n    AND m.energy_type = e.energy_type\n    AND m.period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)\nGROUP BY c.city, e.energy_type\nORDER BY\n  ARRAY_POSITION(ARRAY['台北市','新北市']::text[], c.city),\n  ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)	\N	metrotaipei
reuse_energy_capacity_metrotaipei	\N	{}	\N	static	\N	1	year	經濟部能源署	雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。	並列臺北市與新北市三類再生能源裝置容量；本元件本身即為雙北比較，臺北儀表板亦保留同一視圖。	比較雙北綠能發展結構，輔助再生能源政策評估。	{https://www.moeaea.gov.tw/}	{doit}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	three_d	SELECT\n  CASE c.city WHEN '台北市' THEN '臺北市' ELSE c.city END AS x_axis,\n  e.energy_type AS y_axis,\n  COALESCE(SUM(m.capacity_kw), 0) AS data\nFROM\n  (VALUES ('台北市'),('新北市')) AS c(city)\n  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)\n  LEFT JOIN public.reuse_energy_capacity m\n    ON  m.city        = c.city\n    AND m.energy_type = e.energy_type\n    AND m.period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)\nGROUP BY c.city, e.energy_type\nORDER BY\n  ARRAY_POSITION(ARRAY['台北市','新北市']::text[], c.city),\n  ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)	\N	taipei
reuse_energy_mix_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	臺北市最新期三類再生能源裝置容量占比。	風力：陸域與離岸；太陽光電：屋頂型與地面型合計；其他(含水力)：水力、生質能、地熱等。	觀察臺北市再生能源結構偏向，作為綠色城市核心指標。	{https://www.moeaea.gov.tw/}	{doit}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	two_d	SELECT energy_type AS x_axis, SUM(capacity_kw) AS data\nFROM public.reuse_energy_capacity\nWHERE city = '台北市'\n  AND period_sort = (SELECT MAX(period_sort)\n                     FROM public.reuse_energy_capacity WHERE city = '台北市')\nGROUP BY energy_type\nORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)	\N	taipei
reuse_energy_mix_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	雙北最新期三類再生能源裝置容量占比。	臺北市與新北市裝置容量加總後再依風力／太陽光電／其他(含水力)三類計算占比。	觀察雙北整體再生能源結構，協助大區能源政策評估。	{https://www.moeaea.gov.tw/,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	two_d	SELECT energy_type AS x_axis, SUM(capacity_kw) AS data\nFROM public.reuse_energy_capacity\nWHERE period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)\nGROUP BY energy_type\nORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)	\N	metrotaipei
reuse_energy_trend_column_taipei	\N	{}	\N	static	\N	1	year	經濟部能源署	雙北再生能源裝置容量逐年堆疊長條。	雙北合計，僅取年度列；以縱向堆疊長條呈現。	以長條圖比對雙北各年度裝置容量結構。	{https://www.moeaea.gov.tw/,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:21:23.724176+00	2026-05-02 15:21:23.724176+00	three_d	SELECT p.period_label AS x_axis,\n       e.energy_type AS y_axis,\n       COALESCE(SUM(m.capacity_kw), 0) AS data\nFROM\n  (SELECT DISTINCT period_sort, period_label\n   FROM public.reuse_energy_capacity\n   WHERE period_sort LIKE '%-00'\n  ) AS p\n  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)\n  LEFT JOIN public.reuse_energy_capacity m\n    ON m.period_sort = p.period_sort\n   AND m.energy_type = e.energy_type\nGROUP BY p.period_sort, p.period_label, e.energy_type\nORDER BY p.period_sort,\n         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)	\N	metrotaipei
vehicle_type_count_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	臺北市新領牌車輛各車種輛數（最新月份）。	以最新月份為例，呈現大客車、大貨車、小客車、小貨車、機車五個保留車種的新領牌輛數。已排除全體總計、汽車匯總列、特種車。	比較各車種登記輛數，輔助綠能轉型／污染源評估。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100}	{doit}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	three_d	SELECT\n  v.vehicle_type AS x_axis,\n  CASE f.fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS y_axis,\n  COALESCE(SUM(m.count), 0) AS data\nFROM\n  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)\n  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)\n  LEFT JOIN public.vehicle_registration_monthly m\n    ON  m.vehicle_type  = v.vehicle_type\n    AND m.fuel_category = f.fuel_category\n    AND m.region        = '臺北市'\n    AND m.period_sort   = (SELECT MAX(period_sort)\n                           FROM public.vehicle_registration_monthly\n                           WHERE region = '臺北市')\nGROUP BY v.vehicle_type, f.fuel_category\nORDER BY\n  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),\n  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)	\N	taipei
vehicle_type_count_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	雙北新領牌車輛各車種輛數（最新月份，臺北+新北合計）。	以雙北共同最新月份為例，將臺北市與新北市同車種、同燃料之新領牌輛數加總後呈現。	比較各車種登記輛數，輔助大臺北綠能轉型／污染源評估。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	three_d	SELECT\n  v.vehicle_type AS x_axis,\n  CASE f.fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS y_axis,\n  COALESCE(SUM(m.count), 0) AS data\nFROM\n  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)\n  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)\n  LEFT JOIN public.vehicle_registration_monthly m\n    ON  m.vehicle_type  = v.vehicle_type\n    AND m.fuel_category = f.fuel_category\n    AND m.region IN ('臺北市', '新北市')\n    AND m.period_sort   = (SELECT MAX(period_sort)\n                           FROM public.vehicle_registration_monthly\n                           WHERE region IN ('臺北市', '新北市'))\nGROUP BY v.vehicle_type, f.fuel_category\nORDER BY\n  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),\n  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)	\N	metrotaipei
vehicle_fuel_mix_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	臺北市新領牌車輛 ICE/BEV/Hybrid 占比（最新月份）。	ICE：(1)汽油、(2)柴油、(4)液化石油氣、(5)汽油/LPG；BEV：(3)電能；Hybrid：(6)~(13) 其餘混合與雙動力分類。以最新月份為例。	觀察油轉電進度，作為綠色城市核心指標。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100}	{doit}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	two_d	SELECT\n  CASE fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS x_axis,\n  SUM(count) AS data\nFROM public.vehicle_registration_monthly\nWHERE region = '臺北市'\n  AND period_sort = (SELECT MAX(period_sort)\n                     FROM public.vehicle_registration_monthly\n                     WHERE region = '臺北市')\nGROUP BY fuel_category\nORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)	\N	taipei
vehicle_fuel_mix_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	雙北新領牌車輛 ICE/BEV/Hybrid 占比（最新月份，臺北+新北合計）。	將雙北同月份輛數加總後，再依燃料三類計算占比。	觀察大臺北油轉電進度。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	two_d	SELECT\n  CASE fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS x_axis,\n  SUM(count) AS data\nFROM public.vehicle_registration_monthly\nWHERE region IN ('臺北市', '新北市')\n  AND period_sort = (SELECT MAX(period_sort)\n                     FROM public.vehicle_registration_monthly\n                     WHERE region IN ('臺北市', '新北市'))\nGROUP BY fuel_category\nORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)	\N	metrotaipei
vehicle_fuel_trend_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	臺北市新領牌車輛 ICE/BEV/Hybrid 之月趨勢。	依燃料三類匯總後逐月堆疊。月度資料；已排除整年列、(1~3月) 等累計列。	觀察臺北市油轉電的月度趨勢與季節性變化。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100}	{doit}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	time	SELECT\n  to_timestamp(\n    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text\n    || '-' || split_part(period_sort, '-', 2) || '-01',\n    'YYYY-MM-DD'\n  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,\n  CASE fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS y_axis,\n  SUM(count) AS data\nFROM public.vehicle_registration_monthly\nWHERE region = '臺北市'\nGROUP BY x_axis, fuel_category\nORDER BY y_axis, x_axis	\N	taipei
vehicle_fuel_trend_taipei	\N	{}	\N	static	\N	1	month	交通部統計查詢網	雙北新領牌車輛 ICE/BEV/Hybrid 之月趨勢（臺北+新北合計）。	同月份兩市輛數加總後逐月堆疊。	觀察雙北油轉電的月度趨勢與季節性變化。	{https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100,https://data.ntpc.gov.tw/}	{doit,ntpc}	2026-05-02 15:36:15.074386+00	2026-05-02 15:36:15.074386+00	time	SELECT\n  to_timestamp(\n    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text\n    || '-' || split_part(period_sort, '-', 2) || '-01',\n    'YYYY-MM-DD'\n  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,\n  CASE fuel_category\n       WHEN 'ICE'    THEN '純油 (ICE)'\n       WHEN 'BEV'    THEN '純電 (BEV)'\n       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'\n  END AS y_axis,\n  SUM(count) AS data\nFROM public.vehicle_registration_monthly\nWHERE region IN ('臺北市', '新北市')\nGROUP BY x_axis, fuel_category\nORDER BY y_axis, x_axis	\N	metrotaipei
green_buildings_district	\N	{11,12}	{"mode":"byParam","byParam":{"xParam":"ditrict"}}	static	\N	1	month	內政部建築研究所 綠建築標章	臺北市各行政區綠建築認可建築棟數（valid=1）。	統計臺北市 12 個行政區有效認可建築棟數；地圖上非鑽石級為圓點，鑽石級為葉片。	掌握臺北市綠建築空間分布與密度。	{https://gbeval.tabc.org.tw/}	{doit}	2026-05-02 17:38:05.294399+00	2026-05-02 17:38:05.294399+00	two_d	SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data\n    FROM (VALUES\n      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n    ) AS d(district)\n    LEFT JOIN public.green_buildings g\n      ON g.district = d.district AND g.city = '臺北市' AND g.valid = '1'\n    GROUP BY d.district\n    ORDER BY ARRAY_POSITION(\n      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n            '中山區','大同區','中正區','萬華區','大安區','文山區'],\n      d.district)	\N	taipei
green_buildings_district	\N	{11,12}	{"mode":"byParam","byParam":{"xParam":"ditrict"}}	static	\N	1	month	內政部建築研究所 綠建築標章	雙北各行政區綠建築認可建築棟數（valid=1）。	統計雙北 41 區有效認可建築棟數；鑽石級以葉片標示。	比較雙北綠建築空間分布。	{https://gbeval.tabc.org.tw/}	{doit,ntpc}	2026-05-02 17:38:05.29812+00	2026-05-02 17:38:05.29812+00	two_d	SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data\n    FROM (VALUES\n      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n      ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n      ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n      ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n      ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n      ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n    ) AS d(district)\n    LEFT JOIN public.green_buildings g\n      ON g.district = d.district AND g.valid = '1'\n    GROUP BY d.district\n    ORDER BY ARRAY_POSITION(\n      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n            '中山區','大同區','中正區','萬華區','大安區','文山區',\n            '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n            '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n            '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n            '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n            '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n      d.district)	\N	metrotaipei
green_buildings_rank	\N	{}	\N	static	\N	1	month	內政部建築研究所 綠建築標章	臺北市各行政區綠建築等級結構（長條圖%）。	每區一列 100% 堆疊長條：由左至右為合格、銅、銀、黃金、鑽石（占該區 valid=1 棟數比例）。	檢視各行政區認可等級結構差異。	{https://gbeval.tabc.org.tw/}	{doit}	2026-05-02 17:38:05.302881+00	2026-05-02 17:38:05.302881+00	three_d	SELECT d.district AS x_axis,\n          ''::text AS icon,\n          r.rank_name AS y_axis,\n          COALESCE(COUNT(g.id), 0)::int AS data\n    FROM (VALUES\n      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n    ) AS d(district)\n    CROSS JOIN (VALUES\n      (1, '合格級'),\n      (2, '銅級'),\n      (3, '銀級'),\n      (4, '黃金級'),\n      (5, '鑽石級')\n    ) AS r(rank_val, rank_name)\n    LEFT JOIN public.green_buildings g\n      ON g.district = d.district\n     AND g.rank = r.rank_val\n     AND g.city = '臺北市'\n     AND g.valid = '1'\n    GROUP BY d.district, r.rank_val, r.rank_name\n    ORDER BY ARRAY_POSITION(\n      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n            '中山區','大同區','中正區','萬華區','大安區','文山區'],\n      d.district),\n      r.rank_val	\N	taipei
green_buildings_rank	\N	{}	\N	static	\N	1	month	內政部建築研究所 綠建築標章	雙北各行政區綠建築等級結構（長條圖%）。	每區一列 100% 堆疊：合格→鑽石由左至右。	比較雙北各區等級結構。	{https://gbeval.tabc.org.tw/}	{doit,ntpc}	2026-05-02 17:38:05.305096+00	2026-05-02 17:38:05.305096+00	three_d	SELECT d.district AS x_axis,\n          ''::text AS icon,\n          r.rank_name AS y_axis,\n          COALESCE(COUNT(g.id), 0)::int AS data\n    FROM (VALUES\n      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n      ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n      ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n      ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n      ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n      ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n    ) AS d(district)\n    CROSS JOIN (VALUES\n      (1, '合格級'),\n      (2, '銅級'),\n      (3, '銀級'),\n      (4, '黃金級'),\n      (5, '鑽石級')\n    ) AS r(rank_val, rank_name)\n    LEFT JOIN public.green_buildings g\n      ON g.district = d.district\n     AND g.rank = r.rank_val\n     AND g.valid = '1'\n    GROUP BY d.district, r.rank_val, r.rank_name\n    ORDER BY ARRAY_POSITION(\n      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n            '中山區','大同區','中正區','萬華區','大安區','文山區',\n            '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n            '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n            '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n            '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n            '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n      d.district),\n      r.rank_val	\N	metrotaipei
green_buildings	\N	{11,12}	{"mode":"byParam","byParam":{"xParam":"ditrict"}}	static	\N	1	month	內政部建築研究所 綠建築標章	綠建築：行政區分布與等級結構	整合行政區圖、地圖點位與各區 100% 堆疊長條圖（合格至鑽石級）。	空間與等級結構並陳，支援政策規劃。	{https://gbeval.tabc.org.tw/}	{doit}	2026-05-02 17:38:05.306854+00	2026-05-02 18:16:48.163978+00	multi_chart	[{"id":921,"city":"taipei","types":["DistrictChart"]},{"id":922,"city":"taipei","types":["BarPercentChart"]},{"id":922,"city":"taipei","types":["ColumnChart"]}]	\N	taipei
green_buildings	\N	{11,12}	{"mode":"byParam","byParam":{"xParam":"ditrict"}}	static	\N	1	month	內政部建築研究所 綠建築標章	綠建築：行政區分布與等級結構（雙北）	雙北 41 區之行政區圖、地圖與各區等級堆疊長條圖。	跨市比較綠建築分布與等級。	{https://gbeval.tabc.org.tw/}	{doit,ntpc}	2026-05-02 17:38:05.309119+00	2026-05-02 18:16:48.168178+00	multi_chart	[{"id":921,"city":"metrotaipei","types":["DistrictChart"]},{"id":922,"city":"metrotaipei","types":["BarPercentChart"]},{"id":922,"city":"metrotaipei","types":["ColumnChart"]}]	\N	metrotaipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區電動車充電站充電槍數分布	呈現雙北41個行政區的電動車充電站充電槍總數（total_charging_points）。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。	政府可透過本組件掌握充電基礎設施的空間分布，識別充電槍不足的行政區，優先補充資源，推動低碳電動車普及。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:12:05.33001+00	2026-05-02 20:12:05.33001+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
bus_mrt_density	\N	{13,14}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區公車捷運站密度	以 100 公尺格網計算雙北 41 個行政區內公車站牌與捷運站涵蓋的格網數量，呈現各區域的大眾運輸服務密度分布。密度越高代表該區域公車與捷運站點覆蓋越密集，可反映大眾運輸服務的可及性。	交通局可透過本組件識別大眾運輸服務密度不足的行政區，優先規劃新增公車路線或捷運接駁，提升公共運輸的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:05:42.497237+00	2026-05-02 20:05:42.497237+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.bus_mrt_density e\n     ON SUBSTRING(e.district, 4) = d.district\n     AND (e.district LIKE '臺北市%' OR e.district LIKE '新北市%')\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
bus_mrt_density	\N	{13,14}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	雙北各行政區公車捷運站密度	以 100 公尺格網計算雙北 41 個行政區內公車站牌與捷運站涵蓋的格網數量，呈現各區域的大眾運輸服務密度分布。密度越高代表該區域公車與捷運站點覆蓋越密集。	比較雙北大眾運輸服務密度，協助跨區域路線擴建規劃與資源分配。	{}	{hackathon_team}	2026-05-02 20:05:52.255242+00	2026-05-02 20:05:52.255242+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.bus_mrt_density e\n     ON SUBSTRING(e.district, 4) = d.district\n     AND (e.district LIKE '臺北市%' OR e.district LIKE '新北市%')\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	metrotaipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	雙北各行政區電動車充電站充電槍數分布	呈現雙北41個行政區的電動車充電站充電槍總數（total_charging_points），共660站。資料來源為交通部TDX平台。	比較雙北充電基礎設施密度，協助政策規劃與充電站擴建優先區域選定。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:12:15.163961+00	2026-05-02 20:12:15.163961+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	metrotaipei
green_land_vegetation	\N	{}	\N	static	\N	1	year	臺北市政府開放資料平台 / 市容綠美化統計	臺北市行道樹、公園喬木、鄰里公園喬木、灌木、草花逐年培育量。	各類植栽培育量以分組縱向長條圖呈現，單位：株（盆）。各期為當年度培育量原值，未做累計。	城市植栽生態與綠化政策追蹤。	{}	{doit}	2026-05-02 19:02:44.266402+00	2026-05-02 19:02:44.266402+00	three_d	\nSELECT g.stat_label            AS x_axis,\n       ''::text                AS icon,\n       m.metric_label          AS y_axis,\n       m.metric_value::integer AS data\n  FROM public.green_land_beautification g\n  CROSS JOIN LATERAL (VALUES\n    (1, '行道樹[株]',          g.street_trees),\n    (2, '公園內喬木數[株]',     g.park_trees),\n    (3, '鄰里公園內喬木數[株]', g.neighborhood_park_trees),\n    (4, '灌木培育數[株]',       g.shrub_count),\n    (5, '草花培育數[盆]',       g.flower_pots)\n  ) AS m(ord, metric_label, metric_value)\n  where g.roc_year >= 104\n  ORDER BY g.roc_year, m.ord\n	\N	taipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區電動車充電站充電槍數分布	呈現雙北41個行政區的電動車充電站充電槍總數（total_charging_points）。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。	政府可透過本組件掌握充電基礎設施的空間分布，識別充電槍不足的行政區，優先補充資源，推動低碳電動車普及。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:20:43.258365+00	2026-05-02 20:20:43.258365+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	雙北各行政區電動車充電站充電槍數分布	呈現雙北41個行政區的電動車充電站充電槍總數（total_charging_points），共660站。資料來源為交通部TDX平台。	比較雙北充電基礎設施密度，協助政策規劃與充電站擴建優先區域選定。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:21:02.872475+00	2026-05-02 20:21:02.872475+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	metrotaipei
youbike_density	\N	{13,17}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	YouBike 開放資料	臺北市各行政區 YouBike 服務密度	以 100 公尺格網計算雙北 41 個行政區內 YouBike 站點涵蓋的格網數量，呈現各區域的服務密度分布。密度越高代表該區域 YouBike 站點覆蓋越密集，可反映公共自行車服務的可及性。	交通局可透過本組件識別 YouBike 服務密度不足的行政區，優先規劃新設站點，提升公共自行車的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:29:46.445303+00	2026-05-02 20:29:46.445303+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.youbike_density e\n     ON SUBSTRING(e.district, 4) = d.district\n     AND (e.district LIKE '臺北市%' OR e.district LIKE '新北市%')\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
youbike_density	\N	{13,17}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	YouBike 開放資料	雙北各行政區 YouBike 服務密度	以 100 公尺格網計算雙北 41 個行政區內 YouBike 站點涵蓋的格網數量，呈現各區域的服務密度分布。密度越高代表該區域 YouBike 站點覆蓋越密集。	比較雙北 YouBike 服務密度，協助跨區域站點擴建規劃與資源分配。	{}	{hackathon_team}	2026-05-02 20:29:58.166555+00	2026-05-02 20:29:58.166555+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.youbike_density e\n     ON SUBSTRING(e.district, 4) = d.district\n     AND (e.district LIKE '臺北市%' OR e.district LIKE '新北市%')\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	metrotaipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區電動車充電站充電槍數分布	呈現臺北市12個行政區的電動車充電站充電槍總數（total_charging_points）。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。	政府可透過本組件掌握充電基礎設施的空間分布，識別充電槍不足的行政區，優先補充資源，推動低碳電動車普及。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:37:58.301958+00	2026-05-02 20:37:58.301958+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district AND e.city = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區'],\n     d.district\n   )	\N	taipei
youbike_density	\N	{13,17}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	YouBike 開放資料	臺北市各行政區 YouBike 服務密度	以 100 公尺格網計算雙北 41 個行政區內 YouBike 站點涵蓋的格網數量，呈現各區域的服務密度分布。密度越高代表該區域 YouBike 站點覆蓋越密集，可反映公共自行車服務的可及性。	交通局可透過本組件識別 YouBike 服務密度不足的行政區，優先規劃新設站點，提升公共自行車的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:41:37.023037+00	2026-05-02 20:41:37.023037+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.youbike_density e\n     ON SUBSTRING(e.district, 4) = d.district AND e.city = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
youbike_density	\N	{13,17}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	YouBike 開放資料	臺北市各行政區 YouBike 服務密度	以 100 公尺格網計算雙北 41 個行政區內 YouBike 站點涵蓋的格網數量，呈現各區域的服務密度分布。密度越高代表該區域 YouBike 站點覆蓋越密集，可反映公共自行車服務的可及性。	交通局可透過本組件識別 YouBike 服務密度不足的行政區，優先規劃新設站點，提升公共自行車的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:44:50.618644+00	2026-05-02 20:44:50.618644+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n   ) AS d(district)\n   LEFT JOIN public.youbike_density e\n     ON SUBSTRING(e.district, 4) = d.district AND e.city = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
ev_stations	\N	{15}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區電動車充電站充電槍數分布	呈現臺北市12個行政區的電動車充電站充電槍總數（total_charging_points）。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。	政府可透過本組件掌握充電基礎設施的空間分布，識別充電槍不足的行政區，優先補充資源，推動低碳電動車普及。	{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}	{hackathon_team}	2026-05-02 20:45:48.155137+00	2026-05-02 20:45:48.155137+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.total_charging_points), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n   ) AS d(district)\n   LEFT JOIN public.ev_stations e ON e.district = d.district AND e.city = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區'],\n     d.district\n   )	\N	taipei
bus_mrt_density	\N	{13,14}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區公車捷運站密度	以 100 公尺格網計算雙北 41 個行政區內公車站牌與捷運站涵蓋的格網數量，呈現各區域的大眾運輸服務密度分布。密度越高代表該區域公車與捷運站點覆蓋越密集，可反映大眾運輸服務的可及性。	交通局可透過本組件識別大眾運輸服務密度不足的行政區，優先規劃新增公車路線或捷運接駁，提升公共運輸的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:48:29.927346+00	2026-05-02 20:48:29.927346+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),\n     ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),\n     ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),\n     ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),\n     ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),\n     ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')\n   ) AS d(district)\n   LEFT JOIN public.bus_mrt_density e\n     ON SUBSTRING(e.district, 4) = d.district AND e.district = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區',\n           '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',\n           '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',\n           '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',\n           '石碇區','坪林區','三芝區','石門區','八里區','平溪區',\n           '雙溪區','貢寮區','金山區','萬里區','烏來區'],\n     d.district\n   )	\N	taipei
bus_mrt_density	\N	{13,14}	{"mode":"byParam","byParam":{"xParam":"district"}}	static	\N	1	day	交通部 TDX 運輸資料流通服務	臺北市各行政區公車捷運站密度	以 100 公尺格網計算雙北 41 個行政區內公車站牌與捷運站涵蓋的格網數量，呈現各區域的大眾運輸服務密度分布。密度越高代表該區域公車與捷運站點覆蓋越密集，可反映大眾運輸服務的可及性。	交通局可透過本組件識別大眾運輸服務密度不足的行政區，優先規劃新增公車路線或捷運接駁，提升公共運輸的空間覆蓋率與市民使用便利性。	{}	{hackathon_team}	2026-05-02 20:49:34.091969+00	2026-05-02 20:49:34.091969+00	two_d	SELECT d.district AS x_axis, COALESCE(SUM(e.density), 0) AS data\n   FROM (VALUES\n     ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),\n     ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')\n   ) AS d(district)\n   LEFT JOIN public.bus_mrt_density e\n     ON SUBSTRING(e.district, 4) = d.district AND e.district = '台北市'\n   GROUP BY d.district\n   ORDER BY ARRAY_POSITION(\n     ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',\n           '中山區','大同區','中正區','萬華區','大安區','文山區'],\n     d.district\n   )	\N	taipei
green_land_summary	\N	{}	\N	static	\N	1	year	臺北市政府開放資料平台 / 市容綠美化統計	臺北市市容綠美化四項關鍵指標最新累計值。	道路綠地累計面積、路燈累計清洗汰換、後巷美化累計巷數、田園城市示範園圃面積（最新年份快照）。	城市市容綠美化政策成果一覽。	{}	{doit}	2026-05-02 19:02:44.270572+00	2026-05-02 19:09:52.085399+00	three_d	\nSELECT ''::text AS x_axis,\n       m.unit  AS icon,\n       m.label AS y_axis,\n       m.val   AS data\n  FROM (VALUES\n    ('道路綠地累計', '平方公尺',\n       (SELECT road_green_m2     FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),\n    ('路燈累計清洗汰換', '盞',\n       (SELECT streetlight_units FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),\n    ('後巷美化累計', '巷',\n       (SELECT alley_count       FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1)),\n    ('田園城市示範園圃', '平方公尺',\n       (SELECT demo_farm_m2      FROM public.green_land_beautification ORDER BY roc_year DESC LIMIT 1))\n  ) AS m(label, unit, val);\n	\N	taipei
metrotaipei_village_population_density	\N	{18}	{}	static	\N	1	month	內政部戶政司 / 村里界圖	臺北市村里級人口密度（人/km²）	以村里為單位呈現臺北市人口密度資訊。圖層本身為透明 fill，僅在地圖交叉比對時供使用者點擊村里檢視該里之縣市、鄉鎮市區、村里、人口數、戶數、面積、人口密度等資訊，方便與其他主題圖資（如自行車道、公車捷運站、人行道等）交叉判讀。	作為基本圖層疊加於各主題圖資之上，協助規劃單位評估高人口密度區域的設施需求、可及性、服務不足缺口等議題。	{https://data.gov.tw/}	{hackathon_team}	2026-05-02 22:42:55.230959+00	2026-05-02 22:42:55.230959+00	map_legend	SELECT unnest(ARRAY['村里人口密度']) AS name, 'fill' AS type	\N	taipei
metrotaipei_village_population_density	\N	{18}	{}	static	\N	1	month	內政部戶政司 / 村里界圖	雙北村里級人口密度（人/km²）	以村里為單位呈現雙北（臺北市 + 新北市）人口密度資訊。圖層本身為透明 fill，僅在地圖交叉比對時供使用者點擊村里檢視該里之縣市、鄉鎮市區、村里、人口數、戶數、面積、人口密度等資訊，方便與其他主題圖資（如自行車道、公車捷運站、人行道等）交叉判讀。	作為雙北通用的基本圖層，協助跨市、跨主題比較人口密度與都市機能、交通建設、公共服務之關聯。	{https://data.gov.tw/}	{hackathon_team}	2026-05-02 22:42:55.238291+00	2026-05-02 22:42:55.238291+00	map_legend	SELECT unnest(ARRAY['村里人口密度']) AS name, 'fill' AS type	\N	metrotaipei
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name, access_control, modify, read) FROM stdin;
1	admin	t	t	t
2	editor	f	t	t
3	viewer	f	f	t
4	admin	t	t	t
5	editor	f	t	t
6	viewer	f	f	t
7	admin	t	t	t
8	editor	f	t	t
9	viewer	f	f	t
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: view_points; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.view_points (id, user_id, center_x, center_y, zoom, pitch, bearing, name, point_type) FROM stdin;
\.


--
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Name: ai_chatlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ai_chatlog_id_seq', 1, false);


--
-- Name: auth_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_users_id_seq', 3, true);


--
-- Name: chat_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_logs_id_seq', 1, false);


--
-- Name: component_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.component_maps_id_seq', 18, true);


--
-- Name: components_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.components_id_seq', 3, true);


--
-- Name: contributors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contributors_id_seq', 1, false);


--
-- Name: dashboards_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dashboards_id_seq', 361, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.groups_id_seq', 4, true);


--
-- Name: incidents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.incidents_id_seq', 1, false);


--
-- Name: issues_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issues_id_seq', 1, false);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_seq', 9, true);


--
-- Name: view_points_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.view_points_id_seq', 1, false);


--
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: postgres
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- Name: ai_chatlog ai_chatlog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_chatlog
    ADD CONSTRAINT ai_chatlog_pkey PRIMARY KEY (id);


--
-- Name: auth_user_group_roles auth_user_group_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_group_roles
    ADD CONSTRAINT auth_user_group_roles_pkey PRIMARY KEY (auth_user_id, group_id, role_id);


--
-- Name: auth_users auth_users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_users
    ADD CONSTRAINT auth_users_email_key UNIQUE (email);


--
-- Name: auth_users auth_users_idno_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_users
    ADD CONSTRAINT auth_users_idno_key UNIQUE (idno);


--
-- Name: auth_users auth_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_users
    ADD CONSTRAINT auth_users_pkey PRIMARY KEY (id);


--
-- Name: auth_users auth_users_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_users
    ADD CONSTRAINT auth_users_uuid_key UNIQUE (uuid);


--
-- Name: chat_logs chat_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_logs
    ADD CONSTRAINT chat_logs_pkey PRIMARY KEY (id);


--
-- Name: component_charts component_charts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component_charts
    ADD CONSTRAINT component_charts_pkey PRIMARY KEY (index);


--
-- Name: component_maps component_maps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.component_maps
    ADD CONSTRAINT component_maps_pkey PRIMARY KEY (id);


--
-- Name: components components_index_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.components
    ADD CONSTRAINT components_index_key UNIQUE (index);


--
-- Name: components components_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.components
    ADD CONSTRAINT components_pkey PRIMARY KEY (id);


--
-- Name: contributors contributors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contributors
    ADD CONSTRAINT contributors_pkey PRIMARY KEY (id);


--
-- Name: dashboard_groups dashboard_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboard_groups
    ADD CONSTRAINT dashboard_groups_pkey PRIMARY KEY (dashboard_id, group_id);


--
-- Name: dashboards dashboards_index_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_index_key UNIQUE (index);


--
-- Name: dashboards dashboards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: incidents incidents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_pkey PRIMARY KEY (id);


--
-- Name: issues issues_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues
    ADD CONSTRAINT issues_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: view_points view_points_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.view_points
    ADD CONSTRAINT view_points_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_chatlog_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ai_chatlog_session ON public.ai_chatlog USING btree (session_id);


--
-- Name: idx_ai_chatlog_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ai_chatlog_user ON public.ai_chatlog USING btree (user_id);


--
-- Name: auth_user_group_roles fk_auth_user_group_roles_auth_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_group_roles
    ADD CONSTRAINT fk_auth_user_group_roles_auth_user FOREIGN KEY (auth_user_id) REFERENCES public.auth_users(id);


--
-- Name: auth_user_group_roles fk_auth_user_group_roles_group; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_group_roles
    ADD CONSTRAINT fk_auth_user_group_roles_group FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: auth_user_group_roles fk_auth_user_group_roles_role; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_group_roles
    ADD CONSTRAINT fk_auth_user_group_roles_role FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: dashboard_groups fk_dashboard_groups_dashboard; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboard_groups
    ADD CONSTRAINT fk_dashboard_groups_dashboard FOREIGN KEY (dashboard_id) REFERENCES public.dashboards(id);


--
-- Name: dashboard_groups fk_dashboard_groups_group; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboard_groups
    ADD CONSTRAINT fk_dashboard_groups_group FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: groups fk_groups_auth_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT fk_groups_auth_user FOREIGN KEY (create_by) REFERENCES public.auth_users(id);


--
-- Name: view_points fk_view_points_auth_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.view_points
    ADD CONSTRAINT fk_view_points_auth_user FOREIGN KEY (user_id) REFERENCES public.auth_users(id);


--
-- PostgreSQL database dump complete
--

