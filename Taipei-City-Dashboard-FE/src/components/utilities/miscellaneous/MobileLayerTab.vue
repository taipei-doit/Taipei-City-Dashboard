<!-- !Depreciated! Mobile version no longer supports maps -->
<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useMapStore } from "../../../store/mapStore";
import { useContentStore } from "../../../store/contentStore";
import ComponentTag from "../../../dashboardComponent/components/ComponentTag.vue";

const contentStore = useContentStore();
const mapStore = useMapStore();

const props = defineProps(["content"]);

const checked = ref(false);
const toggleCount = ref(0);
const cityTag = ref(contentStore.cityManager.getTagList(props.content.city).find((tag) => tag.value === props.content.city));

// Communicates with the mapStore to open and close map layers on mobile
function handleToggle() {
	if (!props.content.map_config) {
		return;
	}

	if (props.content.city === 'metrotaipei') {
		handleMetroTaipeiToggle();
	} else {
		handleBasicToggle();
	}
}
function handleBasicToggle() {
	if (checked.value) {
		mapStore.addToMapLayerList(props.content.map_config);
	} else {
		mapStore.turnOffMapLayerVisibility(props.content.map_config);
	}
}

function handleMetroTaipeiToggle() {
	let selectedData = contentStore.cityDashboard.components.find((data) => {
		return data.index === props.content.index && data.city !== props.content.city;
	});
	
	if (!selectedData) {
		selectedData = contentStore.allMapLayers.find((data) => {
			return data.index === props.content.index && data.city !== props.content.city;
		});
	}

	if (checked.value && toggleCount.value === 0) {
		// 第一次切換：開啟當前圖層
		mapStore.addToMapLayerList(props.content.map_config);
		toggleCount.value++;
	} else if (toggleCount.value === 1) {
		// 第二次切換：切換到另一個城市
		checked.value = true;
		cityTag.value = contentStore.cityManager
			.getTagList(selectedData.city)
			.find((tag) => tag.value === selectedData.city);
		mapStore.turnOffMapLayerVisibility(props.content.map_config);
		mapStore.addToMapLayerList(selectedData.map_config);
		toggleCount.value++;
	} else {
		// 第三次切換：關閉所有圖層，重置狀態
		checked.value = false
		cityTag.value = contentStore.cityManager
			.getTagList(props.content.city)
			.find((tag) => tag.value === props.content.city);
		toggleCount.value = 0;
		mapStore.turnOffMapLayerVisibility(props.content.map_config);
		mapStore.turnOffMapLayerVisibility(selectedData.map_config);
	}
}
</script>

<template>
  <div class="mobilelayertab">
    <input
      :id="content.index"
      v-model="checked"
      type="checkbox"
      @change="handleToggle"
    >
    <label
      :for="content.index"
      :class="{ checked: checked }"
    >
      <img
        :src="`/images/thumbnails/${content.chart_config.types[0]}.svg`"
      >
    </label>
    <div class="citytagwithname">
      <ComponentTag
        :icon="''"
        :text="cityTag.name"
        :mode="'small'"
        :class="`city-tag-item ${cityTag.value}`"
      />
      <p>
        {{ content.name }}
      </p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.mobilelayertab {
	input {
		width: 0;
		height: 0;
		opacity: 0;
	}

	label {
		width: 73px;
		height: 73px;
		display: inline-block;
		border: solid 1px transparent;
		border-radius: 5px;
		background-color: var(--color-complement-text);
		transition: border 0.2s;
		cursor: pointer;

		img {
			width: 100%;
		}
	}

	input:checked + label {
		border: solid 1px var(--color-highlight);
		background-color: var(--color-highlight);
		img {
			filter: invert(1);
		}
	}

	p {
		margin-top: 4px;
		color: var(--color-complement-text);
		font-size: 0.75rem;
		text-align: center;
	}

	margin-bottom: 8px;
}

.checked {
	border: solid 1px var(--color-highlight);
}

.citytagwithname {
	margin-top: 4px;
	display: flex;
	flex-direction: column;
	align-items: center;
}
</style>
