# 河川水質風險追蹤

## 目的

本組件用來追蹤雙北河川與測站的水質風險，包含 RPI、溶氧量、生化需氧量、氨氮、懸浮固體與大腸桿菌群等指標。使用者可以比較不同城市、流域、河川與測站，快速找出近期水質異常或長期污染壓力較高的位置。

本組件以環境部資料作為雙北一致基準，臺北市河川水質檢測作為臺北細節補強，避免因地方資料欄位不同而破壞雙北比較。

## 核心問題

- 雙北哪些河川或測站近期水質風險最高？
- 哪些測項最常造成異常？
- 同一測站的水質是否有改善或惡化趨勢？
- 臺北市細部資料能否補足中央資料未提供的測項？

## 使用情境

使用者先查看最新月份高風險測站數，再用河川或流域排名判斷需要關注的水域。選取單一測站後，可以檢視歷史趨勢與異常測項，協助判斷是單次異常、季節波動，還是長期污染問題。

## 資料來源

| 來源 | URL | 主要欄位 | 用途 |
|------|-----|----------|------|
| 環境部河川水質監測資料 | https://data.gov.tw/dataset/6078 | `siteid`, `sitename`, `county`, `township`, `basin`, `river`, `twd97lon`, `twd97lat`, `sampledate`, `itemname`, `itemvalue`, `itemunit` | 雙北一致測站與測項長期資料 |
| 環境部河川水質測點基本資料 | https://data.moenv.gov.tw/dataset/detail/WQX_P_06 | `SiteId`, `SiteName`, `County`, `Township`, `Basin`, `River`, `TWD97Lon`, `TWD97Lat`, `SiteAddress`, `StatusOfUse` | 測站基本資料與座標 |
| 臺北市河川水質檢測 | https://data.taipei/dataset/detail?id=759db528-77b5-4aa3-b6fa-2b857890214e | `河川名稱`, `監測站`, `水溫`, `pH`, `溶氧量`, `生化需氧量`, `氨氮`, `懸浮固體`, `化學需氧量`, `重金屬`, `總磷`, `濁度`, `大腸桿菌群` | 臺北市測站補強與更多測項 |

## ETL 設計

### 清理規則

- 以環境部資料建立主表，篩選 `county` 為 `臺北市`、`新北市`。
- TWD97 座標轉為 WGS84，寫入 `wkb_geometry`。
- 測項資料保留 long format：一列代表一個測站、一個採樣日期、一個測項。
- `itemvalue` 轉為 numeric；非數值、低於偵測極限或含符號的值保留 `raw_item_value`，並建立可比較的 `item_value_numeric`。
- 測項名稱標準化，例如 `溶氧量`、`生化需氧量`、`氨氮`、`懸浮固體`、`大腸桿菌群`。
- 臺北市資料若為 wide format，轉為與環境部一致的 long format，再以來源欄位區分。
- RPI 若來源未直接提供，第一版可用可得測項估算並標記 `rpi_method='estimated'`；若缺少必要測項則不估算。

### 建議資料表

`env_river_water_quality_measurements`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `source_name` | text | 環境部或臺北市 |
| `city` | text | 臺北市或新北市 |
| `district` | text | 行政區 |
| `basin` | text | 流域 |
| `river` | text | 河川 |
| `site_id` | text | 測站 ID |
| `site_name` | text | 測站名稱 |
| `sample_date` | date | 採樣日期 |
| `item_name` | text | 標準化測項 |
| `raw_item_value` | text | 原始值 |
| `item_value_numeric` | numeric | 數值化結果 |
| `item_unit` | text | 單位 |
| `quality_flag` | text | 正常、缺值、非數值、低於偵測極限等 |
| `data_time` | timestamptz | 資料內容時間 |

