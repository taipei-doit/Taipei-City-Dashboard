<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import MapContainer from "../components/map/MapContainer.vue";
import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";
import http from "../router/axios";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useMapStore } from "../store/mapStore";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const mapStore = useMapStore();
const route = useRoute();

const isMapView = computed(() => route.name === "eco-diet-mapview");

// http instance baseURL=/api/dev 指 prod；本案要打本機 BE /api/v1/* 須 override baseURL
function ecoApi(path) {
	return http.get(path, { baseURL: "" });
}

// ── 地圖三層 layer ID ──────────────────────────────────────────────────────
const RESTAURANT_LAYER_ID = "eco-diet-restaurants";
const GREEN_STORE_LAYER_ID = "eco-diet-green-stores";
const FOOD_BANK_LAYER_ID = "eco-diet-food-banks";

const SHARED_LINKS = {
	restaurant: [
		"https://data.taipei/dataset/detail?id=12388eaa-4f5e-4225-b62b-d2e0a8b3edb2",
		"https://data.ntpc.gov.tw/datasets/e90d14f8-95dc-431d-9301-4c1a5d8c8e83",
	],
	greenStore: [
		"https://data.taipei/dataset/detail?id=ba3e0fb1-b6e4-4862-b2db-ad81ad5c8c6f",
		"https://data.ntpc.gov.tw/datasets/6ccd0274-b8b3-4dd0-9a5f-1c6bf79d9dca",
	],
	waste: ["https://data.gov.tw/dataset/9079"],
	foodBank: [
		"https://data.taipei/dataset/detail?id=3f1a3e60-1b6e-4f7e-b0c7-7c1c2e8e3b5a",
		"https://data.ntpc.gov.tw/datasets/1c1d0066-2b9e-4d3a-9d1c-7c1f3a8f9b2c",
	],
};

const SHARED_CONTRIBUTORS = ["doit", "ntpc"];

// ── 6 個 component config（hasMap 3 個 + 無空間資料 3 個）─────────────────
const c1aComponent = ref({
	id: "eco-diet-c1a",
	index: "eco_diet_restaurants_points",
	city: "metrotaipei",
	name: "C1a｜環保餐廳點位",
	source: "雙北環保局",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["MapLegend"],
		color: ["#5fcf80", "#5a9cf8"],
		unit: "家",
	},
	chart_data: null,
	map_config: [{ index: RESTAURANT_LAYER_ID, type: "circle", city: "metrotaipei" }],
	short_desc: "雙北環保餐廳全量點位（依城市配色）",
	long_desc: "整合臺北市與新北市環保餐廳名錄，所有列管餐廳依經緯度落圖，臺北市以綠色、新北市以藍色標示，協助使用者直觀掌握雙北環保飲食店家的空間分布。",
	use_case: "市民查詢居家附近的環保餐廳、店家規劃新分店時參考既有環保認證店家分布、政府評估環保餐廳推廣的地理覆蓋率。",
	links: SHARED_LINKS.restaurant,
	contributors: SHARED_CONTRIBUTORS,
});

const c1bComponent = ref({
	id: "eco-diet-c1b",
	index: "eco_diet_restaurants_density",
	city: "metrotaipei",
	name: "C1b｜環保餐廳行政區密度",
	source: "雙北環保局",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["BarChart"],
		color: ["#5fcf80"],
		unit: "家",
	},
	chart_data: null,
	map_config: [null],
	short_desc: "雙北各行政區環保餐廳家數，依家數降冪",
	long_desc: "依行政區聚合雙北環保餐廳家數，呈現雙北環保飲食店家分布密度，協助使用者快速掌握哪些行政區供給較密集。",
	use_case: "市民查詢居住地附近環保餐廳供給度、政府政策評估環保餐廳推廣覆蓋率、店家規劃新分店時參考既有環保餐廳密度。",
	links: SHARED_LINKS.restaurant,
	contributors: SHARED_CONTRIBUTORS,
});

