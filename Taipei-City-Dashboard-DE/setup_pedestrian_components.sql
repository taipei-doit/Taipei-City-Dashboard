-- 在 postgres-manager (dashboardmanager DB) 中新增行人安全儀表板組件
-- 連線：localhost:5432 / dashboardmanager DB
-- 執行前請確認 traffic_pedestrian_* 資料表已有資料

-- ============================================================
-- 1. components 表（組件基本資訊）
-- ============================================================

INSERT INTO public.components (index, name) VALUES
    ('traffic_pedestrian_heatmap',         '雙北行人事故熱區'),
    ('traffic_pedestrian_hourly_taipei',   '雙北行人事故時段分析'),
    ('traffic_pedestrian_yearly_trend',    '雙北行人事故年度趨勢'),
    ('traffic_pedestrian_hotspot_ranking', '行人事故高風險路口排名'),
    ('traffic_pedestrian_ai_report',       'AI 路口安全報告')
ON CONFLICT (index) DO UPDATE SET name = EXCLUDED.name;


-- ============================================================
-- 2. component_charts 表（圖表設定）
-- ============================================================

INSERT INTO public.component_charts (index, color, types, unit) VALUES
    ('traffic_pedestrian_heatmap',
        ARRAY['#FFF9C4', '#FFB300', '#E65100', '#B71C1C'],
        ARRAY['MapLegend'],
        '件'),
    ('traffic_pedestrian_hourly_taipei',
        ARRAY['#FFF9C4', '#FF6F00', '#B71C1C'],
        ARRAY['HeatmapChart'],
        '件'),
    ('traffic_pedestrian_yearly_trend',
        ARRAY['#E53935', '#1E88E5'],
        ARRAY['ColumnLineChart'],
        '件'),
    ('traffic_pedestrian_hotspot_ranking',
        ARRAY['#B71C1C'],
        ARRAY['BarChart'],
        '件'),
    ('traffic_pedestrian_ai_report',
        ARRAY['#5eb3f0'],
        ARRAY['AIHotspotReport'],
        '')
ON CONFLICT (index) DO UPDATE
    SET color = EXCLUDED.color,
        types = EXCLUDED.types,
        unit  = EXCLUDED.unit;


-- ============================================================
-- 3. component_maps 表（地圖圖層設定，供 C1 使用）
-- ============================================================

INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property) VALUES
    (
        'traffic_pedestrian_heatmap',
        '行人事故熱點',
        'circle',
        'geojson',
        'small',
        NULL,
        '{
            "circle-color": [
                "interpolate", ["linear"],
                ["get", "accident_count"],
                1,  "#FFF9C4",
                5,  "#FFB300",
                10, "#E65100",
                20, "#B71C1C"
            ],
            "circle-radius": [
                "interpolate", ["linear"], ["zoom"],
                10, ["interpolate", ["linear"], ["get", "accident_count"],
                      1, 1,   5, 2,   10, 3,   20, 5],
                13, ["interpolate", ["linear"], ["get", "accident_count"],
                      1, 3,   5, 5,   10, 7,   20, 10],
                16, ["interpolate", ["linear"], ["get", "accident_count"],
                      1, 5,   5, 8,   10, 12,  20, 16]
            ],
            "circle-opacity": [
                "interpolate", ["linear"], ["zoom"],
                10, 0.6,
                13, 0.85
            ],
            "circle-stroke-width": 0,
            "circle-blur": 0.1
        }',
        '[
            {"key": "accident_count", "name": "事故件數"},
            {"key": "death_count",    "name": "死亡人數"},
            {"key": "injury_count",   "name": "受傷人數"},
            {"key": "top_cause",      "name": "最主要肇因"},
            {"key": "top_hour",       "name": "高峰時段"},
            {"key": "near_location",  "name": "鄰近路口"},
            {"key": "city",           "name": "城市"}
        ]'
    );

-- 取得剛剛插入的 component_maps id 備用
-- (假設為自動序列，查詢: SELECT id FROM component_maps WHERE index='traffic_pedestrian_heatmap')


