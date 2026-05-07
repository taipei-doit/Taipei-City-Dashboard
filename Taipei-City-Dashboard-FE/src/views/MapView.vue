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
/* global gtag */
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import EcoDietExtras from "../components/extras/EcoDietExtras.vue";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useMapStore } from "../store/mapStore";
import http from "../router/axios";
import MapContainer from "../components/map/MapContainer.vue";
import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const mapStore = useMapStore();
const route = useRoute();

const isEcoDiet = computed(() =>
	contentStore.currentDashboard.index === "eco_diet_metrotaipei"
);

const CITY_SELECT_LIST = [
	{ name: "臺北市", value: "taipei" },
	{ name: "新北市", value: "newtaipei" },
	{ name: "雙北", value: "metrotaipei" },
];

const activeCityMap = reactive({});
const ecoDietExtrasRef = ref(null);

function tagListOf(component) {
	const cityValue = activeCityMap[component.index] ?? component.city ?? "metrotaipei";
	if (cityValue === "taipei") return [{ name: "臺北市", value: "taipei" }];
	if (cityValue === "newtaipei") return [{ name: "新北市", value: "newtaipei" }];
	return [{ name: "雙北", value: "metrotaipei" }];
}

function normalizeEcoDietChartData(data, categories) {
	if (!categories || !data) return data;
	return data.map((series) => ({
		...series,
		data: Array.isArray(series.data) && typeof series.data[0] === "number"
			? series.data.map((y, i) => ({ x: categories[i], y }))
			: series.data,
	}));
}

async function handleEcoDietChangeCity(component, city) {
	activeCityMap[component.index] = city;
	try {
		const res = await http.get(`/component/${component.id}/chart`, {
			params: { city },
		});
		const { data, categories } = res.data;
		if (categories) {
			component.chart_config.categories = categories;
			component.chart_data = normalizeEcoDietChartData(data, categories);
		} else {
			component.chart_data = data ?? null;
		}
		if (component.map_config?.[0]) {
			const cityMapIndex = {
				metrotaipei: 0,
				taipei: 1,
				newtaipei: 2,
			}[city] ?? 0;
			const newMapConfig = [component.map_config[cityMapIndex] ?? component.map_config[0]];
			mapStore.clearByParamFilter(component.map_config);
			mapStore.turnOffMapLayerVisibility(component.map_config);
			component.map_config = newMapConfig;
			mapStore.addToMapLayerList(newMapConfig);
		}
	} catch {
		component.chart_data = null;
	}
}

function handleAiChat(config, event) {
	ecoDietExtrasRef.value?.openAiModal(event, String(config.id), config.name);
}

watch(isEcoDiet, (active) => {
	if (active) {
		contentStore.currentDashboard.storyBtn = {
			onClick: () => ecoDietExtrasRef.value?.openStoryModal(),
		};
	} else {
		contentStore.currentDashboard.storyBtn = null;
	}
}, { immediate: true });

onBeforeUnmount(() => {
	contentStore.currentDashboard.storyBtn = null;
});

const toggleOn = ref({
	hasMap: [],
	noMap: [],
	mapLayer: [],
	basicLayer: [],
});

// Separate components with maps from those without
const parseMapLayers = computed(() => {
	const hasMap = contentStore.currentDashboard.components?.filter(
		(item) => item.map_config[0],
	);
	const noMap = contentStore.currentDashboard.components?.filter(
		(item) => !item.map_config[0],
	);

	return { hasMap: hasMap, noMap: noMap };
});

watch(
	() => route.query.index,
	(newIndex, oldIndex) => {
		if (newIndex !== oldIndex) {
			toggleOn.value = {
				hasMap: new Array(parseMapLayers.value.hasMap?.length).fill(
					false,
				),
				noMap: new Array(parseMapLayers.value.noMap?.length).fill(
					false,
				),
				mapLayer: new Array(
					contentStore.currentDashboard.components?.length,
				).fill(false),
				basicLayer: new Array(contentStore.mapLayers?.length).fill(
					false,
				),
			};
		}
	},
);

