<script setup>
import axios from "axios";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import MapContainer from "../components/map/MapContainer.vue";
import { useContentStore } from "../store/contentStore";
import { useMapStore } from "../store/mapStore";
import { useDialogStore } from "../store/dialogStore";

const contentStore = useContentStore();
const mapStore = useMapStore();
const dialogStore = useDialogStore();
const route = useRoute();

const isMapView = computed(() => route.name === "mrt-a11y-v2-mapview");

// ── 站點 layer：用既有 mrt_station_demo.geojson ─────────────────────────────
const STATION_LAYER = {
	index: "mrt_station_demo",
	title: "捷運站點（依異常狀態著色）",
	type: "circle",
	source: "geojson",
	size: "small",
	icon: null,
	paint: {
		"circle-radius": 6,
		"circle-color": [
			"match",
			["get", "status"],
			"alert", "#ed5a5a",
			"normal", "#5fcf80",
			"#888888",
		],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 1,
		"circle-opacity": 0.92,
	},
	property: [
		{ key: "station_name", name: "車站名稱" },
		{ key: "line", name: "所屬路線" },
		{ key: "status", name: "目前狀態" },
	],
	city: "taipei",
};

// ── Component configs（chart_data 初始為 null）────────────────────────────────
const c1Component = ref({
	id: "mrt-a11y-v2-alert-count",
	index: "mrt_a11y_v2_alert_count",
	city: "taipei",
	name: "C1｜目前異常設施總數",
	source: "BE Live｜/api/v1/mrt/a11y/alert-count",
	time_from: "current",
	time_to: null,
	update_freq: 15,
	update_freq_unit: "minute",
	chart_config: {
		types: ["TextUnitChart"],
		color: ["#888787", "#ed5a5a", "#888787"],
		unit: "處",
	},
	chart_data: null,
	map_config: [null],
});

const c2Component = ref({
	id: "mrt-a11y-v2-alert-by-line",
	index: "mrt_a11y_v2_alert_by_line",
	city: "taipei",
	name: "C2｜各捷運線異常站數",
	source: "BE Live｜/api/v1/mrt/a11y/alert-by-line",
	time_from: "current",
	time_to: null,
	update_freq: 15,
	update_freq_unit: "minute",
	chart_config: {
		types: ["ColumnChart"],
		color: ["#ed5a5a"],
		categories: [],
		unit: "站",
	},
	chart_data: null,
	map_config: [null],
});

const c3Component = ref({
	id: "mrt-a11y-v2-alert-by-type",
	index: "mrt_a11y_v2_alert_by_type",
	city: "taipei",
	name: "C3｜異常設施類型分布",
	source: "BE Live｜/api/v1/mrt/a11y/alert-by-type",
	time_from: "current",
	time_to: null,
	update_freq: 15,
	update_freq_unit: "minute",
	chart_config: {
		types: ["DonutChart"],
		color: ["#ed5a5a", "#f6c344", "#5fcf80", "#5a9cf8", "#a37cf6"],
		unit: "處",
	},
	chart_data: null,
	map_config: [null],
});

const c4Component = ref({
	id: "mrt-a11y-v2-station-overview",
	index: "mrt_a11y_v2_station_overview",
	city: "taipei",
	name: "C4｜捷運站無障礙狀態總覽",
	source: "BE Live｜/api/v1/mrt/a11y/station-overview",
	time_from: "current",
	time_to: null,
	update_freq: 15,
	update_freq_unit: "minute",
	chart_config: {
		types: ["MapLegend"],
		color: ["#ed5a5a", "#5fcf80"],
		unit: "站",
	},
	chart_data: null,
	map_config: [STATION_LAYER],
});

const toggleStationOn = ref(false);

