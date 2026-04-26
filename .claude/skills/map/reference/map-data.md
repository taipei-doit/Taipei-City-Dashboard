## 支援的資料類型

本專案支援透過本地 geojson 或透過圖磚服務 (map tiling server)（如 Geoserver）來渲染地圖。

所有常見的幾何類型均有支援：Point（點）、LineString（線）、Polygon（多邊形）、MultiPoint（多點）、MultiLineString（多線）、以及 MultiPolygon（多多邊形）。建議每個幾何物件中也包含幾個屬性資料(properties)，以便在點擊地圖上的數據點時能顯示額外資訊。

如果您對 geojson 還不熟悉，建議參考 MapBox 提供的 geojson.io 平台，以了解其如何被渲染在地圖上。
