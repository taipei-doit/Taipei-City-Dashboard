<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import mapboxGl from "mapbox-gl";

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

// ── 城市下拉選單（台北 / 新北 / 雙北）— 自包選項，避免動到 cityManager 影響主站 ──
const CITY_SELECT_LIST = [
	{ name: "臺北市", value: "taipei" },
	{ name: "新北市", value: "newtaipei" },
	{ name: "雙北", value: "metrotaipei" },
];
const CITY_LABEL = {
	taipei: "臺北市",
	newtaipei: "新北市",
};

// 各組件分配給臺北／新北的固定圖表色：3 個圖層在地圖上同時打開時要能分辨，
// 故每個組件用不同色相（餐廳=綠/藍、綠色商店=粉/青、實物銀行=黃/紫）。
const CITY_COLOR = {
	eco_diet_restaurants_points: { taipei: "#5fcf80", newtaipei: "#5a9cf8" },
	eco_diet_green_stores_points: { taipei: "#ec7cb1", newtaipei: "#67baca" },
	eco_diet_food_banks_points: { taipei: "#f6c344", newtaipei: "#a37cf6" },
};

// ── 地圖三層 layer ID ──────────────────────────────────────────────────────
const RESTAURANT_LAYER_ID = "eco-diet-restaurants";
const GREEN_STORE_LAYER_ID = "eco-diet-green-stores";
const FOOD_BANK_LAYER_ID = "eco-diet-food-banks";
const HOVER_HIGHLIGHT_LAYER_ID = "eco-diet-hover-highlight";
const HOVER_HIGHLIGHT_SOURCE_ID = `${HOVER_HIGHLIGHT_LAYER_ID}-source`;
const CLICK_HIGHLIGHT_LAYER_ID = "eco-diet-click-highlight";
const CLICK_HIGHLIGHT_SOURCE_ID = `${CLICK_HIGHLIGHT_LAYER_ID}-source`;
const ROUTE_LAYER_ID = "eco-diet-walking-route";
const ROUTE_SOURCE_ID = `${ROUTE_LAYER_ID}-source`;
// 路線色刻意避開所有 layer 配色（綠/藍、粉/青、黃/紫、白/click 藍）
const ROUTE_COLOR = "#ff5e3a";
const ROUTE_HALO_COLOR = "#ffffff";

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
		types: ["DonutChart", "BarChart"],
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
		types: ["DistrictChart", "BarChart"],
		color: ["#5fcf80", "#5a9cf8"],
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
		types: ["DonutChart", "BarChart"],
		color: ["#ec7cb1", "#67baca"],
		unit: "家",
	},
	chart_data: null,
	map_config: [{ index: GREEN_STORE_LAYER_ID, type: "circle", city: "metrotaipei" }],
	short_desc: "雙北綠色商店全量點位（依城市配色）",
	long_desc: "整合雙北環保署認證的綠色商店資料並依城市配色（臺北粉／新北青），刻意與環保餐廳的綠/藍配色錯開，方便雙圖層同時開啟時分辨。",
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
		types: ["TimelineSeparateChart", "BubbleChart"],
		color: [
			"#ed5a5a", "#f6c344", "#5fcf80", "#5a9cf8",
			"#a37cf6", "#ec7cb1", "#888787", "#67baca",
		],
		unit: "公噸",
		// BubbleChart 用：x 走 datetime（與 TimelineSeparate 共用同一份 x），bubble 半徑由 z 決定
		xType: "datetime",
		xTickAmount: 6,
	},
	chart_data: null,
	map_config: [null],
	short_desc: "雙北逐年廚餘量／一般垃圾／資源垃圾／總產生量",
	long_desc: "整合行政院環保署一般廢棄物統計年報資料，呈現臺北市與新北市自 2018 年起的四項廢棄物年度趨勢：廚餘回收量、一般垃圾清運量、資源回收量、總產生量。雙北檢視時共 8 條 series（雙北 × 4 metric），單一城市則僅顯示該城市 4 條，單位皆為公噸。",
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
		types: ["DonutChart", "BarChart"],
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

// ── 每個 component 的 activeCity（下拉選單當前選擇）— 預設 metrotaipei ─────
const activeCityMap = reactive({
	eco_diet_restaurants_points: "metrotaipei",
	eco_diet_restaurants_density: "metrotaipei",
	eco_diet_restaurants_count_city: "metrotaipei",
	eco_diet_green_stores_points: "metrotaipei",
	eco_diet_waste_yearly: "metrotaipei",
	eco_diet_food_banks_points: "metrotaipei",
});

const toggleOn = ref({
	restaurant: false,
	greenStore: false,
	foodBank: false,
});

// 原始 BE 回應快取，切換城市時據此重算 chart_data 與 layer 篩選
const rawData = ref({
	restaurantPoints: [],
	restaurantDensity: [],
	restaurantCountByCity: [],
	greenStorePoints: [],
	wasteCategories: [],
	wasteSeries: [],
	foodBankPoints: [],
});

const featureCache = ref({
	restaurant: [],
	greenStore: [],
	foodBank: [],
});

