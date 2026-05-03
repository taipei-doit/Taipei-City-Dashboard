## 底圖

底圖是指地圖頁面首次加載時在畫面中顯示的基本地圖。 底圖是由`mapStore` 的 `initializeMapBox` 函式渲染，該函式會建立一個 Mapbox 地圖物件，並套用一些基本樣式、設定與圖層。

> **w01**
> 如果您對 Mapbox 圖層和渲染資料的方式不熟悉，請務必閱讀他們的[相關文件](https://docs.mapbox.com/mapbox-gl-js/api/map/)或查看他們的[教學系列影片](https://youtube.com/playlist?list=PL86WBCjNmqh5HQInLsyYW7g76_6eKcQLf)。

### 更改底圖樣式

Mapbox 地圖底圖的樣式(configuration object)存於 `/src/assets/configs/mapbox` 資料夾中的 `mapStyle.js` 檔案中。Mapbox 有提供一個有用的線上地圖樣式設計工具[Mapbox Studio](https://studio.mapbox.com/)，在該工具中建立地圖樣式後即可直接輸出樣式設定檔案(`json`)。

要輸出在 Mapbox Studio 中創建的樣式，請在導航列中點擊“share…”，然後滑到彈出視窗的底部，直到找到下載選項。下載 `zip` 資料夾，然後複製其中包含的 `json` 檔案內容。返回 `mapStyle.js`，用複製內容替換原本的設定。重新加載地圖頁面，地圖的底圖樣式即應被替換成新的樣式。

### 更改初始位置

當初始化 Mapbox 地圖物件時，可以指定一些參數，決定地圖的初始位置與顯示方式。這些參數儲存在 `/src/assets/configs/mapbox` 資料夾中的 `mapConfig.js` 檔案中的 `MapObjectConfig` 變量下。完整物件如下：

```js
export const MapObjectConfig = {
	antialias: true, // 抗鋸齒的自定義圖層
	container: "mapboxBox", // 包含地圖的 div 的 id
	center: [121.536609, 25.044808], // 地圖中心坐標
	// 限制地圖範圍
	maxBounds: [
		[121.3870596781498, 24.95733863075891], // 西南方坐標
		[121.6998231749096, 25.21179993640203], // 東北方坐標
	],
	zoom: 12.5, // 初始縮放級別
	// 限制地圖的最小和最大縮放級別
	minZoom: 11,
	maxZoom: 22,
	projection: "globe", // 以3D球體顯示地圖
};
```

### 更改底圖預設添加的圖層

地圖初始化後不久，`mapStore` 的 `initializeBasicLayers` 函式會被呼叫，並在底圖添加了三個預設圖層。其中兩個添加的圖層為臺北市的行政區和里界標籤，並以本地 `geojson` 儲存；而第三個則為臺北市建築物的 3d 模型，以 Mapbox Tiles 形式儲存，此圖層相關設定請參閱[此先前文章](/front-end/project-setup)。這三個圖層的樣式也儲存在 `mapConfig.js` 文件中。

如要進行編輯，只需刪除或替換 `initializeBasicLayers` 方法中指定的圖層即可。

## 編輯或創建地圖類型

只要是 Mapbox 支援的地圖類型和配置，本專案均可以渲染。可以在 Mapbox 的[文件](https://docs.mapbox.com/mapbox-gl-js/style-spec/layers/)中找到所有的選項。

現有的地圖類型及其相應預設變形(preset variation)的設定位於 `mapConfig.js` 檔案中的 `maplayerCommonPaint` 和 `maplayerCommonLayout` 變量下。前者指定 paint 屬性，後者指定 layout 屬性。配置的基本架構如下。

```js
// Paint 屬性
export const maplayerCommonPaint = {
  circle: {
    // circle 地圖類型屬性
  },
  "circle-heatmap": {
    // circle 地圖類型，heatmap（icon）預設變化屬性
  },
  "circle-small": {
    // circle 地圖類型，small（size）預設變化屬性
  },
  ...
};

// Layout 屬性
export const maplayerCommonLayout = {
  // 和 maplayerCommonPaint 類似的邏輯
};
```

當您完成新的地圖類型或預設變化的設定，只需在適用的組件配置中指定它即可使用。
