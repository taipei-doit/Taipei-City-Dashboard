-- =====================================================
-- 食物相關傳染病行政區分布組件 (infectious_food_disease_district)
-- =====================================================

INSERT INTO public.components ("index", name)
VALUES ('infectious_food_disease_district', '食物相關傳染病行政區分布')
ON CONFLICT ("index") DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.component_charts ("index", color, types, unit)
VALUES (
    'infectious_food_disease_district',
    ARRAY['#ED6A45'],
    ARRAY['DistrictChart'],
    '例'
)
ON CONFLICT ("index") DO UPDATE
SET color = EXCLUDED.color,
    types = EXCLUDED.types,
    unit = EXCLUDED.unit;

DELETE FROM public.query_charts
WHERE "index" = 'infectious_food_disease_district' AND city IN ('taipei');

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
    'infectious_food_disease_district',
    NULL,
    '{}',
    '{}',
    'static',
    NULL,
    1,
    'month',
    '臺北市政府衛生局',
    '顯示臺北市各行政區食物相關傳染病最新月度病例分布。',
    '此圖表呈現臺北市各行政區與食物相關之法定傳染病確定病例分布，資料來源為臺北市政府衛生局公開統計之「法定傳染病確定病例(行政區)」資料。將傷寒、副傷寒、急性病毒性A型肝炎、桿菌性痢疾、阿米巴性痢疾、霍亂、腸道出血性大腸桿菌感染症、李斯特菌症、肉毒桿菌中毒等9種疾病加總，以最新月份為基準，展示各行政區的相對負擔。資料僅呈現整體統計數字，不含個案識別資訊。',
    '適用於公共衛生監測與食品安全風險溝通。政府機關可藉此識別病例相對較高的行政區，評估是否需要加強該區域的食安宣導或稽查力道。市民可了解各區食媒性疾病概況，提升飲食衛生意識。',
    ARRAY['https://statistics.health.gov.tw/tbl/m005法定傳染病確定病例(行政區).html'],
    ARRAY['doit'],
    NOW(),
    NOW(),
    'two_d',
    'SELECT district as x_axis, SUM(total_case_count)::int as data FROM public.infectious_food_disease_district_monthly WHERE data_time = (SELECT MAX(data_time) FROM public.infectious_food_disease_district_monthly) GROUP BY district ORDER BY data DESC',
    NULL,
    'taipei'
);

-- Dashboard 配置：加入食安健康儀表板
INSERT INTO public.dashboards ("index", name, components, icon, updated_at, created_at)
VALUES (
    'food_safety_health',
    '食安健康儀表板',
    ARRAY[
        (SELECT id FROM public.components WHERE "index" = 'food_poisoning_trend'),
        (SELECT id FROM public.components WHERE "index" = 'infectious_food_disease_monthly'),
        (SELECT id FROM public.components WHERE "index" = 'infectious_food_disease_district')
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
