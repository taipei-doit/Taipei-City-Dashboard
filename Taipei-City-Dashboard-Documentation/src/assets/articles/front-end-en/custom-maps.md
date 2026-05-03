## Base Map
The base map is the bare map seen when the map view is first loaded. The method `initializeMapBox` of the `mapStore` creates the mapbox map instance and applies styles and configs to the map.

>**w01**
>If you are unfamiliar with how Mapbox handles data sources and layers, please be sure to read through their [documentation](https://docs.mapbox.com/mapbox-gl-js/api/map/) or check out their [tutorial series](https://youtube.com/playlist?list=PL86WBCjNmqh5HQInLsyYW7g76_6eKcQLf) before continuing.

### Change Base Map Style
The styling for Mapbox maps is specified in a configuration object. The base map style configuration for this project is located in the file `mapStyle.js` in the folder `/src/assets/configs/mapbox`. Mapbox has a helpful online tool, [Mapbox Studio](https://studio.mapbox.com/) that allows users to create map styles via a user interface and then auto-generate a configuration object.

To export the style you created in Mapbox Studio, click on “share…” in the navbar and scroll to the bottom of the dialog until you find the download option. Download the `zip` file then copy the contents of the `json` file contained within. Navigate back to `mapStyle.js` and replace the object inside with the copied contents. Reload the project and your map styles should be applied.

### Change Initial Location
When the mapbox map instance is initialized, it takes in some default parameters that specify the initial location details of the map. The default location parameters for this project are stored in the file `mapConfig.js` in the folder `/src/assets/configs/mapbox` under the variable `MapObjectConfig`. The complete object can be found below.

```js
export const MapObjectConfig = {
  antialias: true, // antialiasing custom layers
  container: "mapboxBox", // id of the div containing the map
  center: [121.536609, 25.044808], // Center of map coordinates
  // restrict the map to an area
  maxBounds: [
    [121.3870596781498, 24.95733863075891], // Southwest coordinates
    [121.6998231749096, 25.21179993640203], // Northeast coordinates
  ],
  zoom: 12.5, // initial zoom
  // restrict the min and max zooms of the map
  minZoom: 11,
  maxZoom: 22,
  projection: "globe", // display the map as a 3D globe
};
```

### Change Default Added Layers
Shortly after the map is initialized, the `initializeBasicLayers` method of the `mapStore` is invoked and three default layers are added to the map. The first two layers added provide labels for Taipei’s districts and villages. Those layers are stored as local `geojsons`. The third layer is a 3d model of buildings in Taipei. This layer is stored in Mapbox Tileset and more information could be found in [this previous article](/front-end/project-setup). The styles for these three layers are also stored in the file `mapConfig.js`.

To edit, simply remove or replace the layers specified in the `initializeBasicLayers` method.

## Edit or Create Map Types
This project can display any map type and configuration as long as it is supported by Mapbox. All of the options available could be found in Mapbox’s [documentation](https://docs.mapbox.com/mapbox-gl-js/style-spec/layers/).

Configuration objects for existing map types and their respective preset variations are located in `mapConfig.js` under the variables `maplayerCommonPaint` and `maplayerCommonLayout`. The former specifies paint properties while the latter specifies layout properties. The basic layout of the config objects can be found below.

```js
// Paint Properties
export const maplayerCommonPaint = {
  circle: {
    // circle map type properties
  },
  "circle-heatmap": {
    // circle map type, heatmap (icon) preset variation properties
  },
  "circle-small": {
    // circle map type, small (size) preset variation properties
  },
  ...
};

// Layout Properties
export const maplayerCommonLayout = {
  // Same logic as maplayerCommonPaint
};
```

When you finish configuring a new map type or variation, simply specify it in an applicable component configurations to apply it.