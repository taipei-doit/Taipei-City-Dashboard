## 地圖篩選配置

地圖篩選功能讓使用者能透過圖表來篩選該組件的地圖圖層。如要在一個組件啟動地圖篩選，必須填寫組件配置的 `map_filter` 參數。下面展示了應該填入 `map_filter` 的詳細內容。

```json
"map_filter": {
    "mode": "byParam", // Enum; ["byParam", "byLayer"] 下方將針對兩個模式進行說明
	"byParam": { // Object || null; 如果篩選模式是 "byParam" 則必填
		"xParam": "", // String || null; 用來篩選的地圖圖層屬性(property) id
		"yParam": "" // String || null; 用來篩選的地圖圖層屬性(property) id
	}
}
```

[`DB` `dashboardmanager.components`](/back-end/components-db)

`map_filter` 物件直接儲存在 `component` table 中。

## 篩選模式

### 依各圖層中屬性 (By Param)

By Param 模式依組件中各圖層中所存的屬性進行篩選。被篩選屬性的各個值需要與圖表 x 軸與 y 軸對應，並完全相同，本模式才能順利運作。

### 依地圖圖層 (By Layer)

By Layer 模式依組件中各圖層的名稱篩選，開關各圖層。各圖層的名稱(title)需要與圖表 x 軸對應，並完全相同，本模式才能順利運作。

## 運作機制

在支援地圖篩選的圖表中，會定義一個名為 `selectedIndex` 的變數來儲存當前選定的資料點（如果沒有選定則為 `null`）。當用戶在圖表上點擊資料點時，會呼叫一個處理函數(handler function)，如果該資料點之前未被選定，則啟用篩選，如果之前已被選定，則關閉篩選。

啟用篩選是透過呼叫 `mapStore` 的 `addByParamFilter` 或 `addByLayerFilter` 函式來達成的。關閉篩選是透過呼叫 `mapStore` 的 `clearByParamFilter` 或 `clearByLayerFilter` 函式來實現的。

## 支援的圖表類型

橫向長條圖(BarChart)、長條圖(%)(BarPercentChart)、縱向長條圖(ColumnChart)、行政區圖(DistrictChart)、圓餅圖(DonutChart)、量表圖(GuageChart)、地圖圖例(MapLegend)、矩形圖(TreemapChart)、熱力圖(HeatmapChart)、極座標圖(PolarAreaChart)。