// ── city → 篩選 helper ────────────────────────────────────────────────────
function matchByCity(row, cityValue) {
	if (cityValue === "metrotaipei") return true;
	return row.city === CITY_LABEL[cityValue];
}
function matchSeriesByCity(seriesName, cityValue) {
	if (cityValue === "metrotaipei") return true;
	return seriesName.startsWith(CITY_LABEL[cityValue]);
}

// ── 各 component 依 activeCity 重算 chart_data ────────────────────────────
function recomputeC1a() {
	const city = activeCityMap.eco_diet_restaurants_points;
	const points = rawData.value.restaurantPoints;
	const tpe = points.filter((p) => p.city === "臺北市").length;
	const ntp = points.filter((p) => p.city === "新北市").length;
	const palette = CITY_COLOR.eco_diet_restaurants_points;
	const buckets = [];
	const colors = [];
	if (city === "metrotaipei" || city === "taipei") {
		buckets.push({ x: "臺北市", y: tpe });
		colors.push(palette.taipei);
	}
	if (city === "metrotaipei" || city === "newtaipei") {
		buckets.push({ x: "新北市", y: ntp });
		colors.push(palette.newtaipei);
	}
	// DonutChart / BarChart 共用 [{name:"", data:[{x,y},...]}] 格式
	c1aComponent.value.chart_data = [{ name: "", data: buckets }];
	c1aComponent.value.chart_config.color = colors;
}

function recomputeC1b() {
	const city = activeCityMap.eco_diet_restaurants_density;
	const allRows = rawData.value.restaurantDensity;
	const filtered = allRows.filter((row) => matchByCity(row, city));
	c1bComponent.value.chart_data = filtered.length
		? [{ data: filtered.map(({ x, y }) => ({ x, y })) }]
		: [{ data: [] }];
}

function recomputeC2() {
	const city = activeCityMap.eco_diet_restaurants_count_city;
	const rows = rawData.value.restaurantCountByCity;
	const tpeRow = rows.find((r) => r.x === "臺北市");
	const ntpRow = rows.find((r) => r.x === "新北市");
	const tpe = Math.round(Number(tpeRow?.y ?? 0));
	const ntp = Math.round(Number(ntpRow?.y ?? 0));
	const cards = [];
	if (city === "metrotaipei" || city === "taipei") {
		cards.push({ name: "臺北市", data: [tpe], icon: "家" });
	}
	if (city === "metrotaipei" || city === "newtaipei") {
		cards.push({ name: "新北市", data: [ntp], icon: "家" });
	}
	c2Component.value.chart_data = cards;
}

function recomputeC4() {
	const city = activeCityMap.eco_diet_green_stores_points;
	const points = rawData.value.greenStorePoints;
	const tpe = points.filter((p) => p.city === "臺北市").length;
	const ntp = points.filter((p) => p.city === "新北市").length;
	const palette = CITY_COLOR.eco_diet_green_stores_points;
	const buckets = [];
	const colors = [];
	if (city === "metrotaipei" || city === "taipei") {
		buckets.push({ x: "臺北市", y: tpe });
		colors.push(palette.taipei);
	}
	if (city === "metrotaipei" || city === "newtaipei") {
		buckets.push({ x: "新北市", y: ntp });
		colors.push(palette.newtaipei);
	}
	c4Component.value.chart_data = [{ name: "", data: buckets }];
	c4Component.value.chart_config.color = colors;
}

function recomputeC5() {
	const city = activeCityMap.eco_diet_waste_yearly;
	const allSeries = rawData.value.wasteSeries;
	const categories = rawData.value.wasteCategories;
	const filtered = allSeries.filter((s) => matchSeriesByCity(s.name, city));
	// TimelineSeparateChart 吃 {x:ISO, y}；BubbleChart 額外吃 z（半徑）
	// z 用 sqrt 壓縮值域：60k→8、1.5M→40，bubble 大小落在合理區間
	c5Component.value.chart_data = filtered.map((s) => ({
		name: s.name,
		data: s.data.map((y, i) => ({
			y,
			x: `${categories[i]}-01-01T00:00:00+08:00`,
			z: Math.max(2, Math.sqrt(y) / 30),
		})),
	}));
}

