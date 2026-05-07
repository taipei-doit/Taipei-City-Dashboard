<!-- 步行路線規劃浮窗 + walk icon FAB，僅在 EcoDiet mapview 時掛載 -->
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import mapboxGl from "mapbox-gl";
import { useDialogStore } from "../store/dialogStore";
import { useMapStore } from "../store/mapStore";

const dialogStore = useDialogStore();
const mapStore = useMapStore();

// ── 路線 layer / source ID ────────────────────────────────────────────────
const ROUTE_LAYER_ID = "eco-diet-walking-route";
const ROUTE_SOURCE_ID = `${ROUTE_LAYER_ID}-source`;
const ROUTE_COLOR = "#ff5e3a";
const ROUTE_HALO_COLOR = "#ffffff";

// ── 步行路線狀態 ──────────────────────────────────────────────────────────
const routeStep = ref(null); // null | "pick-start" | "pick-end"
const routeStart = ref(null); // { lng, lat, name }
const routeEnd = ref(null);
const routeStats = ref(null); // { distanceMeters, durationSeconds }
const routeLoading = ref(false);
let routeStartMarker = null;
let routeEndMarker = null;

// ── 面板開關 + 拖曳位置 ───────────────────────────────────────────────────
const routePanelOpen = ref(false);
const panelPos = ref(null);

const inRouteMode = computed(() => Boolean(routeStep.value || routeStats.value));

// ── 點位 highlight（支援路線 pick 模式下的 click 累積圈圈）───────────────
const CLICK_HIGHLIGHT_LAYER_ID = "eco-diet-click-highlight";
const CLICK_HIGHLIGHT_SOURCE_ID = `${CLICK_HIGHLIGHT_LAYER_ID}-source`;
const clickedFeatures = ref([]);

function syncClickedFeaturesToSource() {
	const source = mapStore.map?.getSource(CLICK_HIGHLIGHT_SOURCE_ID);
	if (!source) return;
	source.setData({ type: "FeatureCollection", features: clickedFeatures.value });
}

function addClickedFeature(feature) {
	clickedFeatures.value = [
		...clickedFeatures.value.slice(-4),
		{ type: "Feature", geometry: feature.geometry, properties: feature.properties },
	];
	syncClickedFeaturesToSource();
}

function clearClickedFeatures() {
	clickedFeatures.value = [];
	syncClickedFeaturesToSource();
}

// ── panel 位置 ────────────────────────────────────────────────────────────
function ensurePanelPos(eventTarget) {
	if (panelPos.value) return;
	const target = eventTarget || document.querySelector(".ecodiet-walkbtn");
	const btnRect = target?.getBoundingClientRect?.();
	if (btnRect && Number.isFinite(btnRect.left)) {
		panelPos.value = {
			x: Math.max(20, btnRect.left - 280),
			y: btnRect.top,
		};
	} else {
		panelPos.value = { x: Math.max(20, window.innerWidth - 320), y: 252 };
	}
}

function toggleRoutePanel(e) {
	if (routePanelOpen.value) {
		routePanelOpen.value = false;
		return;
	}
	routePanelOpen.value = true;
	ensurePanelPos(e?.currentTarget);
}

