-- ============================================================
-- DB Setup SQL for eco_cup (循環杯友善據點)
-- Run this against postgres-manager (dashboard manager DB)
-- ============================================================

-- --------------------------------------------------------
-- 1. components: Register the component
-- --------------------------------------------------------
INSERT INTO public.components (id, index, name)
VALUES (
    300,
    'eco_cup_store',
    '循環杯友善據點'
)
ON CONFLICT (id) DO UPDATE SET
    index = EXCLUDED.index,
    name = EXCLUDED.name;


-- --------------------------------------------------------
-- 2. component_charts: Chart config (BarChart + Map)
-- --------------------------------------------------------
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'eco_cup_store',
    '{#4CAF50}',
    '{BarChart}',
    '家'
)
ON CONFLICT (index) DO UPDATE SET
    color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;


-- --------------------------------------------------------
-- 3. component_maps: Map layer config
-- --------------------------------------------------------
-- Note: id 102 is used. Adjust if it conflicts with existing data.

-- 3a. Circle layer for eco cup store locations
INSERT INTO public.component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES (
    102,
    'eco_cup_store',
    '循環杯據點',
    'circle',
    'geojson',
    NULL,
    NULL,
    '{"circle-color": "#4CAF50"}',
    '[{"key":"brand","name":"品牌"},{"key":"store_name","name":"門市名稱"},{"key":"address","name":"地址"},{"key":"phone","name":"電話"}]'
)
ON CONFLICT (id) DO UPDATE SET
    index = EXCLUDED.index,
    title = EXCLUDED.title,
    type = EXCLUDED.type,
    source = EXCLUDED.source,
    size = EXCLUDED.size,
    icon = EXCLUDED.icon,
    paint = EXCLUDED.paint,
    property = EXCLUDED.property;

-- 3b. Fill layer for district choropleth heatmap
INSERT INTO public.component_maps (id, index, title, type, source, size, icon, paint, property)
VALUES (
    103,
    'eco_cup_district_map',
    '循環杯行政區熱力圖',
    'fill',
    'geojson',
    NULL,
    NULL,
    '{"fill-opacity": 0.6}',
    '[{"key":"TNAME","name":"行政區"},{"key":"count","name":"據點數"}]'
)
ON CONFLICT (id) DO UPDATE SET
    index = EXCLUDED.index,
    title = EXCLUDED.title,
    type = EXCLUDED.type,
    source = EXCLUDED.source,
    size = EXCLUDED.size,
    icon = EXCLUDED.icon,
    paint = EXCLUDED.paint,
    property = EXCLUDED.property;


-- --------------------------------------------------------
-- 4. query_charts: Query config for Taipei + New Taipei
-- --------------------------------------------------------

