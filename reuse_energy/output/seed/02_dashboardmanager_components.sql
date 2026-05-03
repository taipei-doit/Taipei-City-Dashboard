-- ===========================================================================
-- reuse_energy / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
-- 說明：僅管理 components / component_charts / query_charts（不含 dashboards）。
--   ⚠️ 儀表板（永續環境 sustainable_env_taipei/metrotaipei）由
--       component_doc/seed/03_sustainable_env_dashboard.sql 統一管理。
--
-- 雙北 query_charts 作法：
--   * components.id（911/912/913/914）共用
--   * query_charts 對每個 index 各插 city='taipei' / city='metrotaipei' 兩筆
-- ===========================================================================

DELETE FROM public.query_charts
 WHERE index IN ('reuse_energy_capacity_metrotaipei','reuse_energy_mix_taipei','reuse_energy_trend_taipei','reuse_energy_trend_column_taipei');
DELETE FROM public.component_charts
 WHERE index IN ('reuse_energy_capacity_metrotaipei','reuse_energy_mix_taipei','reuse_energy_trend_taipei','reuse_energy_trend_column_taipei');
DELETE FROM public.components
 WHERE index IN ('reuse_energy_capacity_metrotaipei','reuse_energy_mix_taipei','reuse_energy_trend_taipei','reuse_energy_trend_column_taipei')
    OR id IN (911, 912, 913, 914);

-- 1. components（共用，name 不帶城市字樣，雙北儀表板顯示也合理）
INSERT INTO public.components (id, index, name) VALUES
  (911,   'reuse_energy_capacity_metrotaipei', '再生能源裝置容量 - 雙北比較'),
  (912, 'reuse_energy_mix_taipei',           '再生能源裝置容量 - 能源占比'),
  (913, 'reuse_energy_trend_taipei',         '再生能源裝置容量 - 年趨勢'),
  (914, 'reuse_energy_trend_column_taipei',
                                                    '再生能源裝置容量 - 年趨勢（縱向長條）');

-- 2. component_charts（顏色／圖表類型／單位皆共用）
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('reuse_energy_capacity_metrotaipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)'),
  ('reuse_energy_mix_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def','#848c94'],
    ARRAY['DonutChart','BarChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['TimelineStackedChart'],
    '瓩 (kW)'),
  ('reuse_energy_trend_column_taipei',
    ARRAY['#4cb495','#f5c860','#5b8def'],
    ARRAY['ColumnChart'],
    '瓩 (kW)');

-- 3. query_charts（每個 index 各兩筆 city）
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES
-- 3-1 雙北比較（city=metrotaipei，雙北儀表板使用）
(
  'reuse_energy_capacity_metrotaipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。',
  '並列臺北市與新北市三類再生能源裝置容量，以堆疊縱向長條圖呈現；臺北市風力為 0。',
  '比較雙北綠能發展結構，輔助再生能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT
  CASE c.city WHEN '台北市' THEN '臺北市' ELSE c.city END AS x_axis,
  e.energy_type AS y_axis,
  COALESCE(SUM(m.capacity_kw), 0) AS data
FROM
  (VALUES ('台北市'),('新北市')) AS c(city)
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON  m.city        = c.city
    AND m.energy_type = e.energy_type
    AND m.period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY c.city, e.energy_type
ORDER BY
  ARRAY_POSITION(ARRAY['台北市','新北市']::text[], c.city),
  ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)$$,
  NULL,
  'metrotaipei'
),
-- 3-1' 雙北比較（city=taipei，臺北儀表板使用；同一份 SQL）
(
  'reuse_energy_capacity_metrotaipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期再生能源（風力／太陽光電／其他(含水力)）裝置容量。',
  '並列臺北市與新北市三類再生能源裝置容量；本元件本身即為雙北比較，臺北儀表板亦保留同一視圖。',
  '比較雙北綠能發展結構，輔助再生能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT
  CASE c.city WHEN '台北市' THEN '臺北市' ELSE c.city END AS x_axis,
  e.energy_type AS y_axis,
  COALESCE(SUM(m.capacity_kw), 0) AS data
FROM
  (VALUES ('台北市'),('新北市')) AS c(city)
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON  m.city        = c.city
    AND m.energy_type = e.energy_type
    AND m.period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY c.city, e.energy_type
ORDER BY
  ARRAY_POSITION(ARRAY['台北市','新北市']::text[], c.city),
  ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)$$,
  NULL,
  'taipei'
),

