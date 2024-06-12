<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, computed } from "vue";
import { useMapStore } from "../../store/mapStore";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";

import DialogContainer from "./DialogContainer.vue";
import CustomCheckBox from "../utilities/forms/CustomCheckBox.vue";

const mapStore = useMapStore();
const dialogStore = useDialogStore();
const authStore = useAuthStore();

const selectedLocation = ref("0");

const availableLocations = computed(() => {
	const locations = [];

	if (mapStore.userLocation.latitude) {
		locations.push({
			name: "我現在的定位",
			latitude: mapStore.userLocation.latitude,
			longitude: mapStore.userLocation.longitude,
		});
	}

	mapStore.viewPoints.forEach((viewPoint) => {
		if (viewPoint.point_type === "pin")
			locations.push({
				name: viewPoint.name,
				latitude: viewPoint.center_y,
				longitude: viewPoint.center_x,
			});
	});

	return locations;
});

function handleClose() {
	selectedLocation.value = "0";
	dialogStore.hideAllDialogs();
}
function handleFind() {
	mapStore.flyToClosestLocationAndTriggerPopup(
		availableLocations.value[+selectedLocation.value].longitude,
		availableLocations.value[+selectedLocation.value].latitude
	);
	handleClose();
}
</script>

<template>
  <DialogContainer
    dialog="findClosestPoint"
    @on-close="handleClose"
  >
    <div class="findclosestpoint">
      <h2>尋找最近點</h2>
      <div class="findclosestpoint-input">
        <label>
          請選擇搜尋基準點{{ authStore.token && " (用戶定位與地標)" }}
        </label>
        <div
          v-if="availableLocations.length > 0"
          class="findclosestpoint-locations"
        >
          <div
            v-for="(location, index) in availableLocations"
            :key="`findlocation-${location.latitude}-${location.longitude}-${index}`"
          >
            <input
              :id="`${index}`"
              v-model="selectedLocation"
              type="radio"
              :value="`${index}`"
              class="custom-check-input"
            >
            <CustomCheckBox :for="`${index}`">
              {{ location.name }}
            </CustomCheckBox>
          </div>
        </div>
        <div v-else>
          <p>
            查無基準點。請點擊地圖右上角按紐，開啟定位功能{{
              authStore.token && "或加入地標"
            }}。
          </p>
        </div>
      </div>
      <div class="findclosestpoint-control">
        <button
          v-if="availableLocations.length > 0"
          @click="handleFind"
        >
          搜尋
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.findclosestpoint {
	width: 250px;

	&-input {
		display: flex;
		flex-direction: column;

		label {
			margin: 8px 0;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		input {
			display: none;

			& + label {
				font-size: var(--font-ms);
			}

			&:checked + label {
				color: white;
			}

			&:hover + label {
				color: var(--color-highlight);
			}
		}
	}

	&-locations {
		max-height: 80px;
		overflow-y: scroll;

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			border-radius: 4px;
			background-color: rgba(136, 135, 135, 0.5);
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}

	&-control {
		height: var(--font-xl);
		display: flex;
		justify-content: flex-end;
		margin-top: 8px;

		button {
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}
}
</style>
