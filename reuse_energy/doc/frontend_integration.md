# reuse_energy 前端組件整合說明

本文件說明如何把 `reuse_energy/output/reuse_energy_components.json` 中的四個靜態圖表
組件接到 Taipei-City-Dashboard 的前後端，對齊 `component_doc/spec.md`、
`component_doc/db.md`，以及 `Taipei-City-Dashboard-Documentation` 的
`front-end-ch/introduction-to-components.md`、`front-end-ch/chart-data.md`、
`back-end-ch/components-db.md`、`back-end-ch/component-data-apis.md`。

## 組件總覽

| index                               | 圖表                       | query_type | 說明                      |
| ----------------------------------- | -------------------------- | ---------- | ------------------------- |
| `reuse_energy_capacity_metrotaipei` | `ColumnChart`              | `three_d`  | 最新期 雙北 × 三能源 堆疊 |
| `reuse_energy_mix_taipei`           | `DonutChart` ＋ `BarChart` | `two_d`    | 臺北市 最新期 三能源占比  |
| `reuse_energy_trend_taipei`            | `TimelineStackedChart`     | `time`     | 臺北市 年度三能源折線堆疊 |
| `reuse_energy_trend_column_taipei`     | `ColumnChart`              | `three_d`  | 臺北市 年度三能源縱向堆疊長條（與上列同期） |

> 四個組件皆為 **靜態圖表**：`map_config = null`、`map_filter = null`、
> `history_config = null`、`time_from = "static"`，**不含地點/測站交叉**。

## 與 spec.md 對應

- `chart_config.types` 使用 PascalCase：`ColumnChart`、`DonutChart`、`TimelineStackedChart`（本資料集有兩張 `ColumnChart`，分別為 `three_d`）。
- `ColumnChart` 採 **3D** 資料格式（series 內含 `name` + `data: number[]`、外層 `categories` 為 x 標籤）；
  `DonutChart` ＋ `BarChart` 採 **2D**（`{ "x": ..., "y": ... }`）；
  `TimelineStackedChart` 採 **time**（`x` 為 ISO timestamp `+08:00`）。
- 顏色於 `clean_reuse_energy.py` 的 `FE_ENERGY_COLORS` 中可調。

## FE 接法（純前端 mock）

```vue
<DashboardComponent
  v-for="item in reuseEnergyComponents"
  :key="`${item.index}-${item.city}`"
  :config="item"
/>
```

`DashboardComponent.vue` 會根據 `config.chart_config.types[0]` 自動切換到對應的子元件。

## BE 接法（DB ＋ API）

```bash
psql -h <host> -U <user> -d dashboard \
     -f reuse_energy/output/seed/01_dashboard_data.sql
psql -h <host> -U <user> -d dashboardmanager \
     -f reuse_energy/output/seed/02_dashboardmanager_components.sql
```

`02_*.sql` 為冪等檔（先 `DELETE` 再 `INSERT`）。四個 `query_charts` 內的 SQL
回傳欄位皆為 `x_axis` / `y_axis` / `data`，符合
`back-end-ch/component-data-apis.md` 規範。

## ID 配置

| 物件                          | 值                                                                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| `components.id`               | `911`（雙北 ColumnChart）、`912`（DonutChart）、`913`（TimelineStackedChart）、`914`（年趨勢 ColumnChart） |
| `dashboards.id` / `index`     | `902` / `renewable_energy_taipei`、`903` / `renewable_energy_metrotaipei`                            |
| `dashboards.name` / `icon`    | 再生能源 / `solar_power`                                                                              |
| `dashboard_groups`            | `(902, 2 taipei)`、`(903, 3 metrotaipei)`                                                            |
| `query_charts`                | 4 index × 2 city = **8 筆**                                                                          |

> 兩個 dashboard 共用同一組 `components.id`，差別僅在 `query_charts.city` 與 `dashboard_groups.group_id`。
> 通用作法詳見 [`component_doc/cross_city_dashboard_pattern.md`](../../component_doc/cross_city_dashboard_pattern.md)。

## 重跑

```bash
cd reuse_energy
python3 clean_reuse_energy.py
```

會更新 `output/`：

- `reuse_energy_long.csv`：長表（dashboard DB 載入用）
- `reuse_energy_components.json`：**四個 FE 組件**（含 `chart_data`，可直接渲染）
- `reuse_energy_components_sql_template.sql`：後端三表 INSERT 樣板
- `seed/01_dashboard_data.sql`：dashboard DB 建表 + 全部資料
- `seed/02_dashboardmanager_components.sql`：dashboardmanager 四組件、儀表板、群組
- `clean_summary.txt`：摘要

## 已知限制

- 臺北市「風力」歷年皆為 0（受地形限制），DonutChart 與 TimelineStackedChart 中
  該系列會呈現空白堆疊；若資料更新後出現非 0 值會自動顯示。
- `11502` 列為最新月度快照，會作為 ColumnChart 與 DonutChart 的 latest 期，
  但不納入 TimelineStackedChart（後者僅取年度列）。
- 「再生能源裝置容量 - 雙北比較」元件本身即為雙北圖；切到「臺北儀表板」時 SQL 仍會輸出雙北，這是預期行為。
