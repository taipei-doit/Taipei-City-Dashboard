## 概觀

下圖呈現渲染此專案的儀表板與地圖使用者界面所需的步驟。

![應用程式呈現流程圖](/images/front-end/rendering-overview-ch.png)

初始化 Mapbox 地圖是在 `mapStore` 中執行，而其他所有步驟則均由 `contentStore` 執行。

## 地圖圖層

下圖呈現渲染組件空間資料到地圖所需的步驟。

![地圖呈現流程圖](/images/front-end/rendering-map-ch.png)

所有步驟均由 `mapStore` 執行。