// ── fetch + transform（依 reference/api-to-chart-mappings.md 4 種樣板）────────
async function fetchAll() {
	const calls = [
		axios.get("/api/v1/mrt/a11y/alert-count"),
		axios.get("/api/v1/mrt/a11y/alert-by-line"),
		axios.get("/api/v1/mrt/a11y/alert-by-type"),
		axios.get("/api/v1/mrt/a11y/station-overview"),
	];
	const [r1, r2, r3, r4] = await Promise.allSettled(calls);

	// C1 two_d 單點 → TextUnitChart
	if (r1.status === "fulfilled") {
		const point = r1.value.data?.data?.[0]?.data?.[0];
		c1Component.value.chart_data = [
			{
				name: point?.x ?? "今日異常設施",
				data: [Math.round(Number(point?.y ?? 0))],
				icon: "處",
			},
		];
	} else {
		console.error("C1 fetch failed", r1.reason);
		c1Component.value.chart_data = null;
	}

	// C2 three_d → ColumnChart（直接套）
	if (r2.status === "fulfilled") {
		const body = r2.value.data;
		c2Component.value.chart_config.categories = body.categories || [];
		c2Component.value.chart_data = body.data || [];
	} else {
		console.error("C2 fetch failed", r2.reason);
		c2Component.value.chart_data = null;
	}

	// C3 three_d each series 長度 1 → DonutChart（攤平成 2D）
	if (r3.status === "fulfilled") {
		const body = r3.value.data;
		const points = (body.data || []).map((s) => ({
			x: s.name,
			y: Math.round(Number(s.data?.[0] ?? 0)),
		}));
		c3Component.value.chart_data = points.length ? [{ data: points }] : [];
	} else {
		console.error("C3 fetch failed", r3.reason);
		c3Component.value.chart_data = null;
	}

	// C4 map_legend → MapLegend（icon alias mrt_station→metro 對齊既有 icon map）
	if (r4.status === "fulfilled") {
		const body = r4.value.data;
		c4Component.value.chart_data = (body.data || []).map((item) => ({
			name: item.name,
			type: item.type,
			icon: item.icon === "mrt_station" ? "metro" : item.icon,
			value: Math.round(Number(item.value ?? 0)),
		}));
	} else {
		console.error("C4 fetch failed", r4.reason);
		c4Component.value.chart_data = null;
	}
}

// ── 地圖圖層 toggle ──────────────────────────────────────────────────────────
function shouldDisable(map_config) {
	if (!map_config?.[0]) return true;
	const ids = map_config.map(
		(el) => `${el.index}-${el.type}-${el.city}`,
	);
	if (mapStore.isPreloading) return true;
	return mapStore.loadingLayers.filter((el) => ids.includes(el)).length > 0;
}

function handleStationToggle(value, map_config) {
	toggleStationOn.value = value;
	if (!map_config?.[0]) {
		if (value) {
			dialogStore.showNotification(
				"info",
				"本組件沒有空間資料，不會渲染地圖",
			);
		}
		return;
	}
	if (value) {
		mapStore.addToMapLayerList(map_config);
	} else {
		mapStore.clearByParamFilter(map_config);
		mapStore.turnOffMapLayerVisibility(map_config);
	}
}

onMounted(async () => {
	contentStore.currentDashboard.name = "雙城暢行 V2 ｜捷運無障礙即時狀態";
	contentStore.currentDashboard.icon = "accessible";
	await fetchAll();
});

onBeforeUnmount(() => {
	if (mapStore.map) {
		mapStore.clearByParamFilter(c4Component.value.map_config);
		mapStore.turnOffMapLayerVisibility(c4Component.value.map_config);
	}
});
</script>

<template>
  <!-- 儀表板總覽：4 個 component 純 grid -->
  <div
    v-if="!isMapView"
    class="mrtaccessibilityv2view-overview"
  >
    <DashboardComponent
      :config="c1Component"
      mode="default"
      :info-btn="false"
    />
    <DashboardComponent
      :config="c2Component"
      mode="default"
      :info-btn="false"
    />
    <DashboardComponent
      :config="c3Component"
      mode="default"
      :info-btn="false"
    />
    <DashboardComponent
      :config="c4Component"
      mode="default"
      :info-btn="false"
    />
  </div>

  <!-- 地圖交叉比對：左組件右地圖 -->
  <div
    v-else
    class="mrtaccessibilityv2view-mapview"
  >
    <div class="mrtaccessibilityv2view-mapview-charts">
      <h2>無空間資料組件</h2>
      <DashboardComponent
        :config="c1Component"
        mode="map"
        :info-btn="false"
      />
      <DashboardComponent
        :config="c2Component"
        mode="map"
        :info-btn="false"
      />
      <DashboardComponent
        :config="c3Component"
        mode="map"
        :info-btn="false"
      />
      <h2>地圖圖層組件</h2>
      <DashboardComponent
        :config="c4Component"
        mode="map"
        :info-btn="false"
        :toggle-disable="shouldDisable(c4Component.map_config)"
        :toggle-on="toggleStationOn"
        @toggle="handleStationToggle"
      />
      <p class="mrtaccessibilityv2view-mapview-charts-tip">
        打開 C4 開關可在地圖載入站點圖層；
        <br>紅點＝有異常、綠點＝正常。
      </p>
    </div>
    <MapContainer />
  </div>
</template>

<style scoped lang="scss">
.mrtaccessibilityv2view {
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
