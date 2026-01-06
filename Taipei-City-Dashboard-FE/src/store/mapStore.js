// Developed by Taipei Urban Intelligence Center 2023-2024

/* mapStore */
/*
The mapStore controls the map and includes methods to modify it.

!! PLEASE BE SURE TO REFERENCE THE MAPBOX DOCUMENTATION IF ANYTHING IS UNCLEAR !!
https://docs.mapbox.com/mapbox-gl-js/guides/
*/

/* global gtag */

import { createApp, defineComponent, nextTick, ref, watch } from "vue";
import { defineStore } from "pinia";
import mapboxGl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import Hls from 'hls.js';
import { ArcLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import axios from "axios";
import http from "../router/axios.js";

// 3D Mrt Map (202511NEW)
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import mapboxgl from 'mapbox-gl';
import { markRaw } from "vue";
import { point, distance } from '@turf/turf';
import { cutRouteSegment } from "../assets/utilityFunctions/getRouteForAnimation.js";
import { interpolateAlongSegment } from '../assets/utilityFunctions/geometryUtils.js';
import { updateCarsPosition } from "../assets/utilityFunctions/mrtCars.js";

// Other Stores
import { useAuthStore } from "./authStore";
import { useDialogStore } from "./dialogStore";

// Vue Components
import MapPopup from "../components/map/MapPopup.vue";

// Utility Functions or Configs
import {
	MapObjectConfig,
	CityMapView,
	TaipeiBuilding,
	metroTaipeiTown,
	metroTaipeiVillage,
	metroTpDistrict,
	metroTpVillage,
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
		// 3D Mrt Map (202511NEW)
		// 模型及圖徵是否預載中
		isPreloading: true,
		// 預載 3D 模型
		preloadedModels: {},
		// 前一包列車動畫資料
		prevMrtCars: [],
		// 儲存圖層更新時間
		layerUpdateTime: {
    		// [layerId]: Date
  		},
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
			let isFirstZoom = true;
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
				})
				// 圖臺縮放時觸發GA自訂事件
				.on("zoomend",() => {
					if (isFirstZoom) {
						isFirstZoom = false;
					} else {
						gtag('event','map_actions', {
							action_type: "地圖縮放",
							time: Date.now(),
  						});
					}
				});
			this.renderMarkers();

			// 使用者點擊定位功能後觸發GA自訂事件
			geoLocate.on('geolocate', () => {
  				gtag('event','map_actions', {
					action_type: "所在位置定位",
					time: Date.now(),
  				})
			});

			return geoLocate;
		},
		// 2. Adds three basic layers to the map (Taipei District, Taipei Village labels, and Taipei 3D Buildings)
		// Due to performance concerns, Taipei 3D Buildings won't be added in the mobile version
		initializeBasicLayers() {
			const authStore = useAuthStore();
			if (!this.map) return;
			// metroTaipei District Labels
			fetch(`/mapData/metrotaipei_town.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("metrotaipei_town_label", {
							type: "geojson",
							data: data,
						})
						.addLayer(metroTaipeiTown);
				});
			// metroTaipei Village Labels
			fetch(`/mapData/metrotaipei_village.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("metrotaipei_village_label", {
							type: "geojson",
							data: data,
						})
						.addLayer(metroTaipeiVillage);
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
				.addSource(`metrotaipei_village`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:metrotaipei_village@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(metroTpVillage);
			this.map
				.addSource(`metrotaipei_town`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:metrotaipei_town@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(metroTpDistrict);

			this.addSymbolSources();
		},
		// 3. Adds symbols that will be used by some map layers
		async addSymbolSources() {
			const images = [
				"metro",
				"triangle_green",
				"triangle_white",
				"bike_green",
				"bike_orange",
				"bike_red",
				"cctv",
				"live",
				"youbike_elec"
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
			// 3D Mrt Map (202511NEW)
			// 預載 3D 模型
			const models = [
        		{ id: "mrt_car_c381", url: "/images/map/mrt_car_c381.glb" },
        		{ id: "mrt_car_c370", url: "/images/map/mrt_car_c370.glb" },
				// { id: "mrt_car_brown", url: "/images/map/mrt_car_brown.glb" },
    		];

			const loadModel = (m) => {
        		return new Promise((resolve, reject) => {
					const loader = new GLTFLoader();
            		loader.load(
                		m.url,
                		(gltf) => {
                    		this.preloadedModels[m.id] = markRaw(gltf.scene);
                    		resolve();
                		},
                		undefined,
                		(err) => {
                    		console.error(`3D 模型 ${m.id} 載入失敗:`, err);
                    		reject(err);
                		}
            		);
        		});
    		};

    		// 等待所有 3D 模型載入完成
    		await Promise.all(models.map(loadModel));

    		// 全部載入完畢才變 false
    		this.isPreloading = false;
		},
		// 4. Toggle district boundaries
		toggleDistrictBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"metrotaipei_town",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("metrotaipei_town", "visibility", "none");
			}
			// if (status) {
			// 	this.map.setLayoutProperty(
			// 		"tp_district",
			// 		"visibility",
			// 		"visible"
			// 	);
			// } else {
			// 	this.map.setLayoutProperty("tp_district", "visibility", "none");
			// }
		},
		// 5. Toggle village boundaries
		toggleVillageBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"metrotaipei_village",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("metrotaipei_village", "visibility", "none");
			}
			// if (status) {
			// 	this.map.setLayoutProperty(
			// 		"tp_village",
			// 		"visibility",
			// 		"visible"
			// 	);
			// } else {
			// 	this.map.setLayoutProperty("tp_village", "visibility", "none");
			// }
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
				let mapLayerId = `${element.index}-${element.type}-${element.city}`;
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
			// 3D Mrt Map (202511NEW)
			if (!["voronoi", "isoline"].includes(map_config.type) && map_config.type!=='symbol-3d') {
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
			// 3D Mrt Map (202511NEW)
			if (["arc", "voronoi", "isoline","symbol-3d"].includes(map_config.type)) {
				let res = {}
				let res2 = {}
				let res3 = {}
				if (map_config.type === "symbol-3d") {
					res = await axios.get(`${location.origin}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${map_config.index}&maxFeatures=1000000&outputFormat=application%2Fjson`);
					res2 = await axios.get(`/mapData/${map_config.index}_route.geojson`)
					if (map_config.index === 'metro_o_line_car' || map_config.index === 'metro_g_line_car' || map_config.index === 'metro_r_line_car' ) {
						res3 = await axios.get(`/mapData/${map_config.index}_route_2.geojson`)
					}
				} else {
					res = await axios.get(
						`${location.origin}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${map_config.index}&maxFeatures=1000000&outputFormat=application%2Fjson`
					);
				}

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
				} else if (map_config.type === "symbol-3d") {
					this.Add3dMapLayer(map_config, res.data,res2.data, res3?.data);
				}
			} else {
				try {
					// 添加源
					this.map.addSource(`${map_config.layerId}-source`, {
						type: "vector",
						scheme: "tms",
						tolerance: 0,
						tiles: [
							`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:${map_config.index}@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
						],
					});
		
					// 監聽錯誤
					this.map.on('error', (e) => {
						if (e.sourceId === `${map_config.layerId}-source`) {
							console.error('Source error:', e);

							// 清理已添加的源（如果存在）
							if (this.map.getSource(`${map_config.layerId}-source`)) {
								this.map.removeSource(`${map_config.layerId}-source`);
							}
							// 從 loadingLayers 中移除
							this.loadingLayers = this.loadingLayers.filter(
								(el) => el !== map_config.layerId
							);
						}
					});
		
					// 監聽源加載完成
					const sourceLoaded = new Promise((resolve, reject) => {
						const checkSource = (e) => {
							if (e.sourceId === `${map_config.layerId}-source`) {
								if (e.isSourceLoaded) {
									this.map.off('sourcedata', checkSource);
									resolve();
								}
								// 如果有錯誤也需要處理
								if (e.error) {
									this.map.off('sourcedata', checkSource);
									reject(e.error);
								}
							}
						};
						
						this.map.on('sourcedata', checkSource);
						
						// 設置超時
						setTimeout(() => {
							this.map.off('sourcedata', checkSource);
							reject(new Error('Source load timeout'));
						}, 10000);
					});
		
					// 等待源加載完成後添加圖層
					await sourceLoaded;
					this.addMapLayer(map_config);


		
				} catch (error) {
					console.error('Failed to add source:', error);
					// 清理已添加的源（如果存在）
					if (this.map.getSource(`${map_config.layerId}-source`)) {
						this.map.removeSource(`${map_config.layerId}-source`);
					}
					// 從 loadingLayers 中移除
					this.loadingLayers = this.loadingLayers.filter(
						(el) => el !== map_config.layerId
					);
				}
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
			const filterClass = [
				["6h150r", "6h250r", "6h350r"],
				["12h200r", "12h300r", "12h400r"],
				["24h200r", "24h350r", "24h500r", "24h650r"]
			  ];
			  
			  // 初始 filter 設定為第一組 (6 小時降雨)
			  const initialFilter = [
				"in",
				"hazard_class",
				...filterClass[0]
			  ];
			  const config = {
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
				source: `${map_config.layerId}-source`
			}
			if (map_config.layerId === 'wee_hazard_water-fill-extrusion-metrotaipei' || map_config.layerId === 'wee_hazard_water_tp-fill-extrusion-taipei') {
				config.filter = initialFilter
			}
			this.map.addLayer(config);
			if (map_config.layerId === 'wee_hazard_water-fill-extrusion-metrotaipei' || map_config.layerId === 'wee_hazard_water_tp-fill-extrusion-taipei') this.animateFilter(map_config.layerId);
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			// 3D Mrt Map (202511NEW) 
			if (!this.currentVisibleLayers.includes(map_config.layerId)) {
				this.currentVisibleLayers.push(map_config.layerId);
			}
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId
			);
		},
		animateFilter(mapLayerId) {
			this.stopAnimation();
			const filterClass = [
				["6h150r", "6h250r", "6h350r"],
				["12h200r", "12h300r", "12h400r"],
				["24h200r", "24h350r", "24h500r", "24h650r"]
			];
		
			let index = 1;
		
			this.waitUntilReady = setInterval(() => {
				if (this.loadingLayers.length !== 0) return;
		
				clearInterval(this.waitUntilReady); // 停止等待
				this.waitUntilReady = null;
		
				// 啟動動畫
				this.filterInterval = setInterval(() => {
					const currentFilter = [
						"in",
						"hazard_class",
						...filterClass[index]
					];
		
					this.map.setFilter(mapLayerId, currentFilter);
					index = (index + 1) % filterClass.length;
				}, 1000);
			}, 200);
		},
		stopAnimation() {
			if (this.filterInterval) {
				clearInterval(this.filterInterval);
				this.filterInterval = null;
			}
			if (this.waitUntilReady) {
				clearInterval(this.waitUntilReady);
				this.waitUntilReady = null;
			}
		},
		// 4-2-1. Add Map Layer for Arc Maps
		// Developed by Weeee Chill, Taipei Codefest 2024
		AddArcMapLayer(map_config, data) {
			// start loading
			this.loadingLayers.push("rendering");
			const mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
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

			let lngStart = 121.3;
			let lngEnd = 122;
			let latStart = 24.8;
			let latEnd = 25.3;

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
		// 4-5. Create 3DMap for mrtp 202511月新開發
    	Add3dMapLayer(map_config, data, data2, data3) {
    		// 3D 動態圖載入前設定
    		this.loadingLayers.push("rendering");
    		this.currentLayers.push(map_config.layerId);
    		this.mapConfigs[map_config.layerId] = map_config;

			const layerId = map_config.layerId

			// 紀錄資料更新時間
			this.layerUpdateTime[layerId] = new Date()

    		// 注意重複加入Id
    		if (!this.currentVisibleLayers.includes(map_config.layerId)) {
        		this.currentVisibleLayers.push(map_config.layerId);
    		}

    		// 組成渲染所須的列車資料

    		// 須注意的支線特例
    		const branchLineStations = ["蘆洲", "三民高中", "徐匯中學", "三和國中", "三重國小","小碧潭","新北投"]

    		// 建立 mrtCarsInit
    		const mrtCarsInit = data.features.map((item, i) => {

        		let routeCoordinates = null

        		if (branchLineStations.includes(item.properties.curr_stationname) || branchLineStations.includes(item.properties.next_stationname)) {
            		routeCoordinates = cutRouteSegment(data3, [
                    	item.properties.curr_lon,
                    	item.properties.curr_lat
                	],
                	[
                    	item.properties.next_lon,
                    	item.properties.next_lat
                	]);
        		} else {
            		routeCoordinates = cutRouteSegment(data2, [
                    	item.properties.curr_lon,
                    	item.properties.curr_lat
                	],
                	[
                    	item.properties.next_lon,
                    	item.properties.next_lat
                	]);
       			}

        		const coords = routeCoordinates.geometry.coordinates.map(c => [c[0], c[1], 0]);

        		return {
            		id: i,
					route_id: map_config.layerId,
					...item.properties,
           			coords,
            		car_icon: map_config.icon,
            		final_coord: interpolateAlongSegment(coords, 1),
            		progress: 0,
            		speed: 0.00222,
        		};
    		});

    		// 整併 prevMrtCars
    		let mrtCars = [];
			// 把不同路線的舊資料保存起來
			let updatePrevCar = [];

    		if (this.prevMrtCars.length > 0) {
        		// 建立 Map 加速查找
        		const initTrainMap = new Map(
            		mrtCarsInit.map(car => [car.trainnumber, car])
        		);
				// 先確認上一輪有的車
        		this.prevMrtCars.forEach(prevCar => {

					// 先確認新來的資料是不是同一路線
					if(prevCar.route_id !== mrtCarsInit[0].route_id) {
						updatePrevCar.push(prevCar);
						return;
					}

            		const newCar = initTrainMap.get(prevCar.trainnumber);

            		// 同路線新資料沒有該車 → 跳過
					if (!newCar) return;

            		// 判斷車子是否進站（curr_stationname 有無變）
            		const stationChanged = prevCar.curr_stationid !== newCar.curr_stationid;

            		if (stationChanged) {
                		// 用舊 final_coord 當作起點，切新路線到新 curr_station
                		const start = prevCar.final_coord;
                		const end = [
                    		newCar.curr_lon,
                    		newCar.curr_lat
                		];


               			let routeCoordinates = null

                		if (branchLineStations.includes(newCar.curr_stationname) || branchLineStations.includes(newCar.next_stationname)) {
                    		routeCoordinates = cutRouteSegment(data3, start, end);
                		} else {
                    		routeCoordinates = cutRouteSegment(data2, start, end);
                		}

                		const coords = routeCoordinates.geometry.coordinates.map(c => [c[0], c[1], 0]);

                		// 更新新車物件
                		newCar.coords = coords;
                		newCar.final_coord = interpolateAlongSegment(coords, 1);

                		// progress 重置
                		newCar.progress = 0;
                		newCar.dataChanged = true;

           			} else {
                		// curr_station 沒變 → 保留舊狀態
                		newCar.coords = prevCar.coords;
                		newCar.final_coord = prevCar.final_coord;
                		newCar.progress = 0.99;
                		newCar.dataChanged = false;
            		}
					// 把新資料有找到的車推去待跑動畫列車陣列
					mrtCars.push(newCar);
        		});

				// 新資料出現的車
				for (const [trainNumber, car] of initTrainMap) {
    				const existed = this.prevMrtCars.some(prev => prev.trainnumber === trainNumber);
    				if (existed) continue; // 已存在 → 不處理
    				const { coords } = car;

    				if (!coords || coords.length === 0) {
        				car.coords = [];
        				car.final_coord = null;
        				car.progress = 0;
        				continue;
    				}

   					if (coords.length === 1) {
        				const c = coords[0];
        				car.coords = [c];
        				car.final_coord = [c[0], c[1], c[2] ?? 0];
        				car.progress = 0;
        				continue;
    				}

    				const ratio = 90 / 100;
    				const finalCoord = interpolateAlongSegment(coords, ratio); // 插值後 2/3 的點

    				// 切出 2/3 的前段 coords
    				const trimmed = [];
    				trimmed.push(coords[0]);

    				let total = 0;
    				const segLens = [];
    				for (let i = 0; i < coords.length - 1; i++) {
        				const dx = coords[i + 1][0] - coords[i][0];
        				const dy = coords[i + 1][1] - coords[i][1];
        				const dz = (coords[i + 1][2] || 0) - (coords[i][2] || 0);
        				const len = Math.sqrt(dx*dx + dy*dy + dz*dz);
        				total += len;
        				segLens.push(len);
    				}

    				const targetDist = total * ratio;
    				let accum = 0;

    				for (let i = 0; i < segLens.length; i++) {
        				if (accum + segLens[i] < targetDist) {
            				trimmed.push(coords[i + 1]);
            				accum += segLens[i];
        				} else {
            				trimmed.push(finalCoord);
            				break;
        				}
    				}

    				car.coords = trimmed;
    				car.final_coord = finalCoord;
    				car.progress = 0;

					// 把新資料出現的車推去待跑動畫列車陣列
					mrtCars.push(car);
				}
    		} else {
				// 如果是第一次開組件則執行初始化
        		mrtCars = mrtCarsInit.map((item) => {
  					const { coords } = item || {};

  					// 無座標 -> 返回空 coords 且 final_coord 為 null
  					if (!coords || coords.length === 0) {
    					return {
      						...item,
      						coords: [],
      						final_coord: null,
      						progress: 0
    					};
  					}

  					// 只有一個點 -> 2/3 仍然是該點本身
  					if (coords.length === 1) {
    					const only = coords[0];
    					return {
      						...item,
      						coords: [only],
      						final_coord: [only[0], only[1], only[2] ?? 0],
      						progress: 0
    					};
  					}

  					// 兩點或以上 -> 正常按距離計算 2/3 並切出前段 coords（含插值點）
  					const ratio = 90 / 100;
  					const finalCoord = interpolateAlongSegment(coords, ratio); // [lng, lat, z]

  					// 計算每段長度以取得 trimmedCoords
  					const segLens = [];
  					let totalLength = 0;
  					for (let i = 0; i < coords.length - 1; i++) {
    					const dx = coords[i + 1][0] - coords[i][0];
    					const dy = coords[i + 1][1] - coords[i][1];
    					const dz = (coords[i + 1][2] || 0) - (coords[i][2] || 0);
    					const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
    					segLens.push(len);
    					totalLength += len;
  					}

  					const targetDist = totalLength * ratio;
  					const trimmedCoords = [];
  					trimmedCoords.push(coords[0]);

  					let accum = 0;
  					for (let i = 0; i < segLens.length; i++) {
    					if (accum + segLens[i] < targetDist) {
      						trimmedCoords.push(coords[i + 1]);
      						accum += segLens[i];
    					} else {
      					// 2/3 落在這段 -> 補上精準的插值點（finalCoord）然後中斷
      						trimmedCoords.push(finalCoord);
     						break;
    					}
  					}

  					return {
    					...item,
    					coords: trimmedCoords,
    					final_coord: finalCoord,
    					progress: 0
  					};
				});
    		}

    		if (mrtCars.length === 0) {
        		console.error('待跑動畫列車資料為空，請確認!');
        		return;
    		}

    		this.prevMrtCars = [...updatePrevCar,...mrtCars];

    		// === 自訂 3D 圖層 ===
			
    		const customLayer = {
        		id: map_config.layerId,
        		type: "custom",
        		renderingMode: "3d",
        		onAdd: (map, gl) => {
            		customLayer.map = markRaw(map);
            		customLayer.camera = markRaw(new THREE.Camera());
            		customLayer.scene = markRaw(new THREE.Scene());
					customLayer.lastUpdateTime = 0; // 節流用

            		// 環境光
            		const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 3.2);
					hemiLight.position.set(0, 20, 0);
					customLayer.scene.add(hemiLight);

            		// 預載列車模型
            		for (const car of mrtCars) {
                		if (!car.model) {
                    		const carIcon = car.car_icon;
                    		const preModel = this.preloadedModels[carIcon];

                    		if (preModel) {
                        		const modelClone = preModel.clone(true);
								modelClone.traverse((child) => {
    								if (child.isMesh) {
        								child.material = child.material.clone();
    								}
								});
                        		const horizontalOffset = -30;
                        		modelClone.position.x += horizontalOffset;
                        		car.model = modelClone;
                        		customLayer.scene.add(modelClone);
                    		} else {
                        		console.warn(`⚠️ 3D 模型尚未預載完成: ${carIcon}`);
                    		}
                		}
            		}

            		customLayer.renderer = markRaw(
                		new THREE.WebGLRenderer({
                    		canvas: map.getCanvas(),
                    		context: gl,
                    		antialias: true,
               			})
            		);
            		customLayer.renderer.autoClear = false;

					// 加入 2D 圓圈資料
					const sourceId = `mrt-2d-source-${map_config.layerId}`;
    				const layerId = `mrt-2d-circles-${map_config.layerId}`;

					// 各捷運路線對應圓圈顏色
					const circleColor = {
						'metro_br_line_car':'#C48C31',
						'metro_bl_line_car':'#0070BD',
						'metro_g_line_car':'#038258',
						'metro_o_line_car':'#F5B41C',
						'metro_r_line_car':'#E1002C',
					}

					if (!map.getSource(sourceId)) {
        				map.addSource(sourceId, {
            				type: "geojson",
            				data: {
                				type: "FeatureCollection",
                				features: []
            				}
        				});
        
        				map.addLayer({
            				id: layerId,
            				type: "circle",
            				source: sourceId,
            				paint: {
                				"circle-radius": 10,
                				"circle-color": circleColor[map_config.index],
                				"circle-stroke-width": 2,
                				"circle-stroke-color": "#FFFFFF",
                				"circle-opacity": 0.8
            				}
        				});
    				}

					// 儲存 sourceId 和 layerId 供 render 和 onRemove 使用
    				customLayer.sourceId = sourceId;
    				customLayer.layerId2D = layerId;

            		// === Tooltip 只建一次 ===
            		if (!customLayer.carTooltip) {
						// popup 最外層
                		customLayer.carTooltip = document.createElement("div");
                		customLayer.carTooltip.style.position = "absolute";
                		customLayer.carTooltip.style.left = 0;
                		customLayer.carTooltip.style.top = 0;
						customLayer.carTooltip.style.minWidth = '120px';
						customLayer.carTooltip.style.maxHeight = "220px";
						customLayer.carTooltip.style.height = "100%";
                		customLayer.carTooltip.style.willChange = "transform";
                		customLayer.carTooltip.style.background = "#282A2C";
                		customLayer.carTooltip.style.border = "2px solid #817E79";
                		customLayer.carTooltip.style.color = "#fff";
                		customLayer.carTooltip.style.padding = "6px 10px";
                		customLayer.carTooltip.style.borderRadius = "6px";
                		customLayer.carTooltip.style.pointerEvents = "auto";
                		customLayer.carTooltip.style.display = "none";
                		customLayer.carTooltip.style.zIndex = "1";
                		customLayer.carTooltip.style.overflow = "hidden";
               			customLayer.tooltipOffsetX = 5;
                		customLayer.tooltipOffsetY = 5;

                		// popup 關閉按鈕
                		const closeBtn = document.createElement("button");
                		closeBtn.innerText = "×";
                		closeBtn.style.position = "absolute";
                		closeBtn.style.top = "1px";
                		closeBtn.style.right = "8px";
                		closeBtn.style.background = "transparent";
                		closeBtn.style.border = "none";
                		closeBtn.style.color = "#888787";
                		closeBtn.style.cursor = "pointer";
                		closeBtn.style.fontWeight = "bold";
                		closeBtn.style.fontSize = "20px";
                		closeBtn.onclick = () => {
                    		customLayer.carTooltip.style.display = "none";
                    		customLayer.selectedCar = null;
                		};
                		customLayer.carTooltip.appendChild(closeBtn);

						// popup 顯示屬性區塊
						const contentWrapper = document.createElement("div");
						contentWrapper.style.paddingRight = "12px";
						contentWrapper.style.height = "100%";
						contentWrapper.style.overflowY = "auto";

						customLayer.carTooltip.appendChild(closeBtn);
						customLayer.carTooltip.appendChild(contentWrapper);
						customLayer.tooltipContent = contentWrapper;
						map.getContainer().appendChild(customLayer.carTooltip);
           	 		}

            		// === Click 事件只綁一次 ===
            		if (customLayer._carClickHandler) {
                		map.off("click", customLayer._carClickHandler);
            		}
            		customLayer._carClickHandler = (e) => {
                		const clickLngLat = [e.lngLat.lng, e.lngLat.lat];
                		let closestCar = null;
                		let minDist = Infinity;

						// 根據 zoom 等級調整點擊範圍
    					const zoom = customLayer.map.getZoom();
    					let clickRadius = 45; // 預設值
    
    					if (zoom < 11) {
        					clickRadius = 120;  // zoom < 11 時範圍較大
    					} else if (zoom < 13) {
        					clickRadius = 90;
    					} else {
        					clickRadius = 45;
    					}

                		for (const car of mrtCars) {
                    		if (!car.currentLngLat || !car.lastDir) continue;

                    		const offsetMeters = 30;
                    		const norm = Math.sqrt(car.lastDir.x ** 2 + car.lastDir.y ** 2);
                    		const dx = (car.lastDir.y / norm) * offsetMeters;
                    		const dy = (-car.lastDir.x / norm) * offsetMeters;
                    		const offsetCarPos = [car.currentLngLat[0] + dx * 0.00001, car.currentLngLat[1] + dy * 0.00001];

                    		const dist = distance(
                        		point(clickLngLat),
                        		point(offsetCarPos), {
                            		units: "meters"
                        		}
                    		);

                    		if (dist < clickRadius && dist < minDist) {
                        		minDist = dist;
                        		closestCar = car;
                    		}
                		}

                		if (!closestCar) return;

               			customLayer.selectedCar = closestCar;

                		// 清空 tooltip 內容
						customLayer.tooltipContent.innerHTML = "";

                		const getCrowdColor = (level) => {
                    		switch (level) {
                        		case '1':
                            		return "🟩";
                        		case '2':
                            		return "🟨";
                        		case '3':
                            		return "🟧";
                        		case '4':
                            		return "🟥";
                        		default:
                            		return "⬜";
                    		}
                		};

                		const infoContainer = document.createElement("div");
						const fields = map_config.property.map(prop => ({
    						label: prop.name,
    						value: prop.name.includes('擁擠度') 
        						? getCrowdColor(closestCar[prop.key]) 
        						: closestCar[prop.key] || ''
						}));

                		fields.forEach(f => {
                    		const row = document.createElement("div");
                    		row.style.marginBottom = "2px";
                    		row.textContent = `${f.label}: ${f.value ?? "-"}`;
                    		infoContainer.appendChild(row);
                		});

                		customLayer.carTooltip.insertBefore(infoContainer);
                		customLayer.carTooltip.style.display = "block";
            		};
            		map.on("click", customLayer._carClickHandler);
        		},

				onRemove(map) {
					// 清理 tooltip
    				if (customLayer.carTooltip) {
        				customLayer.carTooltip.remove();
        				customLayer.carTooltip = null;
    				}

					// 清理 click 事件
    				if (customLayer._carClickHandler) {
        				map.off("click", customLayer._carClickHandler);
        				customLayer._carClickHandler = null;
    				}

					// 用 sourceId 和 layerId 清理該路線的 2D 圖層
    				if (customLayer.layerId2D && map.getLayer(customLayer.layerId2D)) {
        				map.removeLayer(customLayer.layerId2D);
    				}

    				if (customLayer.sourceId && map.getSource(customLayer.sourceId)) {
        				map.removeSource(customLayer.sourceId);
    				}

					// 清理 3D 模型
    				if (customLayer.scene && mrtCars?.length) {
        				for (const car of mrtCars) {
            				if (car.model) {
                				car.model.traverse(child => {
                    				if (child.isMesh) {
                        				// 釋放 geometry
                        				if (child.geometry) child.geometry.dispose();

                        				// 釋放材質和貼圖
                        				if (child.material) {
                            				const disposeMaterial = mat => {
                                				if (mat.map) mat.map.dispose();
                                				if (mat.normalMap) mat.normalMap.dispose();
                                				if (mat.roughnessMap) mat.roughnessMap.dispose();
                                				if (mat.metalnessMap) mat.metalnessMap.dispose();
                                				mat.dispose();
                            				};

                            				if (Array.isArray(child.material)) {
                                				child.material.forEach(disposeMaterial);
                            				} else {
                                				disposeMaterial(child.material);
                            				}
                        				}
                    				}
                				});

                				// 從 scene 移除
                				customLayer.scene.remove(car.model);
                				car.model = null;
            				}
        				}

        				// 清空 mrtCars 陣列，避免舊引用被再次使用
        				mrtCars.length = 0;
    				}

    				// 清理 scene / camera
    				if (customLayer.scene) {
        				// 移除剩餘 children
        				while (customLayer.scene.children.length) {
            				customLayer.scene.remove(customLayer.scene.children[0]);
        				}
    				}
    				customLayer.scene = null;
    				customLayer.camera = null;

					// 清理 selectedCar
    				customLayer.selectedCar = null;
				},

        		render: (gl, matrix) => {
					// 取得當下的 zoom
					const zoom = customLayer.map.getZoom();
					const now = performance.now();

					let allFinished = true;
					// 確認當下各列車是否都跑完動畫
    				for (const car of mrtCars) {
        				if (car.progress < 1) allFinished = false;
    				}

					if (zoom < 13) {
        				// 2D 模式
        				for (const car of mrtCars) if (car.model) car.model.visible = false;
        				if (!allFinished) {
            				if (now - customLayer.lastUpdateTime >= 200) {

                				const features = updateCarsPosition(mrtCars);
                				customLayer.map.getSource(customLayer.sourceId).setData({
                    				type: "FeatureCollection",
                    				features
                				});
                				customLayer.lastUpdateTime = now;
            				}
        				} else if (allFinished && !customLayer.updated2D) {
							const features = updateCarsPosition(mrtCars);
    						customLayer.map.getSource(customLayer.sourceId).setData({
        						type: "FeatureCollection",
        						features
    						});
    						customLayer.updated2D = true; // 標記已經更新過一次
						}

        				// 更新 2D tooltip
        				if (customLayer.selectedCar?.currentLngLat && customLayer.selectedCar?.lastDir) {
            				const dir = customLayer.selectedCar.lastDir;
            				const pos = customLayer.selectedCar.currentLngLat;
            				const side = new THREE.Vector3(-dir.y, dir.x, 0).normalize();
            				const offsetMeters = -30;
            				const lngOffset = side.x * offsetMeters * 0.00001;
            				const latOffset = side.y * offsetMeters * 0.00001;
           				 	const offsetLngLat = [pos[0] + lngOffset, pos[1] + latOffset];
            				const screenPos = customLayer.map.project(offsetLngLat);
            				customLayer.carTooltip.style.transform =
                				`translate(${screenPos.x + customLayer.tooltipOffsetX}px, ${screenPos.y + customLayer.tooltipOffsetY}px)`;
        				}

        				// 顯示 2D layer
        				if (customLayer.map.getLayoutProperty(customLayer.layerId2D, "visibility") !== "visible") {
            				customLayer.map.setLayoutProperty(customLayer.layerId2D, "visibility", "visible");
        				}
    				} else {
						// 3D 模式
						for (const car of mrtCars) if (car.model) car.model.visible = true;

						// 隱藏 2D layer
        				if (customLayer.map.getLayoutProperty(customLayer.layerId2D, "visibility") === "visible") {
            				customLayer.map.setLayoutProperty(customLayer.layerId2D, "visibility", "none");
        				}

						const scene = customLayer.scene;
        				const camera = customLayer.camera;
        				const renderer = customLayer.renderer;
						const rotationX = new THREE.Matrix4().makeRotationAxis(new THREE.Vector3(1, 0, 0), Math.PI / 2);

						if (now - customLayer.lastUpdateTime >= 200) {
							updateCarsPosition(mrtCars);
							customLayer.lastUpdateTime = now;
						}

						for (const car of mrtCars) {
           					// updateCarsPosition([car]); // 單台車也用同一個計算

            				const pos = car.currentLngLat;
            				const dir = car.lastDir;

            				const merc = mapboxgl.MercatorCoordinate.fromLngLat(pos, pos[2]);
           					const scale = merc.meterInMercatorCoordinateUnits() * 1.25;
            				const fromDir = new THREE.Vector3(1, 0, 0);

            				const quaternion = new THREE.Quaternion().setFromUnitVectors(fromDir, dir);
            				const extraRot = new THREE.Matrix4().makeRotationZ(Math.PI / 2);
            				const rotationMatrix = new THREE.Matrix4().makeRotationFromQuaternion(quaternion).multiply(extraRot);

            				const translation = new THREE.Matrix4().makeTranslation(merc.x, merc.y, merc.z);
            				const scaleMatrix = new THREE.Matrix4().makeScale(scale, -scale, scale);

            				const modelMatrix = new THREE.Matrix4()
                				.multiply(translation)
                				.multiply(scaleMatrix)
                				.multiply(rotationMatrix)
                				.multiply(rotationX);

            				camera.projectionMatrix = new THREE.Matrix4().fromArray(matrix).multiply(modelMatrix);

            				renderer.resetState();
            				renderer.render(scene, camera);

            				// 更新 tooltip
            				if (customLayer.selectedCar?.currentLngLat && customLayer.selectedCar?.lastDir) {
                				const dir = customLayer.selectedCar.lastDir;
                				const pos = customLayer.selectedCar.currentLngLat;
                				const side = new THREE.Vector3(-dir.y, dir.x, 0).normalize();
                				const offsetMeters = -30;
                				const lngOffset = side.x * offsetMeters * 0.00001;
                				const latOffset = side.y * offsetMeters * 0.00001;
                				const offsetLngLat = [pos[0] + lngOffset, pos[1] + latOffset];
                				const screenPos = customLayer.map.project(offsetLngLat);
                				customLayer.carTooltip.style.transform =
                    				`translate(${screenPos.x + customLayer.tooltipOffsetX}px, ${screenPos.y + customLayer.tooltipOffsetY}px)`;
            				}
        				}
					}
            		// 下一幀
            		customLayer.map.triggerRepaint();
        		},
    		};

			if (!this.customLayers) this.customLayers = {};
			this.customLayers[map_config.layerId] = customLayer;

    		// === 加入圖層 ===
    		this.map.addLayer(customLayer);

    		// loading 結束
    		this.loadingLayers = this.loadingLayers.filter((el) => el !== map_config.layerId);
    		return;
		},
		//  5. Turn on the visibility for a exisiting map layer
		turnOnMapLayerVisibility(mapLayerId) {
			if (mapLayerId.indexOf("-arc") !== -1) {
				this.deckGlLayer[mapLayerId].config.visible = true;
				this.step = 1;
				this.currentVisibleLayers.push(mapLayerId);
				this.renderDeckGLLayer();
			} else {
				if (mapLayerId === 'wee_hazard_water-fill-extrusion-metrotaipei' || mapLayerId === 'wee_hazard_water_tp-fill-extrusion-taipei') {
					const filterClass = [
						["6h150r", "6h250r", "6h350r"],
						["12h200r", "12h300r", "12h400r"],
						["24h200r", "24h350r", "24h500r", "24h650r"]
					  ];
					  
					  // 初始 filter 設定為第一組 (6 小時降雨)
					  const initialFilter = [
						"in",
						"hazard_class",
						...filterClass[0]
					  ];
					  this.map.setFilter(mapLayerId, initialFilter);
					this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
					this.animateFilter(mapLayerId);

				} else {
					this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
				}
			}
		},
		// 6. Turn off the visibility of an exisiting map layer but don't remove it completely
		// 3D Mrt Map (202511NEW)
		turnOffMapLayerVisibility(map_config) {
			this.stopAnimation();
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}-${element.city}`;
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

			// 如果3D捷運地圖 popup 存在把它清除
			// 關閉 popup + reset
			map_config.forEach((item)=>{
				const customLayer = this.customLayers[`${item.index}-${item.type}-${item.city}`];
				if (customLayer?.carTooltip) {
    				customLayer.carTooltip.style.display = "none";
    				customLayer.selectedCar = null;
				}
				if (customLayer?.layerId2D && this.map.getLayer(customLayer.layerId2D)) {
    				customLayer.map.setLayoutProperty(customLayer.layerId2D, "visibility", "none");
				}
			})
		},

		/* Popup Related Functions */
		// 1. Adds a popup when the user clicks on a item. The event will be passed in.
		addPopup(event) {
			const formatValue = (value, key) => {
				if (key === 'occupied_rate') {
					return value === -99 ? '-' : value;
				}
				return value;
			};

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

				// format properties
				const feature = {...clickFeatureDatas[i]};
				feature.properties = {...feature.properties};
				Object.keys(feature.properties).forEach(key => {
					feature.properties[key] = formatValue(feature.properties[key], key);
				});

				previousParsedLayer = clickFeatureDatas[i].layer.id;
				mapConfigs.push(this.mapConfigs[clickFeatureDatas[i].layer.id]);
				parsedPopupContent.push(feature);
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
					const hls = ref(null)
					const activeTab = ref(0)
					const videoRef = ref(null)

					const isHlsUrl = (url) => {
						return url && (url.includes('.m3u8') || url.includes('hls'))
					}

					const initHlsPlayer = (videoElement, src) => {
						
						if (Hls.isSupported()) {
							const hlsInstance = new Hls()
							
							// 添加錯誤監聽
							hlsInstance.on(Hls.Events.ERROR, (event, data) => {
								if (data.fatal) {
									hlsInstance.destroy();
								}
							})
							
							hlsInstance.loadSource(src)
							hlsInstance.attachMedia(videoElement)
							return hlsInstance
						} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
							videoElement.src = src
							return null
						}
						
						return null
					}

					const handleVideoLoad = () => {
						const activeTabValue = activeTab.value
						let videoElement = videoRef.value
						
						// 如果 videoRef 是數組，取第一個元素
						if (Array.isArray(videoElement)) {
							videoElement = videoElement[0]
						}
						
						if (!videoElement || !parsedPopupContent[activeTabValue]) {
							return;
						}
						
						// 找到 video 模式的 property
						const videoProperty = mapConfigs[activeTabValue].property.find(item => item.mode === 'video')
						if (!videoProperty) {
							return;
						}
						
						const videoUrl = parsedPopupContent[activeTabValue].properties[videoProperty.key]
						if (!videoUrl) {
							return;
						}
						
						// 如果是 HLS URL，使用 HLS 播放器
						if (isHlsUrl(videoUrl)) {
							if (hls.value) {
								hls.value.destroy()
							}
							hls.value = initHlsPlayer(videoElement, videoUrl)
						} else {
							videoElement.src = videoUrl
						}
					}

					// 初始化影像
					nextTick(() => {
						handleVideoLoad()
					})

					// 監聽 activeTab 變化，重新載入影片
					watch(activeTab, () => {
						nextTick(() => {
							handleVideoLoad()
						})
					})

					// Only show the data of the topmost layer
					return {
						popupContent: parsedPopupContent,
						mapConfigs: mapConfigs,
						activeTab,
						videoRef,
					};
				},
			});
			// This helps vue determine the most optimal time to mount the component
			nextTick(() => {
				const app = createApp(PopupComponent);
				app.mount("#vue-popup-content");
			});

			// 使用者點擊圖徵時觸發GA自訂事件
			if (mapConfigs[0].city && mapConfigs[0].title && mapConfigs[0].source && mapConfigs[0].type) {
				gtag("event", "popular_feature_click", {
					dashboard_city: mapConfigs[0].city,
					layer_name: mapConfigs[0].title,
					city_layer: `${mapConfigs[0].city}-${mapConfigs[0].title}`,
					data_type: mapConfigs[0].source,
					feature_type: mapConfigs[0].type,
					time: Date.now(),
				});
			}
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
		// 4. Update the zoom and center of the map
		updateMapViewForCity(city) {
			this.map.setZoom(CityMapView[city].zoom);
			this.map.setCenter(CityMapView[city].center);
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
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
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
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
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
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
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
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
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
