# car-type 前端組件整合說明

本文件說明如何把 `car-type/output/vehicle_components.json` 中的靜態圖表組件接到
Taipei-City-Dashboard 的前後端，對齊 `component_doc/spec.md`、`component_doc/db.md`，以及
`Taipei-City-Dashboard-Documentation` 的 `front-end-ch/introduction-to-components.md`、
`front-end-ch/chart-data.md`、`back-end-ch/components-db.md`、`back-end-ch/component-data-apis.md`。

## 組件總覽

| index | 圖表 | query_type | 說明 |
| --- | --- | --- | --- |
| `vehicle_type_count_taipei` | `ColumnChart` | `three_d` | 最新月份各車種 × ICE/BEV/Hybrid 堆疊（笛卡兒補零） |
| `vehicle_fuel_mix_taipei` | `DonutChart` ＋ `BarChart` | `two_d` | 最新月份 ICE / BEV / Hybrid 占比 |
| `vehicle_fuel_trend_taipei` | `TimelineStackedChart` | `time` | 月趨勢，三類燃料堆疊 |

> 三個組件皆為 **靜態圖表**：`map_config = null`、`map_filter = null`、
> `history_config = null`、`time_from = "static"`，**不含地點/測站交叉**。

## 臺北與雙北

- 後端：`query_charts` 對每個 `index` 各有 `city='taipei'`（僅 `region='臺北市'`）與
  `city='metrotaipei'`（`region IN ('臺北市','新北市')` 加總）兩筆。
- 儀表板：`green_transition_taipei`（901，group 2）與 `green_transition_metrotaipei`（904，group 3）
  共用同一組 `components.id`（901–903）。
- 前端 mock：`vehicle_components.json` 為 **六個物件**（三組件 × 兩種 `city`），
  `:key="`${item.index}-${item.city}`"` 即可並列渲染。
- 通用模式見 [`component_doc/cross_city_dashboard_pattern.md`](../../component_doc/cross_city_dashboard_pattern.md)。

## 與 spec.md 對應

- `chart_config.types` 使用 PascalCase：`ColumnChart`、`DonutChart`、`TimelineStackedChart`。
- `ColumnChart`（各車種）採 **three_d**（`categories` + 多 series）；`DonutChart`／`BarChart` 採 **two_d**；
  `TimelineStackedChart` 採 **time**（`x` 為 ISO timestamp）。
- 色票於 `clean_vehicle_data.py` 的 `FE_FUEL_COLORS`、`FE_DONUT_PALETTE` 等可調。

## FE 接法（純前端 mock）

```vue
<DashboardComponent
  v-for="item in vehicleComponents"
  :key="`${item.index}-${item.city}`"
  :config="item"
/>
```

`DashboardComponent.vue` 會根據 `config.chart_config.types[0]` 自動切換子元件。

## BE 接法（DB ＋ API）

1. 灌入 `dashboard`：`car-type/output/seed/01_dashboard_data.sql`（含 `vehicle_registration_monthly` 臺北+新北列）。
2. 灌入 `dashboardmanager`：`car-type/output/seed/02_dashboardmanager_components.sql`（三組件、6 筆 `query_charts`、兩個 dashboard）。
3. API：`GET /api/v1/component/:id/chart?city=taipei|metrotaipei`。

## 重跑

```bash
cd car-type
python3 clean_vehicle_data.py
```

會更新 `output/`：

- `vehicle_registrations_monthly_long.csv`：長表。
- `vehicle_monthly_dashboard.json`：每月、每車種、每區的 ICE/BEV/Hybrid 與占比。
- `vehicle_monthly_timeline_stack.json`：`doc/data_collect.txt` 之 `timeline_fuel_stack` 結構。
- `vehicle_components.json`：**六筆** FE mock（`city`: `taipei` 與 `metrotaipei`）。
- `vehicle_components_sql_template.sql`：後端樣板（可能與 seed 細節不同步，以 `seed/02_*.sql` 為準）。
- `seed/01_dashboard_data.sql`、`seed/02_dashboardmanager_components.sql`。
