<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";
import { IsochroneMapConfig } from "../../assets/configs/mapbox/mapConfig.js";

const dialogStore = useDialogStore();
const mapStore = useMapStore();

const currentTimeSlot = computed(() => {
	const timeSlots = mapStore.getIsochroneTimeSlots();
	return timeSlots[mapStore.isochroneTimeSlotIndex] || "";
});

const timeSlotOptions = computed(() => mapStore.getIsochroneTimeSlots());
const timeSliderMax = computed(() => Math.max(timeSlotOptions.value.length - 1, 0));
const timeSliderProgress = computed(() => {
	if (timeSliderMax.value === 0) return "0%";
	return `${(mapStore.isochroneTimeSlotIndex / timeSliderMax.value) * 100}%`;
});
const timeSliderBubblePosition = computed(() =>
	`clamp(26px, ${timeSliderProgress.value}, calc(100% - 26px))`,
);
const timeBubblePositionClass = computed(() => {
	if (mapStore.isochroneTimeSlotIndex === 0) return "is-start";
	if (mapStore.isochroneTimeSlotIndex === timeSliderMax.value) return "is-end";
	return "";
});

const dayTypeOptions = IsochroneMapConfig.dayTypes;
const timeDirectionOptions = IsochroneMapConfig.timeDirections;
const modeOptions = IsochroneMapConfig.modes;

const selectedModes = computed({
	get: () => dialogStore.isochrone.modes,
	set: (value) => {
		dialogStore.isochrone.modes = value;
		dialogStore.isochrone.error = "";
		mapStore.refreshIsochroneQuery();
	},
});

const selectedTimeSlotIndex = computed({
	get: () => mapStore.isochroneTimeSlotIndex,
	set: (value) => {
		mapStore.setIsochroneTimeSlotIndex(Number(value));
	},
});

const selectedDayType = computed({
	get: () => dialogStore.isochrone.dayType,
	set: (value) => {
		dialogStore.isochrone.dayType = value;
		dialogStore.isochrone.error = "";
		mapStore.refreshIsochroneQuery();
	},
});

const selectedTimeDirection = computed({
	get: () => dialogStore.isochrone.timeDirection,
	set: (value) => {
		dialogStore.isochrone.timeDirection = value;
		dialogStore.isochrone.error = "";
		mapStore.refreshIsochroneQuery();
	},
});

function toggleNetwork() {
	dialogStore.isochrone.showNetwork = !dialogStore.isochrone.showNetwork;
	mapStore.toggleNetworkVisibility();
}

function closePanel() {
	mapStore.resetIsochronePickMode();
	dialogStore.dialogs.isochroneSettings = false;
}
</script>

