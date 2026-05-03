-- ===========================================================================
-- people-density / 03_map_layers_dashboard.sql
-- 目標 DB: dashboardmanager
--
-- 將「村里人口密度」(components.id=941) 掛到「基本圖層」儀表板：
--   * 106 → map-layers-taipei      (圖資資訊 / 臺北)
--   * 359 → map-layers-metrotaipei (圖資資訊 / 雙北)
--
-- 機制：「基本圖層」其實就是 index 為 map-layers-{city} 的特殊儀表板。
-- 前端進入「地圖交叉比對」頁面時會自動抓 /dashboard/map-layers-{city}，
-- 該儀表板的 components 陣列就是顯示在左側「基本圖層」區塊的組件清單。
--
-- 冪等：以 array_append + DISTINCT 的方式合併，重跑不會重覆插入。
-- ⚠️ 此檔僅維護 dashboards.components；若新增基本圖層組件本體，
--    請先執行 02_dashboardmanager_components.sql。
-- ===========================================================================

-- 1. map-layers-taipei (id=106) 加入 941
UPDATE public.dashboards
   SET components = (
         SELECT ARRAY_AGG(DISTINCT cid ORDER BY cid)
         FROM unnest(COALESCE(components, '{}'::int[]) || ARRAY[941]::int[]) AS cid
       ),
       updated_at = NOW()
 WHERE id = 106;

-- 2. map-layers-metrotaipei (id=359) 加入 941
UPDATE public.dashboards
   SET components = (
         SELECT ARRAY_AGG(DISTINCT cid ORDER BY cid)
         FROM unnest(COALESCE(components, '{}'::int[]) || ARRAY[941]::int[]) AS cid
       ),
       updated_at = NOW()
 WHERE id = 359;

-- 3. 驗證輸出（可在 psql 互動模式檢視）
--   SELECT id, index, name, components FROM public.dashboards WHERE id IN (106, 359);
