# 再生能源（reuse_energy）組件技術文件

本文件說明如何把 `reuse_energy/` 內的「再生能源裝置容量」資料，落地成
Taipei-City-Dashboard 的 **四個靜態圖表組件**，並說明前後端如何整合。

涵蓋的圖表（對應 `component_doc/spec.md` 第 17 行的 PascalCase 名稱）：

| index                                  | 中文名                                      | 圖表類型                   | `query_type` |
| -------------------------------------- | ------------------------------------------- | -------------------------- | ------------ |
| `reuse_energy_capacity_metrotaipei`    | 再生能源裝置容量 - 雙北比較                 | `ColumnChart`              | `three_d`    |
| `reuse_energy_mix_taipei`              | 再生能源裝置容量 - 能源占比                 | `DonutChart` ＋ `BarChart` | `two_d`      |
| `reuse_energy_trend_taipei`            | 再生能源裝置容量 - 年趨勢                   | `TimelineStackedChart`     | `time`       |
| `reuse_energy_trend_column_taipei`     | 再生能源裝置容量 - 年趨勢（縱向長條）       | `ColumnChart`              | `three_d`    |

> 四組件皆為 **靜態圖表（無地點維度）**：`map_config = NULL`、`map_filter = NULL`、
> `history_config = NULL`、`time_from = static`。
>
> 自 v2 起，四個組件**同時掛載於「臺北儀表板」與「雙北儀表板」**：
>
> - `query_charts` 對每個 `index` 各插 `city='taipei'`／`city='metrotaipei'` 兩筆 SQL
> - `dashboards` 兩筆：`renewable_energy_taipei`(902, group=2) 與 `renewable_energy_metrotaipei`(903, group=3)
> - 詳見 [`cross_city_dashboard_pattern.md`](./cross_city_dashboard_pattern.md)。

---

## 1. 系統架構與檔案位置

```
┌────────────────────────────┐                                          ┌─────────────────────────────────────┐
│  reuse_energy/             │                                          │  Taipei-City-Dashboard-FE           │
│  ├─ 再生能源-台北.csv       │   clean_reuse_energy.py (Python)        │  └─ src/dashboardComponent/         │
│  ├─ 再生能源-雙北.csv       │ ───────────────────────────────────────▶│       DashboardComponent.vue        │
│  ├─ doc/data_collect.txt    │                                          │       components/                   │
│  ├─ clean_reuse_energy.py   │                                          │         ColumnChart.vue             │
│  └─ output/                 │                                          │         DonutChart.vue              │
│     ├─ reuse_energy_components.json     ──── 直接 mock                │         TimelineStackedChart.vue    │
│     ├─ reuse_energy_long.csv                                          └─────────────────────────────────────┘
│     └─ seed/
│        ├─ 01_dashboard_data.sql        ──▶ DB: dashboard
│        └─ 02_dashboardmanager_components.sql  ──▶ DB: dashboardmanager   API: GET /api/v1/component/:id/chart
└────────────────────────────┘
```

兩條接入路徑（擇一或同時使用）：

1. **純前端 mock（無後端）**：把 `output/reuse_energy_components.json` 餵給 `DashboardComponent.vue`。
2. **完整前後端**：執行 `output/seed/*.sql` 灌入 PostgreSQL，前端透過既有 API 取得。

---

## 2. 資料管線（Data Pipeline）

### 2.1 來源

- `reuse_energy/再生能源-台北.csv`：經濟部能源署「再生能源裝置容量」CSV，**utf-8** 編碼（含 BOM）。
  - 兩份 `再生能源-台北.csv` 與 `再生能源-雙北.csv` 內容完全相同（皆同時含臺北/新北兩列）。
- `reuse_energy/doc/data_collect.txt`：清洗規則（年別解析、欄位、單位）。

### 2.2 清洗規則（已套用於腳本）

- **三類能源**：`風力`、`太陽光電`、`其他(含水力)`
- **城市**：保留 `台北市`、`新北市`
- **時間**：
  - `101`–`114` → period_sort = `{ROC:03d}-00`，視為**年度**
  - `11502` → period_sort = `115-02`，視為**最新月度快照**
