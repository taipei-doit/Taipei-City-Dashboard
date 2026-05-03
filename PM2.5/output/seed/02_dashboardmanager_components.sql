-- ===========================================================================
-- PM2.5 / 02_dashboardmanager_components.sql
-- 目標 DB: dashboardmanager
--
-- 註冊「即時 PM2.5 空氣品質」地圖組件（circle 圖層 + heatmap 變化）：
--   * components.id = 942
--   * index         = 'pm25_realtime'
--   * 地圖類型      = circle，icon='heatmap'（縮小時模糊成熱點圖效果，
--                     放大時還原為單點圓圈；參考 spec.md「Circle」段落）
--   * 圖表類型      = MapLegend（依 EPA AQI 6 段標準色顯示圖例）
--   * map_filter    = byParam(aqi_label_zh)，點擊圖例可篩選對應 AQI 等級之點位
--
-- GeoJSON 檔案位置：
--   Taipei-City-Dashboard-FE/public/mapData/pm25_realtime.geojson
--   （由 PM2.5/fetch_pm25.py 產出，內含雙北約 1000+ 站點，
--    每個 feature 帶 weight=pm25、aqi、aqi_label_zh、aqi_color 等欄位）
--
-- ⚠️ 將此組件實際掛入「永續環境」儀表板（905/906），請執行
--    03_sustainable_env_dashboard_addon.sql。
-- ===========================================================================

-- 0. 冪等：清舊紀錄
DELETE FROM public.query_charts
 WHERE index = 'pm25_realtime';
DELETE FROM public.component_charts
 WHERE index = 'pm25_realtime';
DELETE FROM public.component_maps
 WHERE index = 'pm25_realtime';
DELETE FROM public.components
 WHERE index = 'pm25_realtime'
    OR id = 942;

-- ============================================================================
-- 1. components
-- ============================================================================
INSERT INTO public.components (id, index, name) VALUES
  (942, 'pm25_realtime', '即時 PM2.5 空氣品質');

-- ============================================================================
-- 2. component_charts
--    EPA AQI 6 段標準色（順序須與 query_charts 回傳的 series 順序一致）：
--      良好 / 普通 / 對敏感族群不健康 / 對所有族群不健康 / 非常不健康 / 危害
-- ============================================================================
INSERT INTO public.component_charts (index, color, types, unit) VALUES
  ('pm25_realtime',
    ARRAY['#00E400','#FFFF00','#FF7E00','#FF0000','#8F3F97','#7E0023'],
    ARRAY['MapLegend'],
    '站');

-- ============================================================================
-- 3. component_maps
--    type=circle, icon='heatmap'：
--      circle-color 直接讀 feature 的 aqi_color 欄位（已由抓取腳本依 EPA
--      標準計算），保持與 MapLegend 顏色一致。
--      其餘 circle-radius / circle-blur / circle-opacity 由前端
--      mapConfig.js 的 maplayerCommonPaint['circle-heatmap'] 預設變化套入，
--      不需要在 paint 內重新指定。
-- ============================================================================
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'pm25_realtime',
  '即時 PM2.5',
  'circle',
  'geojson',
  NULL,
  'heatmap',
  '{"circle-color": ["get", "aqi_color"]}'::json,
  '[
    {"key":"station",       "name":"測站名稱"},
    {"key":"city",          "name":"縣市"},
    {"key":"township",      "name":"鄉鎮市區"},
    {"key":"area",          "name":"區域"},
    {"key":"pm25",          "name":"PM2.5（μg/m³）"},
    {"key":"aqi",           "name":"AQI"},
    {"key":"aqi_label_zh",  "name":"AQI 等級"},
    {"key":"authority",     "name":"資料機關"},
    {"key":"localTime",     "name":"觀測時間"}
  ]'::json
);

-- ============================================================================
-- 4. query_charts
--    query_type = 'map_legend'：SQL 回傳 (name, type) 兩欄，
--      type='circle' 會在 MapLegend 顯示為圓點，顏色取自
--      component_charts.color 對應 index。
--    map_filter byParam(aqi_label_zh)：點擊任一圖例會在地圖上篩選
--      對應 AQI 等級的測站。
-- ============================================================================

-- 4-1 taipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'pm25_realtime', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'pm25_realtime'),
  '{"mode":"byParam","byParam":{"xParam":"aqi_label_zh"}}'::json,
  'static', NULL, 5, 'minute',
  '民生公共物聯網 STA Air Quality (EPA IoT)',
  '臺北市即時 PM2.5 微型感測器分布與 AQI 等級',
  '以民生公共物聯網 SensorThings API（環境部空品微型感測器）為來源，呈現臺北市即時 PM2.5（μg/m³）站點分布。圖層為 circle 類型並套用 heatmap 變化（縮小時模糊成熱點圖、放大時還原為單點圓圈），顏色依 EPA AQI 標準分為 6 段（良好 → 危害）。',
  '可用於即時掌握臺北市空氣品質熱點、結合自行車道 / 公車 / 學校等圖層做交叉判讀，輔助永續環境與市民健康相關政策。',
  ARRAY[
    'https://sta.colife.org.tw/STA_AirQuality_EPAIoT/v1.0/Things',
    'https://airtw.moenv.gov.tw/'
  ]::text[],
  ARRAY['hackathon_team']::text[],
  NOW(), NOW(),
  'map_legend',
  $$SELECT * FROM (VALUES
      ('良好',                'circle'),
      ('普通',                'circle'),
      ('對敏感族群不健康',    'circle'),
      ('對所有族群不健康',    'circle'),
      ('非常不健康',          'circle'),
      ('危害',                'circle')
    ) AS t(name, type)$$,
  NULL,
  'taipei'
);

-- 4-2 metrotaipei
INSERT INTO public.query_charts (
  index, history_config, map_config_ids, map_filter,
  time_from, time_to, update_freq, update_freq_unit,
  source, short_desc, long_desc, use_case,
  links, contributors,
  created_at, updated_at,
  query_type, query_chart, query_history, city
) VALUES (
  'pm25_realtime', NULL,
  (SELECT ARRAY_AGG(id ORDER BY id) FROM public.component_maps
    WHERE index = 'pm25_realtime'),
  '{"mode":"byParam","byParam":{"xParam":"aqi_label_zh"}}'::json,
  'static', NULL, 5, 'minute',
  '民生公共物聯網 STA Air Quality (EPA IoT)',
  '雙北即時 PM2.5 微型感測器分布與 AQI 等級',
  '以民生公共物聯網 SensorThings API（環境部空品微型感測器）為來源，呈現雙北（臺北市 + 新北市）即時 PM2.5（μg/m³）站點分布。圖層為 circle 類型並套用 heatmap 變化（縮小時模糊成熱點圖、放大時還原為單點圓圈），顏色依 EPA AQI 標準分為 6 段（良好 → 危害）。',
  '比較雙北空氣品質熱區，協助跨市環境政策、交通管制與健康風險溝通。',
  ARRAY[
    'https://sta.colife.org.tw/STA_AirQuality_EPAIoT/v1.0/Things',
    'https://airtw.moenv.gov.tw/'
  ]::text[],
  ARRAY['hackathon_team']::text[],
  NOW(), NOW(),
  'map_legend',
  $$SELECT * FROM (VALUES
      ('良好',                'circle'),
      ('普通',                'circle'),
      ('對敏感族群不健康',    'circle'),
      ('對所有族群不健康',    'circle'),
      ('非常不健康',          'circle'),
      ('危害',                'circle')
    ) AS t(name, type)$$,
  NULL,
  'metrotaipei'
);
