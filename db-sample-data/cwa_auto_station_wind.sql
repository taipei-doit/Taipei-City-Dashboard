-- ============================================================
-- CWA 自動氣象站即時風速風向
-- 資料來源: 中央氣象署 OpenData O-A0001-001
-- ============================================================
-- 執行順序:
--   Step 1: 在 dashboard DB 執行 Section A
--   Step 2: 在 dashboardmanager DB 執行 Section B
--   Step 3: 設定環境變數 CWA_API_KEY，重啟後端
-- ============================================================


-- ============================================================
-- SECTION A: dashboard 資料庫
-- ============================================================

-- A1. 建立即時快照資料表
CREATE TABLE IF NOT EXISTS cwa_auto_station_wind (
    id                SERIAL PRIMARY KEY,
    station_id        VARCHAR(20)    NOT NULL,
    station_name      VARCHAR(100),
    county_name       VARCHAR(50),
    town_name         VARCHAR(50),
    station_altitude  NUMERIC(8, 2),
    latitude          NUMERIC(10, 6) NOT NULL,
    longitude         NUMERIC(10, 6) NOT NULL,
    wind_direction    NUMERIC(7, 2),    -- 風向 (度 0–360)，NULL = 無效值 (-99)
    wind_speed        NUMERIC(7, 2),    -- 風速 (m/s)，NULL = 無效值 (-99)
    air_temperature   NUMERIC(7, 2),    -- 氣溫 (°C)
    relative_humidity NUMERIC(7, 2),    -- 相對濕度 (%)
    air_pressure      NUMERIC(8, 2),    -- 氣壓 (hPa)
    gust_speed        NUMERIC(7, 2),    -- 最大瞬間風速 (m/s)
    gust_direction    NUMERIC(7, 2),    -- 最大瞬間風向 (度)
    obs_time          TIMESTAMPTZ,      -- 觀測時間
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- A2. 查詢用索引
CREATE INDEX IF NOT EXISTS idx_cwa_wind_station_id
    ON cwa_auto_station_wind (station_id);

CREATE INDEX IF NOT EXISTS idx_cwa_wind_county
    ON cwa_auto_station_wind (county_name);

CREATE INDEX IF NOT EXISTS idx_cwa_wind_speed
    ON cwa_auto_station_wind (wind_speed DESC NULLS LAST);


-- ============================================================
-- SECTION B: dashboardmanager 資料庫
-- ============================================================

-- B1. 組件主體 (components 表)
--     index 為唯一識別碼，前端用此 index 對應資料
INSERT INTO public.components (index, name)
VALUES ('cwa_auto_station_wind', '自動氣象站即時風速風向')
ON CONFLICT (index) DO UPDATE SET name = EXCLUDED.name;

-- B2. 圖表 UI 設定 (component_charts 表)
--     types: ColumnChart 柱狀圖，BarChart 橫條圖
--     color: 藍色系 (風速)，橙色系 (風向)
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
    'cwa_auto_station_wind',
    ARRAY['#56CCF2', '#2F80ED', '#F2994A', '#EB5757'],
    ARRAY['ColumnChart', 'BarChart'],
    'm/s'
)
ON CONFLICT (index) DO UPDATE
    SET color = EXCLUDED.color,
        types = EXCLUDED.types,
        unit  = EXCLUDED.unit;

-- B3. 資料查詢設定 (query_charts 表)
--     query_type = two_d : 回傳 x_axis (站名) + data (風速) 兩欄
--     query_chart 會在後端對 dashboard DB 執行
INSERT INTO public.query_charts (
    index,
    query_type,
    query_chart,
    query_history,
    time_from,
    time_to,
    update_freq,
    update_freq_unit,
    source,
    short_desc,
    long_desc,
    use_case,
    links,
    contributors,
    city
)
VALUES (
    'cwa_auto_station_wind',
    'two_d',
    -- 即時風速查詢 (前 30 個最高風速站)
    $SQL$
SELECT
    station_name || ' (' || COALESCE(county_name, '') || ')' AS x_axis,
    ROUND(wind_speed::numeric, 1)                            AS data
FROM public.cwa_auto_station_wind
WHERE wind_speed IS NOT NULL
ORDER BY wind_speed DESC
LIMIT 30
    $SQL$,
    -- 歷史查詢 (暫不提供，未儲存歷史資料)
    NULL,
    'static',
    'static',
    10,
    'minute',
    '中央氣象署 OpenData O-A0001-001',
    '各自動氣象站最新觀測風速 (m/s)',
    '資料來源為中央氣象署自動氣象站，每 10 分鐘更新一次即時觀測資料，包含全台各站風速、風向、氣溫、氣壓等。',
    '即時氣象監控、風力評估',
    ARRAY['https://opendata.cwa.gov.tw/dataset/observation/O-A0001-001'],
    ARRAY['中央氣象署'],
    'taipei'
)
ON CONFLICT DO NOTHING;

-- B4. 地圖圖層設定 (component_maps 表) — 各站點位置
--     type=symbol : 點位符號圖層
--     source=geojson : 前端從 /api/v1/component/:id/chart 取得資料後自行繪製
INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
    'cwa_auto_station_wind',
    '氣象站位置',
    'symbol',
    'geojson',
    NULL,
    'weather-station',
    '{}',
    '[
        {"key": "station_name", "name": "站名"},
        {"key": "county_name",  "name": "縣市"},
        {"key": "wind_speed",   "name": "風速 (m/s)"},
        {"key": "wind_direction","name": "風向 (度)"},
        {"key": "obs_time",     "name": "觀測時間"}
    ]'
)
ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION C: 驗證查詢 (執行後確認資料正確)
-- ============================================================

-- C1. 確認 dashboard DB 資料表存在且有資料
-- SELECT COUNT(*) FROM cwa_auto_station_wind;

-- C2. 列出各縣市的平均風速 (確認資料合理性)
-- SELECT county_name, ROUND(AVG(wind_speed)::numeric,2) AS avg_wind_speed, COUNT(*) AS station_count
-- FROM cwa_auto_station_wind
-- WHERE wind_speed IS NOT NULL
-- GROUP BY county_name
-- ORDER BY avg_wind_speed DESC;

-- C3. 確認 dashboardmanager DB 組件已註冊
-- SELECT c.id, c.index, c.name, qc.query_type, qc.update_freq, qc.update_freq_unit
-- FROM components c
-- JOIN query_charts qc ON c.index = qc.index
-- WHERE c.index = 'cwa_auto_station_wind';