<template>
  <Transition name="isochrone-panel">
    <section
      v-if="dialogStore.dialogs.isochroneSettings"
      class="isochrone"
    >
      <div class="isochrone-header">
        <h2>等時圈設定</h2>
        <div class="isochrone-header-right">
          <span
            v-if="currentTimeSlot && !dialogStore.isochrone.loading"
            class="isochrone-time"
          >{{ currentTimeSlot }}</span>
          <button
            type="button"
            class="isochrone-closeBtn"
            title="關閉"
            @click="closePanel"
          >
            <span>close</span>
          </button>
        </div>
      </div>

      <label>時間</label>
      <div
        class="isochrone-slider"
        :style="{ '--progress': timeSliderProgress }"
      >
        <div class="isochrone-slider-control">
          <output
            class="isochrone-slider-bubble"
            :class="timeBubblePositionClass"
            :style="{ left: timeSliderBubblePosition }"
          >
            {{ currentTimeSlot }}
          </output>
          <input
            v-model="selectedTimeSlotIndex"
            type="range"
            min="0"
            :max="timeSliderMax"
            step="1"
            :aria-valuetext="currentTimeSlot"
          >
        </div>
      </div>

      <label>服務日型</label>
      <div class="isochrone-daytypes">
        <label
          v-for="dayType in dayTypeOptions"
          :key="dayType.value"
          :class="{
            active: selectedDayType === dayType.value,
          }"
        >
          <input
            v-model="selectedDayType"
            type="radio"
            :value="dayType.value"
          >
          {{ dayType.label }}
        </label>
      </div>

      <label>時間參數</label>
      <div class="isochrone-time-directions">
        <label
          v-for="direction in timeDirectionOptions"
          :key="direction.value"
          :class="{
            active: selectedTimeDirection === direction.value,
          }"
        >
          <input
            v-model="selectedTimeDirection"
            type="radio"
            :value="direction.value"
          >
          {{ direction.label }}
        </label>
      </div>

      <label>交通模式</label>
      <div class="isochrone-modes">
        <label
          v-for="mode in modeOptions"
          :key="mode.value"
          :class="{ active: selectedModes.includes(mode.value) }"
          :style="{ '--mode-color': mode.color }"
        >
          <input
            v-model="selectedModes"
            type="checkbox"
            :value="mode.value"
          >
          <span class="mode-dot" />
          {{ mode.label }}
        </label>
      </div>

      <div class="isochrone-divider" />

      <label class="isochrone-toggle">
        <input
          type="checkbox"
          :checked="dialogStore.isochrone.showNetwork"
          @change="toggleNetwork"
        >
        顯示路網
      </label>

      <p
        v-if="dialogStore.isochrone.loading"
        class="isochrone-status"
      >
        查詢等時圈中，請稍候...
      </p>
      <p
        v-else-if="dialogStore.isochrone.networkLoading"
        class="isochrone-status"
      >
        路網資料載入中...
      </p>
      <p
        v-else-if="dialogStore.isochrone.error"
        class="isochrone-error"
      >
        {{ dialogStore.isochrone.error }}
      </p>
      <p
        v-else
        class="isochrone-hint"
      >
        在元件上點選定位按鈕後，於地圖點一下重新計算等時圈
      </p>
    </section>
  </Transition>
</template>