`env_river_monitoring_sites`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city` | text | 城市 |
| `district` | text | 行政區 |
| `basin` | text | 流域 |
| `river` | text | 河川 |
| `site_id` | text | 測站 ID |
| `site_name` | text | 測站名稱 |
| `site_address` | text | 地址 |
| `status_of_use` | text | 啟用狀態 |
| `data_time` | timestamptz | 資料內容時間 |
| `wkb_geometry` | geometry(Point, 4326) | 測站位置 |

`env_river_site_risk_monthly`

| 欄位 | 型別 | 說明 |
|------|------|------|
| `city` | text | 城市 |
| `district` | text | 行政區 |
| `basin` | text | 流域 |
| `river` | text | 河川 |
| `site_id` | text | 測站 ID |
| `site_name` | text | 測站名稱 |
| `sample_month` | date | 月份 |
| `rpi_value` | numeric | RPI 或估算 RPI |
| `risk_level` | text | `low`, `medium`, `high`, `critical` |
| `abnormal_item_count` | integer | 異常測項數 |
| `main_abnormal_item` | text | 主要異常測項 |
| `data_time` | timestamptz | 資料內容時間 |
| `wkb_geometry` | geometry(Point, 4326) | 測站位置 |

## 風險分級

第一版以規則式風險分級：

- `critical`：RPI 達嚴重污染，或多個關鍵測項同月異常。
- `high`：RPI 達中度污染，或氨氮、生化需氧量、大腸桿菌群任一測項明顯異常。
- `medium`：單一測項偏離建議門檻，或近期出現連續異常。
- `low`：近期測項未見明顯異常。

實際門檻需在 ETL 註解中記錄來源，並可在後續依環境部標準校正。

## Dashboard 組件設計

### 指標卡

- 最新月份高風險測站數
- 最高風險河川
- 異常測項數
- 啟用測站數
- 最新資料月份

### 圖表

| 圖表 | query type | chart type | 說明 |
|------|------------|------------|------|
| 高風險測站排名 | `two_d` | `BarChart` | `x=site_name`, `y=rpi_value` 或風險分數 |
| 河川風險分布 | `three_d` | `BarPercentChart` | `x=river`, series 為風險等級 |
| 測站水質趨勢 | `time` | `TimelineSeparateChart` | 單一測站與測項的歷史變化 |
| 異常測項分布 | `two_d` | `DonutChart` 或 `BarChart` | `x=item_name`, `y=abnormal_count` |

### 地圖

本組件可支援 map layer，但不是四組件中唯一必要地圖。若實作地圖：

- 圖層為河川水質測站 Point。
- 顏色依 `risk_level`，大小依 `abnormal_item_count`。
- popup 顯示測站、河川、最新 RPI、主要異常測項、採樣月份。
- `map_filter` 使用 `byParam`，以 `river` 或 `site_id` 篩選。

## Backend 查詢範例

高風險測站排名：

```sql
SELECT site_name AS x, rpi_value AS y
FROM env_river_site_risk_monthly
WHERE sample_month = (
  SELECT MAX(sample_month)
  FROM env_river_site_risk_monthly
)
  AND city = ANY($1)
ORDER BY rpi_value DESC
LIMIT 10;
```

測站測項趨勢：

```sql
SELECT sample_date AS x, item_value_numeric AS y
FROM env_river_water_quality_measurements
WHERE site_id = $1
  AND item_name = $2
ORDER BY sample_date;
```

## 驗收標準

- 雙北一致資料以環境部資料為基準。
- 測項資料以 long format 儲存，前端查詢時再依圖表需求聚合。
- 臺北市補充資料不得造成雙北比較欄位不一致。
- 測站座標輸出為 WGS84/EPSG:4326。
- 非數值水質資料需保留原始值與 quality flag。

## 風險與處理

- 水質測項單位可能不一致：ETL 需建立單位檢查，不同單位不得直接比較。
- RPI 估算需要完整測項：缺必要測項時不估算，避免製造假精準。
- 測站名稱可能重複：以 `source_name + site_id` 作為主要識別，名稱只作顯示。
