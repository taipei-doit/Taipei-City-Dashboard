-- ===========================================================================
-- green_building / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
--
-- 兩個獨立組件（皆雙北 query_charts 雙寫，符合 cross_city_dashboard_pattern）：
--   * green_buildings_district (id=921)
--       - 圖表：DistrictChart（無 MapLegend）
--       - 地圖：circle 僅 valid='1' 且 rank≠5（鑽石級只顯示葉子）；symbol 僅 rank=5 葉子
--       - city='taipei'      → 12 區
--       - city='metrotaipei' → 41 區（雙北）
--   * green_buildings_rank (id=922)
--       - 圖表：BarChart 橫向長條，數值為占 valid=1 總數之百分比（%）
--       - 不含地圖
--       - city='taipei'      → 僅臺北市 valid='1'
--       - city='metrotaipei' → 雙北 valid='1' 合計
--
-- ⚠️ Dashboards 由 component_doc/seed/03_sustainable_env_dashboard.sql 統一管理
-- ===========================================================================

-- 0. 冪等：清舊紀錄
DELETE FROM public.query_charts
 WHERE index IN ('green_buildings_district', 'green_buildings_rank',
                 'green_buildings');           -- 同時清除舊版單一 index
DELETE FROM public.component_charts
 WHERE index IN ('green_buildings_district', 'green_buildings_rank',
                 'green_buildings');
DELETE FROM public.component_maps
 WHERE index IN ('green_buildings_district', 'green_buildings_rank',
                 'green_buildings');
DELETE FROM public.components
 WHERE index IN ('green_buildings_district', 'green_buildings_rank',
                 'green_buildings')
    OR id IN (921, 922);

-- ============================================================================
-- 1. components
-- ============================================================================
INSERT INTO public.components (id, index, name) VALUES
  (921, 'green_buildings_district', '綠建築 - 各行政區棟數分布'),
  (922, 'green_buildings_rank',     '綠建築 - 認可等級結構');

-- ============================================================================
-- 2. component_charts
-- ============================================================================
-- 2-1 行政區圖：色階由淺到深（DistrictChart 會依數值映射）
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('green_buildings_district',
    ARRAY['#E8F5E9','#C8E6C9','#A5D6A7','#81C784','#66BB6A',
          '#4CAF50','#43A047','#388E3C','#2E7D32','#1B5E20'],
    ARRAY['DistrictChart'],
    '棟');

-- 2-2 等級結構橫向長條：rank 5→1 對應 鑽石→合格 的綠色漸層
--     橫向長條圖最左邊（HorizontalBarChart 由下往上 / 由左往右排序）為陣列首項。
--     這裡 SQL 會 ORDER BY rank ASC，意即 rank1(合格) 是首項，因此最左/最低位
--     即為合格級，符合需求。
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('green_buildings_rank',
    ARRAY['#A5D6A7','#9CCC65','#66BB6A','#FBC02D','#78A75A'],
    ARRAY['BarChart'],
    '%');

-- ============================================================================
-- 3. component_maps（兩個 layer 都掛在 green_buildings_district 這個 index 下）
--    GeoJSON 檔名：green_buildings_district.geojson
-- ============================================================================
-- Layer 1：valid='1' 且非鑽石級（rank≠5）— 鑽石僅由下方 symbol 葉子顯示
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'green_buildings_district',
  '綠建築認可建築',
  'circle',
  'geojson',
  NULL, NULL,
  '{"circle-color": "#4CAF50",
    "circle-radius": 5,
    "circle-opacity": 0.8,
    "circle-stroke-color": "#ffffff",
    "circle-stroke-width": 1,
    "filter": ["all", ["==", ["get", "valid"], "1"], ["!=", ["get", "rank"], 5]]}'::json,
  '[{"key":"建築物名稱","name":"建築物名稱"},
    {"key":"認可等級","name":"認可等級"},
    {"key":"rank","name":"等級分數"},
    {"key":"建築物概要","name":"建築物概要"},
    {"key":"認可版本","name":"認可版本"},
    {"key":"認可類別","name":"認可類別"},
    {"key":"有效期間","name":"有效期間"},
    {"key":"建築物使用類別","name":"建築物使用類別"},
    {"key":"設計人","name":"設計人"},
    {"key":"ditrict","name":"行政區"}]'::json
);

