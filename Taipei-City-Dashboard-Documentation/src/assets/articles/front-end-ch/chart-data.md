## 支援的資料類型

本專案目前支援 5 種圖表資料類型。每種資料類型都有預定的格式並支援一組圖表。如要了解更多有關各圖表類型的資訊，請參考[下一篇文章](/front-end/supported-chart-types)。

[`GET` `/api/v1/component/:id/chart`](/back-end/component-data-apis) [`DB` `dashboardmanager.components`](/back-end/components-db)

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

### 二維資料 (two_d)

二維資料（以下簡稱 2D 資料）是可以使用簡單的 **key-value (x-y)** 編排的資料。

**格式：**

```json
{
	"data": [
		{
			"data": [
				// key (x): String，value (y): Number
				{ "x": "機車竊盜", "y": 17 },
				{ "x": "住宅竊盜", "y": 12 },
				{ "x": "汽車竊盜", "y": 3 },
				{ "x": "搶奪", "y": 0 },
				{ "x": "強盜", "y": 0 }
			]
		}
	]
}
```

**支援的圖表類型：** 圓餅圖(DonutChart)、橫向長條圖(BarChart)、縱向長條圖(ColumnChart)、矩形圖(TreemapChart)、行政區圖(DistrictChart)、捷運行駛圖(MetroChart)、雷達圖(RadarChart)、極座標圖(PolarAreaChart)

> **i01**
> 行政區圖的 key (x) 必須為雙北 41 個行政區的全名（例如：大安區），並遵循以下順序：
>
> ["北投區", "士林區", "內湖區", "南港區", "松山區", "信義區", "中山區", "大同區", "中正區", "萬華區", "大安區", "文山區", "新莊區", "淡水區", "汐止區", "板橋區", "三重區", "樹林區", "土城區", "蘆洲區", "中和區", "永和區", "新店區", "鶯歌區", "三峽區", "瑞芳區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"]

> **i02**
> 有關捷運行駛圖的 key-value 格式，請參[下一篇文章](/front-end/supported-chart-types#metro-chart)。

### 三維資料 (three_d)

三維資料（以下簡稱 3D 資料）是可以以 **key-子類別(subcategory)-value（x-y-z）** 編排的資料。

**格式：**

```json
{
	// keys (x): Array of Strings
	"categories": [
		"士林區",
		"大安區",
		"文山區",
		"松山區",
		"南港區",
		"大同區",
		"中山區",
		"內湖區",
		"北投區",
		"中正區",
		"萬華區",
		"信義區"
	],
	"data": [
		{
			// 子類別 (y): String
			"name": "低收",
			// value (z): Array of Numbers
			// value 的排序應對應到keys (x)的排序
			"data": [
				5330, 1889, 5752, 1702, 2542, 3019, 2441, 3183, 4519, 1773,
				6770, 3065
			]
		},
		{
			"name": "中低收",
			"data": [
				1740, 754, 2204, 561, 1170, 980, 921, 1423, 1508, 518, 2540,
				1215
			]
		},
		{
			"name": "身障補助",
			"data": [696, 252, 688, 186, 425, 343, 351, 565, 635, 234, 751, 442]
		},
		{
			"name": "身障",
			"data": [
				13240, 11383, 12378, 7970, 6084, 6387, 9481, 10683, 11800, 6401,
				11299, 10196
			]
		}
	]
}
```

**支援的圖表類型：** 縱向長條圖(ColumnChart)、長條圖(%)(BarPercentChart)、雷達圖(RadarChart)、行政區圖(DistrictChart)、熱力圖(HeatmapChart)、極座標圖(PolarAreaChart)、指標圖(IndicatorChart)
、文字單位圖(TextUnitChart)
>**i03**
> 有關指標圖的 key-subcategory-value 格式，和文字單位圖的具體應用方式請參[下一篇文章](/front-end/supported-chart-types)。

### 時間序列資料 (time)

時間序列資料（以下簡稱時間資料）是可以以 **key-value (x-y)** 編排的資料，其中 key 是時間戳記。

**格式：**

```json
{
	"data": [
		{
			// 系列(series)名稱：String
			"name": "進站",
			"data": [
				// key (x)：String（時間戳記），value (y)：Number
				{ "x": "2023-05-25T06:29:00+08:00", "y": 19891 },
				{ "x": "2023-05-25T06:59:00+08:00", "y": 42930 },
				{ "x": "2023-05-25T07:29:00+08:00", "y": 83705 },
				{ "x": "2023-05-25T07:59:00+08:00", "y": 121326 },
				{ "x": "2023-05-25T08:29:00+08:00", "y": 128056 }
			]
		},
		// 附加系列（非必填）
		{
			"name": "出站",
			"data": [
				// key (x) 必須與第一個系列相同
				{ "x": "2023-05-25T06:29:00+08:00", "y": 9263 },
				{ "x": "2023-05-25T06:59:00+08:00", "y": 23142 },
				{ "x": "2023-05-25T07:29:00+08:00", "y": 49352 },
				{ "x": "2023-05-25T07:59:00+08:00", "y": 92718 },
				{ "x": "2023-05-25T08:29:00+08:00", "y": 124858 }
			]
		}
	]
}
```

**支援的圖表類型：** 折線圖(比較)(TimelineSeparateChart)、折線圖(堆疊)(TimelineStackedChart)、長條折線圖(ColumnLineChart)

### 百分比資料 (percent)

百分比資料是可以以 **key-value (x-y)** 編排的資料，其中 value 是百分比。如希望顯示百分比資料應提供除數（重點顯示的數據）和餘數（總數減除數），百分比的計算會由圖表 Vue 元件執行。

**格式：**

```json
{
	// key (x)：Array of Strings
	"categories": ["運行中公車", "運行中路線"],
	"data": [
		// 系列 1：除數（重點顯示的數據）
		{
			// 除數的標題
			"name": "營運中",
			// 除數：Array of Numbers
			// value 的位置對應到 keys 的排序 (x)
			"data": [1564, 273],
			"icon": "" // 僅適用於圖示比例圖 (google icons)
		},
		// 系列 2：餘數（總數減除數）
		{
			// 餘數的標題
			"name": "未營運",
			// 餘數：Array of Numbers
			// value 的位置對應到 keys 的排序 (x)
			"data": [164, 109],
			"icon": "" // 僅適用於圖示比例圖 (google icons)
		}
	]
}
// *百分比由圖表自動計算
```

**支援的圖表類型：** 量表圖(GuageChart)、長條圖(%)(BarPercentChart)、長條圖(目標)(BarChartWithGoal)、圖示比例圖(IconPercentChart)

### 圖例資料 (map_legend)

圖例資料是以配置 Object 形式儲存，形式如下。

**格式：**

```json
{
	"data": [
		{
			"name": "居住推估人數", // String; 圖例名稱
			"type": "fill-extrusion", // String; 地圖類型
			"icon": null, // String || null; 僅適用於 symbol 地圖
			"value": 843306 // Optional
		},
		...
	]
}
```

**支援的圖表類型：** 地圖圖例 (MapLegend)
