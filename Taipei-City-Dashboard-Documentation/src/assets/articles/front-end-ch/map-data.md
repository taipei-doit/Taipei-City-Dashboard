## 支援的資料類型

本專案支援透過本地 `geojson` 或透過圖磚服務 (map tiling server)（如 [Geoserver](https://geoserver.org/)）來渲染地圖。

所有常見的幾何類型均有支援：`Point`（點）、`LineString`（線）、`Polygon`（多邊形）、`MultiPoint`（多點）、`MultiLineString`（多線）、以及 `MultiPolygon`（多多邊形）。建議每個幾何物件中也包含幾個屬性資料(properties)，以便在點擊地圖上的數據點時能顯示額外資訊。

> **i01**
> 我們仍在努力將我們的 Geoserver 設定開源。因此，對於希望貢獻本專案的外部開發者，目前僅支援本地 `geojson` 檔案。
>
> 如果您正在開發自己的專案，歡迎您配置一個動態圖磚服務（如 Geoserver 或 MapBox），並修改 `mapStore` 以從您自己的服務中獲取資料。

> **t01**
> 如果您對 `geojson` 還不熟悉，建議參考 MapBox 提供的 [geojson.io](https://geojson.io/) 平台，以了解其如何被渲染在地圖上。
