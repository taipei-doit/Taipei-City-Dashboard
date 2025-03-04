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
import { onBeforeMount, onMounted, onBeforeUnmount, ref, computed, watch } from "vue";
import { useRoute } from "vue-router"
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

const authStore = useAuthStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();
const timeToUpdate = ref(600);

const mapStore = useMapStore();
const route = useRoute();
const updateBoards = import.meta.env.VITE_PERSONAL_BOARD_UPDATE?.split(',') || [];
const boardIndex = ref(null);
const board =ref(null);
const frequency = ref(600);
const isMappedToUpdateBoards =ref(false);

const updateBoardsMap = computed(()=>{
	let needUpdateBoards = []
	updateBoards.map((board) => {
		const id = board.split(':')[0];
		const updateSeconds = board.split(':')[1];
		needUpdateBoards.push({ id, frequency: updateSeconds });
	})
	return needUpdateBoards
})

const formattedTimeToUpdate = computed(() => {
	const minutes = Math.floor(timeToUpdate.value / 60);
	const seconds = timeToUpdate.value % 60;
	return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
});

function reloadChartData() {
	if (!["dashboard", "mapview"].includes(authStore.currentPath)) return;
	contentStore.setCurrentDashboardAllChartData();
	timeToUpdate.value = frequency.value;

	if (isMappedToUpdateBoards.value) {
		reloadMapData()
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

watch(() => route.query, (query) => {
	boardIndex.value = query.index;
	board.value = updateBoardsMap.value.find(board =>{
		return board.id === boardIndex.value
	})
	frequency.value = board.value ? board.value.frequency : 600;
	isMappedToUpdateBoards.value = updateBoardsMap.value.some(board =>{
		return board.id === query.index
	});
	timeToUpdate.value = frequency.value;

}), { immediate: true };

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

	setInterval(reloadChartData, 1000 * frequency.value);
	setInterval(updateTimeToUpdate, 1000 * 5);
});
onBeforeUnmount(() => {
	clearInterval(reloadChartData);
	clearInterval(updateTimeToUpdate);
	// contentStore.wsDisconnect();
});
</script>

<template>
  <div class="app-container">
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
  </div>
</template>

<style scoped lang="scss">
.app {
	&-container {
		max-width: 100vw;
		max-height: 100vh;
		max-height: calc(var(--vh) * 100);
	}

	&-content {
		width: 100vw;
		max-width: 100vw;
		height: calc(100vh - 60px);
		height: calc(var(--vh) * 100 - 60px);
		display: flex;

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
</style>