function recomputeC7a() {
	const city = activeCityMap.eco_diet_food_banks_points;
	const points = rawData.value.foodBankPoints;
	const tpe = points.filter((p) => p.city === "臺北市").length;
	const ntp = points.filter((p) => p.city === "新北市").length;
	const palette = CITY_COLOR.eco_diet_food_banks_points;
	const buckets = [];
	const colors = [];
	if (city === "metrotaipei" || city === "taipei") {
		buckets.push({ x: "臺北市", y: tpe });
		colors.push(palette.taipei);
	}
	if (city === "metrotaipei" || city === "newtaipei") {
		buckets.push({ x: "新北市", y: ntp });
		colors.push(palette.newtaipei);
	}
	c7aComponent.value.chart_data = [{ name: "", data: buckets }];
	c7aComponent.value.chart_config.color = colors;
}

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

	// C1a: 點位 → 快取後依 activeCity 算 MapLegend
	if (r1a.status === "fulfilled") {
		rawData.value.restaurantPoints = r1a.value.data?.data || [];
		featureCache.value.restaurant = rawData.value.restaurantPoints
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
		recomputeC1a();
	} else {
		console.error("C1a fetch failed", r1a.reason);
		c1aComponent.value.chart_data = null;
	}

	// C1b: 行政區密度，依 activeCity 篩選 city 欄位後給 BarChart
	if (r1b.status === "fulfilled") {
		rawData.value.restaurantDensity = r1b.value.data?.data?.[0]?.data || [];
		recomputeC1b();
	} else {
		console.error("C1b fetch failed", r1b.reason);
		c1bComponent.value.chart_data = null;
	}

	// C2: 雙城家數，雙北自行加總一張卡
	if (r2.status === "fulfilled") {
		rawData.value.restaurantCountByCity = r2.value.data?.data?.[0]?.data || [];
		recomputeC2();
	} else {
		console.error("C2 fetch failed", r2.reason);
		c2Component.value.chart_data = null;
	}

	// C4: 綠色商店點位，依 activeCity 算 MapLegend（依城市分組，非店家類型）
	if (r4.status === "fulfilled") {
		rawData.value.greenStorePoints = r4.value.data?.data || [];
		featureCache.value.greenStore = rawData.value.greenStorePoints
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
		recomputeC4();
	} else {
		console.error("C4 fetch failed", r4.reason);
		c4Component.value.chart_data = null;
	}

	// C5: 廢棄物趨勢，依 activeCity 過濾雙北/單城 series
	if (r5.status === "fulfilled") {
		const body = r5.value.data;
		rawData.value.wasteCategories = body.categories || [];
		rawData.value.wasteSeries = body.data || [];
		recomputeC5();
	} else {
		console.error("C5 fetch failed", r5.reason);
		c5Component.value.chart_data = null;
	}

	// C7a: 實物銀行點位 → 依 activeCity 算 MapLegend
	if (r7a.status === "fulfilled") {
		rawData.value.foodBankPoints = r7a.value.data?.data || [];
		featureCache.value.foodBank = rawData.value.foodBankPoints
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
		recomputeC7a();
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
			["get", "city"],
			"臺北市", "#ec7cb1",
			"新北市", "#67baca",
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
	ensureHighlightLayer();
	attachHoverPopup(layerId, key);
}

// hover 圈圈（小白環）+ 點擊圈圈（更大、更顯眼），兩個分開避免互相覆蓋
function ensureHighlightLayer() {
	if (!mapStore.map) return;
	if (!mapStore.map.getLayer(HOVER_HIGHLIGHT_LAYER_ID)) {
		mapStore.map.addSource(HOVER_HIGHLIGHT_SOURCE_ID, {
			type: "geojson",
			data: { type: "FeatureCollection", features: [] },
		});
		mapStore.map.addLayer({
			id: HOVER_HIGHLIGHT_LAYER_ID,
			type: "circle",
			source: HOVER_HIGHLIGHT_SOURCE_ID,
			paint: {
				"circle-radius": 10,
				"circle-color": "rgba(255, 255, 255, 0)",
				"circle-stroke-color": "#ffffff",
				"circle-stroke-width": 2.5,
				"circle-stroke-opacity": 0.9,
			},
		});
	}
	if (!mapStore.map.getLayer(CLICK_HIGHLIGHT_LAYER_ID)) {
		mapStore.map.addSource(CLICK_HIGHLIGHT_SOURCE_ID, {
			type: "geojson",
			data: { type: "FeatureCollection", features: [] },
		});
		mapStore.map.addLayer({
			id: CLICK_HIGHLIGHT_LAYER_ID,
			type: "circle",
			source: CLICK_HIGHLIGHT_SOURCE_ID,
			paint: {
				"circle-radius": 14,
				// fill 全透明：原本的點不會被遮蓋
				"circle-color": "rgba(0, 0, 0, 0)",
				"circle-stroke-color": "#5a9cf8",
				"circle-stroke-width": 3,
				"circle-stroke-opacity": 0.95,
			},
		});
	}
}

function setHighlightFeature(feature) {
	const source = mapStore.map?.getSource(HOVER_HIGHLIGHT_SOURCE_ID);
	if (!source) return;
	source.setData({
		type: "FeatureCollection",
		features: feature ? [feature] : [],
	});
}

// 累加：每次點擊的圈圈都保留，使用者可一直疊加。同 lng,lat 不重複。
const clickedFeatures = ref([]);

function addClickedFeature(feature) {
	if (!feature?.geometry?.coordinates) return;
	const [lng, lat] = feature.geometry.coordinates;
	const key = `${lng},${lat}`;
	const existing = new Set(
		clickedFeatures.value.map((f) => {
			const [x, y] = f.geometry.coordinates;
			return `${x},${y}`;
		}),
	);
	if (existing.has(key)) return;
	clickedFeatures.value.push(feature);
	syncClickedFeaturesToSource();
}

function clearClickedFeatures() {
	clickedFeatures.value = [];
	syncClickedFeaturesToSource();
	clickPopup?.remove();
	clickPopup = null;
}

