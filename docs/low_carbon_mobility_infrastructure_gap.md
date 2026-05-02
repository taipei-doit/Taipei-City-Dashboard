# 低碳移動基礎建設缺口：充電沙漠與轉型公平

## 目的

本組件用來評估雙北低碳補能基礎設施是否分布均衡，尤其是電動機車與電動汽車充電站在行政區間的服務缺口。它將充電站數、人口或面積標準化後，產生低碳補能缺口分數，協助回答「如果要降低移動污染，哪裡最該先補充電站」。

本組件應定位為 Sustainable Environment 題目中的能源轉型與排放減量支援，不以一般交通便利性作為主軸。

## 核心問題

- 哪些行政區的電動機車或電動汽車充電站密度偏低？
- 臺北市與新北市在低碳補能覆蓋上是否存在落差？
- 若優先補設充電站，哪些行政區的公平性與減碳效益最高？
- 地址型資料尚未地理編碼前，能否先提供可靠的行政區級判斷？

## 使用情境

使用者可切換臺北市或雙北合併視圖，先看每萬人口與每平方公里充電站密度，再查看低碳補能缺口排名。若有座標，地圖呈現充電站點位與行政區缺口熱區；若暫無座標，第一版仍可用行政區聚合圖完成政策判斷。

## 資料來源

| 來源 | URL | 主要欄位 | 用途 |
|------|-----|----------|------|
| 臺北市電動機車充電站 | https://data.taipei/dataset/detail?id=c66e2f53-92f5-4ccd-8aa9-eb71a288e09e | `編號`, `單位`, `縣市`, `行政區`, `行政區域代碼`, `地址`, `備註` | 臺北電動機車充電站 |
| 臺北市營利型電動車充換電站資訊 | https://data.taipei/dataset/detail?id=668313d7-bcfc-4c90-b769-e398b08a1b2d | `序號`, `廠商`, `名稱`, `地址`, `縣市`, `縣市代碼` | 臺北電動汽車與營利型站點 |
| 臺北市電動車充電停車位概況 | https://data.taipei/dataset/detail?id=155db1cd-b75b-4d80-a341-a23e820d5d52 | `統計期`, `車輛種類別`, `總停車位數`, `路外停車位數`, `路邊停車位數` | 充電停車位趨勢 |
| 新北市電動機車充電站 | https://data.ntpc.gov.tw/datasets/e461bc62-34d2-42c5-a871-f2fc2fb88d01 | 依實際下載欄位校正 | 新北電動機車充電站 |
| 新北市電動汽車充電站 | https://data.ntpc.gov.tw/datasets/1bb694e3-17c7-4ef0-ac75-52990c40edcd | 依實際下載欄位校正 | 新北電動汽車充電站 |

可選補強資料：

- 行政區人口數：用於每萬人口充電站密度。
- 行政區面積：用於每平方公里充電站密度。
- 公有停車場、捷運站或商圈資料：用於後續服務範圍分析，不列為第一版必要條件。

## ETL 設計

### 清理規則

- 統一城市欄位為 `city`，行政區欄位為 `district`。
- 站點類型標準化為 `electric_scooter`、`electric_car`、`battery_swap`、`unknown`。
- 營利屬性標準化為 `commercial`、`non_commercial`、`unknown`。
- 地址保留原文並產生 `normalized_address`。
- 無座標資料第一版先以行政區聚合；後續可加入地理編碼流程產生 WGS84 點位。
- 同一地址、同一名稱、同一站點類型的資料需去重，避免多來源重複計算。
- 若站點同時支援充電與換電，保留多值能力或拆成兩筆服務紀錄。

### 建議資料表

`env_ev_charging_stations`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `source_name` | text | 來源資料集 |
| `city` | text | 臺北市或新北市 |
| `district` | text | 行政區 |
| `station_id` | text | 原始或合成站點 ID |
| `station_name` | text | 站點名稱 |
| `station_type` | text | 電動機車、電動汽車、換電等 |
| `operator_name` | text | 單位或廠商 |
| `commercial_type` | text | 營利、非營利或未知 |
| `address` | text | 原始地址 |
| `normalized_address` | text | 標準化地址 |
| `geocoding_status` | text | `not_required`, `pending`, `matched`, `failed` |
| `data_time` | timestamptz | 資料內容時間 |
| `wkb_geometry` | geometry(Point, 4326) | 站點位置，若有 |