- **單位**：瓩 (kW)，整數轉換時去除千分位逗號

### 2.3 一鍵重跑

```bash
cd reuse_energy
python3 clean_reuse_energy.py
```

輸出（`reuse_energy/output/`）：

| 檔案                                       | 用途                                                                   |
| ------------------------------------------ | ---------------------------------------------------------------------- |
| `reuse_energy_long.csv`                    | 長表（dashboard DB 載入用）                                            |
| `reuse_energy_components.json`             | **四個 FE 組件**（含 `chart_data`）                                    |
| `reuse_energy_components_sql_template.sql` | 後端 INSERT 速查樣板                                                   |
| `seed/01_dashboard_data.sql`               | dashboard DB：建表 + 全部資料 INSERT                                   |
| `seed/02_dashboardmanager_components.sql`  | dashboardmanager DB：components / charts / queries / dashboard / group |
| `clean_summary.txt`                        | 摘要                                                                   |

---

## 3. 前端整合（Frontend）

### 3.1 渲染元件

`Taipei-City-Dashboard-FE/src/dashboardComponent/DashboardComponent.vue` 是統一容器，
依 `chart_config.types[0]` 自動切到子元件：

- `ColumnChart` → `ColumnChart.vue`（3D 資料：series 內 `name` + `data: number[]`，外層 `categories` 為 x 標籤）
- `DonutChart` → `DonutChart.vue`（2D 資料：`{ "x": ..., "y": ... }`）
- `TimelineStackedChart` → `TimelineStackedChart.vue`（time 資料：`x` 為 ISO timestamp `+08:00`）

> 不需要修改任何 `.vue` 檔案；FE 端只需把組件 config 餵給 `DashboardComponent.vue` 即可。

### 3.2 路徑 A：純前端 mock（最快）

```vue
<script setup>
import reuseEnergyComponents from "@/.../reuse_energy/output/reuse_energy_components.json";
import DashboardComponent from "@/dashboardComponent/DashboardComponent.vue";
</script>

<template>
  <DashboardComponent
    v-for="item in reuseEnergyComponents"
    :key="`${item.index}-${item.city}`"
    :config="item"
  />
</template>
```

### 3.3 路徑 B：透過 API（正式）

當 BE 已灌入 SQL（見 §4）後，FE 透過既有的 `contentStore` / `useContentStore`
呼叫 `GET /api/v1/component/:id/chart` 取得 `chart_data`，
`DashboardComponent.vue` 內部已處理。新組件會出現在新建的儀表板
**「再生能源」（`renewable_energy_taipei`）** 中。

### 3.4 chart_data 範例（節錄）

`reuse_energy_capacity_metrotaipei`（ColumnChart, three_d）：

```json
{
  "categories": ["臺北市", "新北市"],
  "data": [
    { "name": "風力", "data": [0, 13340] },
    { "name": "太陽光電", "data": [83862, 202752] },
    { "name": "其他 (含水力)", "data": [260, 111970] }
  ]
}
```

`reuse_energy_mix_taipei`（DonutChart, 2D）：

```json
{
  "name": "",
  "data": [
    { "x": "風力", "y": 0 },
    { "x": "太陽光電", "y": 83862 },
    { "x": "其他 (含水力)", "y": 260 }
  ]
}
```

`reuse_energy_trend_taipei`（TimelineStackedChart, time）：

```json
[
  { "name": "風力",          "data": [{ "x": "2012-01-01T00:00:00+08:00", "y": 0 }, ...] },
  { "name": "太陽光電",      "data": [{ "x": "2012-01-01T00:00:00+08:00", "y": 172 }, ...] },
  { "name": "其他 (含水力)", "data": [{ "x": "2012-01-01T00:00:00+08:00", "y": 0 }, ...] }
]
```

`reuse_energy_trend_column_taipei`（ColumnChart, three_d；與雙北比較圖同形，X 改為民國年）：

```json
{
  "categories": ["101年", "102年", "103年", "..."],
  "data": [
    { "name": "風力", "data": [0, 0, ...] },
    { "name": "太陽光電", "data": [172, 236, ...] },
    { "name": "其他 (含水力)", "data": [0, 0, ...] }
  ]
}
```

