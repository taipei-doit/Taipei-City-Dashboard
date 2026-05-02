<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
/* global gtag */
import { onMounted, computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../store/authStore";
import { useContentStore } from "../../store/contentStore";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";

import AddViewPoint from "../dialogs/AddViewPoint.vue";
import MobileLayers from "../dialogs/MobileLayers.vue";
import IncidentReport from "../dialogs/IncidentReport.vue";
import FindClosestPoint from "../dialogs/FindClosestPoint.vue";
import { savedLocations } from "../../assets/configs/mapbox/savedLocations.js";

const authStore = useAuthStore();
const mapStore = useMapStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();
const route = useRoute();
const isRoutePanelOpen = ref(false);
const routeStart = ref("");
const routeEnd = ref("");
const routeProfile = ref("mapbox/driving");
const routeMessage = ref("");
const isRouting = ref(false);
const routeProfileOptions = [
	{
		label: "開車",
		icon: "directions_car",
		value: "mapbox/driving",
	},
	{
		label: "步行",
		icon: "directions_walk",
		value: "mapbox/walking",
	},
	{
		label: "單車",
		icon: "directions_bike",
		value: "mapbox/cycling",
	},
];

const canUseFindClosestPoint = computed(() => {
	let pointLayerCount = 0;

	mapStore.currentVisibleLayers.forEach((layer) => {
		if (["circle", "symbol"].includes(layer.split("-")[1])) {
			pointLayerCount++;
		}
	});

	return pointLayerCount === 1;
});

// 尋找最近點時觸發GA自訂事件
function findClosestPointGA() {
	gtag('event','map_actions', {
		action_type: "尋找最近點",
		time: Date.now(),
  	})
}

const cinematicPitchValue = computed(() =>
	Math.round(mapStore.cinematicPitch),
);
const cinematicPitchLabel = computed(() => {
	if (mapStore.cinematicPitch < 18) return "俯視";
	if (mapStore.cinematicPitch < 50) return "中視";
	return "斜視";
});

function setCinematicPitch(event) {
	mapStore.setCinematicMapPitch(event.target.value);
}

function formatRouteDistance(distanceMeters) {
	if (!Number.isFinite(Number(distanceMeters))) return "";
	if (distanceMeters >= 1000) {
		return `${(distanceMeters / 1000).toFixed(1)} km`;
	}
	return `${Math.round(distanceMeters)} m`;
}

function formatRouteDuration(durationSeconds) {
	if (!Number.isFinite(Number(durationSeconds))) return "";
	const roundedMinutes = Math.max(1, Math.round(durationSeconds / 60));
	if (roundedMinutes >= 60) {
		const hours = Math.floor(roundedMinutes / 60);
		const minutes = roundedMinutes % 60;
		return minutes ? `${hours} 小時 ${minutes} 分` : `${hours} 小時`;
	}
	return `${roundedMinutes} 分`;
}

const routeStatusText = computed(() => {
	const summary = mapStore.navigationRouteSummary;
	if (!summary) return routeMessage.value;
	const prefix = summary.isApproximate ? "直線估算" : "簡易路線";
	return `${prefix} ${formatRouteDistance(summary.distance)} / ${formatRouteDuration(summary.duration)}`;
});

function toggleRoutePanel() {
	isRoutePanelOpen.value = !isRoutePanelOpen.value;
}

async function handleSimpleRoute() {
	if (!routeStart.value || !routeEnd.value) {
		routeMessage.value = "請輸入起點與終點";
		return;
	}
	isRouting.value = true;
	routeMessage.value = "路線搜尋中...";
	try {
		const summary = await mapStore.findSimpleRoute({
			startText: routeStart.value,
			endText: routeEnd.value,
			profile: routeProfile.value,
		});
		routeMessage.value = summary.isApproximate
			? "無法取得道路路線，已改用直線估算"
			: "路線已標示";
		gtag("event", "map_actions", {
			action_type: "簡易導航",
			time: Date.now(),
		});
	} catch (error) {
		routeMessage.value = error?.message || "無法建立路線";
		dialogStore.showNotification("fail", routeMessage.value);
	} finally {
		isRouting.value = false;
	}
}

function clearSimpleRoute() {
	routeMessage.value = "";
	mapStore.clearSimpleRoute();
}

watch(
	() => route.query?.city,
	(newValue) => {
		newValue 
			? mapStore.updateMapViewForCity(newValue)
			: mapStore.updateMapViewForCity('default');
	}
);

onMounted(() => {
	mapStore.initializeMapBox();
	route.query.city 
		? mapStore.updateMapViewForCity(route.query.city)
		: mapStore.updateMapViewForCity('default');
});
</script>

<template>
  <div class="mapcontainer">
    <div class="mapcontainer-map">
      <!-- #mapboxBox needs to be empty to ensure Mapbox performance -->
      <div id="mapboxBox" />
      <div class="mapcontainer-layers">
        <button
          v-if="canUseFindClosestPoint"
          class="hide-if-mobile"
          type="button"
          @click="dialogStore.showDialog('findClosestPoint'); findClosestPointGA();"
        >
          近
        </button>
        <button
          class="show-if-mobile"
          @click="dialogStore.showDialog('mobileLayers')"
        >
          <span>layers</span>
        </button>
      </div>
      <form
        v-if="isRoutePanelOpen"
        class="mapcontainer-navigation hide-if-mobile"
        @submit.prevent="handleSimpleRoute"
      >
        <div class="mapcontainer-navigation-heading">
          <span>ROUTE</span>
          <strong>簡易導航</strong>
        </div>
        <label>
          <span>起點</span>
          <input
            v-model.trim="routeStart"
            autocomplete="off"
            placeholder="例：台北車站"
            type="text"
          >
        </label>
        <label>
          <span>終點</span>
          <input
            v-model.trim="routeEnd"
            autocomplete="off"
            placeholder="例：台北市政府"
            type="text"
          >
        </label>
        <div class="mapcontainer-navigation-profiles">
          <button
            v-for="option in routeProfileOptions"
            :key="option.value"
            class="mapcontainer-navigation-profile"
            :class="{
              'mapcontainer-navigation-profile--active':
                routeProfile === option.value,
            }"
            type="button"
            @click="routeProfile = option.value"
          >
            <span>{{ option.icon }}</span>
            {{ option.label }}
          </button>
        </div>
        <div class="mapcontainer-navigation-actions">
          <button
            class="mapcontainer-navigation-submit"
            :disabled="isRouting"
            type="submit"
          >
            {{ isRouting ? "搜尋中" : "標示路線" }}
          </button>
          <button
            class="mapcontainer-navigation-clear"
            type="button"
            @click="clearSimpleRoute"
          >
            清除
          </button>
        </div>
        <p v-if="routeStatusText">
          {{ routeStatusText }}
        </p>
      </form>
      <div
        class="mapcontainer-camera hide-if-mobile"
        aria-label="地圖攝影機控制"
      >
        <div class="mapcontainer-camera-replay">
          <span>ANIM</span>
          <button
            title="重新播放進場動畫"
            @click="
              mapStore.playInitialMapReveal(
                mapStore.pendingMapViewCity || 'default',
                true,
              )
            "
          >
            <span>play_arrow</span>
          </button>
        </div>
        <div class="mapcontainer-camera-route">
          <span>ROUTE</span>
          <button
            class="mapcontainer-camera-route-button"
            :class="{
              'mapcontainer-camera-route-button--active': isRoutePanelOpen,
            }"
            title="簡易導航"
            type="button"
            @click="toggleRoutePanel"
          >
            <span>navigation</span>
          </button>
        </div>
        <div class="mapcontainer-camera-angle mapcontainer-camera-section">
          <div class="mapcontainer-camera-angle-heading">
            <span>VIEW</span>
            <strong>
              {{ cinematicPitchLabel }} {{ cinematicPitchValue }}°
            </strong>
          </div>
          <input
            :value="mapStore.cinematicPitch"
            aria-label="地圖視角俯視到斜視"
            max="72"
            min="0"
            step="1"
            type="range"
            @input="setCinematicPitch"
          >
          <div class="mapcontainer-camera-angle-presets">
            <button
              class="mapcontainer-camera-textbutton"
              title="俯視"
              @click="mapStore.setCinematicMapPitch(0)"
            >
              0°
            </button>
            <button
              class="mapcontainer-camera-textbutton"
              title="中視角"
              @click="mapStore.setCinematicMapPitch(45)"
            >
              45°
            </button>
            <button
              class="mapcontainer-camera-textbutton"
              title="斜視"
              @click="mapStore.setCinematicMapPitch(68)"
            >
              68°
            </button>
          </div>
        </div>
        <div class="mapcontainer-camera-move mapcontainer-camera-section">
          <span class="mapcontainer-camera-label">PAN</span>
          <div class="mapcontainer-camera-pad">
            <button
              class="mapcontainer-camera-pan-up"
              title="向上平移"
              @click="mapStore.panCinematicMap('up')"
            >
              <span>keyboard_arrow_up</span>
            </button>
            <button
              class="mapcontainer-camera-pan-left"
              title="向左平移"
              @click="mapStore.panCinematicMap('left')"
            >
              <span>keyboard_arrow_left</span>
            </button>
            <button
              class="mapcontainer-camera-pan-reset"
              title="回到目前城市視角"
              @click="mapStore.resetCinematicMapView()"
            >
              <span>my_location</span>
            </button>
            <button
              class="mapcontainer-camera-pan-right"
              title="向右平移"
              @click="mapStore.panCinematicMap('right')"
            >
              <span>keyboard_arrow_right</span>
            </button>
            <button
              class="mapcontainer-camera-pan-down"
              title="向下平移"
              @click="mapStore.panCinematicMap('down')"
            >
              <span>keyboard_arrow_down</span>
            </button>
          </div>
        </div>
        <div class="mapcontainer-camera-tools mapcontainer-camera-section">
          <div class="mapcontainer-camera-tools-row">
            <span>ZOOM</span>
            <div class="mapcontainer-camera-group">
              <button
                title="放大"
                @click="mapStore.zoomCinematicMap(0.8)"
              >
                <span>zoom_in</span>
              </button>
              <button
                title="縮小"
                @click="mapStore.zoomCinematicMap(-0.8)"
              >
                <span>zoom_out</span>
              </button>
            </div>
          </div>
          <div class="mapcontainer-camera-tools-row">
            <span>ROT</span>
            <div class="mapcontainer-camera-group">
              <button
                title="逆時針旋轉"
                @click="mapStore.rotateCinematicMap(-24)"
              >
                <span>rotate_left</span>
              </button>
              <button
                title="順時針旋轉"
                @click="mapStore.rotateCinematicMap(24)"
              >
                <span>rotate_right</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="authStore.user.is_admin"
        class="mapcontainer-layers-incident"
        title="通報災害"
        @click="dialogStore.showDialog('incidentReport')"
      >
        !
      </button><!-- The key prop informs vue that the component should be updated when switching dashboards -->
      <MobileLayers :key="contentStore.currentDashboard.index" />
      <IncidentReport />
      <FindClosestPoint />
    </div>

    <div class="mapcontainer-controls hide-if-mobile">
      <button
        @click="
          mapStore.easeToLocation([
            [121.536609, 25.044808],
            12.5,
            0,
            0,
          ], {
            preserveCamera: true,
            duration: 850,
          })
        "
      >
        返回預設
      </button>
      <template v-if="!authStore.user?.user_id">
        <div
          v-for="(item, index) in savedLocations"
          :key="`${item[4]}-${index}`"
        >
          <button
            @click="
              mapStore.easeToLocation(item, {
                preserveCamera: true,
                duration: 850,
              })
            "
          >
            {{ item[4] }}
          </button>
        </div>
      </template>
      <div
        v-for="(item, index) in mapStore.viewPoints"
        :key="index"
      >
        <button
          v-if="item.point_type === 'view'"
          @click="mapStore.easeToLocation(item)"
        >
          {{ item["name"] }}
        </button>
        <div
          v-if="authStore.user?.user_id"
          class="mapcontainer-controls-delete"
          @click="mapStore.removeViewPoint(item)"
        >
          <span>delete</span>
        </div>
      </div>
      <button
        v-if="authStore.user?.user_id"
        @click="dialogStore.showDialog('addViewPoint')"
      >
        新增
      </button>
    </div>
  </div>
  <AddViewPoint name="addViewPoint" />
