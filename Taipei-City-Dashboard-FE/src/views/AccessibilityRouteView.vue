<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import MapContainer from "../components/map/MapContainer.vue";
import { useContentStore } from "../store/contentStore";
import { useMapStore } from "../store/mapStore";

const contentStore = useContentStore();
const mapStore = useMapStore();
const route = useRoute();

const isMapView = computed(() => route.name === "accessibility-route-mapview");

const TPE_DISTRICTS = [
	"北投區", "士林區", "內湖區", "南港區", "松山區", "信義區",
	"中山區", "大同區", "中正區", "萬華區", "大安區", "文山區",
];

const SLOPE_LAYER_ID = "wheelroute-slope-demo";
const WORK_LAYER_ID = "today-work-demo";

// Mock chart data — BE 將以同樣 schema 回傳 (district -> count)
const slopeCounts = {
	"北投區": 1620, "士林區": 2105, "內湖區": 1840, "南港區": 980,
	"松山區": 1450, "信義區": 1280, "中山區": 1990, "大同區": 1140,
	"中正區": 1720, "萬華區": 1380, "大安區": 2240, "文山區": 1560,
};

const workCounts = {
	"北投區": 56, "士林區": 36, "內湖區": 66, "南港區": 32,
	"松山區": 11, "信義區": 11, "中山區": 40, "大同區": 8,
	"中正區": 41, "萬華區": 27, "大安區": 63, "文山區": 48,
};

function buildSeries(counts, name) {
	return [
		{
			name,
			data: TPE_DISTRICTS.map((d) => ({ x: d, y: counts[d] || 0 })),
		},
	];
}

const slopeComponent = ref({
	id: "wheelroute-slope-demo",
	index: "wheelroute_slope_demo",
	city: "taipei",
	name: "輪行臺北：12 區無障礙斜坡道密度",
	source: "示範資料｜BE 將以行政區彙總回傳",
	time_from: "demo",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["ColumnChart"],
		color: ["#5fcf80"],
		unit: "處",
	},
	chart_data: buildSeries(slopeCounts, "斜坡道處數"),
	map_config: [{ index: SLOPE_LAYER_ID, type: "circle", city: "taipei" }],
});

const workComponent = ref({
	id: "today-work-demo",
	index: "today_work_demo",
	city: "taipei",
	name: "今日施工通報：行政區分布",
	source: "示範資料｜BE 將以每 10 分鐘輪詢更新",
	time_from: "demo",
	time_to: null,
	update_freq: 10,
	update_freq_unit: "minute",
	chart_config: {
		types: ["ColumnChart"],
		color: ["#ed5a5a"],
		unit: "件",
	},
	chart_data: buildSeries(workCounts, "今日施工件數"),
	map_config: [{ index: WORK_LAYER_ID, type: "circle", city: "taipei" }],
});

const toggleOn = ref({
	slope: false,
	work: false,
});

// Mock GeoJSON 給地圖圖層 — BE 串接後改丟真實 FeatureCollection
const slopeMockGeoJson = {
	type: "FeatureCollection",
	features: [
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5436, 25.0330] }, properties: { id: "slope-1", district: "大安區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5687, 25.0325] }, properties: { id: "slope-2", district: "信義區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5170, 25.0470] }, properties: { id: "slope-3", district: "中正區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5320, 25.0680] }, properties: { id: "slope-4", district: "中山區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5060, 25.0392] }, properties: { id: "slope-5", district: "萬華區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5884, 25.0842] }, properties: { id: "slope-6", district: "內湖區" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5238, 25.0935] }, properties: { id: "slope-7", district: "士林區" } },
	],
};

const workMockGeoJson = {
	type: "FeatureCollection",
	features: [
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5104, 25.0301] }, properties: { id: "work-1", district: "中正區", purpose: "捷運工程" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5446, 25.0289] }, properties: { id: "work-2", district: "大安區", purpose: "管線埋設" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.6058, 25.0539] }, properties: { id: "work-3", district: "南港區", purpose: "路面修補" } },
		{ type: "Feature", geometry: { type: "Point", coordinates: [121.5320, 25.1010] }, properties: { id: "work-4", district: "北投區", purpose: "管線埋設" } },
	],
};

function showLayerVisibility(layerId, visible) {
	if (!mapStore.map || !mapStore.map.getLayer(layerId)) return;
	mapStore.map.setLayoutProperty(
		layerId,
		"visibility",
		visible ? "visible" : "none",
	);
}

function handleToggle(value, key, layerId) {
	toggleOn.value[key] = value;
	showLayerVisibility(layerId, value);
}

function ensureMapReady() {
	return new Promise((resolve) => {
		const check = () => {
			if (mapStore.map && mapStore.map.isStyleLoaded()) {
				resolve();
			} else if (mapStore.map) {
				mapStore.map.once("idle", resolve);
			} else {
				setTimeout(check, 100);
			}
		};
		check();
	});
}

