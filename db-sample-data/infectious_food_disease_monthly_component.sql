-- =====================================================
-- 食物相關傳染病月趨勢組件 (infectious_food_disease_monthly)
-- 資料表建立 + 組件配置
-- =====================================================

-- -----------------------------------------------------
-- 1. 資料表（DBDashboard）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS public.infectious_food_disease_monthly (
    data_time timestamp with time zone NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    disease_name text NOT NULL,
    case_count integer DEFAULT 0,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.infectious_food_disease_monthly_history (
    data_time timestamp with time zone NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    disease_name text NOT NULL,
    case_count integer DEFAULT 0,
    _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ogc_fid serial PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS infectious_food_disease_monthly_time_idx
    ON public.infectious_food_disease_monthly (data_time);
CREATE INDEX IF NOT EXISTS infectious_food_disease_monthly_disease_idx
    ON public.infectious_food_disease_monthly (disease_name);

-- -----------------------------------------------------
-- 2. 組件定義（DBManager）
-- -----------------------------------------------------

-- 2.1 components
INSERT INTO public.components ("index", name)
VALUES ('infectious_food_disease_monthly', '食物相關傳染病月趨勢')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

-- 2.2 chart styling
INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'infectious_food_disease_monthly',
    ARRAY['#ED6A45', '#56B96D', '#F8CF58', '#24B0DD', '#9B59B6', '#E74C3C', '#3498DB', '#2ECC71', '#F39C12'],
    ARRAY['TimelineStackedChart'],
    '例'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

-- 2.3 query configuration
DELETE FROM public.query_charts
WHERE "index" = 'infectious_food_disease_monthly' AND city IN ('taipei');

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
    'infectious_food_disease_monthly',
    NULL,
    '{}',
    '{}',
    'static',
    NULL,
    1,
    'month',
    '臺北市政府衛生局',
    '顯示臺北市各類食物相關傳染病確定病例的月度趨勢。',
    '此圖表呈現臺北市與食物相關之法定傳染病確定病例的月度統計趨勢，資料來源為臺北市政府衛生局公開統計之「法定傳染病確定病例(行政區)」資料。涵蓋疾病包括傷寒、副傷寒、急性病毒性A型肝炎、桿菌性痢疾、阿米巴性痢疾、霍亂、腸道出血性大腸桿菌感染症、李斯特菌症、肉毒桿菌中毒等。圖表以月度為單位，將不同疾病以堆疊面積圖方式呈現，幫助公共衛生單位與民眾掌握各類食媒性疾病之時間分布與相對變化。資料僅呈現整體統計數字，不包含個案識別資訊。',
    '適用於公共衛生監測、食品安全政策評估與流行病學教育。政府機關可藉此追蹤食媒性疾病的季節性變化，評估食安宣導與稽查政策之成效。學術研究可運用此時間序列資料，探討氣候、季節或社會因素對各類傳染病發生率的影響。市民可透過趨勢圖了解食媒性疾病概況，提升飲食衛生與食品安全意識。',
    ARRAY['https://statistics.health.gov.tw/tbl/m005法定傳染病確定病例(行政區).html'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'time',
    'SELECT data_time AT TIME ZONE ''Asia/Taipei'' AS x_axis, disease_name AS y_axis, SUM(case_count)::float AS data FROM public.infectious_food_disease_monthly GROUP BY data_time, disease_name ORDER BY x_axis',
    NULL,
    'taipei'
);

-- -----------------------------------------------------
-- 3. Dashboard 配置：加入「食安健康儀表板」
-- -----------------------------------------------------
INSERT INTO public.dashboards ("index", name, components, icon, updated_at, created_at)
VALUES (
    'food_safety_health',
    '食安健康儀表板',
    ARRAY[
        (SELECT id FROM public.components WHERE "index" = 'food_poisoning_trend'),
        (SELECT id FROM public.components WHERE "index" = 'infectious_food_disease_monthly')
    ],
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
