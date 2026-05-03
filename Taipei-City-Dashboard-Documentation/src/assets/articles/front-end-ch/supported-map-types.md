## 地圖配置

為讓每個組件可以包含數個地圖圖層，地圖配置的形式為 Array ，清單的每個項目即為一個圖層的設定。當在地圖頁面展開組件時，所有附屬於該組件的地圖將同時被呼叫並渲染。

以下是完整的地圖配置物件。

```json
"map_config": [
    {
        // String; 必須是唯一的並與地圖資料之檔案名稱相同
        "index": "socl_welfare",
        // Object; 支援所有 Mapbox 的Paint屬性。詳情參見第一個資訊框。
        "paint": {
            "fill-color": [] // 詳見第一個警告框。
        },
        "property": [
            // key: String; 地圖資料中的屬性名稱
            // name: String; 在使用者介面中顯示的名稱
			// mode: "video" || null; 是否嵌入影片或圖片
			{ "key": "vil", "name": "里界" },
			{ "key": "cnt_low_income", "name": "低收入人口數" },
			{ "key": "video_url", "name": "影片連結", "mode": "video"}
        ], // Array of Objects; 在地圖的彈出式視窗中顯示的屬性
        "title": "社福人口", // String; 地圖名稱
        "type": "fill", // String; 輸入 8 種任一種可用的地圖類型
        "size": null, // String || null; 額外預設樣式設定，參見下一節
        "icon": null, // String || null; 額外預設樣式設定，參見下一節
		"source": "raster", // "raster" || "geojson"
        "city": // taipei || metrotaipei; 資料所屬城市
    },
    …
],
```

[`DB` `dashboardmanager.component_maps`](/back-end/components-db)

在資料庫中，圖表配置分開儲存於 `component_maps` table ，並在呼叫 API 時與 `components` table 結合。

> **i01**
> 在 Mapbox 中，每個地圖類型均支援數個 Paint 屬性，用於控制地圖視覺呈現，如顏色、大小、模糊度等。如要微調地圖的預設形式，只需傳遞任何 Mapbox 支援的 Paint 屬性即可。 ([Mapbox 圖層文件](https://docs.mapbox.com/mapbox-gl-js/style-spec/layers/))

> **w01**
> 除了指定擴充地圖類型外，各地圖類型的顏色預設皆為黑色，因此地圖類型的顏色 Paint 屬性(e.g `fill-color`, `circle-color`, etc.)都應該被指定。

## 地圖類型

本專案支援 9 種地圖類型。每個地圖類型都有預設的樣式，相關設定位於 `/src/assets/configs/mapbox` 的 `mapConfig.js` 檔案中。有些地圖亦支援一些預設變形。這可以透過在地圖配置中指定大小(size)或圖示(icon)參數來實現。

### Circle

Circle 地圖類型在地圖上將點(Point)渲染為圓圈。`size`變化包括 `small` 和 `big`。`icon`變化包括 `heatmap`，此效果在地圖拉遠時會將點變模糊，形成類似熱力圖的效果。

### Fill

Fill 地圖類型在地圖上渲染多邊形(Polygon)。沒有預設變化。

### Fill-extrusion

Fill-extrusion 地圖類型從地圖上突出顯示多邊形(Polygon)的 3D 渲染。沒有預設變化。

### Line

Line 地圖類型在地圖上渲染線條(Line)。`size`變化包括 `wide`。`icon`變化包括 `dash`，呈現虛線而不是實線。

### Symbol

Symbol 地圖類型在地圖上將點(Point)渲染為圖示。如使用 symbol 地圖，必須將`icon`參數傳遞給地圖配置。目前可用的圖示包括 `metro`、`metro-density`、`triangle_green`、`triangle_white`、`youbike`、`bus` 和 `cctv`。

### Symbol-3d

Symbol-3d 地圖類型在地圖上將點(Point)渲染為三維模型，現階段僅供三維捷運動態地圖使用。技術核心為透過 mapbox 結合 three.js ，依 geoserver 所發布之即時位置進行動態渲染。Symbol-3d 地圖並不是 Mapbox 的內建地圖類型，故無法以 paint 屬性變換 3D 模型造型，但仍可以 icon 設定不同 3D 模型，或以 size 改變整體 3D 模型大小。

<!-- > **i01** 【 補充說明 - 三維捷運動態地圖 】為擁擠度組件之附屬地圖。地圖資料來源為 Geoserver 提供之即時列車資料，主要資料項目包含列車編號、行駛方向、起站(目前車輛已抵達站點)、迄站及車廂擁擠度資訊。 Geoserver 每1分鐘更新一次列車行駛資料，捷運列車之動態渲染為每1分半更新一次畫面，當畫面更新時會同時參考 Geoserver 最新的列車行駛資料，決定畫面更新時各捷運列車該運行到哪個站點。 -->

### Arc

Arc 地圖類型在地圖上將線條(Line)渲染成立體曲線，Arc 地圖圖資的單一線條都只能包含兩個點，多餘點位均不會被渲染。Arc 地圖並不是 Mapbox 的內建地圖類型，因此只支援四個屬性，規格如下：

```json
"paint": {
	"arc-color": ["#ffffff", "#f34523"], // Array of Strings;
	// 單色曲線僅需提供一個色碼; 雙色漸層請提供兩個色碼
	"arc-width": 4, // Number
	"arc-opacity": 0.5, // Number; 0-1
	"arc-animate": true, // Boolean; 預設為 false
}
```

### Voronoi

Voronoi 地圖類型將點(Point)渲染為沃羅諾邊界。本地圖種類的 paint 屬性、預設的樣式等與 line 地圖類型完全相同。

### Isoline

Isoline 地圖類型將點(Point)渲染為等高線。每個點都必須對應到一個值(存於地圖屬性 properties)，地圖屬性的 key 預設為 `value` ，但可以藉由 `isoline-key` paint 屬性更改 (見下)。本地圖種類的 paint 屬性、預設的樣式等與 line 地圖類型完全相同。

```json
"paint": {
	"isoline-key": "value", // String; 預設為 "value"
	"isoline-step": 2, // Number; 等高線間隔。預設為 2
	"isoline-min": 0, // Number; 最小值。預設為 0
	"isoline-max": 100 // Number; 最大值。預設為 100
	// ...其他 line paint 屬性
}
```
