<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed, onMounted, ref } from "vue";
import { useMapStore } from "../../store/mapStore";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import MobileLayers from "../dialogs/MobileLayers.vue";
import IncidentReport from "../dialogs/IncidentReport.vue";

const mapStore = useMapStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();

const districtLayer = ref(false);
const villageLayer = ref(false);

const mapConfigsLength = computed(
	() => Object.keys(mapStore.currentVisibleLayers).length
);
const currentVisibleLayerKey = computed(() => mapStore.currentVisibleLayers);
const mapConfigs = computed(() => {
	return mapStore.mapConfigs;
});

// const newSavedLocation = ref("");

// function handleSubmitNewLocation() {
// 	mapStore.addNewSavedLocation(newSavedLocation.value);
// 	newSavedLocation.value = "";
// }

function toggleDistrictLayer() {
	districtLayer.value = !districtLayer.value;
	mapStore.toggleDistrictBoundaries(districtLayer.value);
}

function toggleVillageLayer() {
	villageLayer.value = !villageLayer.value;
	mapStore.toggleVillageBoundaries(villageLayer.value);
}

/*
function calculateDistance(lat1, lon1, lat2, lon2) {
	const R = 6371; // Radius of the Earth in km
	const dLat = ((lat2 - lat1) * Math.PI) / 180;
	const dLon = ((lon2 - lon1) * Math.PI) / 180;
	const a =
		Math.sin(dLat / 2) * Math.sin(dLat / 2) +
		Math.cos((lat1 * Math.PI) / 180) *
			Math.cos((lat2 * Math.PI) / 180) *
			Math.sin(dLon / 2) *
			Math.sin(dLon / 2);
	const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
	const distance = R * c; // Distance in km
	return distance;
}

function findClosestHospital(userLat, userLon, hospitals) {
	let minDistance = Infinity;
	let closestHospital = null;

	for (let hospital of hospitals) {
		const { inform } = hospital.properties;
		const [lon, lat] = hospital.geometry.coordinates;

		if (inform === "N") {
			const distance = calculateDistance(userLat, userLon, lat, lon);

			if (distance < minDistance) {
				minDistance = distance;
				closestHospital = hospital;
			}
		}
	}

	return closestHospital;
}

function toggleFindNearestAdvancedLifeSupportWithRoomAvailable() {
	try {
		axios.get(`/mapData/advanced_life_support_plc.geojson`).then((rs) => {
			if (navigator.geolocation) {
				navigator.geolocation.getCurrentPosition(
					(position) => {
						const closestHospital = findClosestHospital(
							location.value.latitude,
							location.value.longitude,
							rs.data.features
						);

						mapStore.flyToLocation(
							closestHospital.geometry.coordinates
						);

						setTimeout(() => {
							mapStore.manualTriggerPopup();
						}, 1000);
					},
					(error) => {
						errorMessage.value = error.message;
					}
				);
			} else {
				errorMessage.value =
					"Geolocation is not supported by this browser.";
			}
		});
	} catch (e) {
		console.error(e);
	}
}
*/

onMounted(() => {
	mapStore.initializeMapBox();
	mapStore.setCurrentLocation();
});

const showTooltip = ref(false);
</script>

<template>
  <div class="mapcontainer">
    <div class="mapcontainer-map">
      <!-- #mapboxBox needs to be empty to ensure Mapbox performance -->
      <div id="mapboxBox" />
      <div
        v-if="mapStore.loadingLayers.length > 0"
        class="mapcontainer-loading"
      >
        <div />
      </div>
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
          v-if="
            mapConfigsLength === 1 &&
              mapConfigs[currentVisibleLayerKey ?? '']?.type ===
              'circle'
          "
          :style="{
            color: villageLayer
              ? 'var(--color-highlight)'
              : 'var(--color-component-background)',
          }"
          type="button"
          @click="mapStore.flyToClosestLocationAndTriggerPopup"
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
      <!-- The key prop informs vue that the component should be updated when switching dashboards -->
      <MobileLayers :key="contentStore.currentDashboard.index" />
      <button
        class="input"
        :style="{
          // color: villageLayer
          // 	? 'var(--color-highlight)'
          // 	: 'var(--color-component-background)'
        }"
        title="通報災害"
        @click="dialogStore.showDialog('incidentReport')"
        @mouseover="showTooltip = true"
        @mouseleave="showTooltip = false"
      >
        <!-- <span class="material-symbols-outlined icon">e911_emergency</span> -->
        <span
          v-if="showTooltip"
          class="tooltip"
        >通報災害</span>
        !
      </button>
      <IncidentReport />
    </div>

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
      <div
        v-for="(item, index) in mapStore.savedLocations"
        :key="`${item[4]}-${index}`"
      >
        <button @click="mapStore.easeToLocation(item)">
          {{ item[4] }}
        </button>
        <!-- <div
					class="mapcontainer-controls-delete"
					@click="mapStore.removeSavedLocation(index)"
				>
					<span>delete</span>
				</div> -->
      </div>
      <!-- <input
				v-if="mapStore.savedLocations.length < 10"
				type="text"
				placeholder="新增後按Enter"
				v-model="newSavedLocation"
				maxlength="6"
				@focusout="newSavedLocation = ''"
				@keypress.enter="handleSubmitNewLocation"
			/> -->
    </div>
  </div>
</template>

<style scoped lang="scss">
.input {
	position: absolute;
	right: 20px;
	bottom: 60px;
	width: 70px;
	height: 70px;
	border-radius: 50%;
	background-color: var(--color-component-background);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: background-color 0.2s, color 0.2s;
	font-size: 32px;
	&:hover {
		background-color: var(--color-highlight);
	}
	.icon {
		color: white;
		font-family: var(--font-icon);
	}

	.tooltip {
		position: absolute;
		background-color: black;
		border-radius: 20px;
		border-width: 0px;
		color: white;
		text-align: center;
		padding: 5px 10px;
		z-index: 1;
		bottom: 125%;
		left: 50%;
		transform: translateX(-50%);
		white-space: nowrap;
	}

	.tooltip::after {
		content: "";
		position: absolute;
		top: 100%;
		left: 50%;
		margin-left: -5px;
		border-color: black transparent transparent transparent;
	}
}
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

	&-loading {
		position: absolute;
		top: 170px;
		right: 10px;
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

		span {
			color: var(--color-component-background);
			font-size: 1.2rem;
			font-family: var(--font-icon);
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
