<template>
  <div class="wind-engine-root">
    <div class="console">
      <h2>3D 都市風道診斷</h2>

      <!-- 氣象站實測風向開關 -->
      <div class="slider-group">
        <label style="display: flex; align-items: center; cursor: pointer">
          <input
            v-model="useStationData"
            type="checkbox"
            style="width: 16px; height: 16px; margin-right: 8px"
          >
          <span>使用氣象站實測風向</span>
        </label>
      </div>

      <!-- 風向控制 -->
      <div
        class="slider-group"
        :class="{ disabled: useStationData }"
      >
        <label>風向: <span class="val">{{ useStationData ? '站點插值' : windDir + '°' }}</span></label>
        <input
          v-model.number="windDir"
          type="range"
          min="0"
          max="360"
          :disabled="useStationData"
        >
      </div>

      <!-- 風速控制 -->
      <div class="slider-group">
        <label>風速:
          <span class="val">{{ windSpeed.toFixed(1) }}x</span></label>
        <input
          v-model.number="windSpeed"
          type="range"
          min="1"
          max="10"
          step="0.1"
        >
      </div>

      <!-- 新增：土地分區切換（移到 console 內部） -->
      <div class="slider-group zone-switch">
        <label
          style="display: flex; align-items: center; cursor: pointer"
        >
          <input
            v-model="showZones"
            type="checkbox"
            style="width: 16px; height: 16px; margin-right: 8px"
            @change="toggleLayer('zone')"
          >
          <span>雙北土地使用分區</span>
        </label>

        <label
          style="display: flex; align-items: center; cursor: pointer"
        >
          <input
            v-model="showGreen"
            type="checkbox"
            style="width: 16px; height: 16px; margin-right: 8px"
            @change="toggleLayer('green')"
          >
          <span>顯示城市綠化點</span>
        </label>

        <label
          style="display: flex; align-items: center; cursor: pointer"
        >
          <input
            v-model="showPollution"
            type="checkbox"
            style="width: 16px; height: 16px; margin-right: 8px"
            @change="toggleLayer('pollution')"
          >
          <span>顯示空氣污染點</span>
        </label>

        <label
          style="display: flex; align-items: center; cursor: pointer"
        >
          <input
            v-model="showWeather"
            type="checkbox"
            style="width: 16px; height: 16px; margin-right: 8px"
            @change="toggleLayer('weather')"
          >
          <span>顯示天氣站點</span>
        </label>
      </div>

      <!-- 熱力圖圖例 -->
      <div class="legend-block">
        <label>通風舒適度熱力區</label>
        <div class="legend" />
        <div class="legend-labels">
          <span>無風/悶熱</span>
          <span>通風良好</span>
        </div>
      </div>
    </div>

    <!-- 地圖容器 -->
    <div
      ref="mapContainer"
      class="map"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import mapboxgl from "mapbox-gl";

const mapContainer = ref(null);
const windDir = ref(45);
const windSpeed = ref(3);

let map = null;
let animationFrameId = null;
let idleRefreshTimer = null;
let buildingSpatialIndex = {};
let buildingData = [];
let windComfortGrid = [];
let windGridIndex = {};
let maxGridCount = 1;

let lastFeatures = [];
let frameCount = 0;
let isZooming = false;
let isMoving = false;
let weatherStations = [];

const showZones = ref(true);
const showPollution = ref(true);
const showGreen = ref(true);
const showWeather = ref(true);
const useStationData = ref(false);
const zoneSources = "/mapData/land_use_zone_metrotaipei.geojson";
const greenSource = "/mapData/green_point_metrotaipei.geojson";
const pollutionSources = {
	'pollution-tpe': '/mapData/air_pollution_emissions_tpe.geojson',
	'pollution-ntp': '/mapData/air_pollution_emissions_new_tpe.geojson'
};
const weatherPath = "/mapData/weather_station_metrotaipei.geojson";