const c2Component = ref({
	id: "eco-diet-c2",
	index: "eco_diet_restaurants_count_city",
	city: "metrotaipei",
	name: "C2｜雙城環保餐廳家數",
	source: "雙北環保局",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["TextUnitChart"],
		color: ["#888787", "#5fcf80", "#888787"],
		unit: "家",
	},
	chart_data: null,
	map_config: [null],
	short_desc: "雙北環保餐廳總家數的單一數字卡呈現",
	long_desc: "顯示臺北市與新北市目前列管的環保餐廳總家數，反映雙北兩市對環保飲食店家認證的覆蓋程度差異。",
	use_case: "雙城環保政策推廣成效對比、研究分析雙北綠色飲食市場規模、簡報快速展示雙城資料量級。",
	links: SHARED_LINKS.restaurant,
	contributors: SHARED_CONTRIBUTORS,
});

const c4Component = ref({
	id: "eco-diet-c4",
	index: "eco_diet_green_stores_points",
	city: "metrotaipei",
	name: "C4｜綠色商店點位",
	source: "雙北環保局",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["MapLegend"],
		color: ["#5a9cf8", "#a37cf6"],
		unit: "家",
	},
	chart_data: null,
	map_config: [{ index: GREEN_STORE_LAYER_ID, type: "circle", city: "metrotaipei" }],
	short_desc: "雙北綠色商店全量點位（依連鎖／一般型配色）",
	long_desc: "整合雙北環保署認證的綠色商店資料並依商店類型（連鎖型／一般型）配色，呈現雙北綠色消費通路的空間分布與類型結構。",
	use_case: "綠色消費研究、零售業者規劃綠色商品上架通路時參考既有商店分布、消費者尋找最近綠色商店。",
	links: SHARED_LINKS.greenStore,
	contributors: SHARED_CONTRIBUTORS,
});

const c5Component = ref({
	id: "eco-diet-c5",
	index: "eco_diet_waste_yearly",
	city: "metrotaipei",
	name: "C5｜雙北年度廢棄物趨勢",
	source: "環境部",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["ColumnChart"],
		color: [
			"#ed5a5a", "#f6c344", "#5fcf80", "#5a9cf8",
			"#a37cf6", "#ec7cb1", "#888787", "#67baca",
		],
		categories: [],
		unit: "公噸",
	},
	chart_data: null,
	map_config: [null],
	short_desc: "雙北逐年廚餘量／一般垃圾／資源垃圾／總產生量",
	long_desc: "整合行政院環保署一般廢棄物統計年報資料，呈現臺北市與新北市自 2018 年起的四項廢棄物年度趨勢：廚餘回收量、一般垃圾清運量、資源回收量、總產生量。共 8 條 series（雙北 × 4 metric），單位皆為公噸。",
	use_case: "雙北減量政策成效評估、廚餘減量趨勢分析、研究新北市轄區人口成長對廢棄物量的影響、媒體製作雙城環境報告。",
	links: SHARED_LINKS.waste,
	contributors: SHARED_CONTRIBUTORS,
});

const c7aComponent = ref({
	id: "eco-diet-c7a",
	index: "eco_diet_food_banks_points",
	city: "metrotaipei",
	name: "C7a｜實物銀行點位",
	source: "雙北社會局",
	time_from: "current",
	time_to: null,
	update_freq: null,
	update_freq_unit: null,
	chart_config: {
		types: ["MapLegend"],
		color: ["#f6c344", "#a37cf6"],
		unit: "處",
	},
	chart_data: null,
	map_config: [{ index: FOOD_BANK_LAYER_ID, type: "circle", city: "metrotaipei" }],
	short_desc: "雙北實物銀行（社福資源）全量點位",
	long_desc: "整合臺北市社福機構名冊與新北市轄區社會福利服務中心資料，篩選出實物銀行（含食物銀行）類別據點，臺北市以橘色、新北市以紫色標示。",
	use_case: "社福政策研究、食物剩餘再分配研究、民眾尋找最近實物銀行的資訊起點，以及綠色飲食「惜食」議題與弱勢福利的交集分析。",
	links: SHARED_LINKS.foodBank,
	contributors: SHARED_CONTRIBUTORS,
});

