## Chart Config

To correctly render chart data, several parameters need to be set and passed into the component configuration as mentioned in [this previous article](/front-end/introduction-to-components#component-configuration). The complete chart config object can be found below.

```json
"chart_config": {
    "color": ["#9c7a3e", …], // Array of Strings; Pass in at least one hex color code
    "types": ["BarPercentChart", …], // Array of Strings; Pass in 1-3 chart names
    "unit": "棟", // String || null; Unit of the data points
    "categories": [], // Array of Strings || null; Automatically appended during API call
},
```

[`DB` `dashboardmanager.component_charts`](/back-end/components-db)

In the database, chart configs are stored separately in the `component_charts` table and joined with the `components` table during API calls.

## Chart Types

The Vue components for each chart could be found in the folder `/src/dashboardComponents/components`. For Apexcharts-based charts, their respective Vue components all contain a `chartOptions` object where various [Apexcharts parameters](https://apexcharts.com/docs/options/annotations/) could be passed in. Some chart Vue components also include parsing functions to clean chart data. This is to increase the interoperability between charts, allowing the same dataset to render multiple different chart types.

Below is a reference of English and Mandarin names for all chart types.

```js
{
    BarChart: "橫向長條圖",
    BarPercentChart: "長條圖(%)",
    ColumnChart: "縱向長條圖",
    DonutChart: "圓餅圖",
    GuageChart: "量表圖",
    RadarChart: "雷達圖",
    TimelineSeparateChart: "折線圖(比較)",
    TimelineStackedChart: "折線圖(堆疊)",
    TreemapChart: "矩形圖",
    DistrictChart: "行政區圖",
    MetroChart: "捷運行駛圖",
	HeatmapChart: "熱力圖",
	PolarAreaChart: "極座標圖",
	ColumnLineChart: "長條折線圖",
	BarChartWithGoal: "長條圖(目標)",
	IconPercentChart: "圖示比例圖",
	IndicatorChart: "指標圖",
     TextUnitChart: "文字單位圖"
};
```

> **i01**
> Charts are always referenced in English Pascal Case in the codebase, while all chart names displayed in the user interface are in Mandarin.
>
> The English-Mandarin reference file is located in `/src/assets/configs/apexcharts` as `chartTypes.js`.

### Bar Chart

Bar charts are usually utilized when there is a long list of data that needs to be displayed.

### Bar Percent Chart

Bar percent charts are used to visualize percentage values in a more concise and tight format compared to gauge charts.

### Column Chart ***new***

Column charts are used to display item lists and are best suited for presenting fewer than 12 data items. When the number of data items exceeds 12, the chart automatically provides a scrolling function to view more data, and a toolbar appears at the top, allowing users to zoom in and out of items.

### Donut Chart

Donut charts are used to display the percentage values of each list item. By default, the list items are sorted in descending order. If the list contains more than 6 items, the rest is summed and categorized as “other”.

### Guage Chart

Guage charts are used to visualize percentage values in a circular format. If there is more than one series, the average percentage value between series is calculated and displayed in the center.

### Radar Chart

Radar charts visualize the value differences within a series in a circular format.

### Timeline Separated Chart

Timeline separated charts are used to display time data. Each series is rendered separately in its own timeline.

### Timeline Stacked Chart

Timeline separated charts are used to display time data. Each series is stacked and summed to visualize aggregate values.

### Treemap Chart

Treemap charts visualize the value of each data point relative to the total by rendering different size rectangles.

> **t01**
> This project only uses treemap charts to visualize area data.

### Metro Chart

Metro charts display the density of metro train carriages on a given metro line. The darker the color, the denser the train carriage is. Metro charts are rendered 2D data but require the keys and values to be in a special format as displayed below.

```json
{
  	"data": [
		{
			"data": [
				{
					// {{ ID Ascending (A) or Descending (D) }} + {{Station ID (Taipei Metro)}}
					"x": "AR13",
					// Each number represents a train carriage
					// Least to most crowded: 1-4
					"y": 222222
				},
				{
					"x": "DR11",
					"y": 111122
				},
				{
					"x": "AR15",
					"y": 111122
				},
				{
					"x": "AR10",
					"y": 121121
				},
				...
			]
		}
  	]
}
```

### District Chart ***new***

District charts are used to display lists where the keys are Taipei and New Taipei City districts. By default, larger values are rendered with higher opacity.

### Heatmap Chart

Heatmap charts are used to display three-dimensional data in a grid form. Each grid cell is asigned a different color based on its value.

### Polar Area Chart

Polar Area Charts are used to display three-dimensional data in circular pie slices.

### Column Line Chart

Column line charts are used to display time series data where the first serie is displayed as columns and the second serie is displayed as a line.

### Bar Chart With Goal

Bar chart with goal adds an additional dimension to ordinary bar charts, showing the target value of each category.

### Icon Percent Chart 

Icon percent charts displays percentage data via a grid of two separate icons.

### Indicator Chart

Indicator charts are used to display whether a value is within a certain range. The chart displays a colored indicator based on the value. Indicator charts are rendered via 3D data but require the keys, subcategories, and values to be in a special format as displayed below.

```json
{
	// Assuming A: 0-10, B: 11-20, C: 21-30
	"categories": ["A", "B", "C"],
	"data": [
		{
			"name": "I", // The value for I is 9 which falls under A
			// The position of A should be filled with 9
			// The positions of B and C should be filled with 0
			"data": [9, 0, 0], 
		},
		{
			"name": "II",
			"data": [0, 15, 0],
		}
	]
}
```

### Text Unit Chart ***new***

The text unit chart is used to clearly display values and their corresponding text descriptions and units. This chart applies three colors set in chart_config sequentially to the display of text descriptions, values, and units. Although the text unit chart uses a 3D data structure, it specifically utilizes the icon field to present unit symbols or other supplementary information, providing more complete context for the data. Usage example as follows:

```json
{
    // categories field is not needed in this chart type
	"categories": [""],
	"data": [
		{
			"name": "Dependency Ratio", // Text description part
			"data": [49], // Value part
            "icon": "%" // Unit or supplementary information part
		},
		{
			"name": "Aging Index",
			"data": [219],
            "icon": "%"
		}
	]
}
```