function syncClickedFeaturesToSource() {
	const source = mapStore.map?.getSource(CLICK_HIGHLIGHT_SOURCE_ID);
	if (!source) return;
	source.setData({
		type: "FeatureCollection",
		features: clickedFeatures.value,
	});
}

// ── Mapbox Directions API（walking）──────────────────────────────────────
function ensureRouteLayer() {
	if (!mapStore.map || mapStore.map.getLayer(ROUTE_LAYER_ID)) return;
	mapStore.map.addSource(ROUTE_SOURCE_ID, {
		type: "geojson",
		data: { type: "FeatureCollection", features: [] },
	});
	// 先畫白色 halo 增加在淺底圖上的對比，再畫主線
	mapStore.map.addLayer({
		id: `${ROUTE_LAYER_ID}-halo`,
		type: "line",
		source: ROUTE_SOURCE_ID,
		layout: { "line-join": "round", "line-cap": "round" },
		paint: {
			"line-color": ROUTE_HALO_COLOR,
			"line-width": 8,
			"line-opacity": 0.5,
		},
	});
	mapStore.map.addLayer({
		id: ROUTE_LAYER_ID,
		type: "line",
		source: ROUTE_SOURCE_ID,
		layout: { "line-join": "round", "line-cap": "round" },
		paint: {
			"line-color": ROUTE_COLOR,
			"line-width": 5,
			"line-opacity": 0.95,
			"line-dasharray": [0.5, 1.5],
		},
	});
}

function makeEndpointMarkerEl(label, color) {
	const el = document.createElement("div");
	el.style.cssText = `
		width: 22px; height: 22px; border-radius: 50%;
		background: ${color}; border: 3px solid #fff;
		box-shadow: 0 0 6px rgba(0,0,0,0.5);
		display: flex; align-items: center; justify-content: center;
		color: #fff; font-size: 11px; font-weight: 600;
		font-family: '微軟正黑體', 'Microsoft JhengHei', sans-serif;
	`;
	el.textContent = label;
	return el;
}

function setStartMarker(coords) {
	routeStartMarker?.remove();
	routeStartMarker = null;
	if (!coords || !mapStore.map) return;
	routeStartMarker = new mapboxGl.Marker({
		element: makeEndpointMarkerEl("A", "#00c853"),
	})
		.setLngLat([coords.lng, coords.lat])
		.addTo(mapStore.map);
}
function setEndMarker(coords) {
	routeEndMarker?.remove();
	routeEndMarker = null;
	if (!coords || !mapStore.map) return;
	routeEndMarker = new mapboxGl.Marker({
		element: makeEndpointMarkerEl("B", ROUTE_COLOR),
	})
		.setLngLat([coords.lng, coords.lat])
		.addTo(mapStore.map);
}

async function fetchWalkingRoute(start, end) {
	const token = mapboxGl.accessToken;
	const coords = `${start.lng},${start.lat};${end.lng},${end.lat}`;
	const url = `https://api.mapbox.com/directions/v5/mapbox/walking/${coords}?geometries=geojson&overview=full&access_token=${token}`;
	const res = await fetch(url);
	if (!res.ok) {
		throw new Error(`Directions API ${res.status}`);
	}
	const json = await res.json();
	if (!json.routes?.length) {
		throw new Error("找不到可行路徑");
	}
	return json.routes[0];
}

async function drawRoute() {
	if (!routeStart.value || !routeEnd.value || !mapStore.map) return;
	routeLoading.value = true;
	try {
		const route = await fetchWalkingRoute(routeStart.value, routeEnd.value);
		ensureRouteLayer();
		mapStore.map.getSource(ROUTE_SOURCE_ID).setData({
			type: "Feature",
			geometry: route.geometry,
			properties: {},
		});
		routeStats.value = {
			distanceMeters: route.distance,
			durationSeconds: route.duration,
		};
		// fitBounds 把整條路線塞進視窗
		const lineCoords = route.geometry.coordinates;
		const bounds = lineCoords.reduce(
			(b, c) => b.extend(c),
			new mapboxGl.LngLatBounds(lineCoords[0], lineCoords[0]),
		);
		mapStore.map.fitBounds(bounds, { padding: 80, duration: 600 });
	} catch (e) {
		dialogStore.showNotification("error", `路徑規劃失敗：${e.message}`);
	} finally {
		routeLoading.value = false;
	}
}

function startRouteFromCurrent() {
	if (!navigator.geolocation) {
		dialogStore.showNotification("error", "瀏覽器不支援定位 API");
		return;
	}
	clearRoute();
	dialogStore.showNotification("info", "正在取得目前位置 ⋯");
	navigator.geolocation.getCurrentPosition(
		(pos) => {
			routeStart.value = {
				lng: pos.coords.longitude,
				lat: pos.coords.latitude,
				name: "目前位置",
			};
			setStartMarker(routeStart.value);
			routeStep.value = "pick-end";
			dialogStore.showNotification("info", "請打開圖層並點選一個點位作為終點");
		},
		() => dialogStore.showNotification("error", "取得位置失敗，請允許瀏覽器定位權限"),
	);
}

