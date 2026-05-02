-- =====================================================
-- 食品中毒趨勢組件 (food_poisoning_trend)
-- 資料表建立 + 組件配置
-- =====================================================

-- -----------------------------------------------------
-- 1. 資料表（DBDashboard）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS public.food_poisoning_trend (
    year integer NOT NULL,
    venue_type text,
    incident_count integer DEFAULT 0,
    affected_people_count integer DEFAULT 0,
    death_count integer DEFAULT 0,
    data_time timestamp with time zone,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.food_poisoning_trend_history (
    year integer NOT NULL,
    venue_type text,
    incident_count integer DEFAULT 0,
    affected_people_count integer DEFAULT 0,
    death_count integer DEFAULT 0,
    data_time timestamp with time zone,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS food_poisoning_trend_year_idx
    ON public.food_poisoning_trend (year);

CREATE INDEX IF NOT EXISTS food_poisoning_trend_venue_idx
    ON public.food_poisoning_trend (venue_type);

-- -----------------------------------------------------
-- 2. 組件定義（DBManager）
-- -----------------------------------------------------

-- 2.1 components
INSERT INTO public.components ("index", name)
VALUES ('food_poisoning_trend', '食品中毒趨勢')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

-- 2.2 chart styling
INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'food_poisoning_trend',
    ARRAY['#ED6A45', '#56B96D', '#F8CF58'],
    ARRAY['TimelineSeparateChart'],
    '件'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- 2.3 query configuration
DELETE FROM public.query_charts
WHERE "index" = 'food_poisoning_trend' AND city IN ('taipei');

INSERT INTO public.query_charts (
    "index",
    history_config,
    map_config_ids,
    map_filter,
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
    created_at,
    updated_at,
    query_type,
    query_chart,
    query_history,
    city
)
VALUES
(
    'food_poisoning_trend',
    NULL,
    '{}',
    '{}',
    'static',
    NULL,
    1,
    'year',
    '臺北市政府衛生局',
    '顯示臺北市歷年食品中毒案件數趨勢。',
    '此圖表呈現臺北市歷年食品中毒案件的統計趨勢，資料來源為臺北市政府衛生局公開統計。圖表以年度為單位，展示食品中毒案件的發生數量變化，幫助民眾與政策制定者了解食品安全事件的長期趨勢。資料僅呈現整體統計數字，不包含個別餐飲業者名稱，以確保客觀呈現事實並避免造成不必要的恐慌。',
    '適用於公共衛生政策評估、食品安全教育與風險溝通。政府機關可藉此掌握食品中毒事件的年度變化趨勢，評估食安宣導與稽查政策的成效。學術研究可運用此時間序列資料，探討季節性因素、氣候變遷或政策介入對食品中毒發生率的影響。市民可透過趨勢圖了解食品安全概況，提升飲食衛生意識。',
    ARRAY['https://statistics.health.gov.tw/tbl/b111食品中毒事件(場所別).html'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'time',
    'SELECT TO_TIMESTAMP(year::text || ''-01-01'', ''YYYY-MM-DD'') AT TIME ZONE ''Asia/Taipei'' AS x_axis, ''案件數'' AS y_axis, SUM(incident_count)::float AS data FROM public.food_poisoning_trend WHERE venue_type = ''總計'' GROUP BY year ORDER BY x_axis',
    NULL,
    'taipei'
);

-- -----------------------------------------------------
-- 3. Dashboard 配置（可選）
-- -----------------------------------------------------
INSERT INTO public.dashboards ("index", name, components, icon, updated_at, created_at)
VALUES (
    'food_safety_health',
    '食安健康儀表板',
    ARRAY[(SELECT id FROM public.components WHERE "index" = 'food_poisoning_trend')],
    'restaurant',
    NOW(),
    NOW()
)
ON CONFLICT ("index") DO UPDATE
SET name = EXCLUDED.name,
    components = EXCLUDED.components,
    updated_at = NOW();

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
VALUES
    ((SELECT id FROM public.dashboards WHERE "index" = 'food_safety_health'), 1),
    ((SELECT id FROM public.dashboards WHERE "index" = 'food_safety_health'), 2)
ON CONFLICT DO NOTHING;

SELECT setval('public.components_id_seq', (SELECT COALESCE(MAX(id), 0) FROM public.components), true);
