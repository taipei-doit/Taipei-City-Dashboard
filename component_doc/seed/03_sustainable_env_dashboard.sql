-- ===========================================================================
-- 03_sustainable_env_dashboard.sql
-- 目標 DB: dashboardmanager
-- 說明：建立「永續環境」合併儀表板（含「我的新儀表板」整合版）。
--
-- 組件排序（前段：來自「我的新儀表板」，後段：原永續環境組件）：
--   前段 8 項（我的新儀表板置頂）：
--       交通 / 人口   : 215 (高齡就業), 218 (長照指標), 216 (年齡分區),
--                       213 (自行車道), 212 (電動巴士), 214 (扶養比),
--                       60  (YouBike),  146 (其他，依執行期實際存在為準)
--   後段 10 項（原永續環境）：
--       car-type      : 901, 902, 903
--       reuse_energy  : 911, 912, 913, 914
--       green_building: 923
--       green_land    : 932, 936
--
--   ⚠️ 組件 146 在初始化 SQL 中無對應紀錄，若執行期確認不存在可手動刪除
--      ARRAY 中的 146。
--
--   * 僅操作 dashboards / dashboard_groups，components / component_charts / query_charts 不動
-- ===========================================================================

-- 0. 清除舊紀錄（冪等）
DELETE FROM public.dashboard_groups
 WHERE dashboard_id IN (901, 902, 903, 904, 905, 906);

DELETE FROM public.dashboards
 WHERE id IN (901, 902, 903, 904, 905, 906)
    OR index IN (
      'green_transition_taipei',
      'green_transition_metrotaipei',
      'renewable_energy_taipei',
      'renewable_energy_metrotaipei',
      'sustainable_env_taipei',
      'sustainable_env_metrotaipei'
    );

-- 1. 建立合併後的「永續環境」儀表板
--    前 8 項來自「我的新儀表板」(id=2, components={215,218,216,213,212,214,60,146})，
--    置頂排在最前面；後 10 項為原永續環境組件。
INSERT INTO public.dashboards (id, index, name, components, icon, updated_at, created_at)
VALUES
  (905, 'sustainable_env_taipei',      '永續環境',
    ARRAY[215, 218, 216, 213, 212, 214, 60, 146,
          901, 902, 903, 911, 912, 913, 914, 923, 932, 936]::integer[],
    'eco', NOW(), NOW()),
  (906, 'sustainable_env_metrotaipei', '永續環境',
    ARRAY[215, 218, 216, 213, 212, 214, 60, 146,
          901, 902, 903, 911, 912, 913, 914, 923, 932, 936]::integer[],
    'eco', NOW(), NOW());

-- 2. 掛入城市群組
INSERT INTO public.dashboard_groups (dashboard_id, group_id) VALUES
  (905, 2),   -- taipei
  (906, 3);   -- metrotaipei
