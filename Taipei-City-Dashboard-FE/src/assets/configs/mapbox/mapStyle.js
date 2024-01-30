export default {
	"version": 8,
	"name": "Basemap-black_NEW",
	"metadata": {
		"mapbox:type": "default",
		"mapbox:origin": "monochrome-dark-v1",
		"mapbox:sdk-support": {
			"android": "9.3.0",
			"ios": "5.10.0",
			"js": "1.10.0"
		},
		"mapbox:autocomposite": true,
		"mapbox:groups": {
			"Road network, traffic-and-closures": {
				"name": "Road network, traffic-and-closures",
				"collapsed": false
			},
			"Transit, transit-labels": {
				"name": "Transit, transit-labels",
				"collapsed": true
			},
			"Administrative boundaries, admin": {
				"name": "Administrative boundaries, admin",
				"collapsed": true
			},
			"Land & water, built": {
				"name": "Land & water, built",
				"collapsed": true
			},
			"Transit, bridges": {"name": "Transit, bridges", "collapsed": true},
			"Transit, surface": {"name": "Transit, surface", "collapsed": true},
			"Land & water, land": {
				"name": "Land & water, land",
				"collapsed": false
			},
			"Road network, bridges": {
				"name": "Road network, bridges",
				"collapsed": true
			},
			"Road network, tunnels": {
				"name": "Road network, tunnels",
				"collapsed": true
			},
			"Road network, road-labels": {
				"name": "Road network, road-labels",
				"collapsed": false
			},
			"Buildings, built": {"name": "Buildings, built", "collapsed": true},
			"Natural features, natural-labels": {
				"name": "Natural features, natural-labels",
				"collapsed": true
			},
			"Road network, surface": {
				"name": "Road network, surface",
				"collapsed": true
			},
			"Place labels, place-labels": {
				"name": "Place labels, place-labels",
				"collapsed": true
			},
			"Point of interest labels, poi-labels": {
				"name": "Point of interest labels, poi-labels",
				"collapsed": true
			},
			"Road network, tunnels-case": {
				"name": "Road network, tunnels-case",
				"collapsed": true
			},
			"Transit, built": {"name": "Transit, built", "collapsed": true},
			"Road network, surface-icons": {
				"name": "Road network, surface-icons",
				"collapsed": true
			},
			"Land & water, water": {
				"name": "Land & water, water",
				"collapsed": true
			}
		},
		"mapbox:uiParadigm": "layers",
		"mapbox:print": {
			"units": "cm",
			"width": 21.59,
			"height": 27.94,
			"resolution": 300,
			"format": "png"
		},
		"mapbox:decompiler": {
			"id": "ckjau5sv0033c19prkctc6byy",
			"componentVersion": "6.0.0",
			"strata": [
				{
					"id": "monochrome-dark-v1",
					"order": [
						["land-and-water", "land"],
						"land Mask",
						"contour",
						["land-and-water", "water"],
						["land-and-water", "built"],
						["transit", "built"],
						["buildings", "built"],
						["road-network", "tunnels-case"],
						["road-network", "tunnels"],
						["transit", "ferries"],
						["road-network", "surface"],
						["transit", "surface"],
						["road-network", "surface-icons"],
						["road-network", "bridges"],
						["transit", "bridges"],
						["road-network", "traffic-and-closures"],
						["buildings", "extruded"],
						["transit", "elevated"],
						["admin-boundaries", "admin"],
						["buildings", "building-labels"],
						"Building",
						["road-network", "road-labels"],
						["transit", "ferry-aerialway-labels"],
						["natural-features", "natural-labels"],
						["point-of-interest-labels", "poi-labels"],
						["transit", "transit-labels"],
						["place-labels", "place-labels"]
					]
				}
			],
			"overrides": {
				"land-and-water": {
					"landuse": {"paint": {"fill-color": {"remove": true}}},
					"land": {
						"paint": {
							"background-color": [
								"interpolate",
								["linear"],
								["zoom"],
								11,
								"hsla(0, 0%, 0%, 0)",
								13,
								"#000000"
							]
						}
					},
					"water": {"paint": {"fill-color": "hsl(0, 0%, 15%)"}},
					"wetland-pattern": {
						"paint": {
							"fill-opacity": [
								"interpolate",
								["linear"],
								["zoom"],
								10,
								0,
								10.5,
								0
							]
						}
					}
				},
				"road-network": {
					"road-label-navigation": {
						"layout": {
							"text-field": [
								"coalesce",
								["get", "name_zh-Hant"],
								["get", "name"]
							]
						},
						"paint": {
							"text-color": "hsl(0, 0%, 54%)",
							// "text-opacity": 0
						}
					},
					"road-secondary-tertiary-navigation": {
						"paint": {"line-color": "#303030"}
					},
					"road-street-navigation": {
						"paint": {"line-color": "#303030"}
					}
				},
				"point-of-interest-labels": {
					// "poi-label": {"paint": {"text-opacity": 0}}
				},
				"place-labels": {
					"settlement-major-label": {"paint": {"text-opacity": 0}},
					"settlement-subdivision-label": {
						"paint": {"text-opacity": 0}
					},
					"settlement-minor-label": {"paint": {"text-opacity": 0}}
				},
				"transit": {"airport-label": {"paint": {"text-opacity": 0}}},
				"natural-features": {
					"natural-point-label": {"paint": {"text-opacity": 0}},
					"waterway-label": {
						"layout": {
							"text-field": [
								"coalesce",
								["get", "name_en"],
								["get", "name"]
							]
						},
						"paint": {"text-opacity": 0}
					},
					"natural-line-label": {
						"layout": {
							"text-field": [
								"coalesce",
								["get", "name_en"],
								["get", "name"]
							]
						},
						"paint": {"text-opacity": 0}
					},
					"water-point-label": {
						"layout": {
							"text-field": [
								"coalesce",
								["get", "name_en"],
								["get", "name"]
							]
						},
						"paint": {"text-opacity": 0}
					}
				}
			},
			"components": {
				"land-and-water": "6.0.0",
				"buildings": "6.0.0",
				"road-network": "6.0.0",
				"admin-boundaries": "6.0.0",
				"natural-features": "6.0.0",
				"point-of-interest-labels": "6.0.0",
				"transit": "6.0.0",
				"place-labels": "6.0.0"
			},
			"propConfig": {
				"land-and-water": {
					"color-base": "#000000",
					"transitionLandOnZoom": true,
					"landStyle": "Outdoors",
					"waterStyle": "Shadow",
					"landcover": true,
					"landuse": true,
					"color-greenspace": "hsl(185, 0%, 46%)"
				},
				"buildings": {
					"color-base": "#000000",
					"houseNumbers": false,
					"3D": false,
					"haloWidth": 1.9,
					"underground": false
				},
				// "road-network": {
				//     "incidents": false,
				//     "icon-color-scheme": "monochrome",
				//     "roadOutlineWidth": 1,
				//     "shields": false,
				//     "trafficSignals": false,
				//     "roadNetwork": "Navigation",
				//     "construction": false,
				//     "oneWayArrows": false,
				//     "railwayCrossings": false,
				//     "exits": false,
				//     "polygonFeatures": false,
				//     "language": "Traditional Chinese",
				//     "color-base": "#000000",
				//     "traffic": false,
				//     "minorRoads": false,
				//     "turningCircles": false
				// },
				"admin-boundaries": {"color-base": "#000000"},
				"natural-features": {
					"color-base": "#000000",
					"labelStyle": "Text only",
					"density": 4
				},
				"point-of-interest-labels": {
					"color-base": "#000000",
					"labelStyle": "Text only",
					"density": 1,
					"color-greenspace": "hsl(185, 0%, 46%)"
				},
				"transit": {
					"color-base": "#000000",
					"aerialways": false,
					"ferries": false,
					"transitLabels": false,
					"railwayStyle": false,
					"icon-color-scheme": "monochrome"
				},
				"place-labels": {"color-base": "#000000"}
			}
		}
	},
	"center": [121.56137441007775, 25.042593623591785],
	"zoom": 14.506492208470563,
	"bearing": 25.405152119092573,
	"pitch": 67.49798204204666,
	"sources": {
		"composite": {
			"url": "mapbox://mapbox.mapbox-terrain-v2,mapbox.mapbox-streets-v8",
			// "url": "mapbox://mapbox.mapbox-terrain-v2,mapbox.mapbox-streets-v8,eltontsern.17trsstd",
			"type": "vector"
		}
	},
	"sprite": "mapbox://sprites/mapbox/dark-v10",
	"glyphs": "mapbox://fonts/mapbox/{fontstack}/{range}.pbf",
	"layers": [
		{
			"id": "land",
			"type": "background",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"layout": {},
			"paint": {
				"background-color": [
					"interpolate",
					["linear"],
					["zoom"],
					11,
					"hsla(0, 0%, 0%, 0)",
					13,
					"#000000"
				]
			}
		},
		{
			"id": "landcover-outdoors",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"source": "composite",
			"source-layer": "landcover",
			"maxzoom": 12,
			"layout": {},
			"paint": {
				"fill-color": [
					"match",
					["get", "class"],
					"snow",
					"rgb(94, 94, 94)",
					"hsl(167, 0%, 0%)"
				],
				"fill-opacity": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					2,
					0.3,
					12,
					0
				],
				"fill-antialias": false
			}
		},
		{
			"id": "national-park",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"source": "composite",
			"source-layer": "landuse_overlay",
			"minzoom": 5,
			"filter": ["==", ["get", "class"], "national_park"],
			"layout": {},
			"paint": {
				"fill-color": "hsl(185, 0%, 46%)",
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					5,
					0,
					6,
					0.75,
					10,
					0.35
				]
			}
		},
		{
			"id": "national-park_tint-band",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"source": "composite",
			"source-layer": "landuse_overlay",
			"minzoom": 9,
			"filter": ["==", ["get", "class"], "national_park"],
			"layout": {"line-cap": "round"},
			"paint": {
				"line-color": "hsl(185, 1%, 41%)",
				"line-width": [
					"interpolate",
					["exponential", 1.4],
					["zoom"],
					9,
					1,
					14,
					8
				],
				"line-offset": [
					"interpolate",
					["exponential", 1.4],
					["zoom"],
					9,
					0,
					14,
					-2.5
				],
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					9,
					0,
					10,
					0.75
				],
				"line-blur": 3
			}
		},
		{
			"id": "landuse",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"source": "composite",
			"source-layer": "landuse",
			"minzoom": 5,
			"filter": [
				"match",
				["get", "class"],
				["park", "airport", "glacier", "pitch", "sand", "facility"],
				true,
				["agriculture", "wood", "grass", "scrub"],
				true,
				"cemetery",
				true,
				false
			],
			"layout": {},
			"paint": {
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					5,
					0,
					6,
					[
						"match",
						["get", "class"],
						["agriculture", "wood", "grass", "scrub"],
						0,
						"glacier",
						0.5,
						1
					],
					15,
					[
						"match",
						["get", "class"],
						"agriculture",
						0.75,
						["wood", "glacier"],
						0.5,
						"grass",
						0.4,
						"scrub",
						0.2,
						1
					]
				]
			}
		},
		{
			"id": "pitch-outline",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, land"
			},
			"source": "composite",
			"source-layer": "landuse",
			"minzoom": 15,
			"filter": ["==", ["get", "class"], "pitch"],
			"layout": {},
			"paint": {"line-color": "hsl(167, 0%, 0%)"}
		},
		{
			"id": "land Mask",
			"type": "background",
			"layout": {},
			"paint": {
				"background-color": [
					"interpolate",
					["linear"],
					["zoom"],
					0,
					"hsla(185, 0%, 100%, 0.28)",
					18,
					"hsla(185, 0%, 99%, 0.76)",
					22,
					"hsl(185, 0%, 99%)"
				],
				"background-opacity": 0,
				"background-pattern": "airport-11"
			}
		},
		{
			//等高線ㄦ-Contour Map 
			"id": "contour",
			"type": "fill-extrusion",
			"source": "composite",
			"source-layer": "contour",
			"layout": {},
			"paint": {
				"fill-extrusion-height": [
					"interpolate",
					["linear"],
					["get", "ele"],
					20,
					0,
					8840,
					8840
				],
				"fill-extrusion-color": "#030303",
				'fill-extrusion-opacity': 0.95
			}
		},
		{
			"id": "waterway-shadow",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "waterway",
			"minzoom": 8,
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 11, "round"],
				"line-join": "round"
			},
			"paint": {
				"line-color": "rgb(0, 0, 0)",
				"line-width": [
					"interpolate",
					["exponential", 1.3],
					["zoom"],
					9,
					["match", ["get", "class"], ["canal", "river"], 0.1, 0],
					20,
					["match", ["get", "class"], ["canal", "river"], 8, 3]
				],
				"line-translate": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					7,
					["literal", [0, 0]],
					16,
					["literal", [-1, -1]]
				],
				"line-translate-anchor": "viewport",
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					8,
					0,
					8.5,
					1
				]
			}
		},
		{
			"id": "water-shadow",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "water",
			"layout": {},
			"paint": {
				"fill-color": "rgb(0, 0, 0)",
				"fill-translate": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					7,
					["literal", [0, 0]],
					16,
					["literal", [-1, -1]]
				],
				"fill-translate-anchor": "viewport"
			}
		},
		{
			"id": "waterway",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "waterway",
			"minzoom": 8,
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 11, "round"],
				"line-join": "round"
			},
			"paint": {
				"line-color": "rgb(26, 26, 26)",
				"line-width": [
					"interpolate",
					["exponential", 1.3],
					["zoom"],
					9,
					["match", ["get", "class"], ["canal", "river"], 0.1, 0],
					20,
					["match", ["get", "class"], ["canal", "river"], 8, 3]
				],
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					8,
					0,
					8.5,
					1
				]
			}
		},
		{
			"id": "water",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "water",
			"layout": {},
			"paint": {"fill-color": "hsl(0, 0%, 15%)"}
		},
		{
			"id": "wetland",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "landuse_overlay",
			"minzoom": 5,
			"filter": [
				"match",
				["get", "class"],
				["wetland", "wetland_noveg"],
				true,
				false
			],
			"paint": {
				"fill-color": "rgb(41, 41, 41)",
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					10,
					0.25,
					10.5,
					0.15
				]
			}
		},
		{
			"id": "wetland-pattern",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, water"
			},
			"source": "composite",
			"source-layer": "landuse_overlay",
			"minzoom": 5,
			"filter": [
				"match",
				["get", "class"],
				["wetland", "wetland_noveg"],
				true,
				false
			],
			"layout": {},
			"paint": {
				"fill-color": "rgb(41, 41, 41)",
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					10,
					0,
					10.5,
					0
				],
				// "fill-pattern": "wetland",
				"fill-translate-anchor": "viewport"
			}
		},
		{
			"id": "land-structure-polygon",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, built"
			},
			"source": "composite",
			"source-layer": "structure",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["geometry-type"], "Polygon"],
				["==", ["get", "class"], "land"]
			],
			"layout": {},
			"paint": {"fill-color": "rgb(36, 36, 36)"}
		},
		{
			"id": "land-structure-line",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "land-and-water",
				"mapbox:group": "Land & water, built"
			},
			"source": "composite",
			"source-layer": "structure",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["geometry-type"], "LineString"],
				["==", ["get", "class"], "land"]
			],
			"layout": {"line-cap": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.99],
					["zoom"],
					14,
					0.75,
					20,
					40
				],
				"line-color": "rgb(36, 36, 36)"
			}
		},
		{
			"id": "aeroway-polygon",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "transit",
				"mapbox:group": "Transit, built"
			},
			"source": "composite",
			"source-layer": "aeroway",
			"minzoom": 11,
			"filter": [
				"all",
				["==", ["geometry-type"], "Polygon"],
				[
					"match",
					["get", "type"],
					["runway", "taxiway", "helipad"],
					true,
					false
				]
			],
			"layout": {},
			"paint": {
				"fill-color": "rgb(59, 59, 59)",
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					11,
					0,
					11.5,
					1
				]
			}
		},
		{
			"id": "aeroway-line",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "transit",
				"mapbox:group": "Transit, built"
			},
			"source": "composite",
			"source-layer": "aeroway",
			"minzoom": 9,
			"filter": ["==", ["geometry-type"], "LineString"],
			"layout": {},
			"paint": {
				"line-color": "rgb(59, 59, 59)",
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					9,
					["match", ["get", "type"], "runway", 1, 0.5],
					18,
					["match", ["get", "type"], "runway", 80, 20]
				]
			}
		},
		{
			"id": "building-outline",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "buildings",
				"mapbox:group": "Buildings, built"
			},
			"source": "composite",
			"source-layer": "building",
			"minzoom": 15,
			"filter": [
				"all",
				["!=", ["get", "type"], "building:part"],
				["==", ["get", "underground"], "false"]
			],
			"layout": {},
			"paint": {
				"line-color": "rgb(26, 26, 26)",
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					0.75,
					20,
					3
				],
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					15,
					0,
					16,
					1
				]
			}
		},
		{
			"id": "building",
			"type": "fill",
			"metadata": {
				"mapbox:featureComponent": "buildings",
				"mapbox:group": "Buildings, built"
			},
			"source": "composite",
			"source-layer": "building",
			"minzoom": 15,
			"filter": [
				"all",
				["!=", ["get", "type"], "building:part"],
				["==", ["get", "underground"], "false"]
			],
			"layout": {},
			"paint": {
				"fill-color": [
					"interpolate",
					["linear"],
					["zoom"],
					15,
					"rgb(38, 38, 38)",
					16,
					"rgb(31, 31, 31)"
				],
				"fill-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					15,
					0,
					16,
					1
				],
				"fill-outline-color": "rgb(26, 26, 26)"
			}
		},
		{
			"id": "tunnel-minor-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					15,
					0.75,
					18,
					1.5
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-street-low-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"maxzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-street-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.5,
					18,
					2
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					14,
					2,
					18,
					20
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-secondary-tertiary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 12,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					0.75,
					18,
					28
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-primary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 10,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				["==", ["get", "class"], "primary"],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-major-link-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-motorway-trunk-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels-case"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(64, 64, 64)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				],
				"line-dasharray": [3, 3]
			}
		},
		{
			"id": "tunnel-major-link-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-minor-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-street-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-secondary-tertiary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					0.75,
					18,
					28
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-primary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				["==", ["get", "class"], "primary"],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "tunnel-motorway-trunk-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, tunnels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "tunnel"],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				],
				"line-color": "rgb(31, 31, 31)"
			}
		},
		{
			"id": "road-minor-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round", "line-cap": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					15,
					0.75,
					18,
					1.5
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				]
			}
		},
		{
			"id": "road-street-low-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 11,
			"maxzoom": 14,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 14, "round"],
				"line-join": ["step", ["zoom"], "miter", 14, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "road-street-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 13, "round"],
				"line-join": ["step", ["zoom"], "miter", 13, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.5,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					14,
					2,
					18,
					20
				]
			}
		},
		{
			"id": "road-secondary-tertiary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 12,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					0.75,
					18,
					28
				]
			}
		},
		{
			"id": "road-primary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 12,
			"filter": [
				"all",
				["==", ["get", "class"], "primary"],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				]
			}
		},
		{
			"id": "road-major-link-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 11,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 13, "round"],
				"line-join": ["step", ["zoom"], "miter", 13, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				]
			}
		},
		{
			"id": "road-motorway-trunk-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				]
			}
		},
		{
			"id": "road-major-link-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 11,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 13, "round"],
				"line-join": ["step", ["zoom"], "miter", 13, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "road-minor-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round", "line-cap": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "road-street-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2,
					18,
					20
				],
				"line-color": "#303030"
			}
		},
		{
			"id": "road-secondary-tertiary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 8,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 11, "round"],
				"line-join": ["step", ["zoom"], "miter", 11, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					0.175,
					10,
					0.75,
					18,
					28
				],
				"line-color": "#303030"
			}
		},
		{
			"id": "road-primary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 6,
			"filter": [
				"all",
				["==", ["get", "class"], "primary"],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 11, "round"],
				"line-join": ["step", ["zoom"], "miter", 11, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "road-motorway-trunk-case-low-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 5,
			"maxzoom": 13,
			"filter": [
				"all",
				[
					"step",
					["zoom"],
					["==", ["get", "class"], "motorway"],
					6,
					[
						"match",
						["get", "class"],
						["motorway", "trunk"],
						true,
						false
					]
				],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				]
			}
		},
		{
			"id": "road-motorway-trunk-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 5,
			"filter": [
				"all",
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["match", ["get", "structure"], ["none", "ford"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 8, "round"],
				"line-join": ["step", ["zoom"], "miter", 8, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "road-rail",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "transit",
				"mapbox:group": "Transit, surface"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["major_rail", "minor_rail"],
					true,
					false
				],
				["match", ["get", "structure"], ["none", "ford"], true, false]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-color": "rgb(31, 31, 31)",
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					14,
					0.5,
					20,
					1
				]
			}
		},
		{
			"id": "bridge-minor-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					15,
					0.75,
					18,
					1.5
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				]
			}
		},
		{
			"id": "bridge-street-low-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"maxzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-street-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.5,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					14,
					2,
					18,
					20
				]
			}
		},
		{
			"id": "bridge-secondary-tertiary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 12,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					0.75,
					18,
					28
				]
			}
		},
		{
			"id": "bridge-primary-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 12,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				["==", ["get", "class"], "primary"],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				]
			}
		},
		{
			"id": "bridge-major-link-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["<=", ["get", "layer"], 1],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				]
			}
		},
		{
			"id": "bridge-motorway-trunk-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["<=", ["get", "layer"], 1],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				]
			}
		},
		{
			"id": "bridge-major-link-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["<=", ["get", "layer"], 1],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-minor-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["secondary_link", "tertiary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					15,
					["match", ["get", "class"], "track", 1, 0.5],
					18,
					10
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-street-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 14,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["street", "street_limited", "primary_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.5,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-secondary-tertiary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["secondary", "tertiary"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"line-cap": ["step", ["zoom"], "butt", 11, "round"],
				"line-join": ["step", ["zoom"], "miter", 11, "round"]
			},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					0.75,
					18,
					28
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-primary-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				["==", ["get", "class"], "primary"],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					10,
					1.125,
					18,
					32
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-motorway-trunk-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["<=", ["get", "layer"], 1],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-major-link-2-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[">=", ["get", "layer"], 2],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					0.75,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				]
			}
		},
		{
			"id": "bridge-motorway-trunk-2-case-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[">=", ["get", "layer"], 2],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.2],
					["zoom"],
					10,
					1,
					18,
					2
				],
				"line-color": "rgb(31, 31, 31)",
				"line-gap-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				]
			}
		},
		{
			"id": "bridge-major-link-2-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[">=", ["get", "layer"], 2],
				[
					"match",
					["get", "class"],
					["motorway_link", "trunk_link"],
					true,
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					12,
					0.75,
					14,
					2,
					18,
					20
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-motorway-trunk-2-navigation",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[">=", ["get", "layer"], 2],
				["match", ["get", "class"], ["motorway", "trunk"], true, false],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {"line-cap": "round", "line-join": "round"},
			"paint": {
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					5,
					1.25,
					18,
					32
				],
				"line-color": "rgb(56, 56, 56)"
			}
		},
		{
			"id": "bridge-rail",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "transit",
				"mapbox:group": "Transit, bridges"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"all",
				["==", ["get", "structure"], "bridge"],
				[
					"match",
					["get", "class"],
					["major_rail", "minor_rail"],
					true,
					false
				]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-color": "rgb(31, 31, 31)",
				"line-width": [
					"interpolate",
					["exponential", 1.5],
					["zoom"],
					14,
					0.5,
					20,
					1
				]
			}
		},
		{
			"id": "admin-1-boundary-bg",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "admin-boundaries",
				"mapbox:group": "Administrative boundaries, admin"
			},
			"source": "composite",
			"source-layer": "admin",
			"minzoom": 7,
			"filter": [
				"all",
				["==", ["get", "admin_level"], 1],
				["==", ["get", "maritime"], "false"],
				["match", ["get", "worldview"], ["all", "US"], true, false]
			],
			"layout": {"line-join": "bevel"},
			"paint": {
				"line-color": [
					"interpolate",
					["linear"],
					["zoom"],
					8,
					"rgb(26, 26, 26)",
					16,
					"rgb(26, 26, 26)"
				],
				"line-width": [
					"interpolate",
					["linear"],
					["zoom"],
					7,
					3.75,
					12,
					5.5
				],
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					7,
					0,
					8,
					0.75
				],
				"line-dasharray": [1, 0],
				"line-blur": ["interpolate", ["linear"], ["zoom"], 3, 0, 8, 3]
			}
		},
		{
			"id": "admin-0-boundary-bg",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "admin-boundaries",
				"mapbox:group": "Administrative boundaries, admin"
			},
			"source": "composite",
			"source-layer": "admin",
			"minzoom": 1,
			"filter": [
				"all",
				["==", ["get", "admin_level"], 0],
				["==", ["get", "maritime"], "false"],
				["match", ["get", "worldview"], ["all", "US"], true, false]
			],
			"layout": {},
			"paint": {
				"line-width": [
					"interpolate",
					["linear"],
					["zoom"],
					3,
					3.5,
					10,
					8
				],
				"line-color": "rgb(26, 26, 26)",
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					3,
					0,
					4,
					0.5
				],
				"line-blur": ["interpolate", ["linear"], ["zoom"], 3, 0, 10, 2]
			}
		},
		{
			"id": "admin-1-boundary",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "admin-boundaries",
				"mapbox:group": "Administrative boundaries, admin"
			},
			"source": "composite",
			"source-layer": "admin",
			"minzoom": 2,
			"filter": [
				"all",
				["==", ["get", "admin_level"], 1],
				["==", ["get", "maritime"], "false"],
				["match", ["get", "worldview"], ["all", "US"], true, false]
			],
			"layout": {"line-join": "round", "line-cap": "round"},
			"paint": {
				"line-dasharray": [
					"step",
					["zoom"],
					["literal", [2, 0]],
					7,
					["literal", [2, 2, 6, 2]]
				],
				"line-width": [
					"interpolate",
					["linear"],
					["zoom"],
					7,
					0.75,
					12,
					1.5
				],
				"line-opacity": [
					"interpolate",
					["linear"],
					["zoom"],
					2,
					0,
					3,
					1
				],
				"line-color": [
					"interpolate",
					["linear"],
					["zoom"],
					3,
					"rgb(59, 59, 59)",
					7,
					"rgb(92, 92, 92)"
				]
			}
		},
		{
			"id": "admin-0-boundary",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "admin-boundaries",
				"mapbox:group": "Administrative boundaries, admin"
			},
			"source": "composite",
			"source-layer": "admin",
			"minzoom": 1,
			"filter": [
				"all",
				["==", ["get", "admin_level"], 0],
				["==", ["get", "disputed"], "false"],
				["==", ["get", "maritime"], "false"],
				["match", ["get", "worldview"], ["all", "US"], true, false]
			],
			"layout": {"line-join": "round", "line-cap": "round"},
			"paint": {
				"line-color": "rgb(99, 99, 99)",
				"line-width": [
					"interpolate",
					["linear"],
					["zoom"],
					3,
					0.5,
					10,
					2
				],
				"line-dasharray": [10, 0]
			}
		},
		{
			"id": "admin-0-boundary-disputed",
			"type": "line",
			"metadata": {
				"mapbox:featureComponent": "admin-boundaries",
				"mapbox:group": "Administrative boundaries, admin"
			},
			"source": "composite",
			"source-layer": "admin",
			"minzoom": 1,
			"filter": [
				"all",
				["==", ["get", "disputed"], "true"],
				["==", ["get", "admin_level"], 0],
				["==", ["get", "maritime"], "false"],
				["match", ["get", "worldview"], ["all", "US"], true, false]
			],
			"layout": {"line-join": "round"},
			"paint": {
				"line-color": "rgb(99, 99, 99)",
				"line-width": [
					"interpolate",
					["linear"],
					["zoom"],
					3,
					0.5,
					10,
					2
				],
				"line-dasharray": [
					"step",
					["zoom"],
					["literal", [3.25, 3.25]],
					6,
					["literal", [2.5, 2.5]],
					7,
					["literal", [2, 2.25]],
					8,
					["literal", [1.75, 2]]
				]
			}
		},
		/*
        {
            "id": "Building",
            "type": "fill-extrusion",
            "source": "composite",
            "source-layer": "_3-4n4uab", //Mapbox don't have this
            "layout": {},
            "paint": {
                "fill-extrusion-height": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0,
                    [
                        "interpolate",
                        ["linear"],
                        ["get", "1_Top_high"],
                        2.2,
                        0,
                        1044.14,
                        1044.14
                    ],
                    22,
                    [
                        "interpolate",
                        ["linear"],
                        ["get", "1_Top_high"],
                        2.2,
                        0,
                        1044.14,
                        1044.14
                    ]
                ],
                "fill-extrusion-opacity": 0.9,
                "fill-extrusion-translate": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    0,
                    ["literal", [0, 0]],
                    22,
                    ["literal", [0, 0]]
                ],
                "fill-extrusion-color": "hsl(0, 0%, 13%)"
            }
        },
        */
		{
			"id": "road-intersection",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, road-labels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 15,
			"filter": [
				"all",
				["==", ["get", "class"], "intersection"],
				["has", "name"]
			],
			"layout": {
				"text-field": [
					"coalesce",
					["get", "name_zh-Hant"],
					["get", "name"]
				],
				"icon-image": "intersection",
				"icon-text-fit": "both",
				"icon-text-fit-padding": [1, 2, 1, 2],
				"text-size": 12,
				"text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"]
			},
			"paint": {"text-color": "rgb(13, 13, 13)"}
		},
		{
			"id": "road-label-navigation",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "road-network",
				"mapbox:group": "Road network, road-labels"
			},
			"source": "composite",
			"source-layer": "road",
			"minzoom": 13,
			"filter": [
				"step",
				["zoom"],
				[
					"match",
					["get", "class"],
					["motorway", "trunk", "primary", "secondary", "tertiary"],
					true,
					false
				],
				15.25,
				[
					"match",
					["get", "class"],
					[
						"motorway",
						"trunk",
						"primary",
						"secondary",
						"tertiary",
						"street"
					],
					true,
					false
				],
				16,
				[
					"match",
					["get", "class"],
					[
						"motorway",
						"trunk",
						"primary",
						"secondary",
						"tertiary",
						"street",
						"street_limited"
					],
					true,
					false
				],
				16.5,
				[
					"match",
					["get", "class"],
					[
						"pedestrian",
						"golf",
						"ferry",
						"aerialway",
						"path",
						"track",
						"service"
					],
					false,
					true
				]
			],
			"layout": {
				"text-size": [
					"interpolate",
					["linear"],
					["zoom"],
					10,
					[
						"match",
						["get", "class"],
						[
							"motorway",
							"trunk",
							"primary",
							"secondary",
							"tertiary"
						],
						10,
						[
							"motorway_link",
							"trunk_link",
							"primary_link",
							"secondary_link",
							"tertiary_link",
							"street",
							"street_limited"
						],
						8,
						6.5
					],
					18,
					[
						"match",
						["get", "class"],
						[
							"motorway",
							"trunk",
							"primary",
							"secondary",
							"tertiary"
						],
						16,
						[
							"motorway_link",
							"trunk_link",
							"primary_link",
							"secondary_link",
							"tertiary_link",
							"street",
							"street_limited"
						],
						14,
						13
					],
					22,
					[
						"match",
						["get", "class"],
						[
							"motorway",
							"trunk",
							"primary",
							"secondary",
							"tertiary"
						],
						50,
						[
							"motorway_link",
							"trunk_link",
							"primary_link",
							"secondary_link",
							"tertiary_link",
							"street",
							"street_limited"
						],
						40,
						30
					]
				],
				"text-max-angle": 30,
				"symbol-spacing": [
					"interpolate",
					["linear"],
					["zoom"],
					10,
					150,
					18,
					450,
					22,
					1500
				],
				"text-font": ["DIN Pro Regular", "Arial Unicode MS Regular"],
				"symbol-placement": "line",
				"text-padding": 1,
				"text-rotation-alignment": "map",
				"text-pitch-alignment": "viewport",
				"text-field": [
					"coalesce",
					["get", "name_zh-Hant"],
					["get", "name"]
				],
				"text-letter-spacing": 0.01
			},
			"paint": {
				"text-color": "hsl(0, 0%, 54%)",
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1,
				"text-halo-blur": 1,
				// "text-opacity": 0
			}
		},
		{
			"id": "waterway-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "natural-features",
				"mapbox:group": "Natural features, natural-labels"
			},
			"source": "composite",
			"source-layer": "natural_label",
			"minzoom": 13,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["canal", "river", "stream"],
					["match", ["get", "worldview"], ["all", "US"], true, false],
					["disputed_canal", "disputed_river", "disputed_stream"],
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"text-font": ["DIN Pro Italic", "Arial Unicode MS Regular"],
				"text-max-angle": 30,
				"symbol-spacing": [
					"interpolate",
					["linear", 1],
					["zoom"],
					15,
					250,
					17,
					400
				],
				"text-size": [
					"interpolate",
					["linear"],
					["zoom"],
					13,
					12,
					18,
					16
				],
				"symbol-placement": "line",
				"text-pitch-alignment": "viewport",
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]]
			},
			"paint": {"text-color": "rgb(84, 84, 84)", "text-opacity": 0}
		},
		{
			"id": "natural-line-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "natural-features",
				"mapbox:group": "Natural features, natural-labels"
			},
			"source": "composite",
			"source-layer": "natural_label",
			"minzoom": 4,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["glacier", "landform"],
					["match", ["get", "worldview"], ["all", "US"], true, false],
					["disputed_glacier", "disputed_landform"],
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["==", ["geometry-type"], "LineString"],
				["<=", ["get", "filterrank"], 4]
			],
			"layout": {
				"text-size": [
					"step",
					["zoom"],
					["step", ["get", "sizerank"], 18, 5, 12],
					17,
					["step", ["get", "sizerank"], 18, 13, 12]
				],
				"text-max-angle": 30,
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"symbol-placement": "line-center",
				"text-pitch-alignment": "viewport"
			},
			"paint": {
				"text-halo-width": 0.5,
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-blur": 0.5,
				"text-color": "rgb(163, 163, 163)",
				"text-opacity": 0
			}
		},
		{
			"id": "natural-point-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "natural-features",
				"mapbox:group": "Natural features, natural-labels"
			},
			"source": "composite",
			"source-layer": "natural_label",
			"minzoom": 4,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["dock", "glacier", "landform", "water_feature", "wetland"],
					["match", ["get", "worldview"], ["all", "US"], true, false],
					[
						"disputed_dock",
						"disputed_glacier",
						"disputed_landform",
						"disputed_water_feature",
						"disputed_wetland"
					],
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["==", ["geometry-type"], "Point"],
				["<=", ["get", "filterrank"], 4]
			],
			"layout": {
				"text-size": [
					"step",
					["zoom"],
					["step", ["get", "sizerank"], 18, 5, 12],
					17,
					["step", ["get", "sizerank"], 18, 13, 12]
				],
				"icon-image": "",
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"text-offset": ["literal", [0, 0]],
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]]
			},
			"paint": {
				"icon-opacity": [
					"step",
					["zoom"],
					["step", ["get", "sizerank"], 0, 5, 1],
					17,
					["step", ["get", "sizerank"], 0, 13, 1]
				],
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 0.5,
				"text-halo-blur": 0.5,
				"text-color": "rgb(163, 163, 163)",
				"text-opacity": 0
			}
		},
		{
			"id": "water-line-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "natural-features",
				"mapbox:group": "Natural features, natural-labels"
			},
			"source": "composite",
			"source-layer": "natural_label",
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["bay", "ocean", "reservoir", "sea", "water"],
					["match", ["get", "worldview"], ["all", "US"], true, false],
					[
						"disputed_bay",
						"disputed_ocean",
						"disputed_reservoir",
						"disputed_sea",
						"disputed_water"
					],
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["==", ["geometry-type"], "LineString"]
			],
			"layout": {
				"text-size": [
					"interpolate",
					["linear"],
					["zoom"],
					7,
					["step", ["get", "sizerank"], 24, 6, 18, 12, 12],
					10,
					["step", ["get", "sizerank"], 18, 9, 12],
					18,
					["step", ["get", "sizerank"], 18, 9, 16]
				],
				"text-max-angle": 30,
				"text-letter-spacing": [
					"match",
					["get", "class"],
					"ocean",
					0.25,
					["sea", "bay"],
					0.15,
					0
				],
				"text-font": ["DIN Pro Italic", "Arial Unicode MS Regular"],
				"symbol-placement": "line-center",
				"text-pitch-alignment": "viewport",
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]]
			},
			"paint": {"text-color": "rgb(84, 84, 84)"}
		},
		{
			"id": "water-point-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "natural-features",
				"mapbox:group": "Natural features, natural-labels"
			},
			"source": "composite",
			"source-layer": "natural_label",
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					["bay", "ocean", "reservoir", "sea", "water"],
					["match", ["get", "worldview"], ["all", "US"], true, false],
					[
						"disputed_bay",
						"disputed_ocean",
						"disputed_reservoir",
						"disputed_sea",
						"disputed_water"
					],
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["==", ["geometry-type"], "Point"]
			],
			"layout": {
				"text-line-height": 1.3,
				"text-size": [
					"interpolate",
					["linear"],
					["zoom"],
					7,
					["step", ["get", "sizerank"], 24, 6, 18, 12, 12],
					10,
					["step", ["get", "sizerank"], 18, 9, 12]
				],
				"text-font": ["DIN Pro Italic", "Arial Unicode MS Regular"],
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-letter-spacing": [
					"match",
					["get", "class"],
					"ocean",
					0.25,
					["bay", "sea"],
					0.15,
					0.01
				],
				"text-max-width": [
					"match",
					["get", "class"],
					"ocean",
					4,
					"sea",
					5,
					["bay", "water"],
					7,
					10
				]
			},
			"paint": {"text-color": "rgb(84, 84, 84)", "text-opacity": 0}
		},
		{
			"id": "poi-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "point-of-interest-labels",
				"mapbox:group": "Point of interest labels, poi-labels"
			},
			"source": "composite",
			"source-layer": "poi_label",
			"minzoom": 6,
			"filter": [
				"<=",
				["get", "filterrank"],
				["+", ["step", ["zoom"], 0, 16, 1, 17, 2], 1]
			],
			"layout": {
				"text-size": [
					"step",
					["zoom"],
					["step", ["get", "sizerank"], 18, 5, 12],
					17,
					["step", ["get", "sizerank"], 18, 13, 12]
				],
				"icon-image": "",
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"text-offset": [0, 0],
				"text-anchor": [
					"step",
					["zoom"],
					["step", ["get", "sizerank"], "center", 5, "top"],
					17,
					["step", ["get", "sizerank"], "center", 13, "top"]
				],
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]]
			},
			"paint": {
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 0.5,
				"text-halo-blur": 0.5,
				"text-color": [
					"step",
					["zoom"],
					[
						"step",
						["get", "sizerank"],
						"rgb(92, 92, 92)",
						5,
						"rgb(130, 130, 130)"
					],
					17,
					[
						"step",
						["get", "sizerank"],
						"rgb(92, 92, 92)",
						13,
						"rgb(130, 130, 130)"
					]
				],
				"text-opacity": 0
			}
		},
		{
			"id": "airport-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "transit",
				"mapbox:group": "Transit, transit-labels"
			},
			"source": "composite",
			"source-layer": "airport_label",
			"minzoom": 8,
			"filter": [
				"match",
				["get", "class"],
				["military", "civil"],
				["match", ["get", "worldview"], ["all", "US"], true, false],
				["disputed_military", "disputed_civil"],
				[
					"all",
					["==", ["get", "disputed"], "true"],
					["match", ["get", "worldview"], ["all", "US"], true, false]
				],
				false
			],
			"layout": {
				"text-line-height": 1.1,
				"text-size": ["step", ["get", "sizerank"], 18, 9, 12],
				"icon-image": [
					"step",
					["get", "sizerank"],
					["concat", ["get", "maki"], "-15"],
					9,
					["concat", ["get", "maki"], "-11"]
				],
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"text-offset": [0, 0.75],
				"text-rotation-alignment": "viewport",
				"text-anchor": "top",
				"text-field": [
					"step",
					["get", "sizerank"],
					["coalesce", ["get", "name_en"], ["get", "name"]],
					15,
					["get", "ref"]
				],
				"text-letter-spacing": 0.01,
				"text-max-width": 9
			},
			"paint": {
				"text-color": "rgb(163, 163, 163)",
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1,
				"text-opacity": 0
			}
		},
		{
			"id": "settlement-subdivision-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "place-labels",
				"mapbox:group": "Place labels, place-labels"
			},
			"source": "composite",
			"source-layer": "place_label",
			"minzoom": 10,
			"maxzoom": 15,
			"filter": [
				"all",
				[
					"match",
					["get", "class"],
					"settlement_subdivision",
					["match", ["get", "worldview"], ["all", "US"], true, false],
					"disputed_settlement_subdivision",
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				["<=", ["get", "filterrank"], 4]
			],
			"layout": {
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-transform": "uppercase",
				"text-font": ["DIN Pro Regular", "Arial Unicode MS Regular"],
				"text-letter-spacing": [
					"match",
					["get", "type"],
					"suburb",
					0.15,
					0.1
				],
				"text-max-width": 7,
				"text-padding": 3,
				"text-size": [
					"interpolate",
					["cubic-bezier", 0.5, 0, 1, 1],
					["zoom"],
					11,
					["match", ["get", "type"], "suburb", 11, 10.5],
					15,
					["match", ["get", "type"], "suburb", 17, 16]
				]
			},
			"paint": {
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1,
				"text-color": "rgb(133, 133, 133)",
				"text-halo-blur": 0.5,
				"text-opacity": 0
			}
		},
		{
			"id": "settlement-minor-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "place-labels",
				"mapbox:group": "Place labels, place-labels"
			},
			"source": "composite",
			"source-layer": "place_label",
			"maxzoom": 15,
			"filter": [
				"all",
				["<=", ["get", "filterrank"], 3],
				[
					"match",
					["get", "class"],
					"settlement",
					["match", ["get", "worldview"], ["all", "US"], true, false],
					"disputed_settlement",
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				[
					"step",
					["zoom"],
					true,
					8,
					[">=", ["get", "symbolrank"], 11],
					10,
					[">=", ["get", "symbolrank"], 12],
					11,
					[">=", ["get", "symbolrank"], 13],
					12,
					[">=", ["get", "symbolrank"], 15],
					13,
					[">=", ["get", "symbolrank"], 11],
					14,
					[">=", ["get", "symbolrank"], 13]
				]
			],
			"layout": {
				"text-line-height": 1.1,
				"text-size": [
					"interpolate",
					["cubic-bezier", 0.2, 0, 0.9, 1],
					["zoom"],
					3,
					[
						"step",
						["get", "symbolrank"],
						12,
						9,
						11,
						10,
						10.5,
						12,
						9.5,
						14,
						8.5,
						16,
						6.5,
						17,
						4
					],
					13,
					[
						"step",
						["get", "symbolrank"],
						25,
						9,
						23,
						10,
						21,
						11,
						19,
						12,
						18,
						13,
						17,
						15,
						15
					]
				],
				"icon-image": [
					"step",
					["zoom"],
					[
						"case",
						["==", ["get", "capital"], 2],
						"border-dot-13",
						[
							"step",
							["get", "symbolrank"],
							"dot-11",
							9,
							"dot-10",
							11,
							"dot-9"
						]
					],
					8,
					""
				],
				"text-font": ["DIN Pro Regular", "Arial Unicode MS Regular"],
				"text-justify": [
					"step",
					["zoom"],
					[
						"match",
						["get", "text_anchor"],
						["left", "bottom-left", "top-left"],
						"left",
						["right", "bottom-right", "top-right"],
						"right",
						"center"
					],
					8,
					"center"
				],
				"text-offset": [
					"step",
					["zoom"],
					[
						"match",
						["get", "capital"],
						2,
						[
							"match",
							["get", "text_anchor"],
							"bottom",
							["literal", [0, -0.3]],
							"bottom-left",
							["literal", [0.3, -0.1]],
							"left",
							["literal", [0.45, 0.1]],
							"top-left",
							["literal", [0.3, 0.1]],
							"top",
							["literal", [0, 0.3]],
							"top-right",
							["literal", [-0.3, 0.1]],
							"right",
							["literal", [-0.45, 0]],
							"bottom-right",
							["literal", [-0.3, -0.1]],
							["literal", [0, -0.3]]
						],
						[
							"match",
							["get", "text_anchor"],
							"bottom",
							["literal", [0, -0.25]],
							"bottom-left",
							["literal", [0.2, -0.05]],
							"left",
							["literal", [0.4, 0.05]],
							"top-left",
							["literal", [0.2, 0.05]],
							"top",
							["literal", [0, 0.25]],
							"top-right",
							["literal", [-0.2, 0.05]],
							"right",
							["literal", [-0.4, 0.05]],
							"bottom-right",
							["literal", [-0.2, -0.05]],
							["literal", [0, -0.25]]
						]
					],
					8,
					["literal", [0, 0]]
				],
				"text-anchor": [
					"step",
					["zoom"],
					["get", "text_anchor"],
					8,
					"center"
				],
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-max-width": 7
			},
			"paint": {
				"text-color": [
					"step",
					["get", "symbolrank"],
					"rgb(163, 163, 163)",
					11,
					"rgb(130, 130, 130)",
					16,
					"rgb(115, 115, 115)"
				],
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1,
				"text-halo-blur": 1,
				"text-opacity": 0
			}
		},
		{
			"id": "settlement-major-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "place-labels",
				"mapbox:group": "Place labels, place-labels"
			},
			"source": "composite",
			"source-layer": "place_label",
			"maxzoom": 15,
			"filter": [
				"all",
				["<=", ["get", "filterrank"], 3],
				[
					"match",
					["get", "class"],
					"settlement",
					["match", ["get", "worldview"], ["all", "US"], true, false],
					"disputed_settlement",
					[
						"all",
						["==", ["get", "disputed"], "true"],
						[
							"match",
							["get", "worldview"],
							["all", "US"],
							true,
							false
						]
					],
					false
				],
				[
					"step",
					["zoom"],
					false,
					8,
					["<", ["get", "symbolrank"], 11],
					10,
					["<", ["get", "symbolrank"], 12],
					11,
					["<", ["get", "symbolrank"], 13],
					12,
					["<", ["get", "symbolrank"], 15],
					13,
					[">=", ["get", "symbolrank"], 11],
					14,
					[">=", ["get", "symbolrank"], 13]
				]
			],
			"layout": {
				"text-line-height": 1.1,
				"text-size": [
					"interpolate",
					["cubic-bezier", 0.2, 0, 0.9, 1],
					["zoom"],
					8,
					["step", ["get", "symbolrank"], 18, 9, 17, 10, 15],
					15,
					[
						"step",
						["get", "symbolrank"],
						28,
						9,
						26,
						10,
						23,
						11,
						21,
						12,
						20,
						13,
						19,
						15,
						16
					]
				],
				"icon-image": [
					"step",
					["zoom"],
					[
						"case",
						["==", ["get", "capital"], 2],
						"border-dot-13",
						[
							"step",
							["get", "symbolrank"],
							"dot-11",
							9,
							"dot-10",
							11,
							"dot-9"
						]
					],
					8,
					""
				],
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"text-justify": [
					"step",
					["zoom"],
					[
						"match",
						["get", "text_anchor"],
						["left", "bottom-left", "top-left"],
						"left",
						["right", "bottom-right", "top-right"],
						"right",
						"center"
					],
					8,
					"center"
				],
				"text-offset": [
					"step",
					["zoom"],
					[
						"match",
						["get", "capital"],
						2,
						[
							"match",
							["get", "text_anchor"],
							"bottom",
							["literal", [0, -0.3]],
							"bottom-left",
							["literal", [0.3, -0.1]],
							"left",
							["literal", [0.45, 0.1]],
							"top-left",
							["literal", [0.3, 0.1]],
							"top",
							["literal", [0, 0.3]],
							"top-right",
							["literal", [-0.3, 0.1]],
							"right",
							["literal", [-0.45, 0]],
							"bottom-right",
							["literal", [-0.3, -0.1]],
							["literal", [0, -0.3]]
						],
						[
							"match",
							["get", "text_anchor"],
							"bottom",
							["literal", [0, -0.25]],
							"bottom-left",
							["literal", [0.2, -0.05]],
							"left",
							["literal", [0.4, 0.05]],
							"top-left",
							["literal", [0.2, 0.05]],
							"top",
							["literal", [0, 0.25]],
							"top-right",
							["literal", [-0.2, 0.05]],
							"right",
							["literal", [-0.4, 0.05]],
							"bottom-right",
							["literal", [-0.2, -0.05]],
							["literal", [0, -0.25]]
						]
					],
					8,
					["literal", [0, 0]]
				],
				"text-anchor": [
					"step",
					["zoom"],
					["get", "text_anchor"],
					8,
					"center"
				],
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-max-width": 7
			},
			"paint": {
				"text-color": [
					"step",
					["get", "symbolrank"],
					"rgb(163, 163, 163)",
					11,
					"rgb(130, 130, 130)",
					16,
					"rgb(115, 115, 115)"
				],
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1,
				"text-halo-blur": 1,
				"text-opacity": 0
			}
		},
		{
			"id": "state-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "place-labels",
				"mapbox:group": "Place labels, place-labels"
			},
			"source": "composite",
			"source-layer": "place_label",
			"minzoom": 3,
			"maxzoom": 9,
			"filter": [
				"match",
				["get", "class"],
				"state",
				["match", ["get", "worldview"], ["all", "US"], true, false],
				"disputed_state",
				[
					"all",
					["==", ["get", "disputed"], "true"],
					["match", ["get", "worldview"], ["all", "US"], true, false]
				],
				false
			],
			"layout": {
				"text-size": [
					"interpolate",
					["cubic-bezier", 0.85, 0.7, 0.65, 1],
					["zoom"],
					4,
					["step", ["get", "symbolrank"], 10, 6, 9.5, 7, 9],
					9,
					["step", ["get", "symbolrank"], 24, 6, 18, 7, 14]
				],
				"text-transform": "uppercase",
				"text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
				"text-field": [
					"step",
					["zoom"],
					[
						"step",
						["get", "symbolrank"],
						["coalesce", ["get", "name_en"], ["get", "name"]],
						5,
						[
							"coalesce",
							["get", "abbr"],
							["get", "name_en"],
							["get", "name"]
						]
					],
					5,
					["coalesce", ["get", "name_en"], ["get", "name"]]
				],
				"text-letter-spacing": 0.15,
				"text-max-width": 6
			},
			"paint": {
				"text-color": "rgb(92, 92, 92)",
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1
			}
		},
		{
			"id": "country-label",
			"type": "symbol",
			"metadata": {
				"mapbox:featureComponent": "place-labels",
				"mapbox:group": "Place labels, place-labels"
			},
			"source": "composite",
			"source-layer": "place_label",
			"minzoom": 1,
			"maxzoom": 10,
			"filter": [
				"match",
				["get", "class"],
				"country",
				["match", ["get", "worldview"], ["all", "US"], true, false],
				"disputed_country",
				[
					"all",
					["==", ["get", "disputed"], "true"],
					["match", ["get", "worldview"], ["all", "US"], true, false]
				],
				false
			],
			"layout": {
				"icon-image": "",
				"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
				"text-line-height": 1.1,
				"text-max-width": 6,
				"text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
				"text-offset": ["literal", [0, 0]],
				"text-justify": [
					"step",
					["zoom"],
					[
						"match",
						["get", "text_anchor"],
						["left", "bottom-left", "top-left"],
						"left",
						["right", "bottom-right", "top-right"],
						"right",
						"center"
					],
					7,
					"center"
				],
				"text-size": [
					"interpolate",
					["cubic-bezier", 0.2, 0, 0.7, 1],
					["zoom"],
					1,
					["step", ["get", "symbolrank"], 11, 4, 9, 5, 8],
					9,
					["step", ["get", "symbolrank"], 28, 4, 22, 5, 21]
				]
			},
			"paint": {
				"icon-opacity": [
					"step",
					["zoom"],
					["case", ["has", "text_anchor"], 1, 0],
					7,
					0
				],
				"text-color": "rgb(97, 97, 97)",
				"text-halo-color": "rgb(0, 0, 0)",
				"text-halo-width": 1.25
			}
		}
	],
	// "created": "2020-12-30T03:04:27.731Z",
	// "modified": "2021-03-13T13:45:47.184Z",
	// "id": "ckjau5sv0033c19prkctc6byy",
	// "owner": "eltontsern",
	"visibility": "private",
	"draft": false
}