// hasMap (有空間資料) vs noMap (無空間資料) 分組 — 對齊主站 MapView
const allComponents = computed(() => [
	c1aComponent.value,
	c1bComponent.value,
	c2Component.value,
	c4Component.value,
	c5Component.value,
	c7aComponent.value,
]);
const hasMapComponents = computed(() =>
	allComponents.value.filter((c) => c.map_config?.[0]),
);
const noMapComponents = computed(() =>
	allComponents.value.filter((c) => !c.map_config?.[0]),
);

const toggleOn = ref({
	restaurant: false,
	greenStore: false,
	foodBank: false,
});

const featureCache = ref({
	restaurant: [],
	greenStore: [],
	foodBank: [],
});

// ── fetch + transform ─────────────────────────────────────────────────────
async function fetchAll() {
	const calls = [
		ecoApi("/api/v1/eco_diet/restaurant/points"),
		ecoApi("/api/v1/eco_diet/restaurant/density-by-district"),
		ecoApi("/api/v1/eco_diet/restaurant/count-by-city"),
		ecoApi("/api/v1/eco_diet/green_store/points"),
		ecoApi("/api/v1/eco_diet/waste/yearly"),
		ecoApi("/api/v1/eco_diet/food_bank/points"),
	];
	const [r1a, r1b, r2, r4, r5, r7a] = await Promise.allSettled(calls);

	// C1a: 點位 → MapLegend (group by city) + GeoJSON layer source
	if (r1a.status === "fulfilled") {
		const points = r1a.value.data?.data || [];
		const tpe = points.filter((p) => p.city === "臺北市").length;
		const ntp = points.filter((p) => p.city === "新北市").length;
		c1aComponent.value.chart_data = [
			{ name: "臺北市", type: "circle", icon: "circle", value: tpe },
			{ name: "新北市", type: "circle", icon: "circle", value: ntp },
		];
		featureCache.value.restaurant = points
			.filter((p) => Number.isFinite(p.lng) && Number.isFinite(p.lat))
			.map((p) => ({
				type: "Feature",
				geometry: { type: "Point", coordinates: [p.lng, p.lat] },
				properties: {
					name: p.name,
					address: p.address,
					city: p.city,
					district: p.district,
					tel: p.tel,
					env_actions: (p.env_actions || []).join(", "),
				},
			}));
	} else {
		console.error("C1a fetch failed", r1a.reason);
		c1aComponent.value.chart_data = null;
	}

	// C1b: BarChart two_d 直接套
	if (r1b.status === "fulfilled") {
		c1bComponent.value.chart_data = r1b.value.data?.data || [];
	} else {
		console.error("C1b fetch failed", r1b.reason);
		c1bComponent.value.chart_data = null;
	}

	// C2: count-by-city 攤平成 TextUnitChart 多卡
	if (r2.status === "fulfilled") {
		const rows = r2.value.data?.data?.[0]?.data || [];
		c2Component.value.chart_data = rows.map((row) => ({
			name: row.x,
			data: [Math.round(Number(row.y ?? 0))],
			icon: "家",
		}));
	} else {
		console.error("C2 fetch failed", r2.reason);
		c2Component.value.chart_data = null;
	}

	// C4: 綠色商店點位 → MapLegend (group by store_type) + layer source
	if (r4.status === "fulfilled") {
		const points = r4.value.data?.data || [];
		const chain = points.filter((p) => p.store_type === "連鎖型綠色商店").length;
		const general = points.filter((p) => p.store_type === "一般型綠色商店").length;
		c4Component.value.chart_data = [
			{ name: "連鎖型", type: "circle", icon: "circle", value: chain },
			{ name: "一般型", type: "circle", icon: "circle", value: general },
		];
		featureCache.value.greenStore = points
			.filter((p) => Number.isFinite(p.lng) && Number.isFinite(p.lat))
			.map((p) => ({
				type: "Feature",
				geometry: { type: "Point", coordinates: [p.lng, p.lat] },
				properties: {
					name: p.name,
					address: p.address,
					city: p.city,
					store_type: p.store_type,
					tel: p.tel,
				},
			}));
	} else {
		console.error("C4 fetch failed", r4.reason);
		c4Component.value.chart_data = null;
	}

	// C5: 3D categories + 8 series → ColumnChart 直接套
	if (r5.status === "fulfilled") {
		const body = r5.value.data;
		c5Component.value.chart_config.categories = body.categories || [];
		c5Component.value.chart_data = body.data || [];
	} else {
		console.error("C5 fetch failed", r5.reason);
		c5Component.value.chart_data = null;
	}

	// C7a: 實物銀行 → MapLegend (group by city) + layer source
	if (r7a.status === "fulfilled") {
		const points = r7a.value.data?.data || [];
		const tpe = points.filter((p) => p.city === "臺北市").length;
		const ntp = points.filter((p) => p.city === "新北市").length;
		c7aComponent.value.chart_data = [
			{ name: "臺北市", type: "circle", icon: "circle", value: tpe },
			{ name: "新北市", type: "circle", icon: "circle", value: ntp },
		];
		featureCache.value.foodBank = points
			.filter((p) => Number.isFinite(p.lng) && Number.isFinite(p.lat))
			.map((p) => ({
				type: "Feature",
				geometry: { type: "Point", coordinates: [p.lng, p.lat] },
				properties: {
					name: p.name,
					org_type: p.org_type,
					city: p.city,
					district: p.district,
					address: p.address,
					tel: p.tel,
				},
			}));
	} else {
		console.error("C7a fetch failed", r7a.reason);
		c7aComponent.value.chart_data = null;
	}
}