function startRoutePickTwo() {
	// 如果使用者剛剛在瀏覽模式點過點：把最新一個當起點 A，其他圈圈清掉、直接進 pick-end
	const latest = clickedFeatures.value[clickedFeatures.value.length - 1];
	if (latest) {
		const [lng, lat] = latest.geometry.coordinates;
		routeStart.value = {
			lng,
			lat,
			name: latest.properties?.name,
		};
		// 清光之前累積的圈圈與 click popup（A marker 會取代視覺）
		clickedFeatures.value = [];
		syncClickedFeaturesToSource();
		clickPopup?.remove();
		clickPopup = null;
		// 清乾淨可能殘留的路線狀態
		routeEnd.value = null;
		routeStats.value = null;
		setEndMarker(null);
		const source = mapStore.map?.getSource(ROUTE_SOURCE_ID);
		source?.setData({ type: "FeatureCollection", features: [] });
		// 設 A marker、跳到等使用者點終點
		setStartMarker(routeStart.value);
		routeStep.value = "pick-end";
		dialogStore.showNotification("info", "已用最後點擊的點當起點，請點選終點");
		return;
	}
	// 沒有先前點擊：完整 pick-two 流程
	clearRoute();
	routeStep.value = "pick-start";
	dialogStore.showNotification("info", "請打開圖層並點選一個點位作為起點");
}

function clearRoute() {
	routeStep.value = null;
	routeStart.value = null;
	routeEnd.value = null;
	routeStats.value = null;
	setStartMarker(null);
	setEndMarker(null);
	const source = mapStore.map?.getSource(ROUTE_SOURCE_ID);
	if (source) {
		source.setData({ type: "FeatureCollection", features: [] });
	}
}

function formatDistance(m) {
	if (m == null) return "—";
	return m >= 1000 ? `${(m / 1000).toFixed(2)} 公里` : `${Math.round(m)} 公尺`;
}
function formatDuration(s) {
	if (s == null) return "—";
	const min = Math.round(s / 60);
	if (min < 60) return `${min} 分鐘`;
	const h = Math.floor(min / 60);
	const m = min % 60;
	return `${h} 小時 ${m} 分鐘`;
}

// ── 地圖點位 hover / click popup ─────────────────────────────────────────
let hoverPopup = null;
let clickPopup = null;

// ── 步行路線狀態（B：從目前位置；C：選兩個既有點位）────────────────────
// routeStep: null | "pick-end"（已有 start，等使用者點終點）| "pick-start"（C 流程初始）
const routeStep = ref(null);
const routeStart = ref(null); // { lng, lat, name }
const routeEnd = ref(null);
const routeStats = ref(null); // { distanceMeters, durationSeconds }
const routeLoading = ref(false);
let routeStartMarker = null;
let routeEndMarker = null;

// 步行面板開關 + 拖曳位置（fixed 定位，初始放在 walk icon 左邊）
const routePanelOpen = ref(false);
const panelPos = ref(null); // null = 第一次開啟前；{x,y} = 已決定位置

// 在 route mode（已選擇從目前位置 / 選兩個點位）才顯示「清除選取」按鈕
const inRouteMode = computed(() => Boolean(routeStep.value || routeStats.value));

function toggleRoutePanel(e) {
	if (routePanelOpen.value) {
		routePanelOpen.value = false;
		return;
	}
	routePanelOpen.value = true;
	if (!panelPos.value) {
		// 初始位置：步行 icon 的左邊（panel 約 260 寬）
		const btnRect = e.currentTarget.getBoundingClientRect();
		panelPos.value = {
			x: Math.max(20, btnRect.left - 280),
			y: btnRect.top,
		};
	}
}

function onPanelDragStart(e) {
	if (e.button !== 0) return; // 只接受左鍵
	e.preventDefault();
	const startX = e.clientX;
	const startY = e.clientY;
	const initial = { ...panelPos.value };
	function onMove(ev) {
		panelPos.value = {
			x: initial.x + (ev.clientX - startX),
			y: initial.y + (ev.clientY - startY),
		};
	}
	function onUp() {
		document.removeEventListener("mousemove", onMove);
		document.removeEventListener("mouseup", onUp);
	}
	document.addEventListener("mousemove", onMove);
	document.addEventListener("mouseup", onUp);
}

function ensureHoverPopup() {
	if (!hoverPopup) {
		hoverPopup = new mapboxGl.Popup({
			closeButton: false,
			closeOnClick: false,
			offset: 10,
			anchor: "bottom",
		});
	}
	return hoverPopup;
}

