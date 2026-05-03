## Supported Data Types

This project supports rendering maps via local `geojson` or via a map tiling service such as [Geoserver](https://geoserver.org/).

All common geometry types are supported: `Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, and `MultiPolygon`. It is also recommended that additional properties be attached to each geometric object to allow additional information to be displayed when a data point is clicked on the map.

> **i01**
> We are still working on open-sourcing our configuration for Geoserver. As such for external developers who wish to contribute to this project, only local `geojson` files are supported at the moment.
>
> If you are working on your own project, feel free to configure a dynamic map tiling service such as Geoserver or MapBox and modify the `mapStore` to fetch data from your own service.

> **t01**
> Learn more about the `geojson` format and how it’s visualized on a map at [geojson.io](https://geojson.io/) by MapBox. Recommended if you are not familiar with `geojsons`.