-- ============================================================
-- 4. query_charts 表
--    注意：map_config_ids 需填入上方 component_maps 的 id
--    請先查詢：
--      SELECT id FROM component_maps WHERE index='traffic_pedestrian_heatmap';
--    再將結果填入下方 ARRAY[?] 中
-- ============================================================

-- C1：雙北行人事故熱區地圖 (metrotaipei)
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_heatmap',
    NULL,
    -- 將 ? 替換為 component_maps 實際 id
    -- e.g. ARRAY[102] 若上方 INSERT 後 id=102
    (SELECT ARRAY[id] FROM public.component_maps WHERE index = 'traffic_pedestrian_heatmap' LIMIT 1),
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '警察局交通大隊、內政部警政署',
    '雙北近三年行人事故熱點分布地圖，顏色深淺代表事故密度。',
    '以圓點密度呈現臺北市與新北市近三年行人事故的空間分布。每個點代表約 100 公尺範圍內的事故聚合，顏色越深、圓點越大代表事故件數越多。可快速識別高風險路段與路口，輔助交通安全政策規劃。',
    '識別行人事故黑點，輔助交通安全政策改善規劃。可與人行道設施、路口型態、號誌設計等圖資套疊分析。',
    ARRAY[
        'https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735',
        'https://data.gov.tw/dataset/13139'
    ],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'map_legend',
    E'SELECT\n    unnest(ARRAY[''1-4件（低）'', ''5-9件（中）'', ''10-19件（高）'', ''20件以上（極高）'']) AS name,\n    NULL::float AS value,\n    ''circle'' AS type',
    NULL,
    'metrotaipei'
);

-- C2：雙北行人事故時段分析（三個 city 版本，對應後端 query_charts.city 篩選）
-- 先刪除舊的單一 taipei 版本，再插入三個版本
DELETE FROM public.query_charts WHERE index = 'traffic_pedestrian_hourly_taipei';

-- 共用 SQL 片段（CASE weekday）抽出為說明，實際各版本重複寫入
-- city = taipei：只查臺北市
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_hourly_taipei',
    NULL,
    '{}',
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '內政部警政署',
    '臺北市行人事故依小時與星期幾的分布熱力格。',
    '以熱力格（HeatmapChart）呈現臺北市近三年行人事故在不同時段（0–23時）與不同星期的分布情形。顏色越深代表事故件數越多，可用於識別高風險時段，輔助交通規劃與執法資源配置。',
    '識別行人事故高峰時段（如通勤時段），協助決定執法資源部署時間或號誌調整時機。',
    ARRAY['https://data.gov.tw/dataset/13139'],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'three_d',
    E'SELECT\n    hour::text AS x_axis,\n    CASE EXTRACT(ISODOW FROM make_date(\n        GREATEST(year, 2022),\n        GREATEST(month, 1),\n        1\n    ))\n        WHEN 1 THEN ''週一''\n        WHEN 2 THEN ''週二''\n        WHEN 3 THEN ''週三''\n        WHEN 4 THEN ''週四''\n        WHEN 5 THEN ''週五''\n        WHEN 6 THEN ''週六''\n        WHEN 7 THEN ''週日''\n    END AS y_axis,\n    COUNT(*) AS data\nFROM traffic_pedestrian_accident_taipei\nWHERE year >= 2022 AND hour IS NOT NULL AND month IS NOT NULL\nGROUP BY hour, y_axis\nORDER BY hour, y_axis',
    NULL,
    'taipei'
);