`env_ev_charging_district_score`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city_scope` | text | `taipei` 或 `twin_city` |
| `city` | text | 城市 |
| `district` | text | 行政區 |
| `scooter_station_count` | integer | 電動機車充電或換電站數 |
| `car_station_count` | integer | 電動汽車充電站數 |
| `total_station_count` | integer | 站點總數 |
| `commercial_station_ratio` | numeric | 營利站點占比 |
| `stations_per_10k_people` | numeric | 每萬人口站點密度 |
| `stations_per_sq_km` | numeric | 每平方公里站點密度 |
| `infrastructure_gap_score` | numeric | 低碳補能缺口分數 |
| `data_completeness_score` | numeric | 資料完整率 |
| `data_time` | timestamptz | 資料內容時間 |

## 低碳補能缺口分數

第一版採行政區聚合分數：

```text
infrastructure_gap_score =
  0.40 * low_stations_per_10k_people_score +
  0.25 * low_stations_per_sq_km_score +
  0.20 * low_total_station_count_score +
  0.10 * low_non_commercial_access_score +
  0.05 * data_completeness_penalty
```

分數越高代表補能缺口越大。若人口資料尚未接入，先停用每萬人口指標，改用站點數、面積密度與資料完整率，並在 UI 顯示限制。

## Dashboard 組件設計

### 指標卡

- 電動機車充電站數
- 電動汽車充電站數
- 每萬人口站點密度
- 每平方公里站點密度
- 高缺口行政區數

### 圖表

| 圖表 | query type | chart type | 說明 |
|------|------------|------------|------|
| 行政區低碳補能缺口排名 | `two_d` | `BarChart` | `x=district`, `y=infrastructure_gap_score` |
| 站點類型分布 | `two_d` | `DonutChart` | 電動機車、電動汽車、換電等 |
| 城市密度比較 | `three_d` | `ColumnChart` | `x=city`, series 為每萬人口與每平方公里密度 |
| 充電停車位趨勢 | `time` | `TimelineSeparateChart` | 臺北市充電停車位歷年變化 |

### 地圖

- 圖層 1：充電站 Point，屬性包含 `city`、`district`、`station_type`、`commercial_type`。
- 圖層 2：行政區缺口熱區，顏色依 `infrastructure_gap_score`。
- `map_filter` 使用 `byParam`，以 `district` 或 `station_type` 篩選。
- 地址尚未地理編碼時，第一版地圖可只顯示行政區缺口熱區，不顯示精準點位。

## Backend 查詢範例

缺口排名：

```sql
SELECT district AS x, infrastructure_gap_score AS y
FROM env_ev_charging_district_score
WHERE city_scope = $1
ORDER BY infrastructure_gap_score DESC;
```

站點類型分布：

```sql
SELECT station_type AS x, COUNT(*) AS y
FROM env_ev_charging_stations
WHERE city = ANY($1)
GROUP BY station_type
ORDER BY y DESC;
```

## 驗收標準

- 支援臺北市與雙北合併視圖。
- 至少能以行政區聚合呈現低碳補能缺口。
- 若有座標，站點 map layer 使用 WGS84/EPSG:4326。
- 若無座標，UI 需明確標示目前為行政區級估算。
- 站點去重規則需可追溯，避免同一站點重複計算。

## 風險與處理

- 地址型資料無座標：第一版做行政區聚合，後續再補地理編碼。
- 人口或車輛持有數資料未接入：先用面積密度與站點數建立基礎缺口分數。
- 營利與非營利分類不完整：保留 `unknown`，不強行推測。
- 本組件容易被誤解為交通便利性：文案需固定使用「低碳補能」、「能源轉型」、「排放減量支援」等語彙。
