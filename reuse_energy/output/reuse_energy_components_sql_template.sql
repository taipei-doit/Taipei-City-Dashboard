-- ==========================================================
-- reuse_energy: 再生能源裝置容量 靜態圖表元件 SQL 樣板
-- 對齊 Taipei-City-Dashboard-Documentation/back-end-ch/components-db.md
-- 假設長表已 import 為 public.reuse_energy_capacity：
--   period_sort  TEXT  -- '101-00' 年度 / '115-02' 月度
--   period_label TEXT
--   iso_date     TIMESTAMPTZ
--   city         TEXT  -- '台北市' / '新北市'
--   energy_type  TEXT  -- '風力' / '太陽光電' / '其他(含水力)'
--   capacity_kw  INT
-- ==========================================================

-- 1. components
INSERT INTO dashboardmanager.components (index, name) VALUES
  ('reuse_energy_capacity_metrotaipei', '再生能源裝置容量 - 雙北比較'),
  ('reuse_energy_mix_taipei',           '再生能源裝置容量 - 臺北市能源占比'),
  ('reuse_energy_trend_taipei',         '再生能源裝置容量 - 臺北市年趨勢'),
  ('reuse_energy_trend_column_taipei',  '再生能源裝置容量 - 臺北市年趨勢（縱向長條）');

-- 2. component_charts
INSERT INTO dashboardmanager.component_charts (index, color, types, unit) VALUES
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

-- 3. query_charts
-- 3-1 ColumnChart (three_d)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_capacity_metrotaipei','three_d','static',NULL,1,'year','經濟部能源署','metrotaipei',
$$
SELECT
  CASE city WHEN '台北市' THEN '臺北市' ELSE city END AS x_axis,
  energy_type AS y_axis,
  SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE period_sort = (SELECT MAX(period_sort) FROM public.reuse_energy_capacity)
GROUP BY x_axis, energy_type
ORDER BY ARRAY_POSITION(ARRAY['臺北市','新北市'], x_axis),
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)
$$
);

-- 3-2 DonutChart (two_d)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_mix_taipei','two_d','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT energy_type AS x_axis, SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市'
  AND period_sort = (SELECT MAX(period_sort)
                     FROM public.reuse_energy_capacity WHERE city = '台北市')
GROUP BY energy_type
ORDER BY ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)'], energy_type)
$$
);

-- 3-3 TimelineStackedChart (time)
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_trend_taipei','time','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT iso_date AS x_axis,
       energy_type AS y_axis,
       SUM(capacity_kw) AS data
FROM public.reuse_energy_capacity
WHERE city = '台北市' AND period_sort LIKE '%-00'
GROUP BY iso_date, energy_type
ORDER BY iso_date, energy_type
$$
);

-- 3-4 ColumnChart 臺北市逐年（three_d；列順序須符合後端 GetThreeDimensionalData 分組）
INSERT INTO dashboardmanager.query_charts
  (index, query_type, time_from, time_to, update_freq, update_freq_unit, source, city, query_chart)
VALUES (
  'reuse_energy_trend_column_taipei','three_d','static',NULL,1,'year','經濟部能源署','taipei',
$$
SELECT p.period_label AS x_axis,
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
         ARRAY_POSITION(ARRAY['風力','太陽光電','其他(含水力)']::text[], e.energy_type)
$$
);