function handleOpenSettings() {
	contentStore.editDashboard = JSON.parse(
		JSON.stringify(contentStore.currentDashboard),
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
				"本組件沒有空間資料，不會渲染地圖",
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

function toggleSwitchBtn(value, Btn, BtnIndex) {
	toggleOn.value[Btn][BtnIndex] = value;
}

function shouldDisable(map_config) {
	const allMapLayerIds = map_config.map(
		(el) => `${el.index}-${el.type}-${el.city}`,
	);
	if (mapStore.isPreloading === true) {
		return true;
	} else {
		return (
			mapStore.loadingLayers.filter((el) => allMapLayerIds.includes(el))
				.length > 0
		);
	}
}

// 開啟主題圖層時觸發GA自訂事件
function popularThematicLayerGA(map_config) {
	if (map_config[0].city && map_config[0].title) {
		gtag("event", "popular_thematic_layer", {
			dashboard_city: map_config[0].city,
			layer_name: map_config[0].title,
			city_layer: `${map_config[0].city}-${map_config[0].title}`,
			time: Date.now(),
		});
	}
}

// 開啟基本圖層時觸發GA自訂事件
function popularBasicLayerGA(map_config) {
	if (map_config[0].city && map_config[0].title) {
		gtag("event", "popular_basic_layer", {
			dashboard_city: map_config[0].city,
			layer_name: map_config[0].title,
			city_layer: `${map_config[0].city}-${map_config[0].title}`,
			time: Date.now(),
		});
	}
}
</script>

<template>
  <div class="map">
    <div class="hide-if-mobile">
      <!-- 1. If the dashboard is map-layers -->
      <div
        v-if="
          contentStore.currentDashboard.index?.includes('map-layers')
        "
        class="map-charts"
      >
        <DashboardComponent
          v-for="(item, arrayIdx) in contentStore.currentDashboard
            .components"
          :key="`map-layer-${item.index}-${item.city}`"
          :config="item"
          mode="halfmap"
          :info-btn="true"
          :active-city="item.city"
          :select-btn="true"
          :select-btn-disabled="
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            ).length === 1
          "
          :select-btn-list="
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            )
          "
          :city-tag="
            contentStore.cityManager.getTagList(
              contentStore.currentDashboard?.city,
            )
          "
          :toggle-disable="shouldDisable(item.map_config)"
          :toggle-on="toggleOn.mapLayer[arrayIdx]"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
              toggleSwitchBtn(value, 'mapLayer', arrayIdx);
              popularThematicLayerGA(map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y,
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
          @change-city="
            (city) => {
              const selectedData =
                contentStore.cityDashboard.components.find(
                  (data) => {
                    if (
                      data.index === item.index &&
                      data.city === city
                    ) {
                      return data;
                    }
                  },
                );

              const componentIndex =
                contentStore.currentDashboard.components.findIndex(
                  (item) => item.id === selectedData.id,
                );

              if (selectedData) {
                mapStore.clearByParamFilter(item.map_config);
                mapStore.turnOffMapLayerVisibility(
                  item.map_config,
                );
                mapStore.addToMapLayerList(
                  selectedData.map_config,
                );

                contentStore.setComponentData(
                  componentIndex,
                  selectedData,
                );
              }
            }
          "
        />
      </div>
      <!-- 2. Dashboards that have components -->
      <div
        v-else-if="
          contentStore.currentDashboard.components?.length !== 0
        "
        class="map-charts"
      >
        <DashboardComponent
          v-for="(item, arrayIdx) in parseMapLayers.hasMap"
          :key="`map-layer-${item.index}-${activeCityMap[item.index] ?? item.city}`"
          :config="item"
          mode="map"
          :info-btn="true"
          :active-city="isEcoDiet ? (activeCityMap[item.index] ?? item.city) : item.city"
          :ai-chat-btn="isEcoDiet"
          :select-btn="true"
          :select-btn-disabled="isEcoDiet ? false : (
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            ).length === 1 ||
              contentStore.currentDashboardExcluded.components.filter(
                (data) => data.index === item.index,
              ).length === 0
          )"
          :select-btn-list="isEcoDiet
            ? CITY_SELECT_LIST
            : (contentStore.currentDashboard?.city
              ? contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city)
              : contentStore.cityManager.getCities(contentStore.cityManager.activeCities))
          "
          :city-tag="isEcoDiet
            ? tagListOf(item)
            : (contentStore.currentDashboard?.city
              ? contentStore.cityManager.getTagList(contentStore.currentDashboard?.city)
              : contentStore.cityManager.getTagList(item.city))
          "
          :toggle-disable="shouldDisable(item.map_config)"
          :toggle-on="toggleOn.hasMap[arrayIdx]"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
              toggleSwitchBtn(value, 'hasMap', arrayIdx);
              popularThematicLayerGA(map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y,
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
          @ai-chat="(config, event) => handleAiChat(config, event)"
          @change-city="
            (city) => {
              if (isEcoDiet) {
                handleEcoDietChangeCity(item, city);
              } else {
                const selectedData =
                  contentStore.cityDashboard.components.find(
                    (data) => {
                      if (
                        data.index === item.index &&
                        data.city === city
                      ) {
                        return data;
                      }
                    },
                  );

                const componentIndex =
                  contentStore.currentDashboard.components.findIndex(
                    (item) => item.id === selectedData.id,
                  );

                if (selectedData) {
                  mapStore.clearByParamFilter(item.map_config);
                  mapStore.turnOffMapLayerVisibility(
                    item.map_config,
                  );
                  mapStore.addToMapLayerList(
                    selectedData.map_config,
                  );

                  contentStore.setComponentData(
                    componentIndex,
                    selectedData,
                  );
                }
              }
            }
          "
        />
        <h2 v-if="contentStore.mapLayers.length > 0">
          基本圖層
        </h2>
        <DashboardComponent
          v-for="(item, arrayIdx) in contentStore.mapLayers"
          :key="`map-layer-${item.index}-${item.city}`"
          :config="item"
          mode="halfmap"
          :info-btn="true"
          :active-city="item.city"
          :select-btn="true"
          :select-btn-disabled="
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            ).length === 1
          "
          :select-btn-list="
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            )
          "
          :city-tag="
            contentStore.cityManager.getTagList(
              contentStore.currentDashboard?.city,
            )
          "
          :toggle-disable="shouldDisable(item.map_config)"
          :toggle-on="toggleOn.basicLayer[arrayIdx]"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
              toggleSwitchBtn(value, 'basicLayer', arrayIdx);
              popularBasicLayerGA(map_config);
            }
          "
          @filter-by-param="
            (map_filter, map_config, x, y) => {
              mapStore.filterByParam(
                map_filter,
                map_config,
                x,
                y,
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
          @change-city="
            (city) => {
              const selectedData = contentStore.allMapLayers.find(
                (data) => {
                  if (
                    data.index === item.index &&
                    data.city === city
                  ) {
                    return data;
                  }
                },
              );

              if (selectedData) {
                mapStore.clearByParamFilter(item.map_config);
                mapStore.turnOffMapLayerVisibility(
                  item.map_config,
                );
                mapStore.addToMapLayerList(
                  selectedData.map_config,
                );

                contentStore.setMapLayerData(
                  arrayIdx,
                  selectedData,
                );
              }
            }
          "
        />
        <h2 v-if="parseMapLayers.noMap?.length > 0">
          無空間資料組件
        </h2>
        <DashboardComponent
          v-for="(item, arrayIdx) in parseMapLayers.noMap"
          :key="`map-layer-${item.index}-${item.city}`"
          :config="item"
          mode="map"
          :info-btn="true"
          :active-city="item.city"
          :select-btn="true"
          :select-btn-disabled="
            contentStore.cityManager.getSelectList(
              contentStore.currentDashboard?.city,
            ).length === 1 ||
              contentStore.currentDashboardExcluded.components.filter(
                (data) => data.index === item.index,
              ).length === 0
          "
          :select-btn-list="
            contentStore.currentDashboard?.city
              ? contentStore.cityManager.getSelectList(
                contentStore.currentDashboard?.city,
              )
              : contentStore.cityManager.getCities(
                contentStore.cityManager.activeCities,
              )
          "
          :city-tag="
            contentStore.currentDashboard?.city
              ? contentStore.cityManager.getTagList(
                contentStore.currentDashboard?.city,
              )
              : contentStore.cityManager.getTagList(item.city)
          "
          :toggle-on="toggleOn.noMap[arrayIdx]"
          @info="
            (item) => {
              dialogStore.showMoreInfo(item);
            }
          "
          @toggle="
            (value, map_config) => {
              handleToggle(value, map_config);
              toggleSwitchBtn(value, 'noMap', arrayIdx);
            }
          "
          @change-city="
            (city) => {
              const selectedData =
                contentStore.cityDashboard.components.find(
                  (data) => {
                    if (
                      data.index === item.index &&
                      data.city === city
                    ) {
                      return data;
                    }
                  },
                );
              const componentIndex =
                contentStore.currentDashboard.components.findIndex(
                  (data) =>
                    data.index === item.index &&
                    data.city === item.city,
                );
              if (selectedData && componentIndex !== -1) {
                contentStore.setComponentData(
                  componentIndex,
                  selectedData,
                );
              }
            }
          "
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
    <EcoDietExtras
      v-if="isEcoDiet"
      ref="ecoDietExtrasRef"
      :is-map-view="true"
    />
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