const ORIGIN_LNG = 121.5646;
const ORIGIN_LAT = 25.0339;
const GRID_CELL_STEP = 0.0005;
const SPATIAL_INDEX_STEP = computed(() => useStationData.value ? 0.004 : 0.008);
const GRID_DECAY = 0.99;
const HIDE_SECONDS_PER_METER = 1 / 40;
const MIN_HIDE_SECONDS = 1.5;
const MAX_HIDE_SECONDS = 12;
const IDLE_REFRESH_MS = 30000;

mapboxgl.accessToken = import.meta.env.VITE_MAPBOXTOKEN;
const emptyGeoJSON = { type: "FeatureCollection", features: [] };

const zoneColorMatch = [
	"match",
	["get", "ZONE"],
	"工業區",
	"#A5A5A5",
	"文教區",
	"#66CC66",
	"住宅區",
	"#F3D34A", // 額外增加常見分區
	"商業區",
	"#E86B6B",
	"rgba(200, 200, 200, 0.5)", // 預設色
];

const loadWeatherStations = async () => {
	try {
		const res = await fetch(weatherPath);
		const data = await res.json();
		weatherStations = data.features
			.filter(f => {
				const p = f.properties;
				return p.wind_speed !== 'NULL' && p.wind_direction !== 'NULL';
			})
			.map(f => {
				const spd = parseFloat(f.properties.wind_speed);
				const dir = parseFloat(f.properties.wind_direction);
				return {
					lng: f.geometry.coordinates[0],
					lat: f.geometry.coordinates[1],
					dir: isNaN(dir) ? 0 : dir,
					speed: isNaN(spd) ? 0 : spd,
				};
			})
			.filter(st => st.speed > 0);
	} catch (e) {
		console.warn('Weather station load failed', e);
	}
};

// Inverse-distance-weighted interpolation from nearby stations
const getLocalWind = (lng, lat) => {
	let wSumSin = 0, wSumCos = 0, wSumSpeed = 0, totalW = 0;
	const MAX_DIST_SQ = 0.08 * 0.08;

	for (const st of weatherStations) {
		const dx = lng - st.lng;
		const dy = lat - st.lat;
		const distSq = dx * dx + dy * dy;
		if (distSq > MAX_DIST_SQ) continue;
		const w = 1 / Math.max(Math.sqrt(distSq), 0.0005);
		const rad = (st.dir * Math.PI) / 180;
		wSumSin += Math.sin(rad) * w;
		wSumCos += Math.cos(rad) * w;
		wSumSpeed += st.speed * w;
		totalW += w;
	}

	if (totalW === 0) return { angle: windDir.value, speed: windSpeed.value };

	const angle = ((Math.atan2(wSumSin / totalW, wSumCos / totalW) * 180 / Math.PI) + 360) % 360;
	const speed = Math.max(1, Math.min(10, wSumSpeed / totalW));
	return { angle, speed };
};

const cancelIdleRefresh = () => {
	if (idleRefreshTimer) {
		clearTimeout(idleRefreshTimer);
		idleRefreshTimer = null;
	}
};

const scheduleIdleRefresh = () => {
	cancelIdleRefresh();
	idleRefreshTimer = setTimeout(() => {
		if (!isMoving && !isZooming) {
			rebuildBuildingIndex();
			generateGrid();
		}
	}, IDLE_REFRESH_MS);
};

const getSafeBounds = () => {
	if (!map) return { south: 0, north: 0, west: 0, east: 0 };
	const bounds = map.getBounds();
	const center = map.getCenter();
	const maxSpan = 0.015;
	return {
		south: Math.max(bounds.getSouth(), center.lat - maxSpan),
		north: Math.min(bounds.getNorth(), center.lat + maxSpan),
		west: Math.max(bounds.getWest(), center.lng - maxSpan),
		east: Math.min(bounds.getEast(), center.lng + maxSpan),
	};
};

