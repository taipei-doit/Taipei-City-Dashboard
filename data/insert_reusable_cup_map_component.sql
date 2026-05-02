-- ============================================================
-- 循環杯門市地圖組件配置
-- 資料庫: dashboardmanager
-- ============================================================

-- ① component_maps：點位圖層樣式
INSERT INTO public.component_maps (index, title, type, source, paint, property)
VALUES (
    'reusable_cup_store_points',
    '循環杯門市',
    'circle',
    'geojson',
    '{
        "circle-color": "#4CAF50",
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 4, 16, 10],
        "circle-opacity": 0.85,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1
    }',
    '[
        {"key": "brand",      "name": "品牌"},
        {"key": "store_name", "name": "門市名稱"},
        {"key": "address",    "name": "地址"},
        {"key": "phone",      "name": "電話"}
    ]'
)
ON CONFLICT DO NOTHING
RETURNING id, index, title;
