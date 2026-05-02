# 噪音陳情案件數：依音源分析

## 目的

本組件用來呈現雙北噪音陳情案件在不同音源類型上的分布與趨勢。資料只使用環境部「噪音陳情案件數（依音源）」，讓使用者比較臺北市、新北市與雙北合併視圖下，噪音陳情主要集中在哪些來源。

本組件不設計地圖圖層，重點放在年度趨勢、音源排名與雙北比較。

## 核心問題

- 臺北市與新北市的噪音陳情主要來自哪些音源？
- 哪些音源類型在雙北合併視圖下案件數最高？
- 各音源類型的年度趨勢是增加、下降，還是維持穩定？
- 臺北市與新北市在同一音源上的案件結構是否不同？

## 使用情境

使用者進入 Sustainable Environment 儀表板後，先切換臺北市或雙北合併視圖，再查看年度噪音陳情總量與音源排名。若「近鄰噪音」或「機動車輛」案件數明顯偏高，使用者可以進一步查看該音源在臺北市與新北市的年度變化。

## 資料來源

| 來源 | URL | 主要欄位 | 用途 |
|------|-----|----------|------|
| 噪音陳情案件數（依音源） | https://data.moenv.gov.tw/dataset/detail/NOS_P_10 | `year`, `county`, 多個音源欄位 | 音源類型與陳情案件 |

## ETL 設計

### 清理規則

- 縣市欄位統一為 `city`，只保留 `臺北市`、`新北市`。
- 噪音陳情資料從 wide format 轉為 long format：`year`、`city`、`noise_source`、`case_count`。
- 音源類型保留原始欄位名稱，另建立 `noise_source_normalized` 供圖表排序與顯示。
- `case_count` 轉為 integer；空值或非數值以 0 或 `NULL` 處理時需保留 `quality_flag`。
- 建立 `city_scope` 查詢邏輯：臺北市視圖只取 `臺北市`，雙北合併視圖取 `臺北市` 與 `新北市` 後聚合。
- 不產生 `wkb_geometry`，本組件不需要地圖圖層。

### 建議資料表

`env_noise_complaints_by_source`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city` | text | 城市 |
| `year` | integer | 年 |
| `noise_source` | text | 音源類型 |
| `noise_source_normalized` | text | 標準化音源類型 |
| `case_count` | integer | 陳情案件數 |
| `quality_flag` | text | 資料品質註記 |
| `data_time` | timestamptz | 資料內容時間 |

## Dashboard 組件設計

### 指標卡

- 年度噪音陳情案件數
- 案件數最高音源
- 案件數成長最快音源
- 臺北市案件數
- 新北市案件數

### 圖表

| 圖表 | query type | chart type | 說明 |
|------|------------|------------|------|
| 陳情音源排名 | `two_d` | `BarChart` | `x=noise_source`, `y=case_count` |
| 城市音源結構比較 | `three_d` | `BarPercentChart` | `x=city`，series 為音源類型 |
| 年度陳情趨勢 | `time` | `TimelineSeparateChart` | 顯示總案件數或指定音源案件數 |
| 音源占比 | `two_d` | `DonutChart` | 顯示選定年度的音源占比 |

### 互動

- 城市範圍切換支援 `臺北市`、`雙北合併`。
- 時間篩選支援年度。
- 點選音源排名時，其他圖表可篩選同一音源或顯示該音源歷年趨勢。
- 不提供 map layer，也不需要 map filter。

## Backend 查詢範例

音源排名：

```sql
SELECT noise_source AS x, SUM(case_count) AS y
FROM env_noise_complaints_by_source
WHERE year = $1
  AND city = ANY($2)
GROUP BY noise_source
ORDER BY y DESC;
```

年度趨勢：

```sql
SELECT make_timestamptz(year, 1, 1, 0, 0, 0) AS x, SUM(case_count) AS y
FROM env_noise_complaints_by_source
WHERE city = ANY($1)
  AND ($2::text IS NULL OR noise_source_normalized = $2)
GROUP BY year
ORDER BY year;
```

## 驗收標準

- 噪音陳情音源資料已轉為 long format，不在前端硬解多欄位。
- 臺北市與雙北合併視圖都能顯示噪音陳情音源排名與年度趨勢。
- 圖表 query 結果符合 Dashboard 支援的 `two_d`、`three_d`、`time` 格式。
- 文件與組件設定都不包含 map layer、map filter 或測站圖層需求。
- 顯示最新資料年度與資料更新時間。

## 風險與處理

- 環境部資料縣市粒度較粗：本組件定位為城市治理壓力比較，不宣稱行政區級精準分析。
- 原始資料為 wide format：ETL 必須轉成 long format，避免前端依賴固定欄位清單。
- 音源分類可能隨年度調整：保留原始音源欄位，並用標準化欄位處理跨年比較。
