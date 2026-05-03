# 車輛類型（car-type）組件技術文件

本文件說明如何把 `car-type/` 內的「機動車輛新車領牌數」資料，落地成
Taipei-City-Dashboard 的 **三個靜態圖表組件**，並說明前後端如何整合。

涵蓋的圖表（對應 `component_doc/spec.md` 第 17 行的英文 PascalCase 圖表名稱）：

| index | 中文名 | 圖表類型 | `query_type` |
| --- | --- | --- | --- |
| `vehicle_type_count_taipei` | 新領牌車輛 - 各車種輛數 | `ColumnChart`（堆疊縱向長條） | `three_d` |
| `vehicle_fuel_mix_taipei` | 新領牌車輛 - 燃料類別占比 | `DonutChart` ＋ `BarChart` | `two_d` |
| `vehicle_fuel_trend_taipei` | 新領牌車輛 - 燃料類別月趨勢 | `TimelineStackedChart` | `time` |

> 三組件皆為 **靜態圖表（無地點維度）**：`map_config = NULL`、`map_filter = NULL`、
> `history_config = NULL`、`time_from = static`。空品/PM2.5 之交叉分析不在此範圍。
>
> **雙北儀表板**：`query_charts` 對每個 `index` 各插 `city='taipei'`（僅 `region='臺北市'`）與
> `city='metrotaipei'`（`region IN ('臺北市','新北市')` 加總）兩筆；儀表板
> `green_transition_taipei`(901) 與 `green_transition_metrotaipei`(904) 共用同一組 `components.id`。
> 通用作法見 [`cross_city_dashboard_pattern.md`](./cross_city_dashboard_pattern.md)。

---

## 1. 系統架構與檔案位置

```
┌───────────────────────────┐                                            ┌──────────────────────────────────────┐
│  car-type/                │                                            │  Taipei-City-Dashboard-FE            │
│  ├─ 車輛類型11303_11503.csv │   clean_vehicle_data.py (Python)         │  └─ src/dashboardComponent/          │
│  ├─ doc/data_collect.txt   │ ───────────────────────────────────────▶ │       DashboardComponent.vue         │
│  ├─ clean_vehicle_data.py  │                                            │       components/                    │
│  └─ output/                │                                            │         BarChart.vue                 │
│     ├─ vehicle_components.json     ──── 直接 mock                       │         DonutChart.vue               │
│     ├─ vehicle_registrations_monthly_long.csv                            │         TimelineStackedChart.vue     │
│     └─ seed/                                                              └──────────────────────────────────────┘
│        ├─ 01_dashboard_data.sql        ──▶ DB: dashboard
│        └─ 02_dashboardmanager_components.sql  ──▶ DB: dashboardmanager   API: GET /api/v1/component/:id/chart
└───────────────────────────┘
```

兩條接入路徑（擇一或同時使用）：

1. **純前端 mock（無後端）**：把 `output/vehicle_components.json` 餵給 `DashboardComponent.vue`。
2. **完整前後端**：執行 `output/seed/*.sql` 灌入 PostgreSQL，前端透過既有 API 取得。

---

## 2. 資料管線（Data Pipeline）

### 2.1 來源

- `car-type/車輛類型11303_11503.csv`：交通部「機動車輛新車領牌數」CSV，**big5** 編碼，
  含 113 年起逐月之雙北數據。
- `car-type/doc/data_collect.txt`：清洗規則（燃料三類、車種篩選、僅月度）。

### 2.2 清洗規則（已套用於腳本）

- **燃料三類（ICE / BEV / Hybrid）**
  - `ICE`：汽油、柴油、液化石油氣、汽油/LPG
  - `BEV`：電能
  - `Hybrid`：汽油/電能、柴油/電能、電能/汽油、電能/柴油、電能(增程)、汽油(油電)、柴油(油電)、汽油(電能)
- **車種**：保留大客車、大貨車、小客車、小貨車、機車；
  排除「全體總計」、「汽車匯總」、「特種車」。
- **時間**：僅保留月度列（`113年 3月` 形式）；排除整年列與 `(1~3月)` 等累計列。
- **地區**：保留 `臺北市`、`新北市`、`總計`（雙北合計）。

