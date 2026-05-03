-- ==========================================================
-- car-type: 機動車輛新車領牌（月度）三張靜態圖表元件 SQL 樣板
-- 對齊 Taipei-City-Dashboard-Documentation/back-end-ch/components-db.md
-- 假設長表已 import 為 public.vehicle_registration_monthly：
--   period_sort TEXT  -- e.g. '114-06'
--   period_label TEXT -- e.g. '114年 6月'
--   vehicle_group TEXT
--   vehicle_type TEXT
--   region TEXT       -- '臺北市' / '新北市' / '總計'
--   fuel_category TEXT -- 'ICE' / 'BEV' / 'Hybrid'
--   count INT
-- ==========================================================

-- 1. components（主表）
INSERT INTO dashboardmanager.components (index, name) VALUES
  ('vehicle_type_count_taipei',   '新領牌車輛 - 各車種輛數'),
  ('vehicle_fuel_mix_taipei',     '新領牌車輛 - 燃料類別占比'),
  ('vehicle_fuel_trend_taipei',   '新領牌車輛 - 燃料類別月趨勢');

-- 2. component_charts（顏色、圖表類型、單位）
INSERT INTO dashboardmanager.component_charts (index, color, types, unit) VALUES
  ('vehicle_type_count_taipei',
    ARRAY['#4cb495','#56b96d','#9ac17c','#f5c860','#e58a4f'],
    ARRAY['BarChart'],
    '輛'),
  ('vehicle_fuel_mix_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '輛'),
  ('vehicle_fuel_trend_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['TimelineStackedChart'],
    '輛');

-- 3. query_charts（查詢設定 + SQL）
-- 3-1 vehicle_type_count_taipei: query_type=two_d
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_type_count_taipei','two_d','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT vehicle_type AS x_axis, SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region = '臺北市')
GROUP BY vehicle_type
ORDER BY data DESC
$$
);

-- 3-2 vehicle_fuel_mix_taipei: query_type=two_d
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_fuel_mix_taipei','two_d','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS x_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region = '臺北市')
GROUP BY fuel_category
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)
$$
);

-- 3-3 vehicle_fuel_trend_taipei: query_type=time
-- 注意：圖表 SQL 可以有 0 或 2 個 %s 占位符。靜態資料不需要時間範圍。
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'vehicle_fuel_trend_taipei','time','static',NULL,1,'month','交通部統計查詢網','taipei',
$$
SELECT
  to_timestamp(
    (CAST(split_part(period_sort, '-', 1) AS INTEGER) + 1911)::text
    || '-' || split_part(period_sort, '-', 2) || '-01',
    'YYYY-MM-DD'
  ) AT TIME ZONE 'Asia/Taipei' AS x_axis,
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region = '臺北市'
GROUP BY x_axis, fuel_category
ORDER BY y_axis, x_axis
$$
);
