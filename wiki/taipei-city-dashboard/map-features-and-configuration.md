# Map Features and Configuration

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [空間資料樣式](../../raw/空間資料樣式.md); [篩選地圖](../../raw/篩選地圖.md); [客製化地圖](../../raw/客製化地圖.md); [客製化彈跳視窗](../../raw/客製化彈跳視窗.md)

## Overview

Taipei City Dashboard renders spatial data through Mapbox and `mapStore`. Components can provide local GeoJSON or map-tile-backed layers, and chart interactions can filter map layers when `map_filter` is configured. Map customization is concentrated in `/src/assets/configs/mapbox`, while map-related interactions often pair with dialogs controlled by `dialogStore`.

## Spatial Data

The project supports local `geojson` and map tiling services such as Geoserver. Common geometry types are supported: `Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, and `MultiPolygon`. Geometry objects should include useful `properties` so clicking map features can reveal extra information.

The documentation notes that external contributors currently only have local GeoJSON support because the project's Geoserver setup is not yet open sourced. Developers building their own deployment can configure a dynamic tiling service such as Geoserver or Mapbox and adjust `mapStore` accordingly.

## Map Filtering

Map filtering lets a chart filter the map layers attached to the same component. It is enabled by filling the component `map_filter` field.

Two modes are documented:

- `byParam`: filters by properties stored in each layer. The target property values must exactly match the chart x-axis or y-axis values.
- `byLayer`: filters by layer title, turning layers on or off. Layer titles must exactly match chart x-axis values.

Interactive chart components maintain a `selectedIndex`. Clicking a chart point toggles selection. Activating filters calls `mapStore.addByParamFilter` or `mapStore.addByLayerFilter`; clearing filters calls `mapStore.clearByParamFilter` or `mapStore.clearByLayerFilter`.

Supported filter-capable chart types include `BarChart`, `BarPercentChart`, `ColumnChart`, `DistrictChart`, `DonutChart`, `GuageChart`, `MapLegend`, `TreemapChart`, `HeatmapChart`, and `PolarAreaChart`.

## Base Map

The base map is initialized by `mapStore.initializeMapBox`, which creates the Mapbox map object and applies base styles, settings, and layers.

Map style configuration lives in `/src/assets/configs/mapbox/mapStyle.js`. The documentation recommends Mapbox Studio for creating styles and exporting JSON to replace the contents of `mapStyle.js`.

Initial map position and constraints live in `/src/assets/configs/mapbox/mapConfig.js` under `MapObjectConfig`. It defines the container, center coordinates, bounds, zoom range, and projection. The documented defaults center on Taipei, constrain the viewport to Taipei's area, start around zoom 12.5, and use a globe projection.

## Basic Layers and Map Layer Types

After map initialization, `mapStore.initializeBasicLayers` adds three default layers: Taipei district boundaries, village boundary labels, and 3D Taipei building models. District and village layers are local GeoJSON; the building layer uses Mapbox Tiles.

Map layer type presets are kept in `mapConfig.js` under `maplayerCommonPaint` and `maplayerCommonLayout`. New Mapbox-supported layer types or preset variations can be added there, then referenced from component map configuration.

## Dialog Connection

Map interactions can use the same dialog system as the rest of the app. Dialog components live in `/src/components/dialogs`, and `dialogStore` controls render state. The documented public dialog list includes map-relevant dialogs such as `mobileLayers`, `addPin`, `addViewPoint`, and `findClosestPoint`.

## See Also

- [Platform Model](platform-model.md)
- [Data and Visualization Formats](data-and-visualization-formats.md)
- [UI Customization and Dialogs](ui-customization-and-dialogs.md)