### 2.3 一鍵重跑

```bash
cd car-type
python3 clean_vehicle_data.py
```

輸出（`car-type/output/`）：

| 檔案 | 用途 |
| --- | --- |
| `vehicle_registrations_monthly_long.csv` | 月度長表（dashboard DB 載入用） |
| `vehicle_monthly_dashboard.json` | 每期/每車種/每區之 ICE/BEV/Hybrid 與占比 |
| `vehicle_monthly_timeline_stack.json` | `data_collect.txt` 的 `timeline_fuel_stack` 結構 |
| `vehicle_components.json` | **三個 FE 組件**（含 `chart_data`，可直接渲染） |
| `vehicle_components_sql_template.sql` | 後端 INSERT 速查樣板 |
| `seed/01_dashboard_data.sql` | dashboard DB：建表 + 全部資料 INSERT |
| `seed/02_dashboardmanager_components.sql` | dashboardmanager DB：components / charts / queries / dashboard / group |
| `clean_summary.txt` | 摘要 |

---

## 3. 前端整合（Frontend）

### 3.1 渲染元件

`Taipei-City-Dashboard-FE/src/dashboardComponent/DashboardComponent.vue` 是統一容器，
依 `chart_config.types[0]` 自動切到子元件（位於同層 `components/`）：

- `BarChart` → `BarChart.vue`（2D 資料：`{ "x": ..., "y": ... }`）
- `DonutChart` → `DonutChart.vue`（2D 資料）
- `TimelineStackedChart` → `TimelineStackedChart.vue`（time 資料：`x` 為 ISO timestamp `+08:00`）

> 不需要修改任何 `.vue` 檔案；FE 端只需把組件 config 餵給 `DashboardComponent.vue` 即可。

### 3.2 路徑 A：純前端 mock（最快）

讀取 `output/vehicle_components.json`，例如：

```vue
<script setup>
import vehicleComponents from "@/.../car-type/output/vehicle_components.json";
import DashboardComponent from "@/dashboardComponent/DashboardComponent.vue";
</script>

<template>
  <DashboardComponent
    v-for="item in vehicleComponents"
    :key="`${item.index}-${item.city}`"
    :config="item"
  />
</template>
```

### 3.3 路徑 B：透過 API（正式）

當 BE 已灌入 SQL（見 §4）後，FE 透過既有的 `contentStore` / `useContentStore`
呼叫 `GET /api/v1/component/:id/chart` 取得 `chart_data`，
`DashboardComponent.vue` 內部已處理。新組件會出現在儀表板 **「綠能轉型」**：臺北側欄為 `green_transition_taipei`（901），
雙北側欄為 `green_transition_metrotaipei`（904）；兩者元件清單相同，差在預設 `city` 與
`query_charts` 的 SQL 範圍。

### 3.4 chart_data 範例（節錄）

`vehicle_type_count_taipei`（`ColumnChart`，`three_d`；X=車種、series=燃料三類）：

```json
{
  "categories": ["小客車", "機車", "小貨車", "大貨車", "大客車"],
  "data": [
    { "name": "純油 (ICE)", "data": [5999, 5050, 650, 68, 22] },
    { "name": "純電 (BEV)", "data": [0, 0, 0, 0, 0] },
    { "name": "油電/混合 (Hybrid)", "data": [0, 0, 0, 0, 0] }
  ]
}
```

`vehicle_fuel_mix_taipei`（DonutChart, 2D）：

```json
{
  "name": "",
  "data": [
    { "x": "純油 (ICE)",         "y": 6515 },
    { "x": "純電 (BEV)",         "y": 2201 },
    { "x": "油電/混合 (Hybrid)", "y": 3073 }
  ]
}
```

`vehicle_fuel_trend_taipei`（TimelineStackedChart, time）：

```json
[
  { "name": "純油 (ICE)",         "data": [{ "x": "2024-03-01T00:00:00+08:00", "y": 7746 }, ...] },
  { "name": "純電 (BEV)",         "data": [{ "x": "2024-03-01T00:00:00+08:00", "y": 1533 }, ...] },
  { "name": "油電/混合 (Hybrid)", "data": [{ "x": "2024-03-01T00:00:00+08:00", "y": 2270 }, ...] }
]
```