function escapeHtml(str) {
	if (str == null) return "";
	return String(str)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

function buildPopupHtml(key, props) {
	const lines = [];
	lines.push(`<h4 style="color:#fff;font-size:0.95rem;font-weight:500;margin-bottom:6px;">${escapeHtml(props.name)}</h4>`);
	const cityDistrict = [props.city, props.district].filter(Boolean).map(escapeHtml).join(" ");
	if (cityDistrict) {
		lines.push(`<p style="color:#888787;font-size:0.75rem;margin-bottom:2px;">${cityDistrict}</p>`);
	}
	if (props.address) {
		lines.push(`<p style="color:#fff;font-size:0.8rem;margin-bottom:2px;">${escapeHtml(props.address)}</p>`);
	}
	if (props.tel) {
		lines.push(`<p style="color:#fff;font-size:0.8rem;margin-bottom:2px;">☎ ${escapeHtml(props.tel)}</p>`);
	}
	if (key === "restaurant" && props.env_actions) {
		lines.push(`<p style="color:#5fcf80;font-size:0.75rem;margin-top:4px;">${escapeHtml(props.env_actions)}</p>`);
	}
	if (key === "greenStore" && props.store_type) {
		lines.push(`<p style="color:#67baca;font-size:0.75rem;margin-top:4px;">${escapeHtml(props.store_type)}</p>`);
	}
	if (key === "foodBank" && props.org_type) {
		lines.push(`<p style="color:#a37cf6;font-size:0.75rem;margin-top:4px;">${escapeHtml(props.org_type)}</p>`);
	}
	return `<div style="padding:10px 12px;font-family:'微軟正黑體','Microsoft JhengHei',sans-serif;">${lines.join("")}</div>`;
}

function attachHoverPopup(layerId, key) {
	if (!mapStore.map) return;
	const map = mapStore.map;

	map.on("mouseenter", layerId, () => {
		map.getCanvas().style.cursor = "pointer";
	});

	map.on("mousemove", layerId, (e) => {
		if (!e.features?.length) return;
		const feature = e.features[0];
		const coords = feature.geometry.coordinates.slice();
		const popup = ensureHoverPopup();
		popup
			.setLngLat(coords)
			.setHTML(buildPopupHtml(key, feature.properties || {}))
			.addTo(map);
		setHighlightFeature(feature);
	});

	map.on("mouseleave", layerId, () => {
		map.getCanvas().style.cursor = "";
		hoverPopup?.remove();
		setHighlightFeature(null);
	});

	map.on("click", layerId, (e) => {
		if (!e.features?.length) return;
		const feature = e.features[0];
		const coords = feature.geometry.coordinates.slice();

		// 路線模式：把點擊的點當成起點 / 終點
		if (routeStep.value === "pick-start") {
			routeStart.value = { lng: coords[0], lat: coords[1], name: feature.properties?.name };
			setStartMarker(routeStart.value);
			routeStep.value = "pick-end";
			dialogStore.showNotification("info", "請點選終點");
			return;
		}
		if (routeStep.value === "pick-end") {
			routeEnd.value = { lng: coords[0], lat: coords[1], name: feature.properties?.name };
			setEndMarker(routeEnd.value);
			routeStep.value = null;
			drawRoute();
			return;
		}

		// 一般點擊：hover popup 拿掉，改用持續性 click popup（有關閉鈕）
		hoverPopup?.remove();
		setHighlightFeature(null);
		// 拉到夠近的 zoom 讓相鄰點自然分開
		map.flyTo({
			center: coords,
			zoom: Math.max(map.getZoom(), 16),
			duration: 600,
		});
		// 圈圈累加（每次點擊保留）
		addClickedFeature(feature);
		clickPopup?.remove();
		clickPopup = new mapboxGl.Popup({
			closeButton: true,
			closeOnClick: false,
			offset: 14,
			anchor: "bottom",
		})
			.setLngLat(coords)
			.setHTML(buildPopupHtml(key, feature.properties || {}))
			.addTo(map);
		clickPopup.on("close", () => {
			// 只關 popup，圈圈保留；要清光圈圈用 UI 上的「清除選取」
			clickPopup = null;
		});
	});
}

function applyLayerCityFilter(layerId, cityValue) {
	if (!mapStore.map?.getLayer(layerId)) return;
	if (cityValue === "metrotaipei") {
		mapStore.map.setFilter(layerId, null);
	} else {
		mapStore.map.setFilter(layerId, ["==", ["get", "city"], CITY_LABEL[cityValue]]);
	}
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
		// 同步當前 activeCity 的篩選
		const indexKey = indexOfKey(key);
		if (indexKey) {
			applyLayerCityFilter(layerId, activeCityMap[indexKey]);
		}
	}
}

function shouldDisable(key) {
	return mapStore.isPreloading || featureCache.value[key].length === 0;
}

function handleMoreInfo(item) {
	// 把當前 city tag 注入 dialog，避免 cityManager 預設帶出 [雙北, 臺北市] 雙標籤
	dialogStore.showMoreInfo({
		...item,
		city_tag_override: tagListOf(item),
	});
}