-- city = ntpc：只查新北市
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_hourly_taipei',
    NULL,
    '{}',
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '內政部警政署',
    '新北市行人事故依小時與星期幾的分布熱力格。',
    '以熱力格（HeatmapChart）呈現新北市近三年行人事故在不同時段（0–23時）與不同星期的分布情形。',
    '識別新北市行人事故高峰時段，協助交通規劃與執法資源配置。',
    ARRAY['https://data.gov.tw/dataset/13139'],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'three_d',
    E'SELECT\n    hour::text AS x_axis,\n    CASE EXTRACT(ISODOW FROM make_date(\n        GREATEST(year, 2022),\n        GREATEST(month, 1),\n        1\n    ))\n        WHEN 1 THEN ''週一''\n        WHEN 2 THEN ''週二''\n        WHEN 3 THEN ''週三''\n        WHEN 4 THEN ''週四''\n        WHEN 5 THEN ''週五''\n        WHEN 6 THEN ''週六''\n        WHEN 7 THEN ''週日''\n    END AS y_axis,\n    COUNT(*) AS data\nFROM traffic_pedestrian_accident_ntpc\nWHERE year >= 2022 AND hour IS NOT NULL AND month IS NOT NULL\nGROUP BY hour, y_axis\nORDER BY hour, y_axis',
    NULL,
    'newtaipei'
);

-- city = metrotaipei：雙北合計
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_hourly_taipei',
    NULL,
    '{}',
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '內政部警政署',
    '雙北行人事故依小時與星期幾的分布熱力格。',
    '以熱力格（HeatmapChart）呈現雙北近三年行人事故在不同時段（0–23時）與不同星期的合計分布情形。',
    '識別雙北行人事故高峰時段，協助決定執法資源部署時間或號誌調整時機。',
    ARRAY['https://data.gov.tw/dataset/13139'],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'three_d',
    E'SELECT\n    hour::text AS x_axis,\n    CASE EXTRACT(ISODOW FROM make_date(\n        GREATEST(year, 2022),\n        GREATEST(month, 1),\n        1\n    ))\n        WHEN 1 THEN ''週一''\n        WHEN 2 THEN ''週二''\n        WHEN 3 THEN ''週三''\n        WHEN 4 THEN ''週四''\n        WHEN 5 THEN ''週五''\n        WHEN 6 THEN ''週六''\n        WHEN 7 THEN ''週日''\n    END AS y_axis,\n    COUNT(*) AS data\nFROM (\n    SELECT hour, year, month FROM traffic_pedestrian_accident_taipei WHERE year >= 2022\n    UNION ALL\n    SELECT hour, year, month FROM traffic_pedestrian_accident_ntpc WHERE year >= 2022\n) combined\nWHERE hour IS NOT NULL AND month IS NOT NULL\nGROUP BY hour, y_axis\nORDER BY hour, y_axis',
    NULL,
    'metrotaipei'
);

-- C3：雙北行人事故年度趨勢 (metrotaipei)
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_yearly_trend',
    NULL,
    '{}',
    '{}',
    'static',
    NULL,
    1,
    'year',
    '警察局交通大隊、內政部警政署',
    '雙北行人事故年度趨勢，呈現台北與新北近年事故件數變化。',
    '以雙軸圖呈現臺北市（長條）與新北市（折線）歷年行人事故件數。可觀察 2023 年行人安全改革後的效果，以及雙北城市間的改善差距，作為政策評估的參考依據。',
    '評估行人安全政策成效，比較雙北改善進度，找出需要加強的城市或年度。',
    ARRAY[
        'https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735',
        'https://data.gov.tw/dataset/13139'
    ],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'three_d',
    E'SELECT\n    year::text AS x_axis,\n    city AS y_axis,\n    accident_count AS data\nFROM traffic_pedestrian_yearly_trend\nWHERE year > 0\nORDER BY year, city',
    NULL,
    'metrotaipei'
);

