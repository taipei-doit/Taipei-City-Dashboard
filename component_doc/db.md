## DB schema

DB: dashboard
→ create table {index} (import csv data)

```
CREATE TABLE public.{index}
```

DB: dashboardmanager
component設定{index}(english_name), name → {index}component_charts設定兩個城市的chart_config → {index}component_maps(自動產生map_config_ids），填寫細節、mapbox樣式、property → query_charts填回map_config_ids

### components

![image.png](attachment:6e64d2f5-81c5-40ef-a216-9bb5af217992:image.png)

### component_charts

set color, chart type

| index                 | color                                                             | types                                    | unit |
| --------------------- | ----------------------------------------------------------------- | ---------------------------------------- | ---- |
| aging_kpi             | {#F65658,#F49F36,#F5C860,#9AC17C,#4CB495,#569C9A,#60819C,#2F8AB1} | {TextUnitChart}                          | NULL |
| aging_workforce_trend | {#24B0DD,#56B96D,#F8CF58,#F5AD4A,#E170A6,#ED6A45,#AF4137,#10294A} | {BarPercentChart,RadarChart,ColumnChart} | %    |

### query_charts

city must be taipei/metrotaipei

| index     | history_config | map_config_ids | map_filter | time_from | time_to | update_freq | update_freq_unit | source | short_desc                     | long_desc                                                                                                                                                                                                                                                                                                                                       | use_case                                                                                                                                                                                                                                                                                           | links                                                                                                                                               | contributors | created_at             | updated_at                 | query_type | query_chart                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | query_history | city        |
| --------- | -------------- | -------------- | ---------- | --------- | ------- | ----------- | ---------------- | ------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | ---------------------- | -------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ----------- |
| aging_kpi | NULL           | {}             | {}         | static    | NULL    | 0           | NULL             | 主計處 | 此圖顯示臺北長照關懷各項指標。 | 此圖表呈現臺北長照關懷相關指標，包括 扶老比、扶幼比、扶養比 及 老化指數。扶老比代表每百名勞動人口需扶養的老年人口數，扶幼比則是需扶養的兒童人口數，而扶養比則合計這兩者，反映整體社會負擔程度。老化指數則比較老年人口與兒童人口比例，顯示人口結構的高齡化趨勢。這些數據可用於評估長照需求，並規劃資源分配與政策方向，以因應人口老化帶來的挑戰。 | 在制定長照政策時，政府可運用 扶老比、扶幼比、扶養比 及 老化指數 來評估未來照護需求。例如，某城市發現扶老比上升且老化指數超過 100，代表老年人口已多於兒童，預示長照需求將持續增加。政府可據此增設長照機構、強化居家照護服務，並鼓勵社區共融計畫，以減輕勞動人口的扶養壓力，確保高齡者獲得適切照顧。 | {https://data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1}                                                                        | {doit}       | 2023-12-20 05:56:00+00 | 2024-06-12 06:02:41.642+00 | three_d    | select y_axis,icon ,round(avg(data))data  from(select '扶老比' as y_axis, percent30 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '扶幼比' as y_axis, percent31 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '扶養比' as y_axis, percent32 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '老化指數' as y_axis, percent33 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計')dgroup by y_axis,icon                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | NULL          | taipei      |
| aging_kpi | NULL           | {}             | {}         | static    | NULL    | 0           | NULL             | 主計處 | 此圖顯示雙北長照關懷各項指標。 | 此圖表呈現雙北長照關懷相關指標，包括 扶老比、扶幼比、扶養比 及 老化指數。扶老比代表每百名勞動人口需扶養的老年人口數，扶幼比則是需扶養的兒童人口數，而扶養比則合計這兩者，反映整體社會負擔程度。老化指數則比較老年人口與兒童人口比例，顯示人口結構的高齡化趨勢。這些數據可用於評估長照需求，並規劃資源分配與政策方向，以因應人口老化帶來的挑戰。 | 在制定長照政策時，政府可運用 扶老比、扶幼比、扶養比 及 老化指數 來評估未來照護需求。例如，某城市發現扶老比上升且老化指數超過 100，代表老年人口已多於兒童，預示長照需求將持續增加。政府可據此增設長照機構、強化居家照護服務，並鼓勵社區共融計畫，以減輕勞動人口的扶養壓力，確保高齡者獲得適切照顧。 | {https://data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1,https://data.ntpc.gov.tw/datasets/8308ab58-62d1-424e-8314-24b65b7ab492} | {doit,ntpc}  | 2023-12-20 05:56:00+00 | 2024-06-12 06:02:41.642+00 | three_d    | select y_axis,icon ,round(avg(data))data  from(select '扶老比' as y_axis, percent30 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '扶幼比' as y_axis, percent31 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '扶養比' as y_axis, percent32 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '老化指數' as y_axis, percent33 as data ,'%' as icon from public.city_age_distribution_taipei where 年份= (select max(年份) from public.city_age_distribution_taipei ) and  區域別='總計' and 統計類型='計'union allselect '扶老比' as y_axis, avg(percent30) as data ,'%' as icon from public.city_age_distribution_newtaipei where 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計'union allselect '扶幼比' as y_axis, avg(percent31) as data ,'%' as icon from public.city_age_distribution_newtaipei where 年份= (select max(年份) from public.city_age_distribution_newtaipei ) and 統計類型='計'union allselect '扶養比' as y_axis, avg(percent32) as data ,'%' as icon from public.city_age_distribution_newtaipei where 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計'union allselect '老化指數' as y_axis, avg(percent33) as data ,'%' as icon from public.city_age_distribution_newtaipei where 年份= (select max(年份) from public.city_age_distribution_newtaipei )  and 統計類型='計')dgroup by y_axis,icon | NULL          | metrotaipei |

component_charts

自行車路網

### component_maps

| id  | index                    | title      | type | source  | size | icon | paint                                                                                    | property |
| --- | ------------------------ | ---------- | ---- | ------- | ---- | ---- | ---------------------------------------------------------------------------------------- | -------- |
| 101 | bike_network_metrotaipei | 自行車路網 | line | geojson | NULL | NULL | {"line-color":["match",["get","direction"],"雙向","#097138","單向","#007BFF","#808080"]} | [        |

{"key": "data_time", "name": "數據時間"},
{"key": "route_name", "name": "路線名稱"},
{"key": "city_code", "name": "城市代碼"},
{"key": "city", "name": "城市"},
{"key": "road_section_start", "name": "起點路段"},
{"key": "road_section_end", "name": "終點路段"},
{"key": "direction", "name": "方向"},
{"key": "cycling_length", "name": "自行車道長度"},
{"key": "finished_time", "name": "完工時間"},
{"key": "update_time", "name": "更新時間"}
] |
| 100 | bike_network_tpe | 自行車路網 | line | geojson | NULL | NULL | {"line-color":["match",["get","direction"],"雙向","#097138","單向","#007BFF","#808080"]} | [
{"key": "data_time", "name": "數據時間"},
{"key": "route_name", "name": "路線名稱"},
{"key": "city_code", "name": "城市代碼"},
{"key": "city", "name": "城市"},
{"key": "road_section_start", "name": "起點路段"},
{"key": "road_section_end", "name": "終點路段"},
{"key": "direction", "name": "方向"},
{"key": "cycling_length", "name": "自行車道長度"},
{"key": "finished_time", "name": "完工時間"},
{"key": "update_time", "name": "更新時間"}
] |
