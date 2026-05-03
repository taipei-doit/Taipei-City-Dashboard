-- ===========================================================================
-- PM2.5 / 03_sustainable_env_dashboard_addon.sql
-- 目標 DB: dashboardmanager
--
-- 將「即時 PM2.5 空氣品質」(components.id=942) 掛入「永續環境」儀表板：
--   * 905 → sustainable_env_taipei
--   * 906 → sustainable_env_metrotaipei
--
-- 冪等：以 unnest + ARRAY_AGG(DISTINCT) 合併，重跑不會重覆插入。
-- ⚠️ 此檔僅維護 dashboards.components；組件本體請先執行
--    PM2.5/output/seed/02_dashboardmanager_components.sql。
--
-- 若要改掛到其他儀表板，把下方 WHERE id IN (...) 改成你要的 dashboard.id 即可。
-- ===========================================================================

-- 1. sustainable_env_taipei (id=905) 加入 942
UPDATE public.dashboards
   SET components = (
         SELECT ARRAY_AGG(DISTINCT cid ORDER BY cid)
         FROM unnest(COALESCE(components, '{}'::int[]) || ARRAY[942]::int[]) AS cid
       ),
       updated_at = NOW()
 WHERE id = 905;

-- 2. sustainable_env_metrotaipei (id=906) 加入 942
UPDATE public.dashboards
   SET components = (
         SELECT ARRAY_AGG(DISTINCT cid ORDER BY cid)
         FROM unnest(COALESCE(components, '{}'::int[]) || ARRAY[942]::int[]) AS cid
       ),
       updated_at = NOW()
 WHERE id = 906;

-- 3. 驗證輸出（可在 psql 互動模式檢視）
--   SELECT id, index, name, components FROM public.dashboards WHERE id IN (905, 906);