</template>

<style scoped lang="scss">
.mapcontainer {
	position: relative;
	width: 100%;
	height: 100%;
	flex: 1;
	isolation: isolate;

	&-map {
		position: relative;
		height: 100%;
		background-color: #020203;

		@media (max-width: 1000px) {
			height: 100%;
		}

		&::before,
		&::after {
			display: none;
		}
	}

	&-controls {
		position: absolute;
		left: 18px;
		bottom: 16px;
		z-index: 5;
		display: flex;
		max-width: calc(100% - 36px);
		margin-top: 0;
		overflow: visible;

		button {
			height: 1.5rem;
			width: fit-content;
			margin-right: 6px;
			padding: 4px;
			border: 1px solid rgba(244, 242, 235, 0.52);
			border-radius: 0;
			background-color: rgba(0, 0, 0, 0.5);
			color: #f4f2eb;
			font-family: Consolas, "Courier New", monospace;
			cursor: pointer;

			&:focus {
				animation-name: colorfade;
				animation-duration: 4s;
			}
		}

		div {
			position: relative;
			overflow: visible;

			div {
				width: 1.2rem;
				height: 1.2rem;
				position: absolute;
				top: -0.5rem;
				right: -0.3rem;
				display: flex;
				align-items: center;
				justify-content: center;
				border-radius: 50%;
				opacity: 0;
				background-color: var(--color-border);
				box-shadow: 0 0 3px black;
				transition: opacity 0.2s;
				z-index: 10;
				pointer-events: none;
				cursor: pointer;

				span {
					color: rgb(185, 185, 185);
					font-family: var(--font-icon);
					font-size: 0.8rem;
					transition: color 0.2s;
				}

				&:hover span {
					color: rgb(255, 65, 44);
				}
			}

			&:hover div {
				opacity: 1;
				pointer-events: all;
			}
		}

		input {
			height: calc(1.5rem - 4px);
			width: 1.7rem;
			margin-right: 6px;
			padding: 2px 4px;
			border-radius: 5px;
			border: none;
			background-color: rgb(30, 30, 30);
			color: var(--color-complement-text);
			font-size: 0.82rem;

			&:focus {
				width: 5.4rem;
			}
		}
	}

	&-layers {
		position: absolute;
		right: 10px;
		top: 150px;
		z-index: 5;
		display: flex;
		flex-direction: column;
		row-gap: 4px;

		button {
			width: 1.75rem;
			height: 1.75rem;
			display: flex;
			align-items: center;
			justify-content: center;
			border: 1px solid rgba(244, 242, 235, 0.7);
			border-radius: 0;
			background-color: rgba(244, 242, 235, 0.92);
			transition: color 0.2s;
		}

		button:hover,
		&-button--active {
			background-color: #ff4ecb;
			color: #050506;
		}

		button:hover span,
		&-button--active span {
			color: #050506;
		}

		span {
			color: var(--color-component-background);
			font-size: 1.2rem;
			font-family: var(--font-icon);
		}

		&-incident {
			position: absolute;
			right: 10px;
			bottom: 60px;
			width: 50px;
			height: 50px;
			border-radius: 50%;
			background-color: var(--color-component-background);
			display: flex;
			align-items: center;
			justify-content: center;
			transition: background-color 0.2s, color 0.2s;
			font-size: var(--font-xl);

			&:hover {
				background-color: var(--color-highlight);
			}
		}
	}

	&-navigation {
		position: absolute;
		right: 24px;
		top: 202px;
		z-index: 7;
		width: min(340px, calc(100vw - 48px));
		max-height: calc(100% - 224px);
		box-sizing: border-box;
		display: grid;
		gap: 10px;
		padding: 12px;
		border: 1px solid rgba(244, 242, 235, 0.5);
		background-color: rgba(0, 0, 0, 0.72);
		box-shadow: 0 0 24px rgba(255, 78, 203, 0.16);
		backdrop-filter: blur(4px);
		color: #f4f2eb;
		font-family: Consolas, "Courier New", monospace;
		overflow-y: auto;
		scrollbar-gutter: stable;

		* {
			box-sizing: border-box;
		}

		&-heading {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 12px;

			span {
				color: rgba(244, 242, 235, 0.52);
				font-size: 0.64rem;
				font-weight: 700;
			}

			strong {
				color: #fff;
				font-size: 0.9rem;
				font-weight: 700;
			}
		}

		label {
			display: grid;
			gap: 5px;
			min-width: 0;

			span {
				color: rgba(244, 242, 235, 0.62);
				font-size: 0.72rem;
				font-weight: 700;
			}
		}

		input {
			width: 100%;
			min-width: 0;
			height: 34px;
			line-height: 34px;
			padding: 0 10px;
			border: 1px solid rgba(244, 242, 235, 0.34);
			border-radius: 0;
			background-color: rgba(255, 255, 255, 0.06);
			color: #fff;
			font-size: 0.84rem;
			outline: none;

			&::placeholder {
				color: rgba(244, 242, 235, 0.36);
			}

			&:focus {
				border-color: rgba(255, 78, 203, 0.88);
				box-shadow: 0 0 0 1px rgba(255, 78, 203, 0.28);
			}
		}

		&-profiles {
			display: grid;
			grid-template-columns: repeat(3, minmax(0, 1fr));
			gap: 6px;
		}

		&-profile {
			height: 34px;
			display: flex;
			align-items: center;
			justify-content: center;
			gap: 4px;
			min-width: 0;
			border: 1px solid rgba(244, 242, 235, 0.32);
			background-color: rgba(255, 255, 255, 0.045);
			color: rgba(244, 242, 235, 0.76);
			font-size: 0.76rem;
			font-weight: 700;
			transition:
				border-color 0.18s,
				background-color 0.18s,
				color 0.18s;

			span {
				font-family: var(--font-icon);
				font-size: 1rem;
			}

			&:hover,
			&--active {
				border-color: rgba(255, 78, 203, 0.95);
				background-color: rgba(255, 78, 203, 0.18);
				color: #fff;
			}
		}

		&-actions {
			display: grid;
			grid-template-columns: minmax(0, 1fr) 76px;
			gap: 8px;
		}

		&-submit,
		&-clear {
			height: 34px;
			border: 1px solid rgba(244, 242, 235, 0.4);
			border-radius: 0;
			font-size: 0.82rem;
			font-weight: 700;
		}

		&-submit {
			background-color: rgba(255, 78, 203, 0.86);
			color: #050506;

			&:disabled {
				opacity: 0.58;
				cursor: progress;
			}
		}

		&-clear {
			background-color: rgba(255, 255, 255, 0.05);
			color: rgba(244, 242, 235, 0.82);
		}

		p {
			min-height: 18px;
			margin: 0;
			color: rgba(244, 242, 235, 0.72);
			font-size: 0.72rem;
			font-weight: 700;
			line-height: 1.35;
		}
	}

	&-camera {
		position: absolute;
		top: 22px;
		right: 24px;
		z-index: 6;
		display: grid;
		grid-template-columns: 60px 60px minmax(172px, 1fr) 126px 118px;
		gap: 10px;
		align-items: stretch;
		width: min(630px, calc(100vw - 500px));
		min-width: 590px;
		padding: 10px;
		border: 1px solid rgba(244, 242, 235, 0.55);
		background-color: rgba(0, 0, 0, 0.66);
		box-shadow: 0 0 24px rgba(255, 255, 255, 0.12);
		backdrop-filter: blur(4px);

		&-section,
		&-replay,
		&-route {
			border: 1px solid rgba(244, 242, 235, 0.22);
			background-color: rgba(255, 255, 255, 0.035);
		}

		&-label,
		&-replay > span,
		&-route > span,
		&-tools-row > span {
			color: rgba(244, 242, 235, 0.48);
			font-family: Consolas, "Courier New", monospace;
			font-size: 0.62rem;
			font-weight: 700;
			line-height: 1;
		}

		button {
			width: 32px;
			height: 32px;
			display: flex;
			align-items: center;
			justify-content: center;
			border: 1px solid rgba(244, 242, 235, 0.48);
			background-color: rgba(7, 7, 8, 0.72);
			color: rgba(244, 242, 235, 0.88);
			transition:
				border-color 0.2s,
				background-color 0.2s,
				color 0.2s;

			&:hover {
				border-color: rgba(255, 255, 255, 0.95);
				background-color: rgba(255, 255, 255, 0.14);
				color: #fff;
			}

			span {
				font-family: var(--font-icon);
				font-size: 1.25rem;
				line-height: 1;
				user-select: none;
			}
		}

		&-textbutton {
			width: auto;
			min-width: 42px;
			padding: 0 8px;
			color: rgba(244, 242, 235, 0.82);
			font-family: Consolas, "Courier New", monospace;
			font-size: 0.72rem;
			font-weight: 700;
		}

		&-replay {
			display: grid;
			grid-template-rows: auto 1fr;
			gap: 8px;
			align-items: center;
			justify-items: center;
			padding: 10px 8px;

			button {
				width: 38px;
				height: 38px;
			}
		}

		&-route {
			display: grid;
			grid-template-rows: auto 1fr;
			gap: 8px;
			align-items: center;
			justify-items: center;
			padding: 10px 8px;

			button {
				width: 38px;
				height: 38px;
			}

			&-button--active {
				border-color: rgba(255, 78, 203, 0.96);
				background-color: rgba(255, 78, 203, 0.88);
				color: #050506;
				box-shadow: 0 0 14px rgba(255, 78, 203, 0.28);
			}
		}

		&-angle {
			display: grid;
			grid-template-rows: auto auto auto;
			gap: 7px;
			min-height: 100%;
			padding: 10px 12px;
			color: rgba(244, 242, 235, 0.82);
			font-family: Consolas, "Courier New", monospace;

			input {
				width: 100%;
				margin: 0;
				accent-color: #f4f2eb;
				cursor: pointer;
			}

			&-heading {
				display: flex;
				align-items: center;
				justify-content: space-between;
				gap: 10px;
				line-height: 1;

				span {
					color: rgba(244, 242, 235, 0.48);
					font-family: Consolas, "Courier New", monospace;
					font-size: 0.64rem;
					font-weight: 700;
				}

				strong {
					color: #fff;
					font-size: 0.76rem;
					font-weight: 700;
					text-shadow: 0 0 10px rgba(255, 255, 255, 0.48);
				}
			}

			&-presets {
				display: grid;
				grid-template-columns: repeat(3, 1fr);
				gap: 5px;

				button {
					width: 100%;
					height: 24px;
				}
			}
		}

		&-group {
			display: grid;
			grid-template-columns: repeat(2, 32px);
			gap: 6px;
		}

		&-move {
			display: grid;
			grid-template-rows: auto 1fr;
			gap: 8px;
			align-items: center;
			justify-items: center;
			padding: 10px;
		}

		&-pad {
			display: grid;
			grid-template-columns: repeat(3, 32px);
			grid-template-rows: repeat(3, 32px);
			gap: 6px;

			.mapcontainer-camera-pan-up {
				grid-column: 2;
				grid-row: 1;
			}

			.mapcontainer-camera-pan-left {
				grid-column: 1;
				grid-row: 2;
			}

			.mapcontainer-camera-pan-reset {
				grid-column: 2;
				grid-row: 2;
			}

			.mapcontainer-camera-pan-right {
				grid-column: 3;
				grid-row: 2;
			}

			.mapcontainer-camera-pan-down {
				grid-column: 2;
				grid-row: 3;
			}
		}

		&-tools {
			display: grid;
			grid-template-rows: 1fr 1fr;
			gap: 8px;
			padding: 10px;

			&-row {
				display: grid;
				grid-template-rows: auto auto;
				gap: 6px;
				align-content: center;
			}
		}
	}
}