---

## 4. 後端整合（Backend）

### 4.1 資料庫角色（依 `component_doc/db.md`）

- **DB: `dashboard`**：實際資料表 `public.vehicle_registration_monthly`，由 SQL 查詢。
- **DB: `dashboardmanager`**：四張組態表
  - `components`（PK `id`）
  - `component_charts`（PK `index`，色票/types/unit）
  - `component_maps`（不需要，本組件無圖層）
  - `query_charts`（FK `index`、`map_config_ids`，含 SQL `query_chart`、`query_type`、`city`）

### 4.2 Schema（與 BE Go model 對齊）

詳見 `Taipei-City-Dashboard-BE/app/models/componentConfig.go`：

```go
type Component       struct { ID, Index, Name }
type ComponentChart  struct { Index, Color[], Types[], Unit }
type QueryCharts     struct { Index, MapConfigIDs[], MapFilter, TimeFrom, TimeTo,
                              UpdateFreq, UpdateFreqUnit, Source, ShortDesc, LongDesc,
                              UseCase, Links[], Contributors[], CreatedAt, UpdatedAt,
                              QueryType, QueryChart, QueryHistory, City }
```

### 4.3 灌入步驟

```bash
# 1. dashboard DB（資料表 + 月度資料）
psql -h <host> -U <user> -d dashboard \
     -f car-type/output/seed/01_dashboard_data.sql

# 2. dashboardmanager DB（三組件 + 綠能轉型儀表板臺北/雙北 + 對應群組）
psql -h <host> -U <user> -d dashboardmanager \
     -f car-type/output/seed/02_dashboardmanager_components.sql
```

`02_dashboardmanager_components.sql` **冪等**：開頭會 `DELETE` 同 `index`/`id` 之
舊紀錄，可重複執行。

### 4.4 query_charts 內的 SQL（已寫進 seed）

依 `component-data-apis.md`，回傳欄位為 `x_axis`、`y_axis`、`data`。

| `index` | `query_type` | `city=taipei` | `city=metrotaipei` |
| --- | --- | --- | --- |
| `vehicle_type_count_taipei` | `three_d` | 笛卡兒（車種×燃料）左連 `region='臺北市'`、臺北最新月 | 同上，`region IN ('臺北市','新北市')`、雙北共同最新月加總 |
| `vehicle_fuel_mix_taipei` | `two_d` | 臺北最新月，三燃料 `SUM` | 雙北最新月加總後三燃料 `SUM` |
| `vehicle_fuel_trend_taipei` | `time` | 臺北逐月 `SUM`，ROC 鍵轉 ISO | 雙北同月加總後逐月堆疊 |

完整 SQL 見 `car-type/output/seed/02_dashboardmanager_components.sql`。

### 4.5 ID 與儀表板配置

| 物件 | 值 |
| --- | --- |
| `components.id` | `901`（各車種 ColumnChart）、`902`（DonutChart）、`903`（TimelineStackedChart） |
| `dashboards.id` / `index` | `901` / `green_transition_taipei`、`904` / `green_transition_metrotaipei` |
| `dashboards.name` / `icon` | 綠能轉型 / `directions_car` |
| `dashboard_groups` | `(901, 2 taipei)`、`(904, 3 metrotaipei)` |
| `query_charts` | 3 index × 2 city = **6 筆** |

---

## 5. 對齊規範對照表

