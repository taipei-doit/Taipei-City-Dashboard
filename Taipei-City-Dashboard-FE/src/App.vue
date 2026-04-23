<!-- Developed By Taipei Urban Intelligence Center 2023-2024 -->
<!-- 
Lead Developer:  Igor Ho (Full Stack Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<script setup>
import {
	onBeforeMount,
	onMounted,
	onBeforeUnmount,
	ref,
	computed,
	watch,
	nextTick,
} from "vue";

import { useRoute } from "vue-router";
import { useAuthStore } from "./store/authStore";
import { useDialogStore } from "./store/dialogStore";
import { useContentStore } from "./store/contentStore";
import { useMapStore } from "./store/mapStore";

import NavBar from "./components/utilities/bars/NavBar.vue";
import SideBar from "./components/utilities/bars/SideBar.vue";
import AdminSideBar from "./components/utilities/bars/AdminSideBar.vue";
import SettingsBar from "./components/utilities/bars/SettingsBar.vue";
import NotificationBar from "./components/dialogs/NotificationBar.vue";
import InitialWarning from "./components/dialogs/InitialWarning.vue";
import ComponentSideBar from "./components/utilities/bars/ComponentSideBar.vue";
import LogIn from "./components/dialogs/LogIn.vue";
import ChatBox from "./components/dialogs/ChatBox.vue";
import ChatBotIcon from "./components/icons/ChatBotIcon.vue";

const authStore = useAuthStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();
const timeToUpdate = ref(600);

const mapStore = useMapStore();
const route = useRoute();
const updateBoards =
	import.meta.env.VITE_PERSONAL_BOARD_UPDATE?.split(",") || [];
const boardIndex = ref(null);
const board = ref(null);
const frequency = ref(600);
const isMappedToUpdateBoards = ref(false);
// Chatroom
const isChatBoxShow = ref(false);
const chatMode = ref("floating"); // 'floating' | 'sidebar'
// Timers
let chartTimer = null;
let crowdingTimer = null;
let timeTimer = null;
let mrtTimer = null;
// Update 狀態
let isCrowdingUpdating = false;

const updateBoardsMap = computed(() => {
	let needUpdateBoards = [];
	updateBoards.map((board) => {
		const id = board.split(":")[0];
		const updateSeconds = board.split(":")[1];
		needUpdateBoards.push({ id, frequency: updateSeconds });
	});
	return needUpdateBoards;
});

const formattedTimeToUpdate = computed(() => {
	const minutes = Math.floor(timeToUpdate.value / 60);
	const seconds = timeToUpdate.value % 60;
	return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
});

function reloadChartData() {
	if (!["dashboard", "mapview"].includes(authStore.currentPath)) return;
	contentStore.updateCurrentDashboardAllChartData();
	timeToUpdate.value = frequency.value;

	if (isMappedToUpdateBoards.value) {
		reloadMapData();
	}
}

async function reloadCrowdingChartData() {
	if (!["dashboard", "mapview"].includes(authStore.currentPath)) return;

	if (isCrowdingUpdating) return;

	isCrowdingUpdating = true;
	try {
		await contentStore.updateCurrentDashboardCertainChartData();
	} finally {
		isCrowdingUpdating = false;
	}
}

function updateTimeToUpdate() {
	if (!["dashboard", "mapview"].includes(authStore.currentPath)) return;
	if (timeToUpdate.value <= 0) {
		timeToUpdate.value = 0;
		reloadChartData();
		return;
	}
	timeToUpdate.value -= 5;
}

function reloadMapData() {
	if (!["mapview"].includes(authStore.currentPath)) return;
	mapStore.currentVisibleLayers.forEach((layerName) => {
		mapStore.map.removeLayer(layerName);
		if (mapStore.map.getSource(`${layerName}-source`)) {
			mapStore.map.removeSource(`${layerName}-source`);
		}
		const layerConfig = mapStore.mapConfigs[layerName];

		// 檢查 source
		if (layerConfig.source === "geojson") {
			// 如果 source 是 "geojson"，則使用 fetchLocalGeoJson
			mapStore.fetchLocalGeoJson(layerConfig);
		} else if (layerConfig.source === "raster") {
			// 如果 source 是 "raster"，則使用 addRasterSource
			mapStore.addRasterSource(layerConfig);
		}
	});
}

function reload3DMRTMapData() {
	if (!["mapview"].includes(authStore.currentPath)) return;
	mapStore.currentVisibleLayers.forEach((layerName) => {
		const layerConfig = mapStore.mapConfigs[layerName];
		const lastUpdate = mapStore.layerUpdateTime[layerName];
		const now = Date.now();

		// 只刷新特定組件附屬圖層
		if (
			!layerConfig.title.includes("擁擠程度") ||
			!lastUpdate ||
			now - new Date(lastUpdate).getTime() < 1.5 * 60 * 1000
		) {
			return;
		}

		mapStore.map.removeLayer(layerName);
		if (mapStore.map.getSource(`${layerName}-source`)) {
			mapStore.map.removeSource(`${layerName}-source`);
		}

		// 檢查 source
		if (layerConfig.source === "geojson") {
			// 如果 source 是 "geojson"，則使用 fetchLocalGeoJson
			mapStore.fetchLocalGeoJson(layerConfig);
		} else if (layerConfig.source === "raster") {
			// 如果 source 是 "raster"，則使用 addRasterSource
			mapStore.addRasterSource(layerConfig);
		}
	});
}

// Chatroom 功能顯示隱藏
const wasDragged = ref(false);
const snapSide = ref("right");   // 'left' | 'right'
const alignMode = ref("end");    // 'end' = 圖示在下（聊天框往上）| 'start' = 圖示在上（聊天框往下）
const isSidebarOpen = computed(() => chatMode.value === "sidebar" && isChatBoxShow.value);

// dragPos.y = 圖示底部到視窗頂部的距離（iconBottomY），與 alignMode 共同決定 CSS
const CHATBOX_H = 500;
const ICON_H = 70;
const SNAP_MARGIN = 24;

function chatbotBtnHandler() {
	if (wasDragged.value) {
		wasDragged.value = false;
		return;
	}
	isChatBoxShow.value = !isChatBoxShow.value;
}

function onChatModeChange(mode) {
	chatMode.value = mode;
}

function onChatClose() {
	isChatBoxShow.value = false;
	chatMode.value = "floating";
}

// 聊天框開啟時：根據圖示位置決定聊天框要往上還是往下展開
watch(isChatBoxShow, async (isOpen) => {
	if (!isOpen || dragPos.value.y === null) return;
	await nextTick();
	const vh = window.innerHeight;
	const iconBottomY = dragPos.value.y;
	if (iconBottomY - CHATBOX_H >= SNAP_MARGIN) {
		alignMode.value = "end";
	} else {
		alignMode.value = "start";
		const maxY = vh - CHATBOX_H + ICON_H - SNAP_MARGIN;
		if (dragPos.value.y > maxY) {
			dragPos.value = { ...dragPos.value, y: maxY };
		}
	}
});

// 拖曳邏輯（dragPos.y = iconBottomY：圖示底部距視窗頂部距離）
const chatbotContainerRef = ref(null);
const dragPos = ref({ x: null, y: null });
const isDragging = ref(false);

function snapToEdge(leftX, iconBottomY) {
	const el = chatbotContainerRef.value;
	if (!el) return { x: SNAP_MARGIN, y: iconBottomY };
	const w = el.offsetWidth;
	const vw = window.innerWidth;
	const vh = window.innerHeight;

	// 決定上下對齊：優先讓聊天框往上（end），空間不夠時改往下（start）
	const hasSpaceAbove = iconBottomY - CHATBOX_H >= SNAP_MARGIN;
	alignMode.value = hasSpaceAbove ? "end" : "start";

	let clampedY;
	if (alignMode.value === "end") {
		// 聊天框往上：確保 container 頂部不超出視窗頂
		clampedY = Math.max(SNAP_MARGIN + CHATBOX_H, Math.min(iconBottomY, vh - SNAP_MARGIN));
	} else {
		// 聊天框往下：確保 container 底部不超出視窗底
		clampedY = Math.max(SNAP_MARGIN + ICON_H, Math.min(iconBottomY, vh - CHATBOX_H + ICON_H - SNAP_MARGIN));
	}

	snapSide.value = leftX + w / 2 < vw / 2 ? "left" : "right";
	return { x: SNAP_MARGIN, y: clampedY };
}

function onChatbotBtnAreaMousedown(e) {
	const el = chatbotContainerRef.value;
	if (!el) return;
	const rect = el.getBoundingClientRect();
	const startX = e.clientX;
	const startY = e.clientY;
	const offsetX = e.clientX - rect.left;
	// 圖示底部 Y（alignMode 決定圖示在 container 頂或底）
	const startIconBottomY = alignMode.value === "start" ? rect.top + ICON_H : rect.bottom;
	const offsetFromIconBottom = e.clientY - startIconBottomY;
	let hasDragged = false;

	const onMouseMove = (ev) => {
		const dx = ev.clientX - startX;
		const dy = ev.clientY - startY;
		if (!hasDragged && Math.sqrt(dx * dx + dy * dy) > 4) {
			hasDragged = true;
			isDragging.value = true;
			dragPos.value = { x: rect.left, y: startIconBottomY };
		}
		if (!hasDragged) return;
		const newX = ev.clientX - offsetX;
		const newIconBottomY = ev.clientY - offsetFromIconBottom;
		dragPos.value = {
			x: Math.max(0, Math.min(newX, window.innerWidth - el.offsetWidth)),
			y: Math.max(SNAP_MARGIN + ICON_H, Math.min(newIconBottomY, window.innerHeight - SNAP_MARGIN)),
		};
	};

	const onMouseUp = () => {
		if (hasDragged) {
			wasDragged.value = true;
			dragPos.value = snapToEdge(dragPos.value.x, dragPos.value.y);
		}
		isDragging.value = false;
		document.removeEventListener("mousemove", onMouseMove);
		document.removeEventListener("mouseup", onMouseUp);
	};

	document.addEventListener("mousemove", onMouseMove);
	document.addEventListener("mouseup", onMouseUp);
}

const chatbotContainerStyle = computed(() => {
	if (chatMode.value === "sidebar") {
		return { top: "0", right: "0", bottom: "0", left: "auto" };
	}
	if (dragPos.value.y === null) return {};

	const vh = window.innerHeight;
	const iconBottomY = dragPos.value.y;

	// Y 方向：end = 圖示在下（container 用 bottom 定位），start = 圖示在上（container 用 top 定位）
	const yStyle = alignMode.value === "start"
		? { top: `${iconBottomY - ICON_H}px`, bottom: "auto" }
		: { bottom: `${vh - iconBottomY}px`, top: "auto" };

	// X 方向：拖曳中用 left，吸附後右側用 right、左側用 left
	let xStyle;
	if (isDragging.value) {
		xStyle = { left: `${dragPos.value.x}px`, right: "auto" };
	} else if (snapSide.value === "right") {
		xStyle = { right: `${dragPos.value.x}px`, left: "auto" };
	} else {
		xStyle = { left: `${dragPos.value.x}px`, right: "auto" };
	}

	return { ...yStyle, ...xStyle };
});

(watch(
	() => route.query,
	(query) => {
		boardIndex.value = query.index;
		board.value = updateBoardsMap.value.find((board) => {
			return board.id === boardIndex.value;
		});
		frequency.value = board.value ? board.value.frequency : 600;
		isMappedToUpdateBoards.value = updateBoardsMap.value.some((board) => {
			return board.id === query.index;
		});
		timeToUpdate.value = frequency.value;
	},
),
{ immediate: true });

onBeforeMount(() => {
	authStore.initialChecks();

	let vh = window.innerHeight * 0.01;
	document.documentElement.style.setProperty("--vh", `${vh}px`);

	window.addEventListener("resize", () => {
		let vh = window.innerHeight * 0.01;
		document.documentElement.style.setProperty("--vh", `${vh}px`);
	});
	// contentStore.wsConnect();
});
onMounted(() => {
	const showInitialWarning = localStorage.getItem("initialWarning");

	if (!showInitialWarning && !window.location.pathname.includes("embed")) {
		dialogStore.showDialog("initialWarning");
	}

	chartTimer = setInterval(reloadChartData, 1000 * frequency.value);
	crowdingTimer = setInterval(reloadCrowdingChartData, 1000 * 60);
	timeTimer = setInterval(updateTimeToUpdate, 1000 * 5);
	mrtTimer = setInterval(reload3DMRTMapData, 1000 * 10);
});
onBeforeUnmount(() => {
	clearInterval(chartTimer);
	clearInterval(crowdingTimer);
	clearInterval(timeTimer);
	clearInterval(mrtTimer);
	// contentStore.wsDisconnect();
});
</script>

<template>
  <div class="app-container" :class="{ 'chatbot-sidebar-open': isSidebarOpen }">
    <NotificationBar />
    <NavBar v-if="authStore.currentPath !== 'embed'" />
    <!-- /mapview, /dashboard layouts -->
    <div
      v-if="
        authStore.currentPath === 'mapview' ||
          authStore.currentPath === 'dashboard'
      "
      class="app-content"
    >
      <SideBar />
      <div class="app-content-main">
        <SettingsBar />
        <RouterView />
      </div>
    </div>
    <!-- /admin layouts -->
    <div
      v-else-if="authStore.currentPath === 'admin'"
      class="app-content"
    >
      <AdminSideBar />
      <div class="app-content-main">
        <RouterView />
      </div>
    </div>
    <!-- /component, /component/:index layouts -->
    <div
      v-else-if="authStore.currentPath.includes('component')"
      class="app-content"
    >
      <ComponentSideBar />
      <div class="app-content-main">
        <RouterView />
      </div>
    </div>
    <div v-else>
      <router-view />
    </div>
    <InitialWarning />
    <LogIn />
    <div
      v-if="
        ['dashboard', 'mapview'].includes(authStore.currentPath) &&
          !authStore.isMobile &&
          !authStore.isNarrowDevice
      "
      class="app-update"
    >
      <p>下次更新：{{ formattedTimeToUpdate }}</p>
    </div>
    <div
      ref="chatbotContainerRef"
      class="chatbot-container"
      :class="{
        'is-dragging': isDragging,
        'snap-left': snapSide === 'left',
        'sidebar-mode': chatMode === 'sidebar',
        'align-start': alignMode === 'start',
      }"
      :style="chatbotContainerStyle"
    >
      <ChatBox
        v-if="isChatBoxShow"
        class="chatbox"
        :mode="chatMode"
        @change-mode="onChatModeChange"
        @close="onChatClose"
      />
      <div
        v-if="!(isChatBoxShow && chatMode === 'sidebar')"
        class="chatbot-btn-area"
        @mousedown.prevent="onChatbotBtnAreaMousedown"
      >
        <button
          class="chatbot-btn"
          @click="chatbotBtnHandler"
        >
          <ChatBotIcon />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.app {
	&-container {
		max-width: 100vw;
		max-height: 100vh;
		max-height: calc(var(--vh) * 100);
		transition: max-width 0.25s ease;

		&.chatbot-sidebar-open {
			max-width: calc(100vw - 400px);
		}
	}

	&-content {
		width: 100vw;
		max-width: 100vw;
		height: calc(100vh - 60px);
		height: calc(var(--vh) * 100 - 60px);
		display: flex;
		transition: width 0.25s ease, max-width 0.25s ease;

		&-main {
			width: 100%;
			display: flex;
			flex-direction: column;
		}
	}

	&-update {
		position: fixed;
		bottom: 0;
		right: 20px;
		color: white;
		opacity: 0.3;
		transition: opacity 0.3s;
		user-select: none;

		p {
			color: var(--color-complement-text);
		}

		&:hover {
			opacity: 1;
		}
	}
}

