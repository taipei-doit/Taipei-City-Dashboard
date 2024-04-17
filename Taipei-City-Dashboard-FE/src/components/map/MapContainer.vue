<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref } from "vue";
import { useMapStore } from "../../store/mapStore";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import MobileLayers from "../dialogs/MobileLayers.vue";

const mapStore = useMapStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();

const districtLayer = ref(false);
const villageLayer = ref(false);

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

onMounted(() => {
	mapStore.initializeMapBox();
});
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
					class="show-if-mobile"
					@click="dialogStore.showDialog('mobileLayers')"
				>
					<span>layers</span>
				</button>
			</div>
			<!-- The key prop informs vue that the component should be updated when switching dashboards -->
			<MobileLayers :key="contentStore.currentDashboard.index" />
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
		top: 104px;
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
