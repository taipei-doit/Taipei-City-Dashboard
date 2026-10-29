<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
/* global gtag */
import { onMounted, ref, computed, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../../store/authStore";
import { useContentStore } from "../../store/contentStore";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";
import { useWindEngine } from "../../composables/useWindEngine";
import { buildMapLegend } from "../../assets/utilityFunctions/parseMapConfigs";

import AddViewPoint from "../dialogs/AddViewPoint.vue";
import MobileLayers from "../dialogs/MobileLayers.vue";
import IncidentReport from "../dialogs/IncidentReport.vue";
import FindClosestPoint from "../dialogs/FindClosestPoint.vue";
import { savedLocations } from "../../assets/configs/mapbox/savedLocations.js";
import Isochrone from "../icons/IsochroneIcon.vue";
import LegendIcon from "../icons/LegendIcon.vue";
import IsochroneSettingPopup from "./IsochroneSettingPopup.vue";

const authStore = useAuthStore();
const mapStore = useMapStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();
const route = useRoute();

// 掛載風場引擎
useWindEngine();

const districtLayer = ref(false);
const villageLayer = ref(false);
const isoMenu = ref(false);
const legendOpen = ref(false);

const legendItems = computed(() => {
	return mapStore.currentVisibleLayers
		.map((layerId) => {
			const group = buildMapLegend(mapStore.mapConfigs[layerId]);
			return group ? { ...group, layerId } : null;
		})
		.filter((group) => group?.items.length);
});

const canUseFindClosestPoint = computed(() => {
	let pointLayerCount = 0;

	mapStore.currentVisibleLayers.forEach((layer) => {
		if (["circle", "symbol"].includes(layer.split("-")[1])) {
			pointLayerCount++;
		}
	});

	return pointLayerCount === 1;
});

function toggleDistrictLayer() {
	districtLayer.value = !districtLayer.value;
	mapStore.toggleDistrictBoundaries(districtLayer.value);
	// 載入區界時觸發GA自訂事件
	gtag("event", "map_actions", {
		action_type: "載入區界",
		time: Date.now(),
	});
}

function toggleVillageLayer() {
	villageLayer.value = !villageLayer.value;
	mapStore.toggleVillageBoundaries(villageLayer.value);
	// 載入里界時觸發GA自訂事件
	gtag("event", "map_actions", {
		action_type: "載入里界",
		time: Date.now(),
	});
}

function toggleIsochroneSettings() {
	isoMenu.value = !isoMenu.value;
}

function getLegendMarkerStyle(item) {
	const style = { opacity: item.opacity };
	const colors = item.colors?.filter((color) => typeof color === "string");

	if (colors?.length > 1) {
		style.background = `linear-gradient(90deg, ${colors.join(", ")})`;
	} else if (item.kind === "circle") {
		style.backgroundColor = item.hollow ? "transparent" : item.color;
		style.borderColor = item.strokeColor || item.color;
	} else if (item.kind === "line") {
		if (item.dashed) {
			style.backgroundImage = `repeating-linear-gradient(90deg, ${item.color} 0 7px, transparent 7px 11px)`;
		} else {
			style.backgroundColor = item.color;
		}
		style.height = `${Math.min(Math.max(item.width || 3, 2), 6)}px`;
	} else {
		style.backgroundColor = item.color;
		style.borderColor = item.strokeColor || "transparent";
	}

	return style;
}

// 尋找最近點時觸發GA自訂事件
function findClosestPointGA() {
	gtag("event", "map_actions", {
		action_type: "尋找最近點",
		time: Date.now(),
	});
}

watch(
	() => route.query?.city,
	(newValue) => {
		newValue
			? mapStore.updateMapViewForCity(newValue)
			: mapStore.updateMapViewForCity("default");
	},
);

onMounted(() => {
	mapStore.initializeMapBox();
	mapStore.setCurrentLocation();
	route.query.city
		? mapStore.updateMapViewForCity(route.query.city)
		: mapStore.updateMapViewForCity("default");
});
</script>

<template>
  <div class="mapcontainer">
    <div class="mapcontainer-map">
      <!-- #mapboxBox needs to be empty to ensure Mapbox performance -->
      <div id="mapboxBox" />
      <div class="mapcontainer-layers">
        <button
          :style="{
            color: districtLayer
              ? 'var(--color-highlight)'
              : 'var(--color-component-background)',
          }"
          @click="toggleDistrictLayer"
        >
          區
        </button>
        <button
          :style="{
            color: villageLayer
              ? 'var(--color-highlight)'
              : 'var(--color-component-background)',
          }"
          @click="toggleVillageLayer"
        >
          里
        </button>
        <button
          class="isochrone-btn"
          @click="toggleIsochroneSettings"
        >
          <Isochrone />
        </button>
        <button
          class="legend-btn"
          :class="{ active: legendOpen }"
          type="button"
          title="圖徵圖例"
          aria-label="切換圖徵圖例"
          :aria-pressed="legendOpen"
          @click="legendOpen = !legendOpen"
        >
          <LegendIcon />
        </button>
        <button
          v-if="canUseFindClosestPoint"
          :style="{
            color: villageLayer
              ? 'var(--color-highlight)'
              : 'var(--color-component-background)',
          }"
          class="hide-if-mobile"
          type="button"
          @click="
            dialogStore.showDialog('findClosestPoint');
            findClosestPointGA();
          "
        >
          近
        </button>
        <button
          class="show-if-mobile"
          @click="dialogStore.showDialog('mobileLayers')"
        >
          <span>layers</span>
        </button>
        <div
          v-if="mapStore.loadingLayers.length > 0"
          class="mapcontainer-layers-loading"
        >
          <div />
        </div>
      </div>

      <section
        v-if="legendOpen"
        class="mapcontainer-legend"
        aria-label="圖徵圖例"
      >
        <header>
          <h3>圖徵圖例</h3>
          <button
            class="mapcontainer-legend-close"
            type="button"
            aria-label="關閉圖徵圖例"
            @click="legendOpen = false"
          >
            ✕
          </button>
        </header>
        <div
          v-if="legendItems.length"
          class="mapcontainer-legend-content"
        >
          <div
            v-for="group in legendItems"
            :key="group.layerId"
            class="mapcontainer-legend-group"
          >
            <h4>{{ group.title }}</h4>
            <div
              v-for="item in group.items"
              :key="`${item.label}-${item.color}-${item.iconSrc}`"
              class="mapcontainer-legend-item"
            >
              <img
                v-if="item.kind === 'symbol'"
                :src="item.iconSrc"
                alt=""
              >
              <span
                v-else
                class="mapcontainer-legend-marker"
                :class="[
                  `mapcontainer-legend-marker--${item.kind}`,
                  { 'mapcontainer-legend-marker--continuous': item.continuous },
                ]"
                :style="getLegendMarkerStyle(item)"
              />
              <span>{{ item.label }}</span>
            </div>
          </div>
        </div>
        <p v-else>
          目前無可顯示的圖例
        </p>
      </section>

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

    <!-- 等時圈設定介面 -->
    <IsochroneSettingPopup
      v-if="isoMenu"
      class="isochrone-setting"
      @close="toggleIsochroneSettings"
    />

    <div class="mapcontainer-controls hide-if-mobile">
      <button
        @click="
          mapStore.easeToLocation([
            [121.536609, 25.044808],
            12.5,
            0,
            0,
          ])
        "
      >
        返回預設
      </button>
      <template v-if="!authStore.user?.user_id">
        <div
          v-for="(item, index) in savedLocations"
          :key="`${item[4]}-${index}`"
        >
          <button @click="mapStore.easeToLocation(item)">
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

	&-map {
		height: calc(100% - 32px);

		@media (max-width: 1000px) {
			height: 100%;
		}
	}

	&-controls {
		display: flex;
		margin-top: 8px;
		overflow: visible;

		button {
			height: 1.5rem;
			width: fit-content;
			margin-right: 6px;
			padding: 4px;
			border-radius: 5px;
			background-color: var(--color-component-background);
			color: var(--color-complement-text);
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
		z-index: 1;
		display: flex;
		flex-direction: column;
		row-gap: 4px;

		button {
			width: 1.75rem;
			height: 1.75rem;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 50%;
			background-color: white;
			transition: color 0.2s;
		}

		.legend-btn {
			&.active {
				background-color: var(--color-highlight);
			}

			:deep(svg) {
				width: 1.1rem;
				height: 1.1rem;
			}
		}

		span {
			color: var(--color-component-background);
			font-size: 1.2rem;
			font-family: var(--font-icon);
		}

		&-loading {
			height: 2rem;
			display: flex;
			align-items: center;
			justify-content: center;
			z-index: 20;

			@media (max-width: 1000px) {
				top: 145px;
			}

			div {
				width: 1.3rem;
				height: 1.3rem;
				border-radius: 50%;
				border: solid 4px var(--color-border);
				border-top: solid 4px var(--color-highlight);
				animation: spin 0.7s ease-in-out infinite;
			}
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
			transition:
				background-color 0.2s,
				color 0.2s;
			font-size: var(--font-xl);

			&:hover {
				background-color: var(--color-highlight);
			}
		}
	}

	&-legend {
		position: absolute;
		left: 10px;
		bottom: 42px;
		z-index: 2;
		display: flex;
		flex-direction: column;
		width: min(350px, calc(100% - 20px));
		max-height: min(55%, 480px);
		overflow: hidden;
		border: 1px solid #555;
		border-radius: 8px;
		background: #2b2c2e;
		box-shadow: 0 4px 12px rgb(0 0 0 / 30%);
		color: #eee;
		font-size: 0.875rem;

		@media (max-width: 1000px) {
			bottom: 10px;
		}

		header {
			display: flex;
			align-items: center;
			justify-content: space-between;
			flex: none;
			padding: 8px 14px;
			border-bottom: 1px solid #555;
			background: #3a3b3d;

			h3 {
				margin: 0;
				font-size: 1rem;
				font-weight: 600;
			}
		}

		&-close {
			display: flex;
			align-items: center;
			justify-content: center;
			flex: none;
			width: 32px;
			height: 32px;
			padding: 0;
			border: 0;
			border-radius: 50%;
			background: transparent;
			color: #aaa;
			font-size: 0.875rem;
			line-height: 1;
			cursor: pointer;
			transition:
				color 0.15s,
				background-color 0.15s;

			&:hover {
				background-color: #4a4b4d;
				color: #eee;
			}
		}

		p {
			margin: 0;
			padding: 14px;
			color: #aaa;
		}

		&-content {
			min-height: 0;
			padding: 6px 14px 14px;
			overflow-y: auto;
		}

		&-group {
			padding-top: 10px;

			h4 {
				margin-bottom: 7px;
				color: #4ba3e3;
				font-size: 0.8rem;
				font-weight: 600;
				letter-spacing: 0.04em;
			}
		}

		&-item {
			display: flex;
			align-items: center;
			gap: 8px;
			min-height: 24px;
			color: #eee;
			font-size: 0.875rem;

			img {
				width: 20px;
				height: 20px;
				object-fit: contain;
			}
		}

		&-marker {
			flex: 0 0 22px;
			width: 22px;
			height: 14px;

			&--circle {
				width: 14px;
				height: 14px;
				flex-basis: 14px;
				border: 2px solid;
				border-radius: 50%;
			}

			&--fill {
				border: 1px solid;
				border-radius: 2px;
			}

			&--line,
			&--arc {
				height: 3px;
				border-radius: 999px;
			}

			&--continuous {
				width: 90px;
				flex-basis: 90px;
			}
		}
	}
}

#mapboxBox {
	width: 100%;
	height: 100%;
	border-radius: 5px;
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