// ── 地圖圖層自管 ──────────────────────────────────────────────────────────
function ensureMapReady() {
	return new Promise((resolve) => {
		const tryNow = () => {
			if (mapStore.map && mapStore.map.isStyleLoaded()) {
				resolve();
			} else if (mapStore.map) {
				mapStore.map.once("idle", resolve);
			} else {
				setTimeout(tryNow, 100);
			}
		};
		tryNow();
	});
}

const PAINT_BY_KEY = {
	restaurant: {
		"circle-radius": 4,
		"circle-color": [
			"match",
			["get", "city"],
			"臺北市", "#5fcf80",
			"新北市", "#5a9cf8",
			"#888888",
		],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 0.5,
		"circle-opacity": 0.85,
	},
	greenStore: {
		"circle-radius": 4,
		"circle-color": [
			"match",
			["get", "store_type"],
			"連鎖型綠色商店", "#5a9cf8",
			"一般型綠色商店", "#a37cf6",
			"#888888",
		],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 0.5,
		"circle-opacity": 0.8,
	},
	foodBank: {
		"circle-radius": 6,
		"circle-color": [
			"match",
			["get", "city"],
			"臺北市", "#f6c344",
			"新北市", "#a37cf6",
			"#888888",
		],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 1,
		"circle-opacity": 0.9,
	},
};

async function ensureLayer(layerId, key) {
	await ensureMapReady();
	if (!mapStore.map) return;
	const sourceId = `${layerId}-source`;
	const data = {
		type: "FeatureCollection",
		features: featureCache.value[key],
	};
	if (mapStore.map.getSource(sourceId)) {
		mapStore.map.getSource(sourceId).setData(data);
		return;
	}
	mapStore.map.addSource(sourceId, { type: "geojson", data });
	mapStore.map.addLayer({
		id: layerId,
		type: "circle",
		source: sourceId,
		layout: { visibility: "none" },
		paint: PAINT_BY_KEY[key],
	});
}