-- Layer 2：鑽石級 (valid='1' AND rank=5) 用 symbol layer + leaf-icon
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'green_buildings_district',
  '鑽石級綠建築',
  'symbol',
  'geojson',
  NULL,
  'leaf-icon',
  '{"layout": {"icon-image": "leaf-icon",
                "icon-size": 1.2,
                "icon-allow-overlap": true},
    "filter": ["all", ["==", ["get", "valid"], "1"], ["==", ["get", "rank"], 5]]}'::json,
  '[{"key":"建築物名稱","name":"建築物名稱"},
    {"key":"認可等級","name":"認可等級"},
    {"key":"rank","name":"等級分數"},
    {"key":"建築物概要","name":"建築物概要"},
    {"key":"有效期間","name":"有效期間"},
    {"key":"ditrict","name":"行政區"}]'::json
);

-- ============================================================================
-- 4. query_charts (green_buildings_district)
--    DistrictChart 需 12/41 個行政區的 valid='1' 棟數（two_d）
-- ============================================================================

-- 4-1 taipei (12 區)
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'green_buildings_district', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'green_buildings_district'),
  '{"mode":"byParam","byParam":{"xParam":"ditrict"}}'::json,
  'static', NULL, 1, 'month',
  '內政部建築研究所 綠建築標章',
  '臺北市各行政區綠建築認可建築棟數（valid=1）。',
  '統計臺北市 12 個行政區獲得有效綠建築認可（valid=1）的建築棟數；地圖上非鑽石級為綠色圓點，鑽石級（rank=5）以葉片圖示標示。',
  '掌握臺北市綠建築空間分布與密度，識別推廣不足的行政區，作為政策資源傾斜依據。',
  ARRAY['https://gbeval.tabc.org.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data
    FROM (VALUES
      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),
      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區')
    ) AS d(district)
    LEFT JOIN public.green_buildings g
      ON g.district = d.district
     AND g.city     = '臺北市'
     AND g.valid    = '1'
    GROUP BY d.district
    ORDER BY ARRAY_POSITION(
      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',
            '中山區','大同區','中正區','萬華區','大安區','文山區'],
      d.district
    )$$,
  NULL,
  'taipei'
);

-- 4-2 metrotaipei (41 區)
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'green_buildings_district', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'green_buildings_district'),
  '{"mode":"byParam","byParam":{"xParam":"ditrict"}}'::json,
  'static', NULL, 1, 'month',
  '內政部建築研究所 綠建築標章',
  '雙北各行政區綠建築認可建築棟數（valid=1，共約 680 棟）。',
  '統計雙北 41 個行政區獲得有效綠建築認可（valid=1）的建築棟數；非鑽石級為綠色圓點，鑽石級以葉片圖示標示。',
  '比較雙北綠建築空間分布密度，協助政策規劃與推廣優先區域選定。',
  ARRAY['https://gbeval.tabc.org.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $$SELECT d.district AS x_axis, COALESCE(COUNT(g.id), 0) AS data
    FROM (VALUES
      ('北投區'),('士林區'),('內湖區'),('南港區'),('松山區'),('信義區'),
      ('中山區'),('大同區'),('中正區'),('萬華區'),('大安區'),('文山區'),
      ('新莊區'),('淡水區'),('汐止區'),('板橋區'),('三重區'),('樹林區'),
      ('土城區'),('蘆洲區'),('中和區'),('永和區'),('新店區'),('鶯歌區'),
      ('三峽區'),('瑞芳區'),('五股區'),('泰山區'),('林口區'),('深坑區'),
      ('石碇區'),('坪林區'),('三芝區'),('石門區'),('八里區'),('平溪區'),
      ('雙溪區'),('貢寮區'),('金山區'),('萬里區'),('烏來區')
    ) AS d(district)
    LEFT JOIN public.green_buildings g
      ON g.district = d.district
     AND g.valid    = '1'
    GROUP BY d.district
    ORDER BY ARRAY_POSITION(
      ARRAY['北投區','士林區','內湖區','南港區','松山區','信義區',
            '中山區','大同區','中正區','萬華區','大安區','文山區',
            '新莊區','淡水區','汐止區','板橋區','三重區','樹林區',
            '土城區','蘆洲區','中和區','永和區','新店區','鶯歌區',
            '三峽區','瑞芳區','五股區','泰山區','林口區','深坑區',
            '石碇區','坪林區','三芝區','石門區','八里區','平溪區',
            '雙溪區','貢寮區','金山區','萬里區','烏來區'],
      d.district
    )$$,
  NULL,
  'metrotaipei'
);

