// Developed by Taipei Urban Intelligence Center 2023-2024

/* mapStore */
/*
The mapStore controls the map and includes methods to modify it.

!! PLEASE BE SURE TO REFERENCE THE MAPBOX DOCUMENTATION IF ANYTHING IS UNCLEAR !!
https://docs.mapbox.com/mapbox-gl-js/guides/
*/
import { createApp, defineComponent, nextTick, ref } from "vue";
import { defineStore } from "pinia";
import mapboxGl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { ArcLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import axios from "axios";
import http from "../router/axios.js";

// Other Stores
import { useAuthStore } from "./authStore";
import { useDialogStore } from "./dialogStore";

// Vue Components
import MapPopup from "../components/map/MapPopup.vue";

// Utility Functions or Configs
import {
	MapObjectConfig,
	TaipeiBuilding,
	TaipeiTown,
	TaipeiVillage,
	TpDistrict,
	TpVillage,
	maplayerCommonLayout,
	maplayerCommonPaint,
} from "../assets/configs/mapbox/mapConfig.js";
import mapStyle from "../assets/configs/mapbox/mapStyle.js";
import { hexToRGB } from "../assets/utilityFunctions/colorConvert.js";
import { interpolation } from "../assets/utilityFunctions/interpolation.js";
import { marchingSquare } from "../assets/utilityFunctions/marchingSquare.js";
import { voronoi } from "../assets/utilityFunctions/voronoi.js";
import { calculateHaversineDistance } from "../assets/utilityFunctions/calculateHaversineDistance";
import { AnimatedArcLayer } from "../assets/configs/mapbox/arcAnimate.js";

export const useMapStore = defineStore("map", {
	state: () => ({
		// Array of layer IDs that are in the map
		currentLayers: [],
		// Array of layer IDs that are in the map and currently visible
		currentVisibleLayers: [],
		// Stores all map configs for all layers (to be used to render popups)
		mapConfigs: {},
		// Stores the mapbox map instance
		map: null,
		// Store deck.gl layer overlay
		overlay: null,
		// Store deck.gl layer
		deckGlLayer: {},
		// Store animate step form 1 to 100
		step: 1,
		// Stores popup information
		popup: null,
		// Store currently loading layers,
		loadingLayers: [],
		// Store all view points
		viewPoints: [],
		marker: null,
		tempMarkerCoordinates: null,
		// Store the user's current location,
		userLocation: { latitude: null, longitude: null },
	}),
	actions: {
		/* Initialize Mapbox */
		// 1. Creates the mapbox instance and passes in initial configs
		initializeMapBox() {
			this.map = null;
			this.marker = null;
			this.overlay = null;
			const MAPBOXTOKEN = import.meta.env.VITE_MAPBOXTOKEN;
			mapboxGl.accessToken = MAPBOXTOKEN;
			this.map = new mapboxGl.Map({
				...MapObjectConfig,
				style: mapStyle,
			});
			this.marker = new mapboxGl.Marker();
			const geoLocate = new mapboxGl.GeolocateControl({
				positionOptions: {
					enableHighAccuracy: true,
				},
				trackUserLocation: true,
				showUserHeading: true,
			});
			this.map.addControl(geoLocate);
			this.map.addControl(new mapboxGl.NavigationControl());
			this.map.doubleClickZoom.disable();
			this.map
				.on("load", () => {
					if (!this.map) return;
					this.overlay = new MapboxOverlay({
						interleaved: true,
						layers: [],
					});
					this.map.addControl(this.overlay);
					this.initializeBasicLayers();
				})
				.on("click", (event) => {
					if (this.popup) {
						this.popup = null;
					}
					this.addPopup(event);
				})
				.on("dblclick", (event) => {
					let coordinates = event.lngLat;
					this.tempMarkerCoordinates = coordinates;
					this.marker.setLngLat(coordinates).addTo(this.map);
				})
				.on("idle", () => {
					this.loadingLayers = this.loadingLayers.filter(
						(el) => el !== "rendering"
					);
				});

			this.renderMarkers();

			return geoLocate;
		},
		// 2. Adds three basic layers to the map (Taipei District, Taipei Village labels, and Taipei 3D Buildings)
		// Due to performance concerns, Taipei 3D Buildings won't be added in the mobile version
		initializeBasicLayers() {
			const authStore = useAuthStore();
			if (!this.map) return;
			// Taipei District Labels
			fetch(`/mapData/taipei_town.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("taipei_town", {
							type: "geojson",
							data: data,
						})
						.addLayer(TaipeiTown);
				});
			// Taipei Village Labels
			fetch(`/mapData/taipei_village.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("taipei_village", {
							type: "geojson",
							data: data,
						})
						.addLayer(TaipeiVillage);
				});
			// Taipei 3D Buildings
			if (!authStore.isMobileDevice) {
				this.map
					.addSource("taipei_building_3d_source", {
						type: "vector",
						url: import.meta.env.VITE_MAPBOXTILE,
					})
					.addLayer(TaipeiBuilding);
			}
			// Taipei Village Boundaries
			this.map
				.addSource(`tp_village`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:tp_village@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(TpVillage);
			// Taipei District Boundaries
			this.map
				.addSource(`tp_district`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:tp_district@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(TpDistrict);

			this.addSymbolSources();
		},
		// 3. Adds symbols that will be used by some map layers
		addSymbolSources() {
			const images = [
				"metro",
				"triangle_green",
				"triangle_white",
				"bike_green",
				"bike_orange",
				"bike_red",
				"cctv",
			];
			images.forEach((element) => {
				this.map.loadImage(
					`/images/map/${element}.png`,
					(error, image) => {
						if (error) throw error;
						this.map.addImage(element, image);
					}
				);
			});
		},
		// 4. Toggle district boundaries
		toggleDistrictBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"tp_district",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("tp_district", "visibility", "none");
			}
		},
		// 5. Toggle village boundaries
		toggleVillageBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"tp_village",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("tp_village", "visibility", "none");
			}
		},
		// 6. Set User Location
		setCurrentLocation() {
			if (navigator.geolocation) {
				navigator.geolocation.getCurrentPosition(
					(position) => {
						this.userLocation = {
							latitude: position.coords.latitude,
							longitude: position.coords.longitude,
						};
					},
					(error) => {
						console.error(error.message);
					}
				);
			} else {
				console.error("Geolocation is not supported by this browser.");
			}
		},

		/* Adding Map Layers */
		// 1. Passes in the map_config (an Array of Objects) of a component and adds all layers to the map layer list
		addToMapLayerList(map_config) {
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}`;
				// 1-1. If the layer exists, simply turn on the visibility and add it to the visible layers list
				if (
					this.currentLayers.find((element) => element === mapLayerId)
				) {
					this.loadingLayers.push("rendering");
					this.turnOnMapLayerVisibility(mapLayerId);
					if (
						!this.currentVisibleLayers.find(
							(element) => element === mapLayerId
						)
					) {
						this.currentVisibleLayers.push(mapLayerId);
					}
					return;
				}
				let appendLayer = { ...element };
				appendLayer.layerId = mapLayerId;
				// 1-2. If the layer doesn't exist, call an API to get the layer data
				this.loadingLayers.push(appendLayer.layerId);
				if (element.source === "geojson") {
					this.fetchLocalGeoJson(appendLayer);
				} else if (element.source === "raster") {
					this.addRasterSource(appendLayer);
				}
			});
		},
		// 2. Call an API to get the layer data
		fetchLocalGeoJson(map_config) {
			axios
				.get(`/mapData/${map_config.index}.geojson`)
				.then((rs) => {
					this.addGeojsonSource(map_config, rs.data);
				})
				.catch((e) => console.error(e));
		},
		// 3-1. Add a local geojson as a source in mapbox
		addGeojsonSource(map_config, data) {
			if (!["voronoi", "isoline"].includes(map_config.type)) {
				this.map.addSource(`${map_config.layerId}-source`, {
					type: "geojson",
					data: { ...data },
				});
			}
			if (map_config.type === "arc") {
				this.AddArcMapLayer(map_config, data);
			} else if (map_config.type === "voronoi") {
				this.AddVoronoiMapLayer(map_config, data);
			} else if (map_config.type === "isoline") {
				this.AddIsolineMapLayer(map_config, data);
			} else {
				this.addMapLayer(map_config);
			}
		},
		// 3-2. Add a raster map as a source in mapbox
		async addRasterSource(map_config) {
			if (["arc", "voronoi", "isoline"].includes(map_config.type)) {
				const res = await axios.get(
					`${location.origin}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${map_config.index}&maxFeatures=1000000&outputFormat=application%2Fjson`
				);

				if (map_config.type === "arc") {
					this.map.addSource(`${map_config.layerId}-source`, {
						type: "geojson",
						data: { ...res.data },
					});
					this.AddArcMapLayer(map_config, res.data);
				} else if (map_config.type === "voronoi") {
					this.AddVoronoiMapLayer(map_config, res.data);
				} else if (map_config.type === "isoline") {
					this.AddIsolineMapLayer(map_config, res.data);
				}
			} else {
				this.map.addSource(`${map_config.layerId}-source`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:${map_config.index}@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				});
				this.addMapLayer(map_config);
			}
		},
		// 4-1. Using the mapbox source and map config, create a new layer
		// The styles and configs can be edited in /assets/configs/mapbox/mapConfig.js
		addMapLayer(map_config) {
			let extra_paint_configs = {};
			let extra_layout_configs = {};
			if (map_config.icon) {
				extra_paint_configs = {
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.icon}`
					],
				};
				extra_layout_configs = {
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.icon}`
					],
				};
			}
			if (map_config.size) {
				extra_paint_configs = {
					...extra_paint_configs,
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.size}`
					],
				};
				extra_layout_configs = {
					...extra_layout_configs,
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.size}`
					],
				};
			}
			this.loadingLayers.push("rendering");
			this.map.addLayer({
				id: map_config.layerId,
				type: map_config.type,
				"source-layer":
					map_config.source === "raster" ? map_config.index : "",
				paint: {
					...maplayerCommonPaint[`${map_config.type}`],
					...extra_paint_configs,
					...map_config.paint,
				},
				layout: {
					...maplayerCommonLayout[`${map_config.type}`],
					...extra_layout_configs,
				},
				source: `${map_config.layerId}-source`,
			});
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			this.currentVisibleLayers.push(map_config.layerId);
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId
			);
		},
		// 4-2-1. Add Map Layer for Arc Maps
		// Developed by Weeee Chill, Taipei Codefest 2024
		AddArcMapLayer(map_config, data) {
			// start loading
			this.loadingLayers.push("rendering");
			const mapLayerId = `${map_config.index}-${map_config.type}`;
			const paintSettings = map_config.paint
				? map_config.paint
				: { "arc-color": ["#ffffff"] };
			paintSettings["arc-color"] = paintSettings["arc-color"]
				? paintSettings["arc-color"]
				: ["#ffffff"];
			// formatted data
			const layerConfig = {
				id: map_config.index,
				data: data.features,
				getSourcePosition: (d) => d.geometry.coordinates[0],
				getTargetPosition: (d) => d.geometry.coordinates[1],
				// color format: [r, g, b, [a]]
				getSourceColor: () => {
					const color = hexToRGB(paintSettings["arc-color"][0]);
					return [
						parseInt(color.r, 16),
						parseInt(color.g, 16),
						parseInt(color.b, 16),
						255 * paintSettings["arc-opacity"] || 255 * 0.5,
					];
				},
				getTargetColor: () => {
					const color = hexToRGB(
						paintSettings["arc-color"][1] ||
							paintSettings["arc-color"][0]
					);
					return [
						parseInt(color.r, 16),
						parseInt(color.g, 16),
						parseInt(color.b, 16),
						255 * paintSettings["arc-opacity"] || 255 * 0.5,
					];
				},
				getWidth: paintSettings["arc-width"] || 2,
				pickable: true,
				...(paintSettings["arc-animate"] && {
					coef: this.step / 1000,
				}),
			};
			// add deckgl layer to overlay
			this.deckGlLayer[mapLayerId] = {
				type: paintSettings["arc-animate"]
					? "AnimatedArcLayer"
					: "ArcLayer",
				config: layerConfig,
				data: data.features,
			};
			// render deckgl layer
			this.currentVisibleLayers.push(map_config.layerId);
			this.renderDeckGLLayer();
			// end loading
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId
			);
		},
		// 4-2-2. Render DeckGL Layer
		// Developed by Weeee Chill, Taipei Codefest 2024
		renderDeckGLLayer() {
			const layers = Object.keys(this.deckGlLayer).map((index) => {
				const l = this.deckGlLayer[index];
				switch (l.type) {
					case "ArcLayer":
						return new ArcLayer(l.config);
					case "AnimatedArcLayer":
						return new AnimatedArcLayer({
							...l.config,
							coef: this.step / 1000,
						});
					default:
						break;
				}
			});
			this.overlay.setProps({
				layers,
			});
			if (
				this.currentVisibleLayers.some(
					(l) =>
						l.indexOf("-arc") !== -1 &&
						typeof this.deckGlLayer[l].config.coef === "number"
				) &&
				this.step < 1000
			)
				this.animateArcLayer();
		},
		// 4-2-3. Animate Arc Layer
		// Developed by Weeee Chill, Taipei Codefest 2024
		animateArcLayer() {
			// 開始時間
			let startTime = performance.now();
			// 每個動畫步驟的持續時間（毫秒）
			const duration = 1000; // 1秒
			const _this = this;

			const step = (timestamp) => {
				// 計算已經過的時間
				const elapsedTime = timestamp - startTime;
				// 計算進度
				const progress = (elapsedTime / duration) * 100;

				// 如果時間已經超過一個步驟，則增加步驟數
				if (progress >= (_this.step / 1000) * 100) {
					_this.step = _this.step + 1;
					_this.renderDeckGLLayer();
				}

				// 如果動畫還未完成，繼續下一個動畫步驟
				if (_this.step <= 1000) {
					requestAnimationFrame(step);
				}
			};
			// 啟動動畫
			requestAnimationFrame(step);
		},
		// 4-3. Add Map Layer for Voronoi Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddVoronoiMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");

			let voronoi_source = {
				type: data.type,
				crs: data.crs,
				features: [],
			};

			// Get features alone
			let { features } = data;

			// Get coordnates alone
			let coords = features.map(
				(location) => location.geometry.coordinates
			);

			// Remove duplicate coordinates (so that they wont't cause problems in the Voronoi algorithm...)
			let shouldBeRemoved = coords.map((coord1, ind) => {
				return (
					coords.findIndex((coord2) => {
						return (
							coord2[0] === coord1[0] && coord2[1] === coord1[1]
						);
					}) !== ind
				);
			});

			features = features.filter((_, ind) => !shouldBeRemoved[ind]);
			coords = coords.filter((_, ind) => !shouldBeRemoved[ind]);

			// Calculate cell for each coordinate
			let cells = voronoi(coords);

			// Push cell outlines to source data
			for (let i = 0; i < cells.length; i++) {
				voronoi_source.features.push({
					...features[i],
					geometry: {
						type: "LineString",
						coordinates: cells[i],
					},
				});
			}

			// Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",
				data: { ...voronoi_source },
			});

			let new_map_config = { ...map_config };
			new_map_config.type = "line";
			new_map_config.source = "geojson";
			this.addMapLayer(new_map_config);
		},
		// 4-4. Add Map Layer for Isoline Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddIsolineMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");
			// Step 1: Generate a 2D scalar field from known data points
			// - Turn the original data into the format that can be accepted by interpolation()
			let dataPoints = data.features
				.filter((item) => item.geometry)
				.map((item) => {
					return {
						x: item.geometry.coordinates[0],
						y: item.geometry.coordinates[1],
						value: item.properties[
							map_config.paint?.["isoline-key"] || "value"
						],
					};
				});

			let lngStart = 121.42955;
			let lngEnd = 121.68351;
			let latStart = 24.94679;
			let latEnd = 25.21811;

			let targetPoints = [];
			let gridSize = 0.001;
			let rowN = 0;
			let colN = 0;

			// - Generate target point coordinates
			for (let i = latStart; i <= latEnd; i += gridSize, rowN += 1) {
				colN = 0;
				for (let j = lngStart; j <= lngEnd; j += gridSize, colN += 1) {
					targetPoints.push({ x: j, y: i });
				}
			}

			// - Get target points interpolation result
			let interpolationResult = interpolation(dataPoints, targetPoints);

			// Step 2: Calculate isolines from the 2D scalar field
			// - Turn the interpolation result into the format that can be accepted by marchingSquare()
			let discreteData = [];
			for (let y = 0; y < rowN; y++) {
				discreteData.push([]);
				for (let x = 0; x < colN; x++) {
					discreteData[y].push(interpolationResult[y * colN + x]);
				}
			}

			// - Initialize geojson data
			let isoline_data = {
				type: "FeatureCollection",
				crs: {
					type: "name",
					properties: { name: "urn:ogc:def:crs:OGC:1.3:CRS84" },
				},
				features: [],
			};

			const min = map_config.paint?.["isoline-min"] || 0;
			const max = map_config.paint?.["isoline-max"] || 100;
			const step = map_config.paint?.["isoline-step"] || 2;

			// - Repeat the marching square algorithm for differnt iso-values (40, 42, 44 ... 74 in this case)
			for (let isoValue = min; isoValue <= max; isoValue += step) {
				let result = marchingSquare(discreteData, isoValue);

				let transformedResult = result.map((line) => {
					return line.map((point) => {
						return [
							point[0] * gridSize + lngStart,
							point[1] * gridSize + latStart,
						];
					});
				});

				isoline_data.features = isoline_data.features.concat(
					// Turn result into geojson format
					transformedResult.map((line) => {
						return {
							type: "Feature",
							properties: { value: isoValue },
							geometry: { type: "LineString", coordinates: line },
						};
					})
				);
			}

			// Step 3: Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",
				data: { ...isoline_data },
			});

			delete map_config.paint?.["isoline-key"];
			delete map_config.paint?.["isoline-min"];
			delete map_config.paint?.["isoline-max"];
			delete map_config.paint?.["isoline-step"];

			let new_map_config = {
				...map_config,
				type: "line",
				source: "geojson",
			};
			this.addMapLayer(new_map_config);
		},
		//  5. Turn on the visibility for a exisiting map layer
		turnOnMapLayerVisibility(mapLayerId) {
			if (mapLayerId.indexOf("-arc") !== -1) {
				this.deckGlLayer[mapLayerId].config.visible = true;
				this.step = 1;
				this.currentVisibleLayers.push(mapLayerId);
				this.renderDeckGLLayer();
			} else {
				this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
			}
		},
		// 6. Turn off the visibility of an exisiting map layer but don't remove it completely
		turnOffMapLayerVisibility(map_config) {
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}`;
				this.loadingLayers = this.loadingLayers.filter(
					(el) => el !== mapLayerId
				);
				if (mapLayerId.indexOf("-arc") !== -1) {
					this.deckGlLayer[mapLayerId].config.visible = false;
					this.renderDeckGLLayer();
				} else if (this.map.getLayer(mapLayerId)) {
					this.map.setFilter(mapLayerId, null);
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none"
					);
				}
				this.currentVisibleLayers = this.currentVisibleLayers.filter(
					(element) => element !== mapLayerId
				);
			});
			this.removePopup();
		},

		/* Popup Related Functions */
		// 1. Adds a popup when the user clicks on a item. The event will be passed in.
		addPopup(event) {
			// Gets the info that is contained in the coordinates that the user clicked on (only visible layers)
			const clickFeatureDatas = this.map.queryRenderedFeatures(
				event.point,
				{
					layers: this.currentVisibleLayers.filter(
						(layer) => layer.indexOf("-arc") === -1
					),
				}
			);
			// Return if there is no info in the click
			if (!clickFeatureDatas || clickFeatureDatas.length === 0) {
				return;
			}
			// Parse clickFeatureDatas to get the first 3 unique layer datas, skip over already included layers
			const mapConfigs = [];
			const parsedPopupContent = [];
			let previousParsedLayer = "";

			for (let i = 0; i < clickFeatureDatas.length; i++) {
				if (mapConfigs.length === 3) break;
				if (previousParsedLayer === clickFeatureDatas[i].layer.id)
					continue;
				previousParsedLayer = clickFeatureDatas[i].layer.id;
				mapConfigs.push(this.mapConfigs[clickFeatureDatas[i].layer.id]);
				parsedPopupContent.push(clickFeatureDatas[i]);
			}
			// Create a new mapbox popup
			this.popup = new mapboxGl.Popup()
				.setLngLat(event.lngLat)
				.setHTML('<div id="vue-popup-content"></div>')
				.addTo(this.map);
			// Mount a vue component (MapPopup) to the id "vue-popup-content" and pass in data
			const PopupComponent = defineComponent({
				extends: MapPopup,
				setup() {
					// Only show the data of the topmost layer
					return {
						popupContent: parsedPopupContent,
						mapConfigs: mapConfigs,
						activeTab: ref(0),
					};
				},
			});
			// This helps vue determine the most optimal time to mount the component
			nextTick(() => {
				const app = createApp(PopupComponent);
				app.mount("#vue-popup-content");
			});
		},
		// 2. Remove the current popup
		removePopup() {
			if (this.popup) {
				this.popup.remove();
			}
			this.popup = null;
		},
		// 3. programmatically trigger the popup, instead of user click
		manualTriggerPopup() {
			const center = this.map.getCenter();
			const point = this.map.project(center);

			this.addPopup({
				point: point,
				lngLat: center,
			});

			this.loadingLayers.pop();
		},

		/* Viewpoint / Marker Functions */
		// 1. Add a viewpoint
		async addViewPoint(name) {
			const { lng, lat } = this.map.getCenter();
			const zoom = this.map.getZoom();
			const pitch = this.map.getPitch();
			const bearing = this.map.getBearing();

			const authStore = useAuthStore();
			const res = await http.post(
				`user/${authStore.user.user_id}/viewpoint`,
				{
					center_x: lng,
					center_y: lat,
					zoom,
					pitch,
					bearing,
					name,
					point_type: "view",
				}
			);
			this.viewPoints.push(res.data.data);
		},
		// 2. Add a marker
		async addMarker(name) {
			const authStore = useAuthStore();
			const res = await http.post(
				`user/${authStore.user.user_id}/viewpoint`,
				{
					center_x: this.tempMarkerCoordinates.lng,
					center_y: this.tempMarkerCoordinates.lat,
					zoom: 0,
					pitch: 0,
					bearing: 0,
					name: name,
					point_type: "pin",
				}
			);

			this.viewPoints.push(res.data.data);

			const { lng, lat } = this.tempMarkerCoordinates;
			this.createMarkerAndPopupOnMap(
				{ color: "#5a9cf8" },
				name,
				res.data.data.id,
				{ lng, lat }
			);
			this.tempMarkerCoordinates = null;
		},
		// 3. Create a marker and popup on the map
		createMarkerAndPopupOnMap(
			colorSetting,
			markerName,
			markerId,
			{ lng, lat }
		) {
			const authStore = useAuthStore();
			const dialogStore = useDialogStore();
			const marker = new mapboxGl.Marker(colorSetting);
			const popup = new mapboxGl.Popup({ closeButton: false }).setHTML(
				`<div class="popup-for-pin"><div>${markerName}</div> <button id="delete-${markerId}" class="delete-pin"}">
						<span>delete</span>
					  </button></div>`
			);

			popup.on("open", () => {
				const el = document.getElementById(`delete-${markerId}`);
				el.addEventListener("click", async () => {
					await http.delete(
						`user/${authStore.user.user_id}/viewpoint/${markerId}`
					);
					dialogStore.showNotification("success", "地標刪除成功");
					this.viewPoints = this.viewPoints.filter(
						(viewPoint) => viewPoint.id !== markerId
					);

					marker.remove();
					this.marker.remove();
				});
			});

			marker.setLngLat({ lng, lat }).setPopup(popup).addTo(this.map);
		},
		// 4. Remove a viewpoint
		async removeViewPoint(item) {
			const authStore = useAuthStore();
			await http.delete(
				`user/${authStore.user.user_id}/viewpoint/${item.id}`
			);
			const dialogStore = useDialogStore();

			this.viewPoints = this.viewPoints.filter(
				(viewPoint) => viewPoint.id !== item.id
			);
			dialogStore.showNotification("success", "視角刪除成功");
		},
		// 5. Fetch all view points
		async fetchViewPoints() {
			const authStore = useAuthStore();

			const res = await http.get(
				`user/${authStore.user.user_id}/viewpoint`
			);
			this.viewPoints = res.data;
			if (this.map) this.renderMarkers();
		},
		// 6. Render all markers
		renderMarkers() {
			if (!this.viewPoints.length) return;

			this.viewPoints.forEach((item) => {
				if (item.point_type === "pin") {
					this.createMarkerAndPopupOnMap(
						{ color: "#5a9cf8" },
						item.name,
						item.id,
						{ lng: item.center_x, lat: item.center_y }
					);
				}
			});
		},

		/* Functions that change the viewing experience of the map */
		// 1. Zoom to a location
		// [[lng, lat], zoom, pitch, bearing, savedLocationName]
		easeToLocation(location_array) {
			if (location_array?.zoom) {
				this.map.easeTo({
					center: [location_array.center_x, location_array.center_y],
					zoom: location_array.zoom,
					duration: 4000,
					pitch: location_array.pitch,
					bearing: location_array.bearing,
				});
			} else {
				this.map.easeTo({
					center: location_array[0],
					zoom: location_array[1],
					duration: 4000,
					pitch: location_array[2],
					bearing: location_array[3],
				});
			}
		},
		// 2. Fly to a location
		flyToLocation(location_array) {
			this.map.flyTo({
				center: location_array,
				duration: 1000,
			});
		},
		// 3. Force map to resize after sidebar collapses
		resizeMap() {
			if (this.map) {
				setTimeout(() => {
					this.map.resize();
				}, 200);
			}
		},

		/* Map Filtering */
		// 1. Add a filter based on a each map layer's properties (byParam)
		filterByParam(map_filter, map_configs, xParam, yParam) {
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config && map_config.type === "arc") {
					this.deckGlLayer[mapLayerId].config.data = this.deckGlLayer[
						mapLayerId
					].data.filter((d) => {
						if (
							map_filter.byParam.xParam &&
							map_filter.byParam.yParam &&
							xParam &&
							yParam
						) {
							return (
								d.properties[map_filter.byParam.xParam] ===
									xParam &&
								d.properties[map_filter.byParam.yParam] ===
									yParam
							);
						} else if (map_filter.byParam.yParam && yParam) {
							return (
								d.properties[map_filter.byParam.yParam] ===
								yParam
							);
						} else if (map_filter.byParam.xParam && xParam) {
							return (
								d.properties[map_filter.byParam.xParam] ===
								xParam
							);
						}
					});
					this.renderDeckGLLayer();
					return;
				}
				// If x and y both exist, filter by both
				if (
					map_filter.byParam.xParam &&
					map_filter.byParam.yParam &&
					xParam &&
					yParam
				) {
					this.map.setFilter(mapLayerId, [
						"all",
						["==", ["get", map_filter.byParam.xParam], xParam],
						["==", ["get", map_filter.byParam.yParam], yParam],
					]);
				}
				// If only y exists, filter by y
				else if (map_filter.byParam.yParam && yParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.yParam],
						yParam,
					]);
				}
				// default to filter by x
				else if (map_filter.byParam.xParam && xParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.xParam],
						xParam,
					]);
				}
			});
		},
		// 2. filter by layer name (byLayer)
		filterByLayer(map_configs, xParam) {
			const dialogStore = useDialogStore();
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config.title !== xParam) {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none"
					);
				} else {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible"
					);
				}
			});
		},
		// 3. Remove any property filters on a map layer
		clearByParamFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config && map_config.type === "arc") {
					this.deckGlLayer[mapLayerId].config.data =
						this.deckGlLayer[mapLayerId].data;
					this.renderDeckGLLayer();
					return;
				}
				this.map.setFilter(mapLayerId, null);
			});
		},
		// 4. Remove any layer filters on a map layer.
		clearByLayerFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
			});
		},

		/* Find Closest Data Point */
		// 1. Calculate the Haversine distance between two points
		findClosestLocation(userCoords, locations) {
			// Check if userCoords has valid latitude and longitude
			if (
				!userCoords ||
				typeof userCoords.latitude !== "number" ||
				typeof userCoords.longitude !== "number"
			) {
				throw new Error("Invalid user coordinates");
			}

			let minDistance = Infinity;
			let closestLocation = null;

			for (let location of locations) {
				try {
					// Check if location, location.geometry, and location.geometry.coordinates are valid
					if (
						!location ||
						!location.geometry ||
						!Array.isArray(location.geometry.coordinates)
					) {
						continue; // Skip this location if any of these are invalid
					}
					const [lon, lat] = location.geometry.coordinates;

					// Check if longitude and latitude are valid numbers
					if (typeof lon !== "number" || typeof lat !== "number") {
						continue; // Skip this location if coordinates are not numbers
					}

					// Calculate the Haversine distance
					const distance = calculateHaversineDistance(
						{
							latitude: userCoords.latitude,
							longitude: userCoords.longitude,
						},
						{ latitude: lat, longitude: lon }
					);

					// Update the closest location if the current distance is smaller
					if (distance < minDistance) {
						minDistance = distance;
						closestLocation = location;
					}
				} catch (e) {
					// Catch and log any errors during processing
					console.error(
						`Error processing location: ${JSON.stringify(
							location
						)}`,
						e
					);
				}
			}
			return closestLocation;
		},
		// 2. Fly to the closest location and trigger a popup
		async flyToClosestLocationAndTriggerPopup(lng, lat) {
			if (this.loadingLayers.length !== 0) return;
			this.loadingLayers.push("rendering");

			let targetLayer = -1;
			this.currentVisibleLayers.forEach((layer, index) => {
				if (["circle", "symbol"].includes(layer.split("-")[1])) {
					targetLayer = index;
				}
			});

			if (targetLayer === -1) {
				this.loadingLayers.pop();
				return;
			}

			this.removePopup();
			const layerSourceType =
				this.mapConfigs[this.currentVisibleLayers[targetLayer]].source;

			const features = [];

			if (layerSourceType === "geojson") {
				features.push(
					...this.map.getSource(
						`${this.currentVisibleLayers[targetLayer]}-source`
					)._data.features
				);
			} else {
				const res = await axios.get(
					`${
						location.origin
					}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${
						this.mapConfigs[this.currentVisibleLayers[targetLayer]]
							.index
					}&maxFeatures=1000000&outputFormat=application%2Fjson`
				);

				features.push(...res.data.features);
			}

			if (!features || features.length === 0) {
				this.loadingLayers.pop();
				return;
			}

			const res = this.findClosestLocation(
				{
					longitude: lng,
					latitude: lat,
				},
				features
			);

			this.map.once("moveend", () => {
				setTimeout(
					() => {
						this.manualTriggerPopup();
					},
					layerSourceType === "geojson" ? 0 : 500
				);
			});

			this.flyToLocation(res.geometry.coordinates);
		},

		/* Clearing the map */
		// 1. Called when the user is switching between maps
		clearOnlyLayers() {
			this.currentLayers.forEach((element) => {
				this.map.removeLayer(element);
				if (this.map.getSource(`${element}-source`)) {
					this.map.removeSource(`${element}-source`);
				}
			});
			this.currentLayers = [];
			this.mapConfigs = {};
			this.currentVisibleLayers = [];
			this.removePopup();
		},
		// 2. Called when user navigates away from the map
		clearEntireMap() {
			this.currentLayers = [];
			this.mapConfigs = {};
			this.map = null;
			this.currentVisibleLayers = [];
			this.removePopup();
			this.tempMarkerCoordinates = null;
		},
	},
});