const generateGrid = () => {
	if (!map) return;
	const safeBounds = getSafeBounds();
	const step = 0.0008;
	const features = [];

	for (let lat = safeBounds.south; lat < safeBounds.north; lat += step) {
		for (let lng = safeBounds.west; lng < safeBounds.east; lng += step) {
			features.push({
				type: "Feature",
				geometry: { type: "Point", coordinates: [lng, lat] },
				properties: {
					oLng: lng,
					oLat: lat,
					cLng: lng,
					cLat: lat,
					angle: windDir.value,
					hiddenUntil: 0,
				},
			});
		}
	}

	lastFeatures = features;
	createWindComfortGrid(safeBounds);
};

const createWindComfortGrid = (safeBounds) => {
	windComfortGrid = [];
	windGridIndex = {};
	const step = GRID_CELL_STEP;
	const minX = Math.floor(safeBounds.west / step);
	const maxX = Math.floor(safeBounds.east / step);
	const minY = Math.floor(safeBounds.south / step);
	const maxY = Math.floor(safeBounds.north / step);

	for (let y = minY; y <= maxY; y++) {
		for (let x = minX; x <= maxX; x++) {
			const cellId = `${x}:${y}`;
			const cell = {
				type: "Feature",
				geometry: {
					type: "Polygon",
					coordinates: [
						[
							[x * step, y * step],
							[x * step + step, y * step],
							[x * step + step, y * step + step],
							[x * step, y * step + step],
							[x * step, y * step],
						],
					],
				},
				properties: { cellId, count: 0, frequency: 0 },
			};
			windComfortGrid.push(cell);
			windGridIndex[cellId] = cell;
		}
	}
};

const pointInRing = (ptLng, ptLat, ring) => {
	let inside = false;
	for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
		const xi = ring[i][0];
		const yi = ring[i][1];
		const xj = ring[j][0];
		const yj = ring[j][1];
		const intersects =
			yi > ptLat !== yj > ptLat &&
			ptLng < ((xj - xi) * (ptLat - yi)) / (yj - yi) + xi;
		if (intersects) inside = !inside;
	}
	return inside;
};

const pointInBuilding = (lng, lat, building) => {
	const { geometry } = building;
	if (!geometry) return false;
	const coords =
		geometry.type === "Polygon"
			? geometry.coordinates
			: geometry.coordinates[0];
	for (let i = 0; i < coords.length; i++) {
		if (pointInRing(lng, lat, coords[i])) return true;
	}
	return false;
};

const getBuildingHeight = (feature) =>
	feature?.properties?.height || feature?.properties?.render_height || 20;

const rebuildBuildingIndex = () => {
	buildingSpatialIndex = {};
	buildingData.forEach((building) => {
		const { geometry } = building;
		let coords = [];

		if (geometry.type === "Polygon") {
			coords = geometry.coordinates[0];
		} else if (geometry.type === "MultiPolygon") {
			coords = geometry.coordinates.flat(2);
		}
		if (coords.length === 0) return;

		let minLng = Infinity;
		let maxLng = -Infinity;
		let minLat = Infinity;
		let maxLat = -Infinity;
		for (const [lng, lat] of coords) {
			if (lng < minLng) minLng = lng;
			if (lng > maxLng) maxLng = lng;
			if (lat < minLat) minLat = lat;
			if (lat > maxLat) maxLat = lat;
		}

		const metadata = {
			feature: building,
			bbox: { minLng, maxLng, minLat, maxLat },
			height: getBuildingHeight(building),
		};

		const startX = Math.floor(minLng / SPATIAL_INDEX_STEP.value);
		const endX = Math.floor(maxLng / SPATIAL_INDEX_STEP.value);
		const startY = Math.floor(minLat / SPATIAL_INDEX_STEP.value);
		const endY = Math.floor(maxLat / SPATIAL_INDEX_STEP.value);

		for (let x = startX; x <= endX; x++) {
			for (let y = startY; y <= endY; y++) {
				const key = `${x}:${y}`;
				if (!buildingSpatialIndex[key]) buildingSpatialIndex[key] = [];
				buildingSpatialIndex[key].push(metadata);
			}
		}
	});
};