（靜態 JSON 裡 `categories` 在 `chart_config.categories`，`data` 在 `chart_data` 陣列；API 回傳時由後端附加 `categories`。）

---

## 4. 後端整合（Backend）

### 4.1 資料庫角色（依 `component_doc/db.md`）

- **DB: `dashboard`**：實際資料表 `public.reuse_energy_capacity`，由 SQL 查詢。
- **DB: `dashboardmanager`**：四張組態表
  - `components`（PK `id`）
  - `component_charts`（PK `index`，色票/types/unit）
  - `component_maps`（不需要，本組件無圖層）
  - `query_charts`（FK `index`、`map_config_ids`，含 SQL `query_chart`、`query_type`、`city`）

### 4.2 灌入步驟

```bash
psql -h <host> -U <user> -d dashboard \
     -f reuse_energy/output/seed/01_dashboard_data.sql

psql -h <host> -U <user> -d dashboardmanager \
     -f reuse_energy/output/seed/02_dashboardmanager_components.sql
```

`02_dashboardmanager_components.sql` **冪等**：開頭會 `DELETE` 同 `index`/`id` 之
舊紀錄，可重複執行。

### 4.3 query_charts 內的 SQL（已寫進 seed）

每個 `index` 在 `query_charts` 各有兩筆 city 版本：

| index                                | `city=taipei`                                                                            | `city=metrotaipei`                              |
| ------------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `reuse_energy_capacity_metrotaipei`  | 與 metrotaipei 相同（本身即雙北比較圖）                                                  | `(city × energy_type)` 笛卡兒交叉左連最新期資料 |
| `reuse_energy_mix_taipei`            | `WHERE city = '台北市'`、最新期                                                          | 移除 city 過濾，最新期；雙北合計三能源          |
| `reuse_energy_trend_taipei`          | `WHERE city = '台北市'`、`period_sort LIKE '%-00'`                                       | 移除 city 過濾、同年度範圍；雙北合計            |
| `reuse_energy_trend_column_taipei`   | `WHERE city = '台北市'`，`x_axis = period_label`，列順序符合 `GetThreeDimensionalData`    | 移除 city 過濾、同樣排序；雙北合計              |

### 4.4 ID 與儀表板配置

| 物件                        | 值                                                                                                   |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| `components.id`             | `911`（雙北 ColumnChart）、`912`（DonutChart）、`913`（TimelineStackedChart）、`914`（年趨勢 ColumnChart） |
| `dashboards.id` / `index`   | `902` / `renewable_energy_taipei`、`903` / `renewable_energy_metrotaipei`                            |
| `dashboards.name` / `icon`  | 再生能源 / `solar_power`                                                                              |
| `dashboard_groups`          | `(902, 2 taipei)`、`(903, 3 metrotaipei)`                                                            |
| `query_charts (index, city)` | 4 個 index × 2 個 city = **8 筆**                                                                    |

> FE 切換城市選單會以 `(component.index, 新 city)` 重打 `GET /component/:id/chart`，
> 因此每個 city 都必須在 `query_charts` 有對應筆，否則切過去會空白。

---

## 5. 對齊規範對照表

| 規範來源                                                                 | 對應實作                                                        |
| ------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `component_doc/spec.md` 第 6–14 行 — `chart_config`                      | `reuse_energy_components.json` 各組件 `chart_config`            |
| `component_doc/spec.md` 第 17 行 — 圖表類型                              | PascalCase：`ColumnChart`、`DonutChart`、`TimelineStackedChart` |
| `component_doc/db.md` `components` / `component_charts` / `query_charts` | seed SQL `02_*` 完整對齊                                        |
| Documentation `front-end-ch/introduction-to-components.md`               | `chart_data` / `query_type` / `city` / `time_from` 全填齊       |
| Documentation `front-end-ch/chart-data.md` `two_d`                       | DonutChart 使用 `{ "x": ..., "y": ... }`                        |
| Documentation `front-end-ch/chart-data.md` `three_d`                     | ColumnChart 使用 `categories` + 多 series                       |
| Documentation `front-end-ch/chart-data.md` `time`                        | TimelineStackedChart 使用 ISO `+08:00`                          |
| Documentation `back-end-ch/component-data-apis.md`                       | `query_chart` 回傳欄位 = `x_axis` / `y_axis` / `data`           |

