## 圖表配置

為了正確地呈現圖表，需要將圖表配置填入組件配置中的`chart_config`參數，詳細內容請參閱[這篇先前的文章](/front-end/introduction-to-components#component-configuration)。完整的圖表配置(Object)如下所示。

```json
"chart_config": {
    "color": ["#9c7a3e", …], // Array of Strings; 至少填入一個hex色碼
    "types": ["BarPercentChart", …], // Array of Strings; 填入 1-3 個圖表名稱（英文名）
    "unit": "棟", // String || null; 資料的單位
	"categories": [], // Array of Strings || null; 呼叫 API 時會自動填入
},
```

[`DB` `dashboardmanager.component_charts`](/back-end/components-db)

在資料庫中，圖表配置分開儲存於 `component_charts` table ，並在呼叫 API 時與 `components` table 結合。

## 圖表類型

每個圖表的 Vue 元件位於 `/src/dashboardComponents/components` 資料夾中。對於使用 Apexcharts 呈現的圖表，它們各自的 Vue 元件都包含一個 `chartOptions` 物件，可以填入各種[Apexcharts 參數](https://apexcharts.com/docs/options/annotations/)。有些圖表 Vue 元件還包含清理函式(parsing functions)，用於清理圖表資料。這樣可以增加圖表之間的互通性，使相同的資料集可以呈現多種不同的圖表類型。

以下是所有圖表類型的英文和中文名稱的參照。

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
> 圖表在程式庫中都是使用英文 Pascal Case，而在使用者介面中顯示的圖表名稱則為其中文名。
>
> 英文-中文對照檔案位於 `/src/assets/configs/apexcharts` 資料夾中，名為 `chartTypes.js`。

### 橫向長條圖

橫向長條圖通常用於需要呈現多筆條列資料的情況。

### 長條圖(%)

長條圖(%)用於呈現百分比值，相較於量表圖更為簡潔。

### 縱向長條圖 ***new***

縱向長條圖用於顯示項目列表，最適合呈現12個以下的數據項目。當數據項目超過12個時，圖表會自動提供滾動功能以便查看更多資料，同時上方會出現工具列，使用者可藉此操作項目的縮放。

### 圓餅圖

圓餅圖用於顯示列表項目的百分比值。預設情況下，列表項目按降序排列。如果列表包含超過 6 個項目，其餘項目將被合併為「其他」。

### 量表圖

量表圖以圓形格式呈現百分比值。如果有多個系列(series)，將計算系列之間的平均百分比值並顯示在中央。

### 雷達圖

雷達圖以圓形格式顯示系列內的各值差異。

### 折線圖(比較)

折線圖(比較)用於顯示時間資料。每個系列獨立呈現。

### 折線圖(堆疊)

折線圖(堆疊)用於顯示時間資料。每個系列將被堆疊呈現合計值。

### 矩形圖

矩形圖用於以不同大小的矩形來呈現每個數據點相對於總數的值。

> **t01**
> 本專案僅使用矩形圖來視覺化土地面積資料。

### 捷運行駛圖

捷運行駛圖顯示給定捷運路線捷運車廂的壅擠程度。顏色越深，車廂越擁擠。捷運行駛圖使用 2D 數據呈現，但需要以特殊 key-value 格式，如下所示。

```json
{
  	"data": [
		{
			"data": [
				{
					// {{ ID 遞升 (A) 或遞減 (D) }} + {{車站 ID (同北捷官方)}}
					"x": "AR13",
					// 每個號碼代表一個車廂的擁擠程度 (1-4)
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

### 行政區圖 ***new***

行政區圖用於顯示 key 為雙北各行政區的列表。預設情況下，越大的數值會越不透明。

### 熱力圖

熱力圖用於顯示三維資料，以網格形式呈現，並依據網格值的高低呈現不同顏色。

### 極座標圖

極座標圖用於顯示三維資料，以數個扇形組成。

### 長條折線圖

長條折線圖用來呈現時間資料。第一個系列以長條圖呈現，第二個系列則以折線圖呈現。

### 長條圖(目標)

長條圖(目標)為一般的長條圖增加一個維度，顯示每個類別的目標值。

### 圖示比例圖

圖示比例圖以兩種不同的圖示的陣列呈現百分比資料。

### 指標圖

指標圖用來顯示數值是否在特定範圍內。圖表會根據數值顯示不同的顏色。指標圖使用 3D 資料呈現，但需要特殊格式的 key、子類別和值，如下所示。

```json
{
	// A: 0-10, B: 11-20, C: 21-30
	"categories": ["A", "B", "C"],
	"data": [
		{
			"name": "I", // I 的值是 9 因此屬於 A 類
			// A 類的位置應填入 9
			// 其餘類別位置應填入 0
			"data": [9, 0, 0], 
		},
		{
			"name": "II",
			"data": [0, 15, 0],
		}
	]
}
```

### 文字單位圖 ***new***

文字單位圖用於清晰展示數值及其對應的文字描述與單位。此圖表根據chart_config中設定的三種顏色，依序分別應用於文字描述、數值及單位的顯示。雖然文字單位圖採用3D數據結構，但它特別利用icon欄位來呈現單位符號或其他補充說明，為數據提供更完整的上下文。使用範例如下：

```json
{
    // categories欄位在此圖表類型中不需使用
	"categories": [""],
	"data": [
		{
			"name": "扶養比", // 文字描述部分
			"data": [49], // 數值部分
            "icon": "%" // 單位或補充說明部分
		},
		{
			"name": "老化指數",
			"data": [219],
            "icon": "%"
		}
	]
}
```