const updateWindComfortSource = () => {
	let currentMax = 0;
	for (const cell of windComfortGrid) {
		cell.properties.count *= GRID_DECAY;
		if (cell.properties.count > currentMax) currentMax = cell.properties.count;
	}
    
	maxGridCount = currentMax;
	const norm = Math.max(maxGridCount, 5); 

	for (const cell of windComfortGrid) {
		const rawFreq = cell.properties.count / norm;
		cell.properties.frequency = Math.pow(rawFreq, 0.7); 
	}
    
	if (map?.getSource("comfort-grid")) {
		map.getSource("comfort-grid").setData({
			type: "FeatureCollection",
			features: windComfortGrid,
		});
	}
};

const toggleLayer = (type) => {
	if (!map) return;
	const visibility = (isVisible) => isVisible ? 'visible' : 'none';
    
	if (type === 'zone') {
		const v = visibility(showZones.value);
		if (map.getLayer('zones-fill')) map.setLayoutProperty('zones-fill', 'visibility', v);
		if (map.getLayer('zones-outline')) map.setLayoutProperty('zones-outline', 'visibility', v);
	} 
	else if (type === 'green') {
		const v = visibility(showGreen.value);
		if (map.getLayer('green-dots')) map.setLayoutProperty('green-dots', 'visibility', v);
		if (map.getLayer('green-labels')) map.setLayoutProperty('green-labels', 'visibility', v);
	} 
	else if (type === 'pollution') {
		const v = visibility(showPollution.value);
		Object.keys(pollutionSources).forEach(id => {
			const layerId = `${id}-dots`;
			if (map.getLayer(layerId)) {
				map.setLayoutProperty(layerId, 'visibility', v);
			}
		});
	}
	else if (type === 'weather') {
		const v = visibility(showWeather.value);
		if (map.getLayer('weather-dots')) map.setLayoutProperty('weather-dots', 'visibility', v);
		if (map.getLayer('weather-temp-labels')) map.setLayoutProperty('weather-temp-labels', 'visibility', v);
	}
};