---

## 6. 操作與維運

### 6.1 來源更新時

1. 替換 `reuse_energy/再生能源-台北.csv`（utf-8）。
2. 重新執行：

   ```bash
   python3 clean_reuse_energy.py
   ```

3. 重新灌 `seed/01_dashboard_data.sql`（會 `DROP TABLE` 後重建）。
4. `seed/02_*` 通常不需重灌（schema 沒變）。

### 6.2 已知限制

- 臺北市「風力」歷年皆為 0（受地形限制），DonutChart、TimelineStackedChart 與年趨勢縱向長條中
  該系列會呈現空白堆疊；若未來資料出現非 0 值會自動顯示。
- `11502` 列為最新月度快照，會作為「雙北比較」ColumnChart 與 DonutChart 的 latest 期，
  但**不**納入 TimelineStackedChart 與「臺北市年趨勢（縱向長條）」（兩者僅取 `period_sort` 結尾為 `-00` 的年度列）。

### 6.3 偵錯

- API 回傳異常：先查 `dashboardmanager.query_charts.query_chart` 是否能在
  `dashboard` DB 直接執行成功。
- 圖表空白：確認 `dashboardmanager.component_charts.types` 是否為 PascalCase；
  確認 FE 取到的 `chart_data` 結構符合 `chart-data.md`。
- TimelineStackedChart 不顯示：時間戳請使用 ISO 並帶時區（範例 `+08:00`）。

---

## 7. 參考輸出（最近一次跑出的範例值）

來自 `reuse_energy_components.json`（`115年 2月`）：

- ColumnChart（雙北）：臺北市 [風力 0 / 太陽光電 83,862 / 其他(含水力) 260]、新北市 [風力 13,340 / 太陽光電 202,752 / 其他(含水力) 111,970]（單位：瓩）
- DonutChart（臺北市）：風力 0 / 太陽光電 83,862 / 其他(含水力) 260
- TimelineStackedChart（臺北市）：101–114 共 14 個年度，三條序列各 14 點
- ColumnChart（臺北市年趨勢）：X 軸 14 個年度，三序列堆疊長條，資料與上列 Timeline 相同年度範圍

---

## 8. 相關檔案索引

| 檔案                                                                    | 角色                                 |
| ----------------------------------------------------------------------- | ------------------------------------ |
| `reuse_energy/clean_reuse_energy.py`                                    | 清洗 + 產生 FE/BE 全部產物           |
| `reuse_energy/doc/data_collect.txt`                                     | 清洗規則                             |
| `reuse_energy/doc/frontend_integration.md`                              | 簡版整合說明                         |
| `reuse_energy/output/reuse_energy_components.json`                      | 四個 FE 組件 config（含 chart_data） |
| `reuse_energy/output/seed/01_dashboard_data.sql`                        | dashboard DB seed                    |
| `reuse_energy/output/seed/02_dashboardmanager_components.sql`           | dashboardmanager DB seed             |
| `component_doc/spec.md`                                                 | 圖表/地圖/篩選/歷史 通用規格         |
| `component_doc/db.md`                                                   | DB schema 與分表規則                 |
| `component_doc/car_type_components.md`                                  | car-type 對應文件（同模式）          |
| `Taipei-City-Dashboard-Documentation/.../introduction-to-components.md` | 組件配置欄位說明                     |
| `Taipei-City-Dashboard-Documentation/.../chart-data.md`                 | 五種 chart_data 形狀                 |
| `Taipei-City-Dashboard-Documentation/.../components-db.md`              | 後端表結構                           |
| `Taipei-City-Dashboard-Documentation/.../component-data-apis.md`        | SQL 結果與 API 編譯規則              |
| `component_doc/cross_city_dashboard_pattern.md`                         | 雙北儀表板與 city 切換通用作法       |
