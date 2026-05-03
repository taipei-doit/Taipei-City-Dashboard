-- dashboardmanager：綠建築 multi_chart（index=green_buildings, id=923）新增「縱向堆疊長條圖」視圖
-- 與 BarPercentChart 共用 922 的 three_d 查詢（行政區 × 等級棟數）；堆疊順序：合格級在底、鑽石級在頂（SQL ORDER BY rank_val ASC）
-- 執行：psql -U postgres -d dashboardmanager -f 03_green_buildings_add_column_stacked.sql

UPDATE public.component_charts
   SET types = ARRAY['DistrictChart', 'BarPercentChart', 'ColumnChart']::varchar[]
 WHERE index = 'green_buildings';

UPDATE public.query_charts
   SET query_chart = '[{"id":921,"city":"taipei","types":["DistrictChart"]},{"id":922,"city":"taipei","types":["BarPercentChart"]},{"id":922,"city":"taipei","types":["ColumnChart"]}]',
       updated_at = NOW()
 WHERE index = 'green_buildings' AND city = 'taipei';

UPDATE public.query_charts
   SET query_chart = '[{"id":921,"city":"metrotaipei","types":["DistrictChart"]},{"id":922,"city":"metrotaipei","types":["BarPercentChart"]},{"id":922,"city":"metrotaipei","types":["ColumnChart"]}]',
       updated_at = NOW()
 WHERE index = 'green_buildings' AND city = 'metrotaipei';
