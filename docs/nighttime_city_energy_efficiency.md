# 夜間城市能源效率：路燈 LED 轉型與維修熱點

## 目的

本組件用來判斷雙北公共照明能源效率與維修壓力。使用者可以在臺北市與雙北合併視圖間切換，快速找出高瓦數、非 LED、老舊或維修頻繁的行政區，作為路燈汰換、巡檢與節能政策的優先排序依據。

本組件應作為 Sustainable Environment 儀表板的主要 map layer 之一。地圖呈現路燈點位或行政區聚合熱區，圖表呈現 LED 轉型比例、維修通報與優先汰換分數。

## 核心問題

- 哪些行政區的非 LED 或高瓦數路燈比例偏高？
- 哪些行政區路燈維修通報量偏高，可能需要優先巡檢？
- 臺北市與雙北合併視圖下，公共照明能源效率差異在哪裡？
- 若只能先汰換部分路燈，哪些行政區或點位的優先順序最高？

## 使用情境

環保、工務或城市治理人員打開儀表板後，先用城市範圍切換檢視臺北市或雙北合併狀態，再用行政區排名找出高風險區。點選圖表中的行政區後，地圖同步篩選該區路燈點位或熱區，輔助確認空間分布。

## 資料來源

| 來源 | URL | 主要欄位 | 用途 |
|------|-----|----------|------|
| 臺北市路燈位置分布圖 | https://data.taipei/dataset/detail?id=262e80cf-579c-4bfb-ba73-31621bc84616 | `SerialNumber`, `Dist`, `Quantity`, `LightKind`, `LightWatt`, `LightHeight`, `LightYear`, `TWD97X`, `TWD97Y`, `UpdDate` | 臺北點位、燈種、瓦數、使用年限、地圖圖層 |
| 臺北市路燈維修資料 | https://data.taipei/dataset/detail?id=0219b559-c9e4-4efe-93f0-9961360bd7bf | `查報序號`, `行政區`, `查報地點`, `故障情形`, `查報日期` | 維修熱點與行政區維修壓力 |
| 臺北市路燈（104 年以後） | https://data.taipei/dataset/detail?id=0087b600-a9b1-4664-9c79-fbf7e14e91f2 | `統計期`, `總數`, `複金屬燈數`, `鈉光燈數`, `LED 燈數`, `日光燈數`, `其他路燈數` | 年度 LED 轉型趨勢 |
| 新北市路燈資料 | https://data.ntpc.gov.tw/datasets/39149fe0-85ab-4e6c-99e5-60657d44895f | 依實際下載欄位校正 | 新北行政區比較與雙北合併視圖 |

## ETL 設計

### 清理規則

- 將臺北市 TWD97 座標轉為 WGS84，寫入 `wkb_geometry`。
- 統一行政區欄位為 `city`、`district`，城市值使用 `臺北市`、`新北市`。
- 燈種標準化為 `LED`、`sodium`、`metal_halide`、`fluorescent`、`other`、`unknown`。
- 瓦數轉為數值欄位 `watt`，無法判讀時保留 `NULL` 並計入資料完整率。
- 使用年分欄位統一為 `installed_or_used_year`，並依目前年份計算 `estimated_age_years`。
- 維修資料以行政區與月份聚合，故障類型保留原文並另建 `repair_type_normalized`。
- 新北若缺少燈種、瓦數或點位座標，第一版仍保留行政區聚合，並在資料品質指標中揭露缺漏。

### 建議資料表

`env_streetlight_assets`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city` | text | 臺北市或新北市 |
| `district` | text | 行政區 |
| `light_id` | text | 原始路燈識別碼 |
| `light_type` | text | 標準化燈種 |
| `watt` | numeric | 瓦數 |
| `installed_or_used_year` | integer | 裝設或使用年分 |
| `estimated_age_years` | numeric | 估算使用年限 |
| `data_completeness_score` | numeric | 欄位完整率 |
| `data_time` | timestamptz | 資料內容時間 |
| `wkb_geometry` | geometry(Point, 4326) | 路燈位置 |

`env_streetlight_repairs_monthly`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city` | text | 城市 |
| `district` | text | 行政區 |
| `repair_month` | date | 維修通報月份 |
| `repair_type_normalized` | text | 標準化故障類型 |
| `repair_count` | integer | 維修通報數 |
| `data_time` | timestamptz | 資料內容時間 |

