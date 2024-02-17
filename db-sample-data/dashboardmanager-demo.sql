--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1 (Debian 16.1-1.pgdg110+1)
-- Dumped by pg_dump version 16.1

-- Started on 2024-02-16 10:38:43 UTC

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
-- TOC entry 3358 (class 0 OID 20086)
-- Dependencies: 215
-- Data for Name: component_charts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.component_charts (index, color, types, unit) FROM stdin;
pump_status	{#ff9800}	{GuageChart,BarPercentChart}	站
welfare_institutions	{#F65658,#F49F36,#F5C860,#9AC17C,#4CB495,#569C9A,#60819C,#2F8AB1}	{BarChart,DonutChart}	間
building_unsued	{#d16ae2,#655fad}	{MapLegend}	處
patrol_criminalcase	{#FD5696,#00A9E0}	{TimelineSeparateChart,TimelineStackedChart,ColumnLineChart}	件
welfare_population	{#2e999b,#80e3d4,#1f9b85,#a5ece0}	{ColumnChart,BarPercentChart,DistrictChart}	人
\.


--
-- TOC entry 3359 (class 0 OID 20091)
-- Dependencies: 216
-- Data for Name: component_maps; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.component_maps (title, type, size, icon, paint, property, index, id, source) FROM stdin;
抽水站	circle	big	\N	{"circle-color":["match",["get","all_pumb_lights"],"+","#ff9800","#00B2FF"]}	[{"key":"station_name","name":"站名"},{"key":"all_pumb_lights","name":"總抽水狀態"},{"key":"warning_level","name":"目前警戒值"},{"key":"start_pumping_level","name":"抽水起始值"},{"key":"door_num","name":"水門數目"},{"key":"pumb_num","name":"抽水機數目"},{"key":"river_basin","name":"流域"},{"key":"rec_time","name":"記錄時間"}]	patrol_rain_floodgate	50	geojson
閒置市有公有地	fill	\N	\N	{"fill-color":"#d16ae2","fill-opacity":0.7}	[{"key":"10712土地_1_土地權屬情形","name":"土地權屬情形"},{"key":"10712土地_1_管理機關","name":"管理機關"}]	building_unsued_land	42	geojson
下水道	circle	big	\N	{"circle-color": ["interpolate", ["linear"], ["to-number", ["get", "ground_far"]], -100, "#F92623", 0.51, "#81bcf5"]}	[{"key": "station_no", "name": "NO"}, {"key": "station_name", "name": "站名"}, {"key": "ground_far", "name": "距地面高[公尺]"}, {"key": "level_out", "name": "水位高[公尺]"}, {"key": "rec_time", "name": "紀錄時間"}]	patrol_rain_sewer	60	geojson
社福機構	circle	big	\N	{"circle-color": ["match", ["get", "main_type"], "銀髮族服務", "#F49F36", "身障機構", "#F65658", "兒童與少年服務", "#F5C860", "社區服務、NPO", "#9AC17C", "婦女服務", "#4CB495", "貧困危機家庭服務", "#569C9A", "保護性服務", "#60819C", "#2F8AB1"]}	[{"key": "main_type", "name": "主要類別"}, {"key": "sub_type", "name": "次要分類"}, {"key": "name", "name": "名稱"}, {"key": "address", "name": "地址"}]	socl_welfare_organization_plc	64	geojson
閒置市有(公用)建物	circle	big	\N	{"circle-color":"#655fad"}	[{"key":"門牌","name":"門牌"},{"key":"房屋現況","name":"房屋現況"},{"key":"目前執行情形","name":"目前執行情形"},{"key":"閒置樓層_閒置樓層/該建物總樓層","name":"閒置樓層/總樓層"},{"key":"閒置面積㎡","name":"閒置面積㎡"},{"key":"基地管理機關","name":"基地管理機關"},{"key":"建物管理機關","name":"建物管理機關"},{"key":"原使用用途","name":"原使用用途"},{"key":"基地所有權人","name":"基地所有權人"},{"key":"建物標示","name":"建物標示"},{"key":"建築完成日期","name":"建築完成日期"}]	building_unsued_public	43	geojson
\.


--
-- TOC entry 3361 (class 0 OID 20097)
-- Dependencies: 218
-- Data for Name: components; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.components (index, name, history_config, map_filter, update_freq, update_freq_unit, source, short_desc, long_desc, use_case, links, contributors, created_at, updated_at, query_type, query_chart, query_history, id, time_from, time_to, map_config_ids) FROM stdin;
welfare_population	社福人口	\N	\N	\N	\N	社會局	顯示社會福利人口（身障、低收、中低收、低收身障）的比例	顯示社會福利人口（身障、低收、中低收、低收身障）的比例，資料來源為台北市社會局內部資料，每月15號更新。	社福人口比例的資料能讓我們了解台北市社會福利的需求變化，從而規劃更貼近民眾需求的社會福利措施。	{}	{tuic}	2023-12-20 05:56:00+00	2024-01-09 03:32:59.233032+00	three_d	SELECT x_axis, y_axis, data FROM (SELECT district AS x_axis, '低收' AS y_axis, is_low_income AS data FROM app_calcu_monthly_socl_welfare_people_ppl UNION ALL SELECT district AS x_axis, '中低收' AS y_axis, is_low_middle_income AS data FROM app_calcu_monthly_socl_welfare_people_ppl UNION ALL SELECT district AS x_axis, '身障補助' AS y_axis, is_disabled_allowance AS data FROM app_calcu_monthly_socl_welfare_people_ppl UNION ALL SELECT district AS x_axis, '身障' AS y_axis, is_disabled AS data FROM app_calcu_monthly_socl_welfare_people_ppl) AS combined_data WHERE x_axis != 'e' ORDER BY ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區']::varchar[], combined_data.x_axis), ARRAY_POSITION(ARRAY['低收', '中低收', '身障補助', '身障'], combined_data.y_axis);	\N	90	static	\N	{}
welfare_institutions	社福機構	\N	{"mode": "byParam", "byParam": {"xParam": "main_type"}}	\N	\N	社會局	顯示社會福利機構點位及機構類型	顯示社會福利機構點位及機構類型，資料來源為台北市社會局內部資料，每月15日更新。	根據機構空間的分佈情況，檢視社會福利機構是否均勻分布，同時整合市有土地、社會住宅等潛在可使用之空間，以研擬增設位置與類型的方案。	{https://data.taipei/dataset/detail?id=cabdf272-e0ec-4e4e-9136-f4b8596f35d9}	{tuic}	2023-12-20 05:56:00+00	2023-12-20 05:56:00+00	two_d	select main_type as x_axis,count(*) as data from socl_welfare_organization_plc group by main_type order by data desc	\N	82	static	\N	{64}
patrol_criminalcase	刑事統計	\N	\N	1	month	警察局	顯示近兩年每月的刑案統計資訊	顯示近兩年每月的刑案統計資訊，資料來源為台北市主計處開放資料，每月更新。	藉由掌握台北市刑事案件近2年的統計資訊，我們可以瞭解案件的增減趨勢及相關特徵，有助於制定更有效的治安策略。	{https://data.taipei/dataset/detail?id=dc7e246a-a88e-42f8-8cd6-9739209af774}	{tuic}	2023-12-20 05:56:00+00	2024-01-17 06:53:41.810511+00	time	WITH date_range AS (\n  SELECT\n    '%s'::timestamp with time zone AS start_time,\n    '%s'::timestamp with time zone AS end_time\n)\nSELECT "年月別" as x_axis, '發生件數' as y_axis, "發生件數[件]" as data FROM public.patrol_criminal_case \nWHERE 年月別 BETWEEN  (SELECT start_time FROM date_range) AND (SELECT end_time FROM date_range)\nUNION ALL\nSELECT "年月別" as x_axis, '破獲件數' as y_axis, "破獲件數/總計[件]" as data FROM public.patrol_criminal_case\nWHERE 年月別 BETWEEN  (SELECT start_time FROM date_range) AND (SELECT end_time FROM date_range)	\N	7	year_ago	now	{}
building_unsued	閒置市有財產	\N	{"mode":"byLayer"}	\N	\N	財政局	\N	\N	\N	{}	{tuic}	2023-12-20 05:56:00+00	2024-01-11 06:01:02.392686+00	map_legend	select '閒置市有公有地' as name, count(*) as value, 'fill' as type from building_unsued_land\nunion all\nselect '閒置市有(公用)建物' as name, count(*) as value, 'circle' as type from building_unsued_public	\N	30	static	\N	{42,43}
pump_status	抽水站狀態	\N	{"mode":"byParam","byParam":{"yParam":"all_pumb_lights"}}	10	minute	工務局水利處	顯示當前全市開啟的抽水站數量	顯示當前全市開啟的抽水站數量，資料來源為工務局水利處內部資料，每十分鐘更新。	考慮當日天氣及「水位監測」組件的資料，來探討抽水站的運作狀況與水位異常之間的關聯性。	{}	{tuic}	2023-12-20 05:56:00+00	2024-01-25 09:36:14.565347+00	percent	select '啟動抽水站' as x_axis, y_axis, data from \n(\nselect '啟動中' as y_axis, count(*) as data from patrol_rain_floodgate where all_pumb_lights = '+'\nunion all\nselect '未啟動' as y_axis, count(*) as data from patrol_rain_floodgate where all_pumb_lights != '+'\n) as parsed_data	\N	43	current	\N	{50}
\.


--
-- TOC entry 3364 (class 0 OID 20106)
-- Dependencies: 221
-- Data for Name: dashboards; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dashboards (name, components, icon, updated_at, created_at, id, index) FROM stdin;
範例組件	{7,43,82,90}	bug_report	2024-01-24 09:12:29.419499+00	2023-12-27 06:11:56.841132+00	1	demo-components
圖資資訊	{30}	public	2024-01-11 09:32:32.465099+00	2024-01-11 09:32:32.465099+00	2	map-layers
\.


--
-- TOC entry 3366 (class 0 OID 20112)
-- Dependencies: 223
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.groups (id, name) FROM stdin;
1	public
\.


--
-- TOC entry 3363 (class 0 OID 20103)
-- Dependencies: 220
-- Data for Name: dashboard_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dashboard_groups (dashboard_id, group_id) FROM stdin;
1	1
2	1
\.


--
-- TOC entry 3374 (class 0 OID 0)
-- Dependencies: 217
-- Name: component_maps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.component_maps_id_seq', 90, true);


--
-- TOC entry 3375 (class 0 OID 0)
-- Dependencies: 225
-- Name: components_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.components_id_seq', 1, false);


--
-- TOC entry 3376 (class 0 OID 0)
-- Dependencies: 219
-- Name: components_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.components_id_seq', 68, true);


--
-- TOC entry 3377 (class 0 OID 0)
-- Dependencies: 222
-- Name: dashboards_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dashboards_id_seq', 71, true);


--
-- TOC entry 3378 (class 0 OID 0)
-- Dependencies: 224
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.groups_id_seq', 41, true);


-- Completed on 2024-02-16 10:38:44 UTC

--
-- PostgreSQL database dump complete
--