const createMap = () => {
	if (!mapContainer.value) return;

	map = new mapboxgl.Map({
		container: mapContainer.value,
		style: "mapbox://styles/mapbox/dark-v11",
		center: [ORIGIN_LNG, ORIGIN_LAT],
		zoom: 15.5,
		pitch: 60,
		bearing: -20,
		antialias: true,
	});

	const arrowCanvas = document.createElement("canvas");
	arrowCanvas.width = 32;
	arrowCanvas.height = 32;
	const ctx = arrowCanvas.getContext("2d");
	ctx.fillStyle = "#00d4ff";
	ctx.strokeStyle = "#00d4ff";
	ctx.lineWidth = 2;
	ctx.beginPath();
	ctx.moveTo(16, 6);
	ctx.lineTo(16, 26);
	ctx.stroke();
	ctx.beginPath();
	ctx.moveTo(16, 6);
	ctx.lineTo(10, 14);
	ctx.lineTo(22, 14);
	ctx.closePath();
	ctx.fill();

	map.on("load", () => {
		map.addSource("weather-source", { type: "geojson", data: weatherPath });
		map.addLayer({
			id: "weather-dots",
			type: "circle",
			source: "weather-source",
			layout: { 'visibility': showWeather.value ? 'visible' : 'none' },
			paint: {
				"circle-color": "#00fbff",
				"circle-radius": 6,
				"circle-stroke-width": 2,
				"circle-stroke-color": "#ffffff",
				"circle-blur": 0.2
			}
		});

		map.addLayer({
			id: "weather-temp-labels",
			type: "symbol",
			source: "weather-source",
			layout: {
				"visibility": showWeather.value ? 'visible' : 'none',
				"text-field": ["concat", ["get", "air_temperature"], "°C"],
				"text-size": 11,
				"text-offset": [0, -1.2],
				"text-font": ["Open Sans Bold"]
			},
			paint: { "text-color": "#00fbff", "text-halo-color": "#000", "text-halo-width": 1 }
		});
	
		Object.entries(pollutionSources).forEach(([id, url]) => {
			map.addSource(id, {
				type: 'geojson',
				data: url
			});

			// 2. 新增圓點圖層
			map.addLayer({
				id: `${id}-dots`,
				type: 'circle',
				source: id,
				layout: { 
					'visibility': showPollution.value ? 'visible' : 'none' 
				},
				paint: {
					// 使用橘紅色，在藍綠色調的風道圖中非常醒目
					'circle-color': '#FF5722',
					// 根據縮放調整大小
					'circle-radius': [
						'interpolate', ['linear'], ['zoom'],
						12, 4,
						16, 10
					],
					// 加入白色外邊框，解決「圖不明顯」的問題
					'circle-stroke-width': 2,
					'circle-stroke-color': '#FFFFFF',
					// 增加一點點發光感
					'circle-blur': 0.2
				}
			});

			// 3. (選用) 點擊互動：顯示設施名稱
			map.on('click', `${id}-dots`, (e) => {
				const props = e.features[0].properties;
				new mapboxgl.Popup()
					.setLngLat(e.lngLat)
					.setHTML(`
                    <div style="color:#333; padding:5px;">
                        <strong style="color:#FF5722;">${props.設施名稱 || props.name}</strong><br/>
                        <small>${props.設施類型 || '排放源'}</small><br/>
                        <p style="font-size:12px; margin:5px 0 0 0;">${props.地址 || ''}</p>
                    </div>
                `)
					.addTo(map);
			});
		});

		map.addSource("green-points", { type: "geojson", data: greenSource });

		map.addLayer({
			id: "green-dots",
			type: "circle",
			source: "green-points",
			paint: {
				// 核心顏色：鮮綠色
				"circle-color": "#2ecc71",
				// 圓點半徑：隨縮放層級調整
				"circle-radius": [
					"interpolate",
					["linear"],
					["zoom"],
					12,
					3,
					16,
					8,
				],
				// 發光邊框：讓它在深色或熱力圖背景上更清晰
				"circle-stroke-width": 2,
				"circle-stroke-color": "#ffffff",
				// 外發光效果
				"circle-blur": 0.2,
			},
		});

		map.addLayer({
			id: "green-labels",
			type: "symbol",
			source: "green-points",
			minzoom: 15,
			layout: {
				"text-field": ["get", "name"],
				"text-size": 12,
				"text-offset": [0, 1.5],
				"text-anchor": "top",
			},
			paint: {
				"text-color": "#ffffff",
				"text-halo-color": "rgba(0,0,0,0.8)",
				"text-halo-width": 1,
			},
		});

		map.addSource("zones-source", { type: "geojson", data: zoneSources });

		map.addLayer({
			id: 'zones-fill',
			type: 'fill',
			source: 'zones-source',
			layout: { 'visibility': showZones.value ? 'visible' : 'none' },
			paint: {
				'fill-color': zoneColorMatch,
				'fill-opacity': 0.08
			}
		});

		map.addLayer({
			id: 'zones-outline',
			type: 'line',
			source: 'zones-source',
			layout: { 'visibility': showZones.value ? 'visible' : 'none' },
			paint: {
				'line-color': zoneColorMatch,
				'line-width': 2,
				'line-opacity': 0.8,
				'line-dasharray': [2, 1] 
			}
		});

		map.addSource("wind-source", { type: "geojson", data: emptyGeoJSON });
		map.addSource("comfort-grid", { type: "geojson", data: emptyGeoJSON });

		map.addLayer({
			id: "comfort-heat",
			type: "fill",
			source: "comfort-grid",
			paint: {
				"fill-color": [
					"interpolate",
					["linear"],
					["get", "frequency"],
					0, "rgba(255, 80, 80, 0.4)",      // 悶熱
					0.15, "rgba(255, 160, 80, 0.4)",   // 微風
					0.35, "rgba(160, 220, 255, 0.4)",  // 通風良好
					0.7, "rgba(0, 170, 255, 0.6)"      // 強風廊道
				],
				"fill-opacity": 0.8,
			},
		});

		map.addImage("arrow-icon", ctx.getImageData(0, 0, 32, 32));
		map.addLayer({
			id: "wind-arrows",
			type: "symbol",
			source: "wind-source",
			layout: {
				"icon-image": "arrow-icon",
				"icon-size": [
					"interpolate",
					["linear"],
					["zoom"],
					12,
					0.2,
					16,
					0.5,
				],
				"icon-rotate": ["get", "angle"],
				"icon-allow-overlap": true,
				"icon-pitch-alignment": "map",
			},
			paint: { "icon-opacity": 0.7 },
		});

		map.addLayer({
			id: "3d-buildings",
			type: "fill-extrusion",
			source: "composite",
			"source-layer": "building",
			paint: {
				"fill-extrusion-color": "#2a2a2a",
				"fill-extrusion-height": ["get", "height"],
				"fill-extrusion-opacity": 0.95,
			},
		});

		const startup = () => {
			buildingData = map.querySourceFeatures("composite", {
				sourceLayer: "building",
			});
			if (buildingData.length === 0) {
				setTimeout(startup, 300);
				return;
			}
			rebuildBuildingIndex();
			generateGrid();
			update();
		};
		startup();
	});

	map.on("zoomstart", () => {
		isZooming = true;
		if (map?.getSource("wind-source"))
			map.getSource("wind-source").setData(emptyGeoJSON);
		if (map?.getSource("comfort-grid"))
			map.getSource("comfort-grid").setData(emptyGeoJSON);
		cancelIdleRefresh();
	});

	map.on("zoomend", () => {
		isZooming = false;
		createWindComfortGrid(getSafeBounds());
		scheduleIdleRefresh();
	});

	map.on("movestart", () => {
		isMoving = true;
		if (map?.getSource("wind-source"))
			map.getSource("wind-source").setData(emptyGeoJSON);
		cancelIdleRefresh();
	});

	map.on("moveend", () => {
		isMoving = false;
		setTimeout(() => {
			buildingData = map.querySourceFeatures("composite", {
				sourceLayer: "building",
			});
			rebuildBuildingIndex();
			generateGrid();
		}, 300);
		scheduleIdleRefresh();
	});
};