-- 3-2 能源占比 city=taipei（DonutChart / BarChart）
(
  'reuse_energy_mix_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市最新期三類再生能源裝置容量占比。',
  '風力：陸域與離岸；太陽光電：屋頂型與地面型合計；其他(含水力)：水力、生質能、地熱等。',
  '觀察臺北市再生能源結構偏向，作為綠色城市核心指標。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.reuse_energy_capacity WHERE city = '台北市')
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)$$,
  NULL,
  'taipei'
),
-- 3-2' 能源占比 city=metrotaipei（雙北合計）
(
  'reuse_energy_mix_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北最新期三類再生能源裝置容量占比。',
  '臺北市與新北市裝置容量加總後再依風力／太陽光電／其他(含水力)三類計算占比。',
  '觀察雙北整體再生能源結構，協助大區能源政策評估。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)$$,
  NULL,
  'metrotaipei'
),

-- 3-3 年趨勢 city=taipei（TimelineStackedChart）
(
  'reuse_energy_trend_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市再生能源裝置容量逐年趨勢。',
  '依民國 101 年起累計裝置容量逐年呈現；以堆疊面積觀察整體成長與結構變化。',
  '觀察臺北市再生能源裝置容量的成長路徑與結構演進。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'time',
  $$SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市' AND period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type$$,
  NULL,
  'taipei'
),
-- 3-3' 年趨勢 city=metrotaipei（雙北合計）
(
  'reuse_energy_trend_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北再生能源裝置容量逐年趨勢。',
  '雙北合計：臺北市與新北市同年加總；以堆疊面積觀察整體成長與結構變化。',
  '評估雙北作為大區之綠能成長路徑。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'time',
  $$SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type$$,
  NULL,
  'metrotaipei'
),

-- 3-4 年趨勢縱向長條 city=taipei
(
  'reuse_energy_trend_column_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '臺北市再生能源裝置容量逐年堆疊長條。',
  '與年趨勢折線堆疊圖相同年度資料；以縱向堆疊長條呈現。11502 未納入。',
  '以長條圖比對各年度裝置容量結構。',
  ARRAY['https://www.moeaea.gov.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT p.period_label AS x_axis,
       e.energy_type AS y_axis,
       COALESCE(m.capacity_kw, 0) AS data
FROM
  (SELECT DISTINCT period_sort, period_label
   FROM public.reuse_energy_capacity
   WHERE city = '台北市' AND period_sort LIKE '%-00'
  ) AS p
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON m.period_sort = p.period_sort
   AND m.city = '台北市'
   AND m.energy_type = e.energy_type
ORDER BY p.period_sort,
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)$$,
  NULL,
  'taipei'
),
-- 3-4' 年趨勢縱向長條 city=metrotaipei（雙北合計）
(
  'reuse_energy_trend_column_taipei', NULL, '{}', NULL,
  'static', NULL, 1, 'year',
  '經濟部能源署',
  '雙北再生能源裝置容量逐年堆疊長條。',
  '雙北合計，僅取年度列；以縱向堆疊長條呈現。',
  '以長條圖比對雙北各年度裝置容量結構。',
  ARRAY['https://www.moeaea.gov.tw/','https://data.ntpc.gov.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'three_d',
  $$SELECT p.period_label AS x_axis,
       e.energy_type AS y_axis,
       COALESCE(SUM(m.capacity_kw), 0) AS data
FROM
  (SELECT DISTINCT period_sort, period_label
   FROM public.reuse_energy_capacity
   WHERE period_sort LIKE '%-00'
  ) AS p
  CROSS JOIN (VALUES ('風力'),('太陽光電'),('其他(含水力)')) AS e(energy_type)
  LEFT JOIN public.reuse_energy_capacity m
    ON m.period_sort = p.period_sort
   AND m.energy_type = e.energy_type
GROUP BY p.period_sort, p.period_label, e.energy_type
ORDER BY p.period_sort,
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)$$,
  NULL,
  'metrotaipei'
);

-- ⚠️ dashboards / dashboard_groups 已移至：
--    component_doc/seed/03_sustainable_env_dashboard.sql
-- 請在此檔執行後，另行執行該檔以建立「永續環境」儀表板。