.app-container.chatbot-sidebar-open .app-content {
	width: calc(100vw - 400px);
	max-width: calc(100vw - 400px);
}

// Chatroom 樣式
.chatbot-container {
	position: fixed;
	bottom: 1.5rem;
	right: 1.5rem;
	display: flex;
	align-items: flex-end;
	gap: 1rem;
	z-index: 10;
	transition: left 0.25s ease, right 0.25s ease, top 0.25s ease, bottom 0.25s ease;

	&.is-dragging {
		transition: none;
		user-select: none;
	}

	// 圖示在左側時，聊天框展開於右側
	&.snap-left {
		flex-direction: row-reverse;
	}

	// 圖示在上方時，align-items 改為 flex-start（聊天框往下展開）
	&.align-start {
		align-items: flex-start;
	}

	// 側邊欄模式
	&.sidebar-mode {
		top: 0;
		right: 0;
		bottom: 0;
		left: auto;
		flex-direction: column;
		align-items: stretch;
		gap: 0;

		.chatbox {
			width: 400px;
			height: 100%;
			margin-bottom: 0;
		}
	}

	.chatbox {
		width: 400px;
		height: 500px;
	}

	.chatbot-btn-area {
		display: flex;
		flex-direction: column;
		cursor: grab;

		&:active {
			cursor: grabbing;
		}

		.chatbot-btn {
			width: 70px;
			height: 70px;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 50%;
			background-color: #3b82f6;
			filter: brightness(1.5);
			transition: filter 0.2s;

			&:hover {
				filter: brightness(1);
			}
		}
	}
}

// 手機板隱藏小幫手
@media (max-width: 600px) {
	.chatbot-container {
		display: none;
	}
}
</style>
