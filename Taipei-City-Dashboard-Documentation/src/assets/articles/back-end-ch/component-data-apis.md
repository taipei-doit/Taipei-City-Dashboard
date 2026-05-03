## 機制

為了讓組件檢索儲存在 `dashboard` 資料庫中的資料，`dashboardmanager` 資料庫的 `component` 表中有儲存 SQL 指令。

當使用 API 請求圖表或歷史資料時，後端伺服器會使用儲存在 `component` 表中的 SQL 指令檢索 `dashboard` 資料庫，然後根據 `query_type` 將資料編譯為前端所需的格式。

### SQL 指令格式

任何 `dashboard` 資料庫可以執行的 SQL 指令均可以被使用。此外，SQL 指令還可以透過佔位符（`%s`）挖空，如果在[組件配置](/front-end/introduction-to-components)中有指定組件時間區間，這些占位符將被替換成指定的時間範圍，以檢索特定時間範圍內的資料。占位符的值會由前端自動生成。

圖表資料的 SQL 指令可以有 0 或 2 個占位符。如果 SQL 指令有 2 個占位符，檢索將回傳指定時間範圍的資料。

至於歷史資料，檢索類型 (query_type) 均為 `time`，且 SQL 指令必須有 3 個占位符。第一個占位符是時間單位（例如 `day`，`week`，`month`，根據開始和結束時間自動計算），第二個占位符是開始時間，第三個占位符是結束時間。

## 檢索類型 (Query Type)

> **t01**
> 我們建議您在閱讀此部分之前先熟悉前端文件中的[圖表資料文章](/front-end/chart-data)。

### two_d

**目標檢索結果：**

```go
type TwoDimensionalData struct {
	Xaxis string  `gorm:"column:x_axis" json:"x"`
	Data  float64 `gorm:"column:data"   json:"y"`
}
```

**編譯為：**

```json
[
	{
		"data": [
			{ "x": "", "y": 17 },
			...
		]
	}
]
```

**範例 SQL 指令：**

```sql
-- '臺北市陳情系統 circular'
SELECT case_subtype AS x_axis, SUM(case_count) AS data
FROM app_calcu_weekly_hellotaipei
WHERE create_time BETWEEN '%s' AND '%s'
GROUP BY case_subtype ORDER BY data desc
```

### three_d

**目標檢索結果：**

```go
type ThreeDimensionalData struct {
	Xaxis string `gorm:"column:x_axis"`
	Icon  string `gorm:"column:icon" OPTIONAL`
	Yaxis string `gorm:"column:y_axis"`
	Data  int    `gorm:"column:data"`
}
```

**編譯為：**

```json
{
	"categories": [...],
	"data": [
		{
			"name": "",
			"icon": "",
			"data": [...]
		},
		...
	]
}
```

**範例 SQL 指令：**

```sql
-- '全市屋齡分布 building_age'
SELECT tname AS x_axis, age AS y_axis, COUNT(age) AS data FROM
	(
		SELECT
			tname,
			CASE WHEN age_2021<=5 THEN '<=5年' WHEN age_2021>5 AND age_2021<=20 THEN '5-20年' WHEN age_2021>20 AND age_2021<=40 THEN '20-40年' WHEN age_2021>40 THEN '>40年' ELSE '無' END age
			FROM building_age
	) AS t
WHERE age != '無'
GROUP BY tname, age
ORDER BY
	ARRAY_POSITION(ARRAY['北投區', '士林區', '內湖區', '南港區', '松山區', '信義區', '中山區', '大同區', '中正區', '萬華區', '大安區', '文山區']::varchar[], t.tname),
	ARRAY_POSITION(ARRAY['<=5年', '5-20年', '20-40年', '>40年'], t.age);
```

> **i01** 
> 為確保編譯順暢，`three_d`、`percent`、`time` 檢索類型的 SQL 指令中應對 `x_axis` 和 `y_axis` 進行排序。
>
> 另外也應確保子類別零值狀況有被處理 (子類別的值如果是 0 一定要確保欄位有顯示，不能直接跳過)。建議先建立一個包含所有 xaxis-yaxis 組合之暫存 table ，並使用 left join 與 query 結合。

### percent

