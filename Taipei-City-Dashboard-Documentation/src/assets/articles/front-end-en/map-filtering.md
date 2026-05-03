## Map Filter Config

Map filtering is a useful feature that allows users to filter out a subset of geographical data attached to a component using charts.

To activate map filtering for a component, the `map_filter` parameter of the component configuration must be filled in. A breakdown of the object that should be passed into `map_filter` is shown below.

```json
"map_filter": {
    "mode": "byParam", // Enum; ["byParam", "byLayer"] More on the two modes below
	"byParam": { // Object || null; Required if mode is "byParam"
		"xParam": "", // String || null; map layer property id to filter by
		"yParam": "" // String || null; map layer property id to filter by
	}
}
```

[`DB` `dashboardmanager.components`](/back-end/components-db)

The `map_filter` object is stored directly in the `components` table.

## Modes

### By Param

The filter by param mode filters each map layer of a component by their respective properties. For this mode to work, the property values in the map layers must match the x-axis and y-axis values displayed on the chart.

### By Layer

The filter by layer mode toggles between the map layers of a component by their respective titles. For this mode to work, the titles in the map layers must match the x-axis values displayed on the chart.

## Mechanism

In charts that support map filtering, a variable called `selectedIndex` is declared to store the currently selected data point (`null` if none is selected). When the user clicks on a data point on the chart, a handler function is invoked that turns on a filter if the data point wasn’t previously selected and turns off the filter if previously selected.

Turning on a filter is achieved by calling the `addByParamFilter` or `addByLayerFilter` method of the `mapStore`. Turning off the filter is achieved by calling the `clearByParamFilter` or `clearByLayerFilter` method of the `mapStore`.

### Charts that Support Map Filtering

Bar Chart, Bar Percent Chart, Column Chart, District Chart, Donut Chart, Guage Chart, Map Legend Chart, Treemap Chart, Heatmap Chart, and Polar Area Chart.