-- ============================================================================
-- 5. query_charts (green_buildings_rank)
--    BarChart（two_d）：rank 1~5 各占 valid=1 總數之百分比；ORDER BY rank ASC（合格→鑽石）
-- ============================================================================

-- 5-1 taipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'green_buildings_rank', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '內政部建築研究所 綠建築標章',
  '臺北市綠建築 valid=1 之認可等級結構（合格→鑽石）。',
  '統計臺北市 valid=1 之綠建築，依合格、銅、銀、黃金、鑽石五級呈現橫向長條圖（各級占總數百分比）。',
  '掌握臺北市綠建築認可等級結構，了解高等級建築（黃金、鑽石）占比，作為更高標準推廣依據。',
  ARRAY['https://gbeval.tabc.org.tw/']::text[],
  ARRAY['doit']::text[],
  NOW(), NOW(),
  'two_d',
  $$WITH ranked AS (
      SELECT r.rank_val, r.rank_name, COALESCE(COUNT(g.id), 0)::numeric AS cnt
      FROM (VALUES
        (1, '合格級'),
        (2, '銅級'),
        (3, '銀級'),
        (4, '黃金級'),
        (5, '鑽石級')
      ) AS r(rank_val, rank_name)
      LEFT JOIN public.green_buildings g
        ON g.rank  = r.rank_val
       AND g.city  = '臺北市'
       AND g.valid = '1'
      GROUP BY r.rank_val, r.rank_name
    ), tot AS (SELECT COALESCE(SUM(cnt), 0) AS s FROM ranked)
    SELECT ranked.rank_name AS x_axis,
           ROUND(100.0 * ranked.cnt / NULLIF((SELECT s FROM tot), 0), 1) AS data
    FROM ranked
    ORDER BY ranked.rank_val ASC$$,
  NULL,
  'taipei'
);

-- 5-2 metrotaipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'green_buildings_rank', NULL, '{}', NULL,
  'static', NULL, 1, 'month',
  '內政部建築研究所 綠建築標章',
  '雙北綠建築 valid=1 之認可等級結構（合格→鑽石）。',
  '統計雙北 valid=1 之綠建築，依合格、銅、銀、黃金、鑽石五級呈現橫向長條圖（各級占總數百分比）。',
  '掌握雙北綠建築認可等級結構，協助評估區域永續建築發展深度。',
  ARRAY['https://gbeval.tabc.org.tw/']::text[],
  ARRAY['doit','ntpc']::text[],
  NOW(), NOW(),
  'two_d',
  $$WITH ranked AS (
      SELECT r.rank_val, r.rank_name, COALESCE(COUNT(g.id), 0)::numeric AS cnt
      FROM (VALUES
        (1, '合格級'),
        (2, '銅級'),
        (3, '銀級'),
        (4, '黃金級'),
        (5, '鑽石級')
      ) AS r(rank_val, rank_name)
      LEFT JOIN public.green_buildings g
        ON g.rank  = r.rank_val
       AND g.valid = '1'
      GROUP BY r.rank_val, r.rank_name
    ), tot AS (SELECT COALESCE(SUM(cnt), 0) AS s FROM ranked)
    SELECT ranked.rank_name AS x_axis,
           ROUND(100.0 * ranked.cnt / NULLIF((SELECT s FROM tot), 0), 1) AS data
    FROM ranked
    ORDER BY ranked.rank_val ASC$$,
  NULL,
  'metrotaipei'
);
