-- ──────────────────────────────────────────────────────────────────────
-- 實物銀行數量 component (food_bank_points) — dashboardmanager seed
--
-- 對應 hw.md §2 「組件設定」可直接匯入版本 (Excel 之外另附 SQL)。
-- 對應 DAG: proj_city_dashboard/food_bank_contacts (臺北)
--           proj_new_taipei_city_dashboard/food_bank_ntpe (新北)
--
-- 套用於 dashboardmanager DB:
--   docker compose exec postgres-manager psql -U postgres -d dashboardmanager \
--       < submission/food_bank_points_seed_dashboard.sql
--
-- 注意:
--   1. components.id 留 NULL (走 serial), 由整併者於 PR review 時指派或保留自動編號;
--      若有預期值 (參考來源 PR #1260 為 604), 可於 INSERT 補上.
--   2. 本期不交付地圖點位 (is_geometry=0), 故不 INSERT component_maps.
--   3. SQL 直接打 postgres-data (含 food_bank_contacts / food_bank_ntpe 兩張 ready table).
-- ──────────────────────────────────────────────────────────────────────

BEGIN;

-- ─── 0. idempotent: 清掉舊資料 ────────────────────────────────
DELETE FROM query_charts     WHERE index = 'food_bank_points';
DELETE FROM components       WHERE index = 'food_bank_points';
DELETE FROM component_charts WHERE index = 'food_bank_points';

-- ─── 1. component_charts (1 筆) ──────────────────────────────
-- color / types / unit 沿用 Taipei City Dashboard 既有 EcoDiet 第 604 號設定.
INSERT INTO component_charts (index, color, types, unit) VALUES
  ('food_bank_points',
   ARRAY['#f6c344','#a37cf6'],
   ARRAY['DonutChart','BarChart'],
   '處');

-- ─── 2. components (1 筆) ────────────────────────────────────
-- id 不指定 (走 serial); 如需固定 id, 由整併者統一指派.
INSERT INTO components (index, name) VALUES
  ('food_bank_points', '實物銀行數量');

-- ─── 3. query_charts (3 筆) ──────────────────────────────────
-- 三個 city: taipei / newtaipei / metrotaipei.
-- SQL 直接打 postgres-data 的兩張 ready table, 不依賴 lng/lat (本期無 geocoding).
INSERT INTO query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES
  -- 臺北
  ('food_bank_points', NULL, NULL, '{}'::json,
   'static', NULL, 6, 'month',
   '臺北市政府社會局', '臺北市實物銀行據點數量',
   '臺北市政府社會局所屬實物銀行據點數量統計, 用於儀表板環圈/長條雙圖呈現.',
   '社福政策研究、食物剩餘再分配研究、民眾尋找最近實物銀行.',
   ARRAY['https://data.taipei/dataset/detail?id=3fbc79e5-0138-4c89-8c47-39feddbd6d3f'],
   ARRAY['ai-plus-one'],
   NOW(), NOW(),
   'two_d',
   'SELECT ''臺北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank_contacts',
   NULL,
   'taipei'),

  -- 新北
  ('food_bank_points', NULL, NULL, '{}'::json,
   'static', NULL, 6, 'month',
   '新北市政府社會局', '新北市實物銀行據點數量',
   '新北市實物銀行分行及領用站數量統計, 用於儀表板環圈/長條雙圖呈現.',
   '社福政策研究、食物剩餘再分配研究、民眾尋找最近實物銀行.',
   ARRAY['https://data.ntpc.gov.tw/datasets/1c1d0066-a4e7-4753-b8bc-d7728d5f3e04'],
   ARRAY['ai-plus-one'],
   NOW(), NOW(),
   'two_d',
   'SELECT ''新北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank_ntpe',
   NULL,
   'newtaipei'),

  -- 雙北合併
  ('food_bank_points', NULL, NULL, '{}'::json,
   'static', NULL, 6, 'month',
   '雙北社會局', '雙北實物銀行據點數量整合',
   '整合臺北市政府社會局實物銀行據點名單與新北市實物銀行分行及領用站清單, 呈現雙北據點數量對比.',
   '社福政策研究、食物剩餘再分配研究、民眾尋找最近實物銀行.',
   ARRAY['https://data.taipei/dataset/detail?id=3fbc79e5-0138-4c89-8c47-39feddbd6d3f',
         'https://data.ntpc.gov.tw/datasets/1c1d0066-a4e7-4753-b8bc-d7728d5f3e04'],
   ARRAY['ai-plus-one'],
   NOW(), NOW(),
   'two_d',
   'SELECT ''臺北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank_contacts'
   ' UNION ALL '
   'SELECT ''新北市'' AS x_axis, COUNT(*)::float AS data FROM food_bank_ntpe'
   ' ORDER BY x_axis',
   NULL,
   'metrotaipei');

COMMIT;