| 規範來源 | 對應實作 |
| --- | --- |
| `component_doc/spec.md` 第 6–14 行 — `chart_config` | `vehicle_components.json` 各組件 `chart_config`（color/types/unit/categories） |
| `component_doc/spec.md` 第 22–40 行 — 圖表類型 | 用 PascalCase：`ColumnChart`、`DonutChart`、`TimelineStackedChart` |
| `component_doc/db.md` `components` / `component_charts` / `query_charts` | seed SQL `02_*` 完整對齊 |
| Documentation `front-end-ch/introduction-to-components.md` | `chart_data` / `query_type` / `city` / `time_from` 全填齊 |
| Documentation `front-end-ch/chart-data.md` `two_d` / `three_d` | DonutChart 使用 `{ "x", "y" }`；各車種圖為 `three_d` + `ColumnChart` |
| Documentation `front-end-ch/chart-data.md` `time` | TimelineStackedChart 使用 ISO `+08:00` 時間戳 |
| Documentation `back-end-ch/component-data-apis.md` | `query_chart` 回傳欄位 = `x_axis` / `y_axis` / `data` |

---

## 6. 操作與維運

### 6.1 來源更新時

1. 替換 `car-type/車輛類型XXXXXX_XXXXXX.csv`（big5）。
2. 若檔名變了，編輯 `clean_vehicle_data.py` 的 `DEFAULT_INPUT`，或執行：
   ```bash
   python3 clean_vehicle_data.py -i path/to/new.csv
   ```
3. 重新灌 `seed/01_dashboard_data.sql`（會 `DROP TABLE` 後重建）。
4. `seed/02_*` 通常不需重灌（schema 沒變）。

### 6.2 多城市擴充

- 已內建 **`taipei` + `metrotaipei`**：`metrotaipei` 以 `region IN ('臺北市','新北市')` 加總
  （資料來源長表已含新北市列，見 `vehicle_registrations_monthly_long.csv`）。
- 若僅要新北單一行政區，可另增 `city='newtaipei'` 與 `WHERE region = '新北市'` 的 `query_charts` 一筆。
- 同 `components.index` 跨城市時，`query_charts` 須每個 `city` 各一筆（主鍵 `(index, city)`）。

### 6.3 偵錯

- API 回傳異常：先查 `dashboardmanager.query_charts.query_chart` 是否能在
  `dashboard` DB 直接執行成功。
- 圖表空白：確認 `dashboardmanager.component_charts.types` 是否為 PascalCase；
  確認 FE 取到的 `chart_data` 結構符合 `chart-data.md`。
- TimelineStackedChart 不顯示：時間戳請使用 ISO 並帶時區（範例 `+08:00`）。

---

## 7. 參考輸出（最近一次跑出的範例值）

來自 `vehicle_components.json`（`115年 3月`，臺北市）：

- BarChart：小客車 5,999 / 機車 5,050 / 小貨車 650 / 大客車 68 / 大貨車 22
- DonutChart：ICE 6,515 / BEV 2,201 / Hybrid 3,073
- TimelineStackedChart：`113-03` ~ `115-03` 共 25 個月，三條序列各 25 點

---

## 8. 相關檔案索引

| 檔案 | 角色 |
| --- | --- |
| `car-type/clean_vehicle_data.py` | 清洗 + 產生 FE/BE 全部產物 |
| `car-type/doc/data_collect.txt` | 清洗規則（含 BE 三圖表 JSON 合約） |
| `car-type/doc/frontend_integration.md` | 簡版整合說明（本文件之精簡先導） |
| `car-type/output/vehicle_components.json` | 六筆 FE mock（臺北 `city=taipei` + 雙北 `city=metrotaipei`，同 index 不同 city） |
| `component_doc/cross_city_dashboard_pattern.md` | 雙北儀表板與 city 切換通用作法 |
| `car-type/output/seed/01_dashboard_data.sql` | dashboard DB seed |
| `car-type/output/seed/02_dashboardmanager_components.sql` | dashboardmanager DB seed |
| `component_doc/spec.md` | 圖表/地圖/篩選/歷史 通用規格 |
| `component_doc/db.md` | DB schema 與分表規則 |
| `Taipei-City-Dashboard-Documentation/.../introduction-to-components.md` | 組件配置欄位說明 |
| `Taipei-City-Dashboard-Documentation/.../chart-data.md` | 五種 chart_data 形狀 |
| `Taipei-City-Dashboard-Documentation/.../components-db.md` | 後端表結構 |
| `Taipei-City-Dashboard-Documentation/.../component-data-apis.md` | SQL 結果與 API 編譯規則 |