// ── 城市切換 ─────────────────────────────────────────────────────────────
function handleChangeCity(component, cityValue) {
	activeCityMap[component.index] = cityValue;
	component.city = cityValue;
	if (component.map_config?.[0]) {
		component.map_config[0].city = cityValue;
	}
	switch (component.index) {
	case "eco_diet_restaurants_points":
		recomputeC1a();
		applyLayerCityFilter(RESTAURANT_LAYER_ID, cityValue);
		break;
	case "eco_diet_restaurants_density":
		recomputeC1b();
		break;
	case "eco_diet_restaurants_count_city":
		recomputeC2();
		break;
	case "eco_diet_green_stores_points":
		recomputeC4();
		applyLayerCityFilter(GREEN_STORE_LAYER_ID, cityValue);
		break;
	case "eco_diet_waste_yearly":
		recomputeC5();
		break;
	case "eco_diet_food_banks_points":
		recomputeC7a();
		applyLayerCityFilter(FOOD_BANK_LAYER_ID, cityValue);
		break;
	}
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
	hoverPopup?.remove();
	hoverPopup = null;
	clickPopup?.remove();
	clickPopup = null;
	routeStartMarker?.remove();
	routeStartMarker = null;
	routeEndMarker?.remove();
	routeEndMarker = null;
	if (!mapStore.map) return;
	[RESTAURANT_LAYER_ID, GREEN_STORE_LAYER_ID, FOOD_BANK_LAYER_ID].forEach((id) => {
		if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
		if (mapStore.map.getSource(`${id}-source`)) {
			mapStore.map.removeSource(`${id}-source`);
		}
	});
	[HOVER_HIGHLIGHT_LAYER_ID, CLICK_HIGHLIGHT_LAYER_ID].forEach((id) => {
		if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
		if (mapStore.map.getSource(`${id}-source`)) {
			mapStore.map.removeSource(`${id}-source`);
		}
	});
	[`${ROUTE_LAYER_ID}-halo`, ROUTE_LAYER_ID].forEach((id) => {
		if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
	});
	if (mapStore.map.getSource(ROUTE_SOURCE_ID)) {
		mapStore.map.removeSource(ROUTE_SOURCE_ID);
	}
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
function indexOfKey(key) {
	if (key === "restaurant") return "eco_diet_restaurants_points";
	if (key === "greenStore") return "eco_diet_green_stores_points";
	if (key === "foodBank") return "eco_diet_food_banks_points";
	return null;
}

// 顯示什麼資料就標什麼 tag（避免動 cityManager 造成主站連動）
function tagListOf(component) {
	const cityValue = activeCityMap[component.index];
	if (cityValue === "taipei") return [{ name: "臺北市", value: "taipei" }];
	if (cityValue === "newtaipei") return [{ name: "新北市", value: "newtaipei" }];
	return [{ name: "雙北", value: "metrotaipei" }];
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
      :key="`${item.index}-${activeCityMap[item.index]}`"
      :config="item"
      mode="default"
      :info-btn="true"
      :active-city="activeCityMap[item.index]"
      :select-btn="true"
      :select-btn-list="CITY_SELECT_LIST"
      :city-tag="tagListOf(item)"
      @info="handleMoreInfo"
      @change-city="(city) => handleChangeCity(item, city)"
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
        :key="`map-${item.index}-${activeCityMap[item.index]}`"
        :config="item"
        mode="map"
        :info-btn="true"
        :active-city="activeCityMap[item.index]"
        :select-btn="true"
        :select-btn-list="CITY_SELECT_LIST"
        :city-tag="tagListOf(item)"
        :toggle-on="toggleOn[toggleKeyOf(item)]"
        :toggle-disable="shouldDisable(toggleKeyOf(item))"
        @info="handleMoreInfo"
        @toggle="(v) => handleToggle(v, toggleKeyOf(item), layerIdOf(item))"
        @change-city="(city) => handleChangeCity(item, city)"
      />
      <!-- 無空間資料組件 section（h2 + 3 個聚合卡片，無地圖層所以用 default 模式直接展開）-->
      <h2 v-if="noMapComponents.length > 0">
        無空間資料組件
      </h2>
      <DashboardComponent
        v-for="item in noMapComponents"
        :key="`nomap-${item.index}-${activeCityMap[item.index]}`"
        :config="item"
        mode="default"
        :info-btn="true"
        :active-city="activeCityMap[item.index]"
        :select-btn="true"
        :select-btn-list="CITY_SELECT_LIST"
        :city-tag="tagListOf(item)"
        @info="handleMoreInfo"
        @change-city="(city) => handleChangeCity(item, city)"
      />
    </div>
    <MapContainer />
    <!-- 步行 icon 按鈕：放在區/里/近 按鈕同一垂直軸下方，預設收合 -->
    <button
      class="ecodietview-walkbtn"
      :class="{ 'ecodietview-walkbtn-active': routePanelOpen }"
      title="步行路線"
      @click="toggleRoutePanel"
    >
      <span>directions_walk</span>
    </button>
    <!-- 可拖曳的步行路線視窗：開啟時 fixed 定位，header 可拖 -->
    <div
      v-if="routePanelOpen"
      class="ecodietview-route"
      :style="{ left: `${panelPos?.x ?? 0}px`, top: `${panelPos?.y ?? 0}px` }"
    >
      <div
        class="ecodietview-route-header"
        @mousedown="onPanelDragStart"
      >
        <span>directions_walk</span>
        <h3>步行路線</h3>
        <button
          class="ecodietview-route-closebtn"
          title="關閉"
          @click="routePanelOpen = false"
        >
          <span>close</span>
        </button>
      </div>
      <div
        v-if="!routeStep && !routeStats && !routeLoading"
        class="ecodietview-route-actions"
      >
        <button
          class="ecodietview-route-btn"
          @click="startRouteFromCurrent"
        >
          從目前位置出發
        </button>
        <button
          class="ecodietview-route-btn"
          @click="startRoutePickTwo"
        >
          選兩個點位
        </button>
        <p class="ecodietview-route-hint">
          先打開圖層再點選點位
        </p>
      </div>
      <div
        v-else-if="routeStep"
        class="ecodietview-route-status"
      >
        <p>{{ routeStep === 'pick-start' ? '請點選起點' : '請點選終點' }}</p>
        <button
          class="ecodietview-route-btn ecodietview-route-btn-cancel"
          @click="clearRoute"
        >
          取消
        </button>
      </div>
      <div
        v-else-if="routeLoading"
        class="ecodietview-route-status"
      >
        <p>計算路徑中 ⋯</p>
      </div>
      <div
        v-else-if="routeStats"
        class="ecodietview-route-stats"
      >
        <div class="ecodietview-route-stats-row">
          <span>straighten</span>
          <p>{{ formatDistance(routeStats.distanceMeters) }}</p>
        </div>
        <div class="ecodietview-route-stats-row">
          <span>schedule</span>
          <p>{{ formatDuration(routeStats.durationSeconds) }}</p>
        </div>
        <p
          v-if="routeStart?.name && routeEnd?.name"
          class="ecodietview-route-stats-od"
        >
          {{ routeStart.name }} → {{ routeEnd.name }}
        </p>
        <button
          class="ecodietview-route-btn ecodietview-route-btn-cancel"
          @click="clearRoute"
        >
          清除路線
        </button>
      </div>
      <!-- 進入 route mode 後才出現「清除選取」-->
      <button
        v-if="inRouteMode && clickedFeatures.length > 0"
        class="ecodietview-route-btn ecodietview-route-btn-secondary"
        @click="clearClickedFeatures"
      >
        清除選取（{{ clickedFeatures.length }}）
      </button>
    </div>
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
		position: relative;
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

	&-walkbtn {
		width: 1.75rem;
		height: 1.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		position: absolute;
		right: 10px;
		top: 252px;
		border-radius: 50%;
		background-color: white;
		transition: color 0.2s, background-color 0.2s;
		z-index: 4;
		cursor: pointer;

		span {
			color: var(--color-component-background);
			font-size: 1.2rem;
			font-family: var(--font-icon);
		}

		&-active {
			background-color: #ff5e3a;

			span {
				color: white;
			}
		}

		&:hover {
			background-color: #ff5e3a;

			span {
				color: white;
			}
		}
	}

	&-route {
		min-width: 240px;
		max-width: 280px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		position: fixed;
		padding: var(--font-s) var(--font-m) var(--font-m) var(--font-m);
		border-radius: 6px;
		background-color: var(--color-component-background);
		font-family: '微軟正黑體', 'Microsoft JhengHei', sans-serif;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
		z-index: 10;
		user-select: none;

		&-header {
			display: flex;
			align-items: center;
			gap: 6px;
			padding-bottom: 4px;
			cursor: move;

			span {
				color: #ff5e3a;
				font-family: var(--font-icon);
				font-size: var(--font-m);
			}

			h3 {
				flex: 1;
				color: var(--color-normal-text);
				font-size: var(--font-ms);
				font-weight: 500;
			}
		}

		&-closebtn {
			width: 22px;
			height: 22px;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 4px;
			background-color: transparent;
			cursor: pointer;
			transition: background-color 0.15s;

			&:hover {
				background-color: var(--color-border);
			}

			span {
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				font-size: var(--font-ms);
			}
		}

		&-actions {
			display: flex;
			flex-direction: column;
			gap: 6px;
		}

		&-status,
		&-stats {
			display: flex;
			flex-direction: column;
			gap: 6px;

			p {
				color: var(--color-normal-text);
				font-size: var(--font-s);
			}
		}

		&-stats {
			&-row {
				display: flex;
				align-items: center;
				gap: 6px;

				span {
					color: var(--color-complement-text);
					font-family: var(--font-icon);
					font-size: var(--font-m);
				}

				p {
					color: var(--color-normal-text);
					font-size: var(--font-ms);
					font-weight: 500;
				}
			}

			&-od {
				color: var(--color-complement-text) !important;
				font-size: var(--font-s) !important;
			}
		}

		&-hint {
			color: var(--color-complement-text);
			font-size: 11px;
			font-style: italic;
		}

		&-btn {
			padding: 6px 10px;
			border-radius: 4px;
			background-color: #ff5e3a;
			color: var(--color-normal-text);
			font-size: var(--font-s);
			text-align: center;
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.85;
			}

			&-cancel {
				background-color: var(--color-border);
			}

			&-secondary {
				background-color: var(--color-border);
				font-size: 11px;
				padding: 4px 8px;
			}
		}
	}
}
</style>
