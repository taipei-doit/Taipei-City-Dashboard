<!-- Developed By Taipei Urban Intelligence Center 2023-2024 -->
<!-- 
Lead Developer:  Igor Ho (Full Stack Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<!-- Map charts will be hidden in mobile mode and be replaced with the mobileLayers dialog -->

<script setup>
import { computed } from "vue";
import { DashboardComponent } from "city-dashboard-component";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useMapStore } from "../store/mapStore";
import MapContainer from "../components/map/MapContainer.vue";
import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const mapStore = useMapStore();

// Separate components with maps from those without
const parseMapLayers = computed(() => {
	const hasMap = contentStore.currentDashboard.components?.filter(
		(item) => item.map_config[0]
	);
	const noMap = contentStore.currentDashboard.components?.filter(
		(item) => !item.map_config[0]
	);

	return { hasMap: hasMap, noMap: noMap };
});

function handleOpenSettings() {
	contentStore.editDashboard = JSON.parse(
		JSON.stringify(contentStore.currentDashboard)
	);
	dialogStore.addEdit = "edit";
	dialogStore.showDialog("addEditDashboards");
}

// Open and closes the component as well as communicates to the mapStore to turn on and off map layers
function handleToggle(value, map_config) {
	if (!map_config[0]) {
		if (value) {
			dialogStore.showNotification(
				"info",
				"本組件沒有空間資料，不會渲染地圖"
			);
		}
		return;
	}
	if (value) {
		mapStore.addToMapLayerList(map_config);
	} else {
		mapStore.clearByParamFilter(map_config);
		mapStore.turnOffMapLayerVisibility(map_config);
	}
}

function shouldDisable(map_config) {
	const allMapLayerIds = map_config.map((el) => `${el.index}-${el.type}`);

	return (
		mapStore.loadingLayers.filter((el) => allMapLayerIds.includes(el))
			.length > 0
	);
}
</script>

<template>
  <div class="map">
    <div class="hide-if-mobile">
      <!-- 1. If the dashboard is map-layers -->
      <div
        v-if="contentStore.currentDashboard.index === 'map-layers'"
        class="map-charts"
      >
        <DashboardComponent
          v-for="item in contentStore.currentDashboard.components"
          :key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
          :config="item"
          mode="halfmap"
          :info-btn="true"
          :toggle-disable="shouldDisable(item.map_config)"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y
              );
            }
          "
          @filter-by-layer="
            (map_config, layer) => {
              mapStore.filterByLayer(map_config, layer);
            }
          "
          @clear-by-param-filter="
            (map_config) => {
              mapStore.clearByParamFilter(map_config);
            }
          "
          @clear-by-layer-filter="
            (map_config) => {
              mapStore.clearByLayerFilter(map_config);
            }
          "
        />
      </div>
      <!-- 2. Dashboards that have components -->
      <div
        v-else-if="
          contentStore.currentDashboard.components?.length !== 0 &&
            contentStore.mapLayers.length > 0
        "
        class="map-charts"
      >
        <DashboardComponent
          v-for="item in parseMapLayers.hasMap"
          :key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
          :config="item"
          mode="map"
          :info-btn="true"
          :toggle-disable="shouldDisable(item.map_config)"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y
              );
            }
          "
          @filter-by-layer="
            (map_config, layer) => {
              mapStore.filterByLayer(map_config, layer);
            }
          "
          @clear-by-param-filter="
            (map_config) => {
              mapStore.clearByParamFilter(map_config);
            }
          "
          @clear-by-layer-filter="
            (map_config) => {
              mapStore.clearByLayerFilter(map_config);
            }
          "
          @fly="
            (location) => {
              mapStore.flyToLocation(location);
            }
          "
        />
        <h2>基本圖層</h2>
        <DashboardComponent
          v-for="item in contentStore.mapLayers"
          :key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
          :config="item"
          mode="halfmap"
          :info-btn="true"
          :toggle-disable="shouldDisable(item.map_config)"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y
              );
            }
          "
          @filter-by-layer="
            (map_config, layer) => {
              mapStore.filterByLayer(map_config, layer);
            }
          "
          @clear-by-param-filter="
            (map_config) => {
              mapStore.clearByParamFilter(map_config);
            }
          "
          @clear-by-layer-filter="
            (map_config) => {
              mapStore.clearByLayerFilter(map_config);
            }
          "
        />
        <h2 v-if="parseMapLayers.noMap?.length > 0">
          無空間資料組件
        </h2>
        <DashboardComponent
          v-for="item in parseMapLayers.noMap"
          :key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
          :config="item"
          mode="map"
          :info-btn="true"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="handleToggle"
        />
      </div>
      <!-- 3. If dashboard is still loading -->
      <div
        v-else-if="contentStore.loading"
        class="map-charts-nodashboard"
      >
        <div />
      </div>
      <!-- 4. If dashboard failed to load -->
      <div
        v-else-if="contentStore.error"
        class="map-charts-nodashboard"
      >
        <span>sentiment_very_dissatisfied</span>
        <h2>發生錯誤，無法載入儀表板</h2>
      </div>
      <!-- 5. Dashboards that don't have components -->
      <div
        v-else
        class="map-charts-nodashboard"
      >
        <span>addchart</span>
        <h2>尚未加入組件</h2>
        <button
          v-if="contentStore.currentDashboard.icon !== 'favorite'"
          class="hide-if-mobile"
          @click="handleOpenSettings"
        >
          加入您的第一個組件
        </button>
        <p v-else>
          點擊其他儀表板組件之愛心以新增至收藏組件
        </p>
      </div>
    </div>
    <MapContainer />
    <MoreInfo />
    <ReportIssue />
  </div>
</template>

<style scoped lang="scss">
.map {
	height: calc(100vh - 127px);
	height: calc(var(--vh) * 100 - 127px);
	display: flex;
	margin: var(--font-m) var(--font-m);

	&-charts {
		width: 360px;
		max-height: 100%;
		height: fit-content;
		display: grid;
		row-gap: var(--font-m);
		margin-right: var(--font-s);
		border-radius: 5px;
		overflow-y: scroll;

		@media (min-width: 1000px) {
			width: 370px;
		}

		@media (min-width: 2000px) {
			width: 400px;
		}

		&-nodashboard {
			width: 360px;
			height: calc(100vh - 127px);
			height: calc(var(--vh) * 100 - 127px);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			margin-right: var(--font-s);

			@media (min-width: 1000px) {
				width: 370px;
			}

			@media (min-width: 2000px) {
				width: 400px;
			}

			span {
				margin-bottom: var(--font-ms);
				font-family: var(--font-icon);
				font-size: 2rem;
			}

			button {
				color: var(--color-highlight);
			}

			div {
				width: 2rem;
				height: 2rem;
				border-radius: 50%;
				border: solid 4px var(--color-border);
				border-top: solid 4px var(--color-highlight);
				animation: spin 0.7s ease-in-out infinite;
			}
		}
	}
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
</style>