// const wrapValue = (value, min, range) =>
// 	((((value - min) % range) + range) % range) + min;

const DT = 2;

const update = () => {
	if (!map || !map.getSource("wind-source") || lastFeatures.length === 0) {
		animationFrameId = requestAnimationFrame(update);
		return;
	}

	const dir = windDir.value;
	const spd = windSpeed.value;
	const useStation = useStationData.value && weatherStations.length > 0;
	const now = performance.now();
	const safeBounds = getSafeBounds();
	const lngRange = safeBounds.east - safeBounds.west;
	const latRange = safeBounds.north - safeBounds.south;
	const visibleFeatures = [];

	for (let i = 0; i < lastFeatures.length; i++) {
		const f = lastFeatures[i];
		const { cLng, cLat } = f.properties;

		// 每幀根據粒子當前位置查詢風向（station mode）或使用全域設定
		let particleAngle, particleSpd;
		if (useStation) {
			const lw = getLocalWind(cLng, cLat);
			particleAngle = lw.angle;
			particleSpd = Math.min(15, lw.speed * (spd / 5));
		} else {
			particleAngle = dir;
			particleSpd = spd;
		}

		const pRad = (particleAngle * Math.PI) / 180;
		const vX = Math.sin(pRad) * 0.00001 * particleSpd;
		const vY = Math.cos(pRad) * 0.00001 * particleSpd;

		// 步進一幀
		const rawLng = cLng + vX * DT;
		const rawLat = cLat + vY * DT;

		// 建築偏轉
		const nearX = Math.floor(rawLng / SPATIAL_INDEX_STEP.value);
		const nearY = Math.floor(rawLat / SPATIAL_INDEX_STEP.value);
		const nearBuildings = buildingSpatialIndex[`${nearX}:${nearY}`] || [];

		// 建立一個斥力場向量
		let repulsionX = 0;
		let repulsionY = 0;

		for (const b of nearBuildings) {
			const box = b.bbox;
			const margin = 0.00025; // 擴大偵測邊界，讓粒子提早轉向

			if (
				rawLng > box.minLng - margin &&
        rawLng < box.maxLng + margin &&
        rawLat > box.minLat - margin &&
        rawLat < box.maxLat + margin
			) {
				// 計算粒子到建築中心點的距離
				const centerX = (box.minLng + box.maxLng) / 2;
				const centerY = (box.minLat + box.maxLat) / 2;
        
				let dx = rawLng - centerX;
				let dy = rawLat - centerY;
				const dist = Math.sqrt(dx * dx + dy * dy);
        
				if (dist > 0) {
					// 斥力強度：距離越近，推力越強（反比平方）
					const force = 0.00012 / (dist * 100); 
					repulsionX += (dx / dist) * force;
					repulsionY += (dy / dist) * force;
				}
			}
		}

		// 這裡使用 lerp (線性插值) 概念，讓粒子平滑地改變軌跡
		const smoothFactor = 0.2; // 數值越小轉彎越平滑
		const finalVX = vX * (1 - smoothFactor) + repulsionX * smoothFactor;
		const finalVY = vY * (1 - smoothFactor) + repulsionY * smoothFactor;

		// --- 修改 update 函式內的粒子位置更新段落 ---

		// 計算原始目標位置
		let nextLng = cLng + finalVX * DT;
		let nextLat = cLat + finalVY * DT;

		// 檢查是否超出目前地圖視窗邊界
		const isOut = nextLng < safeBounds.west || nextLng > safeBounds.east || 
              nextLat < safeBounds.south || nextLat > safeBounds.north;

		// 在 update 函式的粒子循環內
		if (isOut || Math.random() < 0.005) { // 增加微小機率讓粒子隨機重生，保持密度分布
			const side = Math.floor(Math.random() * 4);
			const buffer = 0.0001;

			// 根據隨機選擇的邊，將粒子投放到該邊緣的隨機位置
			if (side === 0) { // 西側進入
				f.properties.cLng = safeBounds.west + buffer;
				f.properties.cLat = safeBounds.south + Math.random() * latRange;
			} else if (side === 1) { // 東側進入
				f.properties.cLng = safeBounds.east - buffer;
				f.properties.cLat = safeBounds.south + Math.random() * latRange;
			} else if (side === 2) { // 南側進入
				f.properties.cLng = safeBounds.west + Math.random() * lngRange;
				f.properties.cLat = safeBounds.south + buffer;
			} else { // 北側進入
				f.properties.cLng = safeBounds.west + Math.random() * lngRange;
				f.properties.cLat = safeBounds.north - buffer;
			}

			// 重置隱藏時間，讓重生不突兀
			f.properties.hiddenUntil = now + Math.random() * 1200;
    
			// 重要：重置停滯計數與路徑記憶
			f.properties.stagnantTicks = 0; 
			continue;
		}

		// 如果沒越界，更新內部座標
		f.properties.cLng = nextLng;
		f.properties.cLat = nextLat;

		// 重要：這裡的渲染座標必須使用更新後的 nextLng/Lat，而不是再 wrap 一次
		const adjLng = nextLng;
		const adjLat = nextLat;

		if ((f.properties.hiddenUntil || 0) > now) {
			continue;
		}

		// 建築碰撞檢測
		const cellX = Math.floor(adjLng / SPATIAL_INDEX_STEP.value);
		const cellY = Math.floor(adjLat / SPATIAL_INDEX_STEP.value);
		const candidateBuildings = buildingSpatialIndex[`${cellX}:${cellY}`] || [];
		let hitBuilding = null;

		for (let j = 0; j < candidateBuildings.length; j++) {
			const bMeta = candidateBuildings[j];
			if (
				adjLng > bMeta.bbox.minLng &&
				adjLng < bMeta.bbox.maxLng &&
				adjLat > bMeta.bbox.minLat &&
				adjLat < bMeta.bbox.maxLat
			) {
				if (pointInBuilding(adjLng, adjLat, bMeta.feature)) {
					hitBuilding = bMeta;
					break;
				}
			}
		}

		if (hitBuilding) {
			const box = hitBuilding.bbox;
			const distX =
				Math.abs(adjLng - (box.minLng + box.maxLng) / 2) /
				((box.maxLng - box.minLng) / 2);
			const distY =
				Math.abs(adjLat - (box.minLat + box.maxLat) / 2) /
				((box.maxLat - box.minLat) / 2);
			const W = 1.0 - Math.max(distX, distY) * 0.6;
			const baseHideDur =
				Math.min(
					MAX_HIDE_SECONDS,
					Math.max(MIN_HIDE_SECONDS, hitBuilding.height * HIDE_SECONDS_PER_METER),
				) * 1000;
			f.properties.hiddenUntil = now + baseHideDur * W;
			continue;
		}

		f.geometry.coordinates[0] = adjLng;
		f.geometry.coordinates[1] = adjLat;
		f.properties.angle = particleAngle;
		visibleFeatures.push(f);

		const gridKey = `${Math.floor(adjLng / GRID_CELL_STEP)}:${Math.floor(adjLat / GRID_CELL_STEP)}`;
		if (windGridIndex[gridKey]) {
			const weight = useStation ? particleSpd * 0.5 : spd * 0.5;
			windGridIndex[gridKey].properties.count += Math.max(1, weight); 
		}
	}

	if (map?.getSource("wind-source")) {
		map.getSource("wind-source").setData({
			type: "FeatureCollection",
			features: visibleFeatures,
		});
	}

	if (++frameCount % 20 === 0) updateWindComfortSource();
	animationFrameId = requestAnimationFrame(update);
};