<style scoped lang="scss">
.isochrone {
	position: absolute;
	top: 12px;
	left: 12px;
	width: 260px;
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 12px;
	border: solid 1px var(--color-border);
	border-radius: 5px;
	background-color: var(--color-component-background);
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
	color: var(--color-complement-text);
	z-index: 2;

	@media (max-width: 600px) {
		right: 12px;
		width: auto;
	}

	&-header {
		display: flex;
		align-items: center;
		justify-content: space-between;

		h2 {
			margin: 0;
			font-size: var(--font-m);
			color: white;
		}

		&-right {
			display: flex;
			align-items: center;
			gap: 8px;
		}

		.isochrone-closeBtn {
			width: 1.5rem;
			height: 1.5rem;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 50%;
			color: var(--color-complement-text);
			transition: color 0.2s;

			&:hover {
				color: var(--color-highlight);
			}

			span {
				font-family: var(--font-icon);
				font-size: 1.1rem;
			}
		}
	}

	&-time {
		font-size: var(--font-m);
		font-weight: 700;
		color: var(--color-highlight);
		font-variant-numeric: tabular-nums;
	}

	label {
		font-size: var(--font-s);
	}

	&-toggle {
		display: flex;
		align-items: center;
		gap: 6px;
		cursor: pointer;
	}

	&-slider {
		display: flex;
		align-items: center;
		min-height: 3.6rem;
		padding: 14px 10px 8px;
		border: solid 1px var(--color-border);
		border-radius: 5px;
		background-color: rgb(30, 30, 30);

		&-control {
			position: relative;
			display: flex;
			align-items: center;
			width: 100%;
			min-width: 0;
			height: 2.4rem;
		}

		&-bubble {
			position: absolute;
			top: -0.35rem;
			transform: translateX(-50%);
			padding: 2px 6px;
			border: solid 1px var(--color-highlight);
			border-radius: 5px;
			background-color: rgba(90, 156, 248, 0.22);
			color: white;
			font-size: var(--font-s);
			font-weight: 700;
			font-variant-numeric: tabular-nums;
			pointer-events: none;
			white-space: nowrap;

			&.is-start {
				left: 0 !important;
				transform: translateX(0);

				&::after {
					left: 8px;
					transform: rotate(45deg);
				}
			}

			&.is-end {
				left: auto !important;
				right: 0;
				transform: translateX(0);

				&::after {
					left: auto;
					right: 8px;
					transform: rotate(45deg);
				}
			}

			&::after {
				content: "";
				position: absolute;
				left: 50%;
				bottom: -5px;
				width: 8px;
				height: 8px;
				border-right: solid 1px var(--color-highlight);
				border-bottom: solid 1px var(--color-highlight);
				background-color: rgba(90, 156, 248, 0.22);
				transform: translateX(-50%) rotate(45deg);
			}
		}

		input {
			width: 100%;
			height: 1.4rem;
			margin: 18px 0 0;
			appearance: none;
			background: transparent;
			cursor: pointer;

			&::-webkit-slider-runnable-track {
				height: 5px;
				border-radius: 999px;
				background: linear-gradient(
					to right,
					var(--color-highlight) 0%,
					var(--color-highlight) var(--progress),
					var(--color-border) var(--progress),
					var(--color-border) 100%
				);
			}

			&::-webkit-slider-thumb {
				width: 16px;
				height: 16px;
				margin-top: -5.5px;
				appearance: none;
				border: solid 3px white;
				border-radius: 50%;
				background-color: var(--color-highlight);
				box-shadow: 0 0 0 1px rgba(90, 156, 248, 0.8);
			}

			&::-moz-range-track {
				height: 5px;
				border-radius: 999px;
				background: var(--color-border);
			}

			&::-moz-range-progress {
				height: 5px;
				border-radius: 999px;
				background: var(--color-highlight);
			}

			&::-moz-range-thumb {
				width: 12px;
				height: 12px;
				border: solid 3px white;
				border-radius: 50%;
				background-color: var(--color-highlight);
				box-shadow: 0 0 0 1px rgba(90, 156, 248, 0.8);
			}
		}
	}

	&-daytypes {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 6px;

		label {
			display: flex;
			align-items: center;
			justify-content: center;
			height: 1.75rem;
			border: solid 1px var(--color-border);
			border-radius: 5px;
			background-color: rgb(30, 30, 30);
			cursor: pointer;
			transition: border-color 0.2s, color 0.2s;

			&.active {
				border-color: var(--color-highlight);
				color: white;
			}
		}

		input {
			display: none;
		}
	}

	&-time-directions {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 6px;

		label {
			display: flex;
			align-items: center;
			justify-content: center;
			height: 1.75rem;
			border: solid 1px var(--color-border);
			border-radius: 5px;
			background-color: rgb(30, 30, 30);
			cursor: pointer;
			transition: border-color 0.2s, color 0.2s;

			&.active {
				border-color: var(--color-highlight);
				color: white;
			}
		}

		input {
			display: none;
		}
	}

	&-modes {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 6px;

		label {
			display: flex;
			align-items: center;
			justify-content: center;
			gap: 4px;
			height: 1.75rem;
			border: solid 1px var(--color-border);
			border-radius: 5px;
			background-color: rgb(30, 30, 30);
			cursor: pointer;
			transition: border-color 0.2s, color 0.2s;

			&.active {
				border-color: var(--mode-color);
				color: white;
			}
		}

		input {
			display: none;
		}
	}

	.mode-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background-color: var(--mode-color);
		flex-shrink: 0;
		opacity: 0.35;
		transition: opacity 0.2s;

		.active & {
			opacity: 1;
		}
	}

	&-divider {
		height: 1px;
		background-color: var(--color-border);
		margin: 4px 0;
	}

	&-status,
	&-error,
	&-hint {
		min-height: 1rem;
		margin: 2px 0 0;
		font-size: var(--font-s);
	}

	&-status {
		color: var(--color-highlight);
	}

	&-error {
		color: rgb(255, 96, 77);
	}
}

.isochrone-panel-enter-from,
.isochrone-panel-leave-to {
	opacity: 0;
	transform: translateY(-6px);
}

.isochrone-panel-enter-active,
.isochrone-panel-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}
</style>
