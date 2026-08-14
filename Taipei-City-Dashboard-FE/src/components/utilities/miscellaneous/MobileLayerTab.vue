<!-- !Depreciated! Mobile version no longer supports maps -->
<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useMapStore } from "../../../store/mapStore";
import { useContentStore } from "../../../store/contentStore";
import ComponentTag from "../../../dashboardComponent/components/ComponentTag.vue";
import AiSummaryIcon from "../../../components/icons/AiSummaryIcon.vue";

const contentStore = useContentStore();
const mapStore = useMapStore();

const props = defineProps(["content"]);
const emits = defineEmits(["openMapAiSummary"]);

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

function handleOpenMapAiSummary() {
	emits("openMapAiSummary", props.content);
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
      <div class="multipletagsArea">
        <button
          v-if="content.enable_ai_summary"
          @click="handleOpenMapAiSummary"
        >
          <AiSummaryIcon style="height: 16px; width: 16px;" />
        </button>
        <ComponentTag
          :icon="''"
          :text="cityTag.name"
          :mode="'small'"
          :class="`city-tag-item ${cityTag.value}`"
        />
      </div>
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
		margin: auto;
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

.multipletagsArea {
	display: flex;
	align-items: center;
	gap: 2px;

	button {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0px 4px;
		border: 1px solid #ffffff;
		border-radius: 5px;
		background: transparent;
		cursor: pointer;
		-webkit-tap-highlight-color: transparent;
		user-select: none;
		-webkit-user-select: none;
		outline: none;
	}
}
</style>
