<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
/* global gtag */
import { onMounted, computed, watch } from "vue";
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

	&-camera {
		position: absolute;
		top: 22px;
		right: 24px;
		z-index: 6;
		display: grid;
		grid-template-columns: 60px minmax(172px, 1fr) 126px 118px;
		gap: 10px;
		align-items: stretch;
		width: min(560px, calc(100vw - 500px));
		min-width: 500px;
		padding: 10px;
		border: 1px solid rgba(244, 242, 235, 0.55);
		background-color: rgba(0, 0, 0, 0.66);
		box-shadow: 0 0 24px rgba(255, 255, 255, 0.12);
		backdrop-filter: blur(4px);

		&-section,
		&-replay {
			border: 1px solid rgba(244, 242, 235, 0.22);
			background-color: rgba(255, 255, 255, 0.035);
		}

		&-label,
		&-replay > span,
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