-- 4a. Taipei City (taipei)
INSERT INTO public.query_charts (
    index,
    history_config,
    map_config_ids,
    map_filter,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES (
    'eco_cup_store',
    NULL,
    '{102}',
    '{}',
    'static',
    NULL,
    1,
    'month',
    '環保署/各連鎖品牌',
    '顯示臺北市循環杯友善據點分布。',
    '顯示臺北市提供循環杯（環保杯）服務之連鎖品牌門市據點分布。循環杯是環保署推動的減塑措施，消費者可在合作門市借用可重複使用的杯子，減少一次性飲料杯的使用。此資料涵蓋臺北市各行政區的循環杯據點，包括 21風味館、subway、義美食品、摩斯漢堡等連鎖品牌門市，方便民眾查詢附近可借用循環杯的地點。',
    '適用於環保政策推廣、綠色生活導引及都市永續發展分析。政府與環保團體可透過此資料評估循環杯據點覆蓋率，識別服務空白區域，並規劃新增據點以提升便民性。市民亦可利用此資訊查詢鄰近的循環杯門市，實踐減塑生活。企業與研究機構可結合人口密度、交通流量等資料，分析循環杯使用潛力與減塑效益。',
    '{}',
    '{doit}',
    NOW(),
    NOW(),
    'two_d',
    E'SELECT brand as x_axis, COUNT(*) as data FROM eco_cup_store WHERE city = \'臺北市\' GROUP BY brand ORDER BY data DESC',
    NULL,
    'taipei'
)
ON CONFLICT (index, city) DO UPDATE SET
    history_config = EXCLUDED.history_config,
    map_config_ids = EXCLUDED.map_config_ids,
    map_filter = EXCLUDED.map_filter,
    time_from = EXCLUDED.time_from,
    time_to = EXCLUDED.time_to,
    update_freq = EXCLUDED.update_freq,
    update_freq_unit = EXCLUDED.update_freq_unit,
    source = EXCLUDED.source,
    short_desc = EXCLUDED.short_desc,
    long_desc = EXCLUDED.long_desc,
    use_case = EXCLUDED.use_case,
    links = EXCLUDED.links,
    contributors = EXCLUDED.contributors,
    updated_at = EXCLUDED.updated_at,
    query_type = EXCLUDED.query_type,
    query_chart = EXCLUDED.query_chart,
    query_history = EXCLUDED.query_history;


-- 4b. New Taipei City (metrotaipei)
INSERT INTO public.query_charts (
    index,
    history_config,
    map_config_ids,
    map_filter,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES (
    'eco_cup_store',
    NULL,
    '{102}',
    '{}',
    'static',
    NULL,
    1,
    'month',
    '環保署/各連鎖品牌',
    '顯示新北市循環杯友善據點分布。',
    '顯示新北市提供循環杯（環保杯）服務之連鎖品牌門市據點分布。循環杯是環保署推動的減塑措施，消費者可在合作門市借用可重複使用的杯子，減少一次性飲料杯的使用。此資料涵蓋新北市各行政區的循環杯據點，包括 subway、摩斯漢堡等連鎖品牌門市，方便民眾查詢附近可借用循環杯的地點。',
    '適用於環保政策推廣、綠色生活導引及都市永續發展分析。政府與環保團體可透過此資料評估循環杯據點覆蓋率，識別服務空白區域，並規劃新增據點以提升便民性。市民亦可利用此資訊查詢鄰近的循環杯門市，實踐減塑生活。企業與研究機構可結合人口密度、交通流量等資料，分析循環杯使用潛力與減塑效益。',
    '{}',
    '{ntpc}',
    NOW(),
    NOW(),
    'two_d',
    E'SELECT brand as x_axis, COUNT(*) as data FROM eco_cup_store WHERE city = \'新北市\' GROUP BY brand ORDER BY data DESC',
    NULL,
    'metrotaipei'
)
ON CONFLICT (index, city) DO UPDATE SET
    history_config = EXCLUDED.history_config,
    map_config_ids = EXCLUDED.map_config_ids,
    map_filter = EXCLUDED.map_filter,
    time_from = EXCLUDED.time_from,
    time_to = EXCLUDED.time_to,
    update_freq = EXCLUDED.update_freq,
    update_freq_unit = EXCLUDED.update_freq_unit,
    source = EXCLUDED.source,
    short_desc = EXCLUDED.short_desc,
    long_desc = EXCLUDED.long_desc,
    use_case = EXCLUDED.use_case,
    links = EXCLUDED.links,
    contributors = EXCLUDED.contributors,
    updated_at = EXCLUDED.updated_at,
    query_type = EXCLUDED.query_type,
    query_chart = EXCLUDED.query_chart,
    query_history = EXCLUDED.query_history;


-- --------------------------------------------------------
-- 6. dashboards: Add components to dashboards
-- --------------------------------------------------------
-- 6a. Deduplicate components array (fix any previous duplicate inserts)
UPDATE public.dashboards
SET components = ARRAY(
    SELECT DISTINCT e
    FROM UNNEST(components) AS e
    ORDER BY e
)
WHERE index IN ('map-layers-taipei', 'map-layers-metrotaipei');

-- 6b. Add eco_cup map layer component
UPDATE public.dashboards
SET components = array_append(components, 300)
WHERE index IN ('map-layers-taipei', 'map-layers-metrotaipei')
  AND NOT (components @> ARRAY[300]);

-- 6c. Remove eco_cup_brand if it exists
UPDATE public.dashboards
SET components = array_remove(components, 301)
WHERE index IN ('map-layers-taipei', 'map-layers-metrotaipei');

-- --------------------------------------------------------
-- 7. eco_cup_district: District distribution component
-- --------------------------------------------------------

-- 7a. Register the district component
INSERT INTO public.components (id, index, name)
VALUES (
    302,
    'eco_cup_district',
    '循環杯行政區分布'
)
ON CONFLICT (id) DO UPDATE SET
    index = EXCLUDED.index,
    name = EXCLUDED.name;

-- 7b. Chart config (DistrictChart)
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'eco_cup_district',
    '{#4CAF50}',
    '{DistrictChart}',
    '家'
)
ON CONFLICT (index) DO UPDATE SET
    color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- 7c. Query config for Taipei
INSERT INTO public.query_charts (
    index,
    history_config,
    map_config_ids,
    map_filter,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES (
    'eco_cup_district',
    NULL,
    '{103}',
    '{"mode":"byParam","byParam":{"xParam":"district"}}',
    'static',
    NULL,
    1,
    'month',
    '環保署/各連鎖品牌',
    '顯示臺北市各行政區循環杯據點數量分布。',
    '顯示臺北市各行政區循環杯友善據點的數量分布。透過行政區著色圖，可直觀了解循環杯服務在不同行政區的覆蓋密度，識別據點集中區域與服務空白區域。顏色越深代表該行政區的循環杯據點數量越多。',
    '適用於環保政策評估與城市規劃。政府單位可透過此圖表評估循環杯計畫在各行政區的推廣成效，識別據點覆蓋不足區域並規劃新增據點。點擊特定行政區可篩選地圖，只顯示該區域的循環杯門市位置，方便進行區域性分析與規劃。',
    '{}',
    '{doit}',
    NOW(),
    NOW(),
    'two_d',
    E'SELECT district as x_axis, COUNT(*) as data FROM eco_cup_store WHERE city = \'臺北市\' GROUP BY district ORDER BY data DESC',
    NULL,
    'taipei'
)
ON CONFLICT (index, city) DO UPDATE SET
    history_config = EXCLUDED.history_config,
    map_config_ids = EXCLUDED.map_config_ids,
    map_filter = EXCLUDED.map_filter,
    time_from = EXCLUDED.time_from,
    time_to = EXCLUDED.time_to,
    update_freq = EXCLUDED.update_freq,
    update_freq_unit = EXCLUDED.update_freq_unit,
    source = EXCLUDED.source,
    short_desc = EXCLUDED.short_desc,
    long_desc = EXCLUDED.long_desc,
    use_case = EXCLUDED.use_case,
    links = EXCLUDED.links,
    contributors = EXCLUDED.contributors,
    updated_at = EXCLUDED.updated_at,
    query_type = EXCLUDED.query_type,
    query_chart = EXCLUDED.query_chart,
    query_history = EXCLUDED.query_history;

-- 7d. Query config for New Taipei
INSERT INTO public.query_charts (
    index,
    history_config,
    map_config_ids,
    map_filter,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES (
    'eco_cup_district',
    NULL,
    '{103}',
    '{"mode":"byParam","byParam":{"xParam":"district"}}',
    'static',
    NULL,
    1,
    'month',
    '環保署/各連鎖品牌',
    '顯示雙北各行政區循環杯據點數量分布。',
    '顯示臺北市與新北市各行政區循環杯友善據點的數量分布。透過行政區著色圖，可直觀了解循環杯服務在不同行政區的覆蓋密度，識別據點集中區域與服務空白區域。',
    '適用於環保政策評估與城市規劃。政府單位可透過此圖表評估循環杯計畫在各行政區的推廣成效，識別據點覆蓋不足區域。點擊特定行政區可篩選地圖，只顯示該區域的循環杯門市位置。',
    '{}',
    '{doit,ntpc}',
    NOW(),
    NOW(),
    'two_d',
    E'SELECT x_axis, SUM(data) as data FROM (SELECT district as x_axis, COUNT(*) as data FROM eco_cup_store WHERE city = \'臺北市\' GROUP BY district UNION ALL SELECT district as x_axis, COUNT(*) as data FROM eco_cup_store WHERE city = \'新北市\' GROUP BY district) d GROUP BY x_axis ORDER BY data DESC',
    NULL,
    'metrotaipei'
)
ON CONFLICT (index, city) DO UPDATE SET
    history_config = EXCLUDED.history_config,
    map_config_ids = EXCLUDED.map_config_ids,
    map_filter = EXCLUDED.map_filter,
    time_from = EXCLUDED.time_from,
    time_to = EXCLUDED.time_to,
    update_freq = EXCLUDED.update_freq,
    update_freq_unit = EXCLUDED.update_freq_unit,
    source = EXCLUDED.source,
    short_desc = EXCLUDED.short_desc,
    long_desc = EXCLUDED.long_desc,
    use_case = EXCLUDED.use_case,
    links = EXCLUDED.links,
    contributors = EXCLUDED.contributors,
    updated_at = EXCLUDED.updated_at,
    query_type = EXCLUDED.query_type,
    query_chart = EXCLUDED.query_chart,
    query_history = EXCLUDED.query_history;

-- 7e. Add district component to dashboards
UPDATE public.dashboards
SET components = array_append(components, 302)
WHERE index IN ('map-layers-taipei', 'map-layers-metrotaipei')
  AND NOT (components @> ARRAY[302]);