async function handleToggle(value, key, layerId) {
	toggleOn.value[key] = value;
	if (!featureCache.value[key].length) {
		if (value) {
			dialogStore.showNotification("info", "資料尚未載入完成");
		}
		return;
	}
	await ensureLayer(layerId, key);
	if (mapStore.map?.getLayer(layerId)) {
		mapStore.map.setLayoutProperty(
			layerId,
			"visibility",
			value ? "visible" : "none",
		);
	}
}

function shouldDisable(key) {
	return mapStore.isPreloading || featureCache.value[key].length === 0;
}

function handleMoreInfo(item) {
	dialogStore.showMoreInfo(item);
}

// 切回 dashboard tab 時重置 toggle，避免下次切回 mapview tab 殘留狀態
watch(isMapView, (active) => {
	if (!active) {
		toggleOn.value.restaurant = false;
		toggleOn.value.greenStore = false;
		toggleOn.value.foodBank = false;
	}
});

onMounted(async () => {
	contentStore.currentDashboard.name = "綠色飲食行為流程儀表板";
	contentStore.currentDashboard.icon = "eco";
	await fetchAll();
});

onBeforeUnmount(() => {
	if (!mapStore.map) return;
	[RESTAURANT_LAYER_ID, GREEN_STORE_LAYER_ID, FOOD_BANK_LAYER_ID].forEach((id) => {
		if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
		if (mapStore.map.getSource(`${id}-source`)) {
			mapStore.map.removeSource(`${id}-source`);
		}
	});
});

// 對應 hasMap 三個 component 的 toggle key 與 layer id（依 component.index）
function toggleKeyOf(component) {
	if (component.index === "eco_diet_restaurants_points") return "restaurant";
	if (component.index === "eco_diet_green_stores_points") return "greenStore";
	if (component.index === "eco_diet_food_banks_points") return "foodBank";
	return null;
}
function layerIdOf(component) {
	return component.map_config?.[0]?.index;
}
</script>

<template>
  <!-- 儀表板總覽 tab：6 個 component grid -->
  <div
    v-if="!isMapView"
    class="ecodietview-overview"
  >
    <DashboardComponent
      v-for="item in allComponents"
      :key="item.index"
      :config="item"
      mode="default"
      :info-btn="true"
      :active-city="item.city"
      :city-tag="contentStore.cityManager.getTagList(item.city)"
      @info="handleMoreInfo"
    />
    <MoreInfo />
    <ReportIssue />
  </div>

  <!-- 地圖交叉比對 tab：仿 MapView 兩段結構（hasMap → 無空間資料組件）-->
  <div
    v-else
    class="ecodietview-mapview"
  >
    <div class="ecodietview-mapview-charts">
      <!-- hasMap section（無 h2，第一段）：3 個點位元件，可 toggle layer -->
      <DashboardComponent
        v-for="item in hasMapComponents"
        :key="`map-${item.index}`"
        :config="item"
        mode="map"
        :info-btn="true"
        :active-city="item.city"
        :city-tag="contentStore.cityManager.getTagList(item.city)"
        :toggle-on="toggleOn[toggleKeyOf(item)]"
        :toggle-disable="shouldDisable(toggleKeyOf(item))"
        @info="handleMoreInfo"
        @toggle="(v) => handleToggle(v, toggleKeyOf(item), layerIdOf(item))"
      />
      <!-- 無空間資料組件 section（h2 + 3 個聚合卡片）-->
      <h2 v-if="noMapComponents.length > 0">
        無空間資料組件
      </h2>
      <DashboardComponent
        v-for="item in noMapComponents"
        :key="`nomap-${item.index}`"
        :config="item"
        mode="map"
        :info-btn="true"
        :active-city="item.city"
        :city-tag="contentStore.cityManager.getTagList(item.city)"
        @info="handleMoreInfo"
      />
    </div>
    <MapContainer />
    <MoreInfo />
    <ReportIssue />
  </div>
</template>

<style scoped lang="scss">
.ecodietview {
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
			height: fit-content;
			display: grid;
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
				color: var(--color-complement-text);
				font-size: var(--font-m);
				font-weight: 500;
			}
		}
	}
}
</style>
