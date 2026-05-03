## Supported Data Types

This project currently supports 5 main chart data types. Each data type has a predefined format and set of supported charts that could be utilized for visualization. To learn more about the supported chart types, refer to [this later article](/front-end/supported-chart-types).

[`GET` `/api/v1/component/:id/chart`](/back-end/component-data-apis) [`DB` `dashboardmanager.components`](/back-end/components-db)

<!-- _[Try out the API in our API Tester](/api)_ -->

### Two-Dimensional Data (two_d)

Two-Dimensional Data (henceforth referred to as 2D data) is data that could be formatted in simple **key-value (x-y)** pairs.

**Format:**

```json
{
	"data": [
		{
			"data": [
				// key (x): String, value (y): Number
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

**Supported Chart Types:** Donut Chart, Bar Chart, Column Chart, Treemap Chart, District Chart, Metro Chart, Radar Chart, Polar Area Chart

> **i01**
> If using District Charts, the keys (x) must be the full Mandarin name (e.g. 大安區) of all forty-one districts in Taipei City and New Taipei City in the following order:
>
> `[ "北投區", "士林區", "內湖區", "南港區", "松山區", "信義區", "中山區", "大同區", "中正區", "萬華區", "大安區", "文山區", "新莊區", "淡水區", "汐止區", "板橋區", "三重區", "樹林區", "土城區", "蘆洲區", "中和區", "永和區", "新店區", "鶯歌區", "三峽區", "瑞芳區", "五股區", "泰山區", "林口區", "深坑區", "石碇區", "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區", "金山區", "萬里區", "烏來區"]`

> **i02**
> More details regarding the key-value pairs for Metro Charts are explained in [this later article](/front-end/supported-chart-types#metro-chart).

### Three-Dimensional Data (three_d)

Three-Dimensional Data (henceforth referred to as 3D data) is data that could be categorized into a **key-subcategory-value (x-y-z)** format.

**Format:**

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
			// subcategory (y): String
			"name": "低收",
			// values (z): Array of Numbers
			// value placement corresponds to keys (x)
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

**Supported Chart Types:** Column Chart, Bar Percent Chart, Radar Chart, District Chart, Heatmap Chart, Polar Area Chart, Indicator Chart

> **i03**
> More details regarding the key-subcategory-value pairs for Indicator Charts are explained in [this later article](/front-end/supported-chart-types#indicator-chart).

### Time Series Data (time)

Time Series Data (henceforth referred to as time data) is data that could be formatted in simple **key-value (x-y)** pairs where the keys are timestamps.

**Format:**

```json
{
	"data": [
		{
			// Series Name: String
			"name": "進站",
			"data": [
				// key (x): String (Time Stamp), value (y): Number
				{ "x": "2023-05-25T06:29:00+08:00", "y": 19891 },
				{ "x": "2023-05-25T06:59:00+08:00", "y": 42930 },
				{ "x": "2023-05-25T07:29:00+08:00", "y": 83705 },
				{ "x": "2023-05-25T07:59:00+08:00", "y": 121326 },
				{ "x": "2023-05-25T08:29:00+08:00", "y": 128056 }
			]
		},
		// Additional Series (Optional)
		{
			"name": "出站",
			"data": [
				// keys (x) must be the same as first serie
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

**Supported Chart Types:** Timeline Separate Chart, Timeline Stacked Chart, Column Line Chart

### Percentage Data (percent)

Percentage Data is data that could be formatted in simple **key-value (x-y)** pairs where the values are percentages. To provide more context behind percentage values, the divisor and the remainder (subtracting the divisor from the total) should also be provided.

**Format:**

```json
{
	// keys (x): Array of Strings
	"categories": ["運行中公車", "運行中路線"],
	"data": [
		// Serie 1: Divisor
		{
			// Title for Divisors
			"name": "營運中",
			// Divisor: Array of Numbers
			// value placement corresponds to keys (x)
			"data": [1564, 273],
			"icon": "" // Only for IconPercentCharts (google icons)
		},
		// Serie 2: Remainder
		{
			// Title for Remainders
			"name": "未營運",
			// Remainder: Array of Numbers
			// value placement corresponds to keys (x)
			"data": [164, 109],
			"icon": "" // Only for IconPercentCharts (google icons)
		}
	]
}
// *Percentages are calculated by the charts
```

**Supported Chart Types:** Guage Chart, Bar Percent Chart, Bar Chart With Goal, Icon Percent Chart

### Map Legend Data (map_legend)

Map Legend Data is stored in configuration objects that are used to render map legends. The format is as follows:

**Format:**

```json
{
	"data": [
		{
			"name": "居住推估人數", // String; Legend title
			"type": "fill-extrusion", // String; Map type
			"icon": null, // String || null; Only for symbol maps
			"value": 843306 // Optional
		},
		...
	]
}
```

**Supported Chart Types:** Map Legend