function registerLayer(layerId, geojson, paint) {
	if (!mapStore.map) return;
	if (mapStore.map.getLayer(layerId)) return;
	mapStore.map.addSource(`${layerId}-source`, {
		type: "geojson",
		data: geojson,
	});
	mapStore.map.addLayer({
		id: layerId,
		type: "circle",
		source: `${layerId}-source`,
		layout: { visibility: "none" },
		paint,
	});
}

async function pushLayersToMap() {
	await ensureMapReady();
	registerLayer(SLOPE_LAYER_ID, slopeMockGeoJson, {
		"circle-radius": 5,
		"circle-color": "#5fcf80",
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 1,
		"circle-opacity": 0.9,
	});
	registerLayer(WORK_LAYER_ID, workMockGeoJson, {
		"circle-radius": 6,
		"circle-color": "#ed5a5a",
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 1.2,
		"circle-opacity": 0.9,
	});
	// 還原 toggle 狀態（在 tab 切換間切回 map 時保留使用者選擇）
	showLayerVisibility(SLOPE_LAYER_ID, toggleOn.value.slope);
	showLayerVisibility(WORK_LAYER_ID, toggleOn.value.work);
}

watch(
	isMapView,
	(active) => {
		if (active) {
			pushLayersToMap();
		}
	},
	{ immediate: true },
);

onMounted(() => {
	// 讓 SettingsBar 顯示 demo 標題（demo 不走 contentStore 的 dashboard 流程）
	contentStore.currentDashboard.name = "雙城暢行：無障礙路網即時導覽";
	contentStore.currentDashboard.icon = "accessible";
});

onBeforeUnmount(() => {
	if (!mapStore.map) return;
	[SLOPE_LAYER_ID, WORK_LAYER_ID].forEach((layerId) => {
		if (mapStore.map.getLayer(layerId)) {
			mapStore.map.removeLayer(layerId);
		}
		if (mapStore.map.getSource(`${layerId}-source`)) {
			mapStore.map.removeSource(`${layerId}-source`);
		}
	});
});
</script>

<template>
  <!-- 儀表板總覽：純組件 grid（路由 /accessibility-route）-->
  <div
    v-if="!isMapView"
    class="accessibilityrouteview-overview"
  >
    <DashboardComponent
      :config="slopeComponent"
      mode="default"
      :info-btn="false"
    />
    <DashboardComponent
      :config="workComponent"
      mode="default"
      :info-btn="false"
    />
  </div>

  <!-- 地圖交叉比對：左組件右地圖（路由 /accessibility-route/mapview）-->
  <div
    v-else
    class="accessibilityrouteview-mapview"
  >
    <div class="accessibilityrouteview-mapview-charts">
      <h2>無空間資料組件</h2>
      <DashboardComponent
        :config="slopeComponent"
        mode="map"
        :info-btn="false"
        :toggle-on="toggleOn.slope"
        @toggle="(value) => handleToggle(value, 'slope', SLOPE_LAYER_ID)"
      />
      <DashboardComponent
        :config="workComponent"
        mode="map"
        :info-btn="false"
        :toggle-on="toggleOn.work"
        @toggle="(value) => handleToggle(value, 'work', WORK_LAYER_ID)"
      />
      <p class="accessibilityrouteview-mapview-charts-tip">
        打開組件右上角的開關，可在地圖疊加對應圖層。
        <br>綠點＝斜坡道；紅點＝今日施工通報。
      </p>
    </div>
    <MapContainer />
  </div>
</template>

<style scoped lang="scss">
.accessibilityrouteview {
	// 仿 DashboardView：純組件 grid
	&-overview {
		max-height: calc(100vh - 127px);
		max-height: calc(var(--vh) * 100 - 127px);
		display: grid;
		row-gap: var(--font-s);
		column-gap: var(--font-s);
		margin: var(--font-m) var(--font-m);
		overflow-y: scroll;

		@media (min-width: 720px) {
			grid-template-columns: 1fr 1fr;
		}

		@media (min-width: 1296px) {
			grid-template-columns: 1fr 1fr 1fr;
		}
	}

	// 仿 MapView：左組件右地圖
	&-mapview {
		height: calc(100vh - 127px);
		height: calc(var(--vh) * 100 - 127px);
		display: flex;
		margin: var(--font-m) var(--font-m);

		&-charts {
			width: 360px;
			max-height: 100%;
			display: flex;
			flex-direction: column;
			row-gap: var(--font-m);
			margin-right: var(--font-s);
			border-radius: 5px;
			overflow-y: scroll;

			@media (min-width: 1000px) {
				width: 370px;
			}

			@media (min-width: 2000px) {
				width: 400px;
			}

			h2 {
				margin: 4px 0 0 4px;
				color: var(--color-complement-text);
				font-size: var(--font-m);
				font-weight: 500;
			}

			&-tip {
				padding: var(--font-s);
				color: var(--color-complement-text);
				font-size: var(--font-s);
				line-height: 1.6;
			}
		}
	}
}
</style>