watch(useStationData, () => {
	rebuildBuildingIndex();
	if (lastFeatures.length > 0) generateGrid();
});

onMounted(() => {
	loadWeatherStations();
	createMap();
});

onBeforeUnmount(() => {
	if (animationFrameId) cancelAnimationFrame(animationFrameId);
	if (map) map.remove();
});
</script>

<style scoped>
.wind-engine-root {
	position: relative;
	width: 100%;
	height: 100vh;
}

.map {
	position: absolute;
	top: 0;
	right: 0;
	bottom: 0;
	left: 0;
}

.console {
	position: absolute;
	width: 280px;
	margin: 20px;
	padding: 20px;
	background: rgba(20, 20, 20, 0.85);
	color: white;
	border-radius: 12px;
	backdrop-filter: blur(5px);
	z-index: 10;
	border: 1px solid rgba(255, 255, 255, 0.1);
}

.slider-group {
	margin: 15px 0;
}

.slider-group.disabled {
	opacity: 0.4;
	pointer-events: none;
}

input[type="range"] {
	width: 100%;
}

h2 {
	margin: 0;
	font-size: 16px;
	color: #00d4ff;
}

.val {
	font-family: monospace;
	color: #ffcc00;
	float: right;
}

.legend-block {
	margin-top: 20px;
}

.legend {
	margin-top: 15px;
	font-size: 12px;
	display: flex;
	justify-content: space-between;
	background: linear-gradient(
		to right,
		rgba(255, 80, 80, 0.8),
		rgba(0, 170, 255, 0.8)
	);
	height: 10px;
	border-radius: 5px;
}

.legend-labels {
	display: flex;
	justify-content: space-between;
	font-size: 11px;
	color: #aaa;
	margin-top: 5px;
}
</style>
