-- ===========================================================================
-- car-type / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
-- 說明：僅管理 components / component_charts / query_charts（不含 dashboards）。
--   ⚠️ 儀表板（永續環境 sustainable_env_taipei/metrotaipei）由
--       component_doc/seed/03_sustainable_env_dashboard.sql 統一管理。
--
-- 雙北 query_charts 作法：
--   * components.id（901/902/903）共用
--   * query_charts 每個 index 各 city='taipei' / 'metrotaipei' 一筆
-- ===========================================================================

-- 0. 移除既有相同 index/id 的舊紀錄，使本檔案可重複執行
DELETE FROM public.query_charts
 WHERE index IN ('vehicle_type_count_taipei','vehicle_fuel_mix_taipei','vehicle_fuel_trend_taipei');
DELETE FROM public.component_charts
 WHERE index IN ('vehicle_type_count_taipei','vehicle_fuel_mix_taipei','vehicle_fuel_trend_taipei');
DELETE FROM public.components
 WHERE index IN ('vehicle_type_count_taipei','vehicle_fuel_mix_taipei','vehicle_fuel_trend_taipei')
    OR id IN (901, 902, 903);

-- 1. components（主表）
INSERT INTO public.components (id, index, name) VALUES
  (901,   'vehicle_type_count_taipei', '新領牌車輛 - 各車種輛數'),
  (902, 'vehicle_fuel_mix_taipei',   '新領牌車輛 - 燃料類別占比'),
  (903, 'vehicle_fuel_trend_taipei', '新領牌車輛 - 燃料類別月趨勢');

-- 2. component_charts（顏色 / 圖表類型 / 單位）
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('vehicle_type_count_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['ColumnChart'],
    '輛'),
  ('vehicle_fuel_mix_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '輛'),
  ('vehicle_fuel_trend_taipei',
    ARRAY['#9b6b3e','#4cb495','#f5c860'],
    ARRAY['TimelineStackedChart'],
    '輛');

-- 3. query_charts（查詢設定 + SQL 指令；每 index 兩筆 city）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES
(
  'vehicle_type_count_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛各車種輛數（最新月份）。',
  '以最新月份為例，呈現大客車、大貨車、小客車、小貨車、機車五個保留車種的新領牌輛數。已排除全體總計、汽車匯總列、特種車。',
  '比較各車種登記輛數，輔助綠能轉型／污染源評估。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT
  v.vehicle_type AS x_axis,
  CASE f.fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  COALESCE(SUM(m.count), 0) AS data
FROM
  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)
  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)
  LEFT JOIN public.vehicle_registration_monthly m
    ON  m.vehicle_type  = v.vehicle_type
    AND m.fuel_category = f.fuel_category
    AND m.region        = '臺北市'
    AND m.period_sort   = (SELECT MAX(period_sort)
                           FROM public.vehicle_registration_monthly
                           WHERE region = '臺北市')
GROUP BY v.vehicle_type, f.fuel_category
ORDER BY
  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),
  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)$$,
  NULL,
  'taipei'
),
(
  'vehicle_type_count_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛各車種輛數（最新月份，臺北+新北合計）。',
  '以雙北共同最新月份為例，將臺北市與新北市同車種、同燃料之新領牌輛數加總後呈現。',
  '比較各車種登記輛數，輔助大臺北綠能轉型／污染源評估。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT
  v.vehicle_type AS x_axis,
  CASE f.fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS y_axis,
  COALESCE(SUM(m.count), 0) AS data
FROM
  (VALUES ('小客車'),('機車'),('小貨車'),('大客車'),('大貨車')) AS v(vehicle_type)
  CROSS JOIN (VALUES ('ICE'),('BEV'),('Hybrid')) AS f(fuel_category)
  LEFT JOIN public.vehicle_registration_monthly m
    ON  m.vehicle_type  = v.vehicle_type
    AND m.fuel_category = f.fuel_category
    AND m.region IN ('臺北市', '新北市')
    AND m.period_sort   = (SELECT MAX(period_sort)
                           FROM public.vehicle_registration_monthly
                           WHERE region IN ('臺北市', '新北市'))
GROUP BY v.vehicle_type, f.fuel_category
ORDER BY
  ARRAY_POSITION(ARRAY['小客車','機車','小貨車','大客車','大貨車']::text[], v.vehicle_type),
  ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid']::text[], f.fuel_category)$$,
  NULL,
  'metrotaipei'
),
(
  'vehicle_fuel_mix_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛 ICE/BEV/Hybrid 占比（最新月份）。',
  'ICE：(1)汽油、(2)柴油、(4)液化石油氣、(5)汽油/LPG；BEV：(3)電能；Hybrid：(6)~(13) 其餘混合與雙動力分類。以最新月份為例。',
  '觀察油轉電進度，作為綠色城市核心指標。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT
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
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)$$,
  NULL,
  'taipei'
),
(
  'vehicle_fuel_mix_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛 ICE/BEV/Hybrid 占比（最新月份，臺北+新北合計）。',
  '將雙北同月份輛數加總後，再依燃料三類計算占比。',
  '觀察大臺北油轉電進度。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT
  CASE fuel_category
       WHEN 'ICE'    THEN '純油 (ICE)'
       WHEN 'BEV'    THEN '純電 (BEV)'
       WHEN 'Hybrid' THEN '油電/混合 (Hybrid)'
  END AS x_axis,
  SUM(count) AS data
FROM public.vehicle_registration_monthly
WHERE region IN ('臺北市', '新北市')
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.vehicle_registration_monthly
                     WHERE region IN ('臺北市', '新北市'))
GROUP BY fuel_category
ORDER BY ARRAY_POSITION(ARRAY['ICE','BEV','Hybrid'], fuel_category)$$,
  NULL,
  'metrotaipei'
),
(
  'vehicle_fuel_trend_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '臺北市新領牌車輛 ICE/BEV/Hybrid 之月趨勢。',
  '依燃料三類匯總後逐月堆疊。月度資料；已排除整年列、(1~3月) 等累計列。',
  '觀察臺北市油轉電的月度趨勢與季節性變化。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'time',
  $$SELECT
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
ORDER BY y_axis, x_axis$$,
  NULL,
  'taipei'
),
(
  'vehicle_fuel_trend_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '交通部統計查詢網',
  '雙北新領牌車輛 ICE/BEV/Hybrid 之月趨勢（臺北+新北合計）。',
  '同月份兩市輛數加總後逐月堆疊。',
  '觀察雙北油轉電的月度趨勢與季節性變化。',
  ARRAY['https://stat.motc.gov.tw/mocdb/stmain.jsp?sys=100','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'time',
  $$SELECT
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
WHERE region IN ('臺北市', '新北市')
GROUP BY x_axis, fuel_category
ORDER BY y_axis, x_axis$$,
  NULL,
  'metrotaipei'
);

-- ⚠️ dashboards / dashboard_groups 已移至：
--    component_doc/seed/03_sustainable_env_dashboard.sql
-- 請在此檔執行後，另行執行該檔以建立「永續環境」儀表板。