#mapboxBox {
	width: 100%;
	height: 100%;
	border-radius: 0;
}

:deep(.simple-navigation-marker) {
	width: 30px;
	height: 30px;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2px solid #050506;
	border-radius: 50%;
	background-color: #f4f2eb;
	color: #050506;
	font-family: "Noto Sans TC", sans-serif;
	font-size: 0.78rem;
	font-weight: 800;
	box-shadow:
		0 0 0 2px rgba(244, 242, 235, 0.34),
		0 0 18px rgba(255, 78, 203, 0.42);
}

:deep(.simple-navigation-marker--start) {
	background-color: #ff4ecb;
}

:deep(.simple-navigation-marker--end) {
	background-color: #f4f2eb;
}

:deep(.mapboxgl-ctrl-group) {
	border: 1px solid rgba(244, 242, 235, 0.55);
	border-radius: 0;
	background-color: rgba(0, 0, 0, 0.54);
}

:deep(.mapboxgl-ctrl-group button) {
	filter: invert(1) grayscale(1);
}

:deep(.mapboxgl-ctrl-bottom-left),
:deep(.mapboxgl-ctrl-bottom-right) {
	opacity: 0.42;
}

@keyframes colorfade {
	0% {
		color: var(--color-highlight);
	}

	75% {
		color: var(--color-highlight);
	}

	100% {
		color: var(--color-complement-text);
	}
}
</style>