function onPanelDragStart(e) {
	if (e.button !== 0) return;
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

// ── route layer 建立 ──────────────────────────────────────────────────────
function ensureRouteLayer() {
	if (!mapStore.map || mapStore.map.getLayer(ROUTE_LAYER_ID)) return;
	mapStore.map.addSource(ROUTE_SOURCE_ID, {
		type: "geojson",
		data: { type: "FeatureCollection", features: [] },
	});
	mapStore.map.addLayer({
		id: `${ROUTE_LAYER_ID}-halo`,
		type: "line",
		source: ROUTE_SOURCE_ID,
		layout: { "line-join": "round", "line-cap": "round" },
		paint: { "line-color": ROUTE_HALO_COLOR, "line-width": 8, "line-opacity": 0.5 },
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

// ── marker helpers ────────────────────────────────────────────────────────
function makeEndpointMarkerEl(label, color) {
	const el = document.createElement("div");
	el.style.cssText = `
		width:22px;height:22px;border-radius:50%;
		background:${color};border:3px solid #fff;
		box-shadow:0 0 6px rgba(0,0,0,0.5);
		display:flex;align-items:center;justify-content:center;
		color:#fff;font-size:11px;font-weight:600;
		font-family:'微軟正黑體','Microsoft JhengHei',sans-serif;
	`;
	el.textContent = label;
	return el;
}

function setStartMarker(coords) {
	routeStartMarker?.remove();
	routeStartMarker = null;
	if (!coords || !mapStore.map) return;
	routeStartMarker = new mapboxGl.Marker({ element: makeEndpointMarkerEl("A", "#00c853") })
		.setLngLat([coords.lng, coords.lat])
		.addTo(mapStore.map);
}

function setEndMarker(coords) {
	routeEndMarker?.remove();
	routeEndMarker = null;
	if (!coords || !mapStore.map) return;
	routeEndMarker = new mapboxGl.Marker({ element: makeEndpointMarkerEl("B", ROUTE_COLOR) })
		.setLngLat([coords.lng, coords.lat])
		.addTo(mapStore.map);
}

// ── Mapbox Directions API ─────────────────────────────────────────────────
async function fetchWalkingRoute(start, end) {
	const token = mapboxGl.accessToken;
	const coords = `${start.lng},${start.lat};${end.lng},${end.lat}`;
	const url = `https://api.mapbox.com/directions/v5/mapbox/walking/${coords}?geometries=geojson&overview=full&access_token=${token}`;
	const res = await fetch(url);
	if (!res.ok) throw new Error(`Directions API ${res.status}`);
	const json = await res.json();
	if (!json.routes?.length) throw new Error("找不到可行路徑");
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

function clearRoute() {
	routeStep.value = null;
	routeStart.value = null;
	routeEnd.value = null;
	routeStats.value = null;
	setStartMarker(null);
	setEndMarker(null);
	const source = mapStore.map?.getSource(ROUTE_SOURCE_ID);
	if (source) source.setData({ type: "FeatureCollection", features: [] });
}

async function pickEndProgrammatic(point) {
	routeEnd.value = { lng: point.lng, lat: point.lat, name: point.name };
	setEndMarker(routeEnd.value);
	routeStep.value = null;
	await drawRoute();
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
	const latest = clickedFeatures.value[clickedFeatures.value.length - 1];
	if (latest) {
		const [lng, lat] = latest.geometry.coordinates;
		routeStart.value = { lng, lat, name: latest.properties?.name };
		clearClickedFeatures();
		routeEnd.value = null;
		routeStats.value = null;
		setEndMarker(null);
		const source = mapStore.map?.getSource(ROUTE_SOURCE_ID);
		source?.setData({ type: "FeatureCollection", features: [] });
		setStartMarker(routeStart.value);
		routeStep.value = "pick-end";
		dialogStore.showNotification("info", "已用最後點擊的點當起點，請點選終點");
		return;
	}
	clearRoute();
	routeStep.value = "pick-start";
	dialogStore.showNotification("info", "請打開圖層並點選一個點位作為起點");
}

// ── 供 parent（EcoDietExtras）透過 apply-actions 呼叫 ────────────────────
async function simulateClickRouteToFacility(to) {
	if (!navigator.geolocation) {
		dialogStore.showNotification("error", "瀏覽器不支援定位 API");
		return;
	}
	clearRoute();
	panelPos.value = null;
	routePanelOpen.value = true;
	ensurePanelPos();
	const pos = await new Promise((resolve, reject) => {
		navigator.geolocation.getCurrentPosition(resolve, reject, {
			enableHighAccuracy: true,
			timeout: 5000,
		});
	}).catch(() => null);
	if (!pos) {
		dialogStore.showNotification("error", "取得位置失敗，請允許瀏覽器定位權限");
		return;
	}
	routeStart.value = {
		lng: pos.coords.longitude,
		lat: pos.coords.latitude,
		name: "目前位置",
	};
	setStartMarker(routeStart.value);
	routeStep.value = "pick-end";
	await pickEndProgrammatic(to);
}

defineExpose({ simulateClickRouteToFacility, routeStep, addClickedFeature, clearClickedFeatures, clickedFeatures });

// ── map click handler（pick-start / pick-end）────────────────────────────
function attachMapClickHandler() {
	if (!mapStore.map) return;
	mapStore.map.on("click", onMapClick);
}

function onMapClick(e) {
	if (!routeStep.value) return;
	const point = { lng: e.lngLat.lng, lat: e.lngLat.lat, name: null };
	// 嘗試取得最上層 feature 的名稱
	const features = mapStore.map.queryRenderedFeatures(e.point);
	if (features.length) point.name = features[0].properties?.name ?? null;

	if (routeStep.value === "pick-start") {
		routeStart.value = point;
		setStartMarker(routeStart.value);
		routeStep.value = "pick-end";
		dialogStore.showNotification("info", "請點選終點");
	} else if (routeStep.value === "pick-end") {
		pickEndProgrammatic(point);
	}
}

// ── formatters ────────────────────────────────────────────────────────────
function formatDistance(m) {
	if (m == null) return "—";
	return m >= 1000 ? `${(m / 1000).toFixed(2)} 公里` : `${Math.round(m)} 公尺`;
}
function formatDuration(s) {
	if (s == null) return "—";
	const min = Math.round(s / 60);
	return min < 60 ? `${min} 分鐘` : `${Math.floor(min / 60)} 小時 ${min % 60} 分鐘`;
}

// ── lifecycle ─────────────────────────────────────────────────────────────
onMounted(() => {
	// map 可能還沒 ready，等一個 tick 再掛
	const tryAttach = () => {
		if (mapStore.map) {
			attachMapClickHandler();
		} else {
			setTimeout(tryAttach, 200);
		}
	};
	tryAttach();
});

onBeforeUnmount(() => {
	mapStore.map?.off("click", onMapClick);
	routeStartMarker?.remove();
	routeStartMarker = null;
	routeEndMarker?.remove();
	routeEndMarker = null;
	if (mapStore.map) {
		[`${ROUTE_LAYER_ID}-halo`, ROUTE_LAYER_ID].forEach((id) => {
			if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
		});
		if (mapStore.map.getSource(ROUTE_SOURCE_ID)) {
			mapStore.map.removeSource(ROUTE_SOURCE_ID);
		}
		if (mapStore.map.getLayer(CLICK_HIGHLIGHT_LAYER_ID)) {
			mapStore.map.removeLayer(CLICK_HIGHLIGHT_LAYER_ID);
		}
		if (mapStore.map.getSource(CLICK_HIGHLIGHT_SOURCE_ID)) {
			mapStore.map.removeSource(CLICK_HIGHLIGHT_SOURCE_ID);
		}
	}
});
</script>

<template>
  <!-- 步行 icon 按鈕（fixed 定位，右下角） -->
  <button
    class="ecodiet-walkbtn"
    :class="{ 'ecodiet-walkbtn-active': routePanelOpen }"
    title="步行路線"
    @click="toggleRoutePanel"
  >
    <span>directions_walk</span>
  </button>

  <!-- 可拖曳步行路線面板 -->
  <div
    v-if="routePanelOpen"
    class="ecodiet-route"
    :style="{ left: `${panelPos?.x ?? 0}px`, top: `${panelPos?.y ?? 0}px` }"
  >
    <div
      class="ecodiet-route-header"
      @mousedown="onPanelDragStart"
    >
      <span>directions_walk</span>
      <h3>步行路線</h3>
      <button
        class="ecodiet-route-closebtn"
        title="關閉"
        @click="routePanelOpen = false"
      >
        <span>close</span>
      </button>
    </div>
    <div
      v-if="!routeStep && !routeStats && !routeLoading"
      class="ecodiet-route-actions"
    >
      <button
        class="ecodiet-route-btn"
        @click="startRouteFromCurrent"
      >
        從目前位置出發
      </button>
      <button
        class="ecodiet-route-btn"
        @click="startRoutePickTwo"
      >
        選兩個點位
      </button>
      <p class="ecodiet-route-hint">
        先打開圖層再點選點位
      </p>
    </div>
    <div
      v-else-if="routeStep"
      class="ecodiet-route-status"
    >
      <p>{{ routeStep === 'pick-start' ? '請點選起點' : '請點選終點' }}</p>
      <button
        class="ecodiet-route-btn ecodiet-route-btn-cancel"
        @click="clearRoute"
      >
        取消
      </button>
    </div>
    <div
      v-else-if="routeLoading"
      class="ecodiet-route-status"
    >
      <p>計算路徑中 ⋯</p>
    </div>
    <div
      v-else-if="routeStats"
      class="ecodiet-route-stats"
    >
      <div class="ecodiet-route-stats-row">
        <span>straighten</span>
        <p>{{ formatDistance(routeStats.distanceMeters) }}</p>
      </div>
      <div class="ecodiet-route-stats-row">
        <span>schedule</span>
        <p>{{ formatDuration(routeStats.durationSeconds) }}</p>
      </div>
      <p
        v-if="routeStart?.name && routeEnd?.name"
        class="ecodiet-route-stats-od"
      >
        {{ routeStart.name }} → {{ routeEnd.name }}
      </p>
      <button
        class="ecodiet-route-btn ecodiet-route-btn-cancel"
        @click="clearRoute"
      >
        清除路線
      </button>
    </div>
    <button
      v-if="inRouteMode && clickedFeatures.length > 0"
      class="ecodiet-route-btn ecodiet-route-btn-secondary"
      @click="clearClickedFeatures"
    >
      清除選取（{{ clickedFeatures.length }}）
    </button>
  </div>
</template>

<style scoped lang="scss">
.ecodiet-walkbtn {
	width: 44px;
	height: 44px;
	display: flex;
	align-items: center;
	justify-content: center;
	position: fixed;
	right: 32px;
	bottom: 176px;
	border: none;
	border-radius: 50%;
	background: var(--color-component-background);
	border: 1px solid var(--color-border);
	color: var(--color-normal-text);
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
	cursor: pointer;
	transition: background 0.15s ease;
	z-index: 11;

	span {
		font-family: var(--font-icon);
		font-size: 22px;
	}

	&:hover,
	&-active {
		background: #ff5e3a;
		color: #fff;
		border-color: #ff5e3a;
	}
}

.ecodiet-route {
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
</style>