-- C4：行人事故高風險路口排名 (metrotaipei)
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_hotspot_ranking',
    NULL,
    '{}',
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '警察局交通大隊、內政部警政署',
    '近三年雙北行人事故最多的前 20 個路口排名。',
    '列出雙北近三年行人事故件數最多的前 20 個熱點位置。事故件數越高代表該路口的行人安全狀況越需要關注，建議相關單位評估是否需要改善交通設計、號誌規劃或加強執法。',
    '識別最需要優先改善的路口，供政府規劃改善工程（行人保護時相、縮短右轉等待、行人庇護島等）的順序參考。',
    ARRAY[
        'https://data.taipei/dataset/detail?id=2f238b4f-1b27-4085-93e9-d684ef0e2735',
        'https://data.gov.tw/dataset/13139'
    ],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'two_d',
    E'SELECT\n    COALESCE(\n        NULLIF(near_location, ''''),\n        ROUND(center_lng::numeric, 4)::text || '', '' || ROUND(center_lat::numeric, 4)::text\n    ) AS x_axis,\n    accident_count AS data\nFROM traffic_pedestrian_hotspot\nORDER BY accident_count DESC\nLIMIT 20',
    NULL,
    'metrotaipei'
);

-- C5：AI 路口安全報告 (metrotaipei)
INSERT INTO public.query_charts (
    index, history_config, map_config_ids, map_filter,
    time_from, time_to, update_freq, update_freq_unit,
    source, short_desc, long_desc, use_case,
    links, contributors, created_at, updated_at,
    query_type, query_chart, query_history, city
) VALUES (
    'traffic_pedestrian_ai_report',
    NULL,
    '{}',
    '{}',
    'year_start',
    'now',
    1,
    'year',
    '內政部警政署、AI 分析（llama3.3-ffm-70b）',
    '輸入路口名稱，AI 自動查詢事故統計並生成行人安全改善建議報告。',
    '使用 Tool Calling 架構，AI 根據使用者輸入的路口名稱自動呼叫後端 API 查詢該路口的統計資料，並生成包含事故概況、風險因素與具體改善建議的白話報告，展現「數據 → AI 分析 → 行動建議」的完整閉環。',
    '協助決策者快速了解特定路口的行人安全狀況，並取得具體可行的改善方向。',
    ARRAY['https://data.gov.tw/dataset/13139'],
    ARRAY['b12705030'],
    NOW(),
    NOW(),
    'custom',
    E'SELECT 1',
    NULL,
    'metrotaipei'
);


-- ============================================================
-- 5. dashboards 表（建立行人安全儀表板）
-- ============================================================

INSERT INTO public.dashboards (index, name, components, icon, created_at, updated_at)
SELECT
    'pedestrian-safety',
    '行人安全地圖',
    ARRAY(
        SELECT id FROM public.components
        WHERE index IN (
            'traffic_pedestrian_heatmap',
            'traffic_pedestrian_hourly_taipei',
            'traffic_pedestrian_yearly_trend',
            'traffic_pedestrian_hotspot_ranking',
            'traffic_pedestrian_ai_report'
        )
        ORDER BY ARRAY_POSITION(
            ARRAY[
                'traffic_pedestrian_heatmap',
                'traffic_pedestrian_hourly_taipei',
                'traffic_pedestrian_yearly_trend',
                'traffic_pedestrian_hotspot_ranking',
                'traffic_pedestrian_ai_report'
            ],
            index
        )
    ),
    'directions_walk',
    NOW(),
    NOW()
ON CONFLICT (index) DO UPDATE
    SET name       = EXCLUDED.name,
        components = EXCLUDED.components,
        icon       = EXCLUDED.icon,
        updated_at = NOW();


-- ============================================================
-- 6. dashboard_groups 表（將儀表板加入 metrotaipei group）
-- ============================================================

INSERT INTO public.dashboard_groups (dashboard_id, group_id)
SELECT
    d.id,
    g.id
FROM public.dashboards d
CROSS JOIN public.groups g
WHERE d.index = 'pedestrian-safety'
  AND g.name IN ('public', 'metrotaipei')
ON CONFLICT DO NOTHING;


-- ============================================================
-- 驗證
-- ============================================================
SELECT
    c.id,
    c.index,
    c.name,
    cc.types,
    qc.city,
    qc.query_type
FROM public.components c
JOIN public.component_charts cc ON c.index = cc.index
JOIN public.query_charts qc ON c.index = qc.index
WHERE c.index LIKE 'traffic_pedestrian%'
ORDER BY c.index, qc.city;
