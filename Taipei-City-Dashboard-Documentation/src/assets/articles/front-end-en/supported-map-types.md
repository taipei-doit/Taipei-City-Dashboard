## Map Config

This project supports more than one map for each component. As such, the `map_config` parameter in the component configuration takes an array of map config objects, with each map config representing one map. When a component is expanded in the map view, all maps attached to that component will be rendered simultaneously.

The complete map config object can be found below.

```json
"map_config": [
    {
        // String; must be unique and the same as the map data file name
        "index": "socl_welfare",
        // Object; supports all Mapbox paint properties. See 1st info box below for details.
        "paint": {
            "fill-color": [] // See 1st warning box for details.
        },
        "property": [
	        // key: String; a property name in the map data
	        // name: String; Display name in the user interface
			// mode: "video" || null; whether to embed a video or image
            { "key": "vil", "name": "里界" },
            { "key": "cnt_low_income", "name": "低收入人口數" },
			{ "key": "video_url", "name": "影片連結", "mode": "video"}
        ], // Array of Objects; properties to show in map popup
        "title": "社福人口", // String; map name
        "type": "fill", // String; pass in 1 of the 8 available map types
        "size": null, // String || null; additional preset style setting. See next section.
        "icon": null, // String || null; additional preset style setting. See next section
		"source": "raster", // "raster" || "geojson"
        "city": // taipei || metrotaipei; Source city of the data
    },
    …
],
```

[`DB` `dashboardmanager.component_maps`](/back-end/components-db)

In the database, map configs are stored separately in the `component_maps` table and joined with the `components` table during API calls.

> **i01**
> In Mapbox, each map type supports numerous paint properties that control visual details such as color, size, blur, etc. To customize a map beyond its default form, simply pass in any paint property supported by Mapbox. ([Mapbox layers docs](https://docs.mapbox.com/mapbox-gl-js/style-spec/layers/))

> **w01**
> As the default color for all map types is black, the color paint property (e.g `fill-color`, `circle-color`, etc.) for all map types should ALWAYS be specified.

## Map Types

9 map types are supported in this project. Each map type has preset default styling applied which is listed in the file `mapConfig.js` located at `/src/assets/configs/mapbox`. Several maps also support preset variations to the default styling. This is achieved by specifying the size or icon parameters in the map config.

### Circle

The circle map type renders points as circles on the map. `Size` variations include `small` and `big`. `Icon` variations include `heatmap` which blurs the dots to create a heatmap-like effect when zoomed out.

### Fill

The fill map type renders polygons onto the map. There are no preset variations.

### Fill-extrusion

The fill-extrusion map type protrudes a 3D rendering of polygons from the map. There are no preset variations.

### Line

The line map type renders lines onto the map. `Size` variations include `wide`. `Icon` variations include `dash` which renders dashed lines instead of solid ones.

### Symbol

The symbol map type renders points as icons. For symbol maps, the `icon` parameter must be passed into the map config. Available icons include `metro`, `metro-density`, `triangle_green`, `triangle_white`, `youbike`, `bus`, and `cctv`.

### Symbol-3d

The Symbol-3D map type renders point features as 3D models on the map and is currently intended solely for use in the 3D metro dynamic map.

Its core implementation integrates Mapbox with Three.js to dynamically render models based on real-time location data published by GeoServer.

As Symbol-3D is not a native Mapbox layer type, paint properties cannot be used to alter the appearance of 3D models. Nevertheless, different 3D models may be specified via the `icon` property, and the overall model scale can be adjusted using the `size` property.

### Arc

The arc map type renders lines as 3D arcs. Each line should only contain 2 points as any additional points wouldn't be rendered. The arc map type was custom built and as such only supports the following four paint properties:

```json
"paint": {
	"arc-color": ["#ffffff", "#f34523"], // Array of Strings;
	// Fill in 1 color code for single color arcs; 2 colors for a gradient arc
	"arc-width": 4, // Number
	"arc-opacity": 0.5, // Number; 0-1
	"arc-animate": true, // Boolean; Default is false
}
```

### Voronoi

The voronoi map type generates voronoi boundaries from points. The resulting map layer can be styled the same way as line maps (see above).

### Isoline

The isoline map type generates contour lines from points and their respective values. Each point must contain a property that is a number. The key of the property defaults to `value` but can be modified by passing in the `isoline-key` parameter (see below). The resulting map layer can be styled the same way as line maps (see above).

```json
"paint": {
	"isoline-key": "value", // null || String; Defaults to "value"
	"isoline-step": 2, // Number; The interval between lines. Default is 2
	"isoline-min": 0, // Number; Min value. Default is 0
	"isoline-max": 100, // Number; Max value. Default is 100
	// ...other line paint properties
}
```