`percent` 檢索類型與 `three_d` 檢索類型的格式相同，但對於資料意義有一些額外的限制。更多資訊請參考前端文件中的[圖表資料文章](/front-end/chart-data)。

**範例 SQL 指令：**

```sql
-- 'YouBike使用情況 youbike_availability'
SELECT
	'Youbike在站車輛' AS x_axis,
	unnest(ARRAY['可借車輛', '空位']) AS y_axis,
	unnest(ARRAY[sbi, bemp]) AS data FROM
	(
		SELECT sbi, bemp
		FROM app_calcu_hour_traffic_youbike
		WHERE bike_type = 2
		ORDER BY _ctime desc
		LIMIT 1
	) AS t
```

### time

**目標檢索結果：**

```go
type TimeSeriesData struct {
	Xaxis time.Time `gorm:"column:x_axis"`
	Yaxis string    `gorm:"column:y_axis"`
	Data  float64   `gorm:"column:data"`
}
```

**編譯為：**

```json
[
	{
		"name": "",
		"data": [
			{ "x": "2023-05-25T06:29:00+08:00", "y": 17 },
			...
		]
	},
	...
]
```

**範例 SQL 指令 (圖表資料)：**

```sql
-- '建照使照發照量 building_license'
WITH date_range AS (
  SELECT
    '%s'::timestamp with time zone AS start_time,
    '%s'::timestamp with time zone AS end_time
)
SELECT * FROM (
	SELECT DATE_TRUNC('month', "發照日"::timestamp) AS x_axis, '建照' AS y_axis, COUNT(*) AS data
	FROM building_permit
	WHERE 發照日 BETWEEN (SELECT start_time FROM date_range) AND (SELECT end_time FROM date_range)
	GROUP BY x_axis
	UNION ALL
	SELECT DATE_TRUNC('month', "發照日"::timestamp) AS x_axis, '使照' AS y_axis, COUNT(*) AS data
	FROM building_license
	WHERE 發照日 BETWEEN (SELECT start_time FROM date_range) AND (SELECT end_time FROM date_range)
	GROUP BY x_axis
) AS t
ORDER BY y_axis, x_axis;
```

**範例 SQL 指令 (歷史資料)：**

```sql
-- '捷運人流趨勢 metro_passengers'
SELECT date_trunc('%s', sdatetime) AS x_axis, sum(outcount) AS data
FROM traffic_metro_capacity_realtime_history
WHERE sdatetime BETWEEN '%s' AND '%s'
GROUP BY x_axis
ORDER BY x_axis desc
```

### map_legend

**目標檢索結果：**

```go
type MapLegendData struct {
	Name  string  `gorm:"column:name" json:"name"`
	Type  string  `gorm:"column:type" json:"type"`
	Icon  string  `gorm:"column:icon" json:"icon" OPTIONAL`
	Value float64 `gorm:"column:value" json:"value"`
}
```

**範例 SQL 指令：**

```sql
-- '居職人口推估 fet_work_live'
SELECT
	unnest(ARRAY['居住推估人數', '工作推估人數']) AS name,
	unnest(ARRAY[SUM(CASE pop_live WHEN null THEN 0 ELSE pop_live::NUMERIC END), SUM(CASE pop_work WHEN null THEN 0 ELSE pop_work::NUMERIC END)]) AS value,
	'fill-extrusion' as type
FROM tp_fet_work_live
```

## APIs

`GET` `/component/:id/chart`

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

| 項目     | 描述                                                                               |
| -------- | ---------------------------------------------------------------------------------- |
| 權限     | `Guest`                                                                            |
| 查詢參數 | `timefrom` ---- 查詢的開始時間。可選。<br>`timeto` -------- 查詢的結束時間。可選。 |

**Response:**

```json
{
	"categories": [...], // 如果是 three_d 或 percent 檢索類型
	"data": [...], // 圖表資料,
	"status": "success"
}
```

`GET` `/component/:id/history`

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

| 項目     | 描述                                                                               |
| -------- | ---------------------------------------------------------------------------------- |
| 權限     | `Guest`                                                                            |
| 查詢參數 | `timefrom` ---- 查詢的開始時間。必填。<br>`timeto` -------- 查詢的結束時間。必填。 |

**Response:**

```json
{
	"data": [...], // 歷史資料,
	"status": "success"
}
```
