// Initial Position and Settings
export const MapObjectConfig = {
	antialias: true,
	container: "mapboxBox",
	center: [121.536609, 25.044808],
	maxBounds: [
		[121.3870596781498, 24.95733863075891], // Southwest coordinates
		[121.6998231749096, 25.21179993640203], // Northeast coordinates
	],
	zoom: 12.5,
	minZoom: 11,
	maxZoom: 22,
	projection: "globe", // display the map as a 3D globe
};

// Styles for base layer "Taipei Town"
export const TaipeiTown = {
	id: "taipei_town",
	source: "taipei_town",
	type: "symbol",
	layout: {
		"text-field": ["to-string", ["get", "TNAME"]],
		"text-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11,
			10,
			13,
			12,
			15.5,
			14,
		],
		"text-allow-overlap": true,
	},
	paint: {
		"text-color": [
			"interpolate",
			["linear"],
			["zoom"],
			15,
			"#aaa",
			16,
			"#fff",
		],
		"text-halo-color": "#888",
		"text-halo-width": ["interpolate", ["linear"], ["zoom"], 15, 0, 16, 1],
		"text-opacity": ["interpolate", ["linear"], ["zoom"], 15.99, 1, 16, 0],
	},
};

// Styles for Base Layer "Taipei Village"
export const TaipeiVillage = {
	id: "taipei_village",
	source: "taipei_village",
	type: "symbol",
	layout: {
		"text-field": ["to-string", ["get", "VNAME"]],
		"text-size": 14,
	},
	paint: {
		"text-color": "#85bdbd",
		"text-opacity": [
			"interpolate",
			["linear"],
			["zoom"],
			15.49,
			0,
			15.5,
			1,
		],
	},
};

export const TaipeiBuilding = {
	id: "taipei_building_3d",
	source: "taipei_building_3d_source",
	"source-layer": "tp_building_height84-18p8j0",
	type: "fill-extrusion",
	minzoom: 14,
	paint: {
		"fill-extrusion-height": [
			"interpolate",
			["linear"],
			["get", "1_top_high"],
			0,
			0,
			1044.14,
			1044.14,
		],
		"fill-extrusion-opacity": 0.8,
		"fill-extrusion-color": [
			"interpolate",
			["linear"],
			["zoom"],
			14.4,
			"#121212",
			14.5,
			"#272727",
		],
	},
};

// Map base styles and preset variations

// Paint Properties
export const maplayerCommonPaint = {
	circle: {
		"circle-radius": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			2,
			12,
			2,
			13.5,
			2.5,
			15,
			3,
			22,
			5,
		],
	},
	"circle-heatmap": {
		"circle-radius": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			5,
			12,
			5,
			13.5,
			2.5,
			15,
			3,
			22,
			5,
		],
		"circle-blur": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			1,
			12,
			1,
			13.5,
			0.5,
			15,
			0,
		],
		"circle-opacity": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.2,
			12,
			0.2,
			13.5,
			0.5,
			15,
			1,
		],
	},
	"circle-small": {
		"circle-opacity": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.4,
			13,
			0.5,
			17,
			1,
		],
	},
	"circle-big": {
		"circle-radius": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			3.5,
			12,
			3.5,
			13.5,
			4,
			15,
			5,
			22,
			7,
		],
	},
	"fill-extrusion": {
		"fill-extrusion-opacity": 0.5,
	},
	fill: {
		"fill-opacity": [
			"interpolate",
			["linear"],
			["zoom"],
			10,
			0.3,
			22,
			0.15,
		],
	},
	line: {
		"line-width": [
			"interpolate",
			["linear"],
			["zoom"],
			10.99,
			1,
			12,
			1,
			18,
			3,
		],
	},
	"line-wide": {
		"line-width": [
			"interpolate",
			["linear"],
			["zoom"],
			10.99,
			0,
			12,
			1.5,
			18,
			4,
		],
	},
	"line-dash": {
		"line-dasharray": [2, 4],
	},
	symbol: {},
};

// Layout Properties
export const maplayerCommonLayout = {
	line: {
		"line-join": "round",
		"line-cap": "round",
	},
	fill: {},
	"fill-extrusion": {},
	circle: {},
	symbol: {
		"icon-allow-overlap": true,
		"icon-ignore-placement": true,
		"icon-padding": 0,
		"icon-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.15,
			14,
			0.4,
			22,
			0.5,
		],
	},
	"symbol-metro": {
		"icon-image": "metro",
		"icon-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.3,
			14,
			0.4,
			22,
			0.9,
		],
	},
	"symbol-triangle_green": {
		"icon-image": "triangle_green",
	},
	"symbol-triangle_white": {
		"icon-image": "triangle_white",
	},
	"symbol-youbike": {
		"icon-image": [
			"case",
			["==", ["get", "left_bikes"], ["get", "total_bikes"]],
			"bike_red",
			["==", ["get", "left_bikes"], 0],
			"bike_orange",
			"bike_green",
		],
		"icon-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			1,
			14,
			1.5,
			22,
			2,
		],
	},
	"symbol-bus": {
		"icon-image": "bus",
		"icon-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.7,
			14,
			1.1,
			22,
			1.4,
		],
	},
	"symbol-metro-density": {
		"icon-image": "metro",
		"icon-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			0.3,
			14,
			0.4,
			22,
			0.9,
		],
		"text-field": "•",
		"text-offset": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			["literal", [0.3, -0.3]],
			14,
			["literal", [0.4, -0.4]],
			22,
			["literal", [0.8, -0.8]],
		],
		"text-size": [
			"interpolate",
			["linear"],
			["zoom"],
			11.99,
			32,
			14,
			40,
			22,
			60,
		],
	},
};