`env_streetlight_district_score`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city_scope` | text | `taipei` 或 `twin_city` |
| `city` | text | 城市 |
| `district` | text | 行政區 |
| `light_count` | integer | 路燈數 |
| `led_count` | integer | LED 路燈數 |
| `led_ratio` | numeric | LED 路燈占比 |
| `high_watt_count` | integer | 高瓦數燈具數 |
| `avg_age_years` | numeric | 平均使用年限 |
| `repair_count_recent_12m` | integer | 近 12 個月維修通報數 |
| `lights_per_sq_km` | numeric | 每平方公里路燈密度 |
| `replacement_priority_score` | numeric | 優先汰換分數 |
| `data_time` | timestamptz | 資料內容時間 |

## 優先汰換分數

第一版採透明加權分數，不使用黑箱模型：

```text
replacement_priority_score =
  0.30 * non_led_ratio_score +
  0.25 * high_watt_ratio_score +
  0.20 * age_score +
  0.20 * repair_pressure_score +
  0.05 * data_completeness_penalty
```

各子分數以行政區內 min-max normalization 轉為 0 到 100。資料不足的城市或行政區不應被誤判為低風險，需以 `data_completeness_penalty` 呈現資料限制。

## Dashboard 組件設計

### 指標卡

- 路燈總數
- LED 路燈占比
- 高瓦數燈具數
- 近 12 個月維修通報數
- 優先汰換行政區數

### 圖表

| 圖表 | query type | chart type | 說明 |
|------|------------|------------|------|
| 行政區優先汰換排名 | `two_d` | `BarChart` | `x=district`, `y=replacement_priority_score` |
| LED 與非 LED 結構 | `percent` | `GuageChart` 或 `IconPercentChart` | 顯示 LED 占比 |
| 年度 LED 轉型趨勢 | `time` | `TimelineSeparateChart` | 使用臺北市年度統計資料 |
| 維修類型分布 | `three_d` | `BarPercentChart` | `x=district`, series 為故障類型 |

### 地圖

- 圖層 1：路燈點位，屬性包含 `city`、`district`、`light_type`、`watt`、`replacement_priority_score`。
- 圖層 2：行政區聚合熱區，顏色依 `replacement_priority_score`。
- `map_filter` 使用 `byParam`，以 `district` 對應圖表 x 軸。
- 若新北沒有點位座標，雙北合併視圖第一版用行政區聚合熱區；臺北市視圖保留點位 drill-down。

## Backend 查詢範例

行政區排名：

```sql
SELECT district AS x, replacement_priority_score AS y
FROM env_streetlight_district_score
WHERE city_scope = $1
ORDER BY replacement_priority_score DESC;
```

LED 占比：

```sql
SELECT 'LED' AS x, SUM(led_count) AS y
FROM env_streetlight_district_score
WHERE city_scope = $1
UNION ALL
SELECT '非 LED' AS x, SUM(light_count - led_count) AS y
FROM env_streetlight_district_score
WHERE city_scope = $1;
```

## 驗收標準

- 可在臺北市與雙北合併視圖間切換。
- 至少臺北市視圖具備可點選或可篩選的路燈 map layer。
- 圖表資料皆來自 PostgreSQL ready table，不直接讀取原始 CSV。
- 坐標輸出為 WGS84/EPSG:4326。
- 新北資料欄位不足時，文件與 UI 皆清楚揭露資料完整率。

## 風險與處理

- 新北資料欄位可能與臺北差異大：先以共同欄位做雙北比較，臺北提供細節 drill-down。
- 維修地址不一定可精準定位：第一版以行政區與月份聚合。
- 高瓦數門檻需可調整：先以資料分布的前 25% 或政策門檻建立預設值，後續再依專家意見校正。
