<!-- Developed By Taipei Urban Intelligence Center 2023-2024 -->
<!-- 
Lead Developer:  Igor Ho (Full Stack Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<script setup>
/* global gtag */
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import EcoDietExtras from "../components/extras/EcoDietExtras.vue";
import router from "../router";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useAuthStore } from "../store/authStore";
import http from "../router/axios";

import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const authStore = useAuthStore();

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

watch(
	() => contentStore.currentDashboard.components,
	(components) => {
		if (!isEcoDiet.value || !components) return;
		components.forEach((component) => {
			const categories = component.chart_config?.categories;
			if (!categories || !component.chart_data) return;
			const needsNormalize = Array.isArray(component.chart_data) &&
				component.chart_data[0]?.data &&
				typeof component.chart_data[0].data[0] === "number";
			if (needsNormalize) {
				component.chart_data = normalizeEcoDietChartData(component.chart_data, categories);
			}
		});
	},
	{ deep: true }
);

onBeforeUnmount(() => {
	contentStore.currentDashboard.storyBtn = null;
});

function handleOpenSettings() {
	contentStore.editDashboard = JSON.parse(
		JSON.stringify(contentStore.currentDashboard)
	);
	dialogStore.addEdit = "edit";
	dialogStore.showDialog("addEditDashboards");
}

function toggleFavorite(id,name,city) {
	if (contentStore.favorites.components.includes(id)) {
		contentStore.unfavoriteComponent(id);
	} else {
		contentStore.favoriteComponent(id);
		// 成功收藏組件時觸發GA自訂事件
		if (city && name) {
			gtag('event','popular_component', {
				dashboard_city:city,
				component_name:name,
				city_component:`${city}-${name}`,
				time: Date.now(),
  			})
		}
	}
}
function handleMoreInfo(item) {
	// 檢視更多資訊時觸發GA自訂事件
	if (item.city && item.name){
		gtag('event','popular_component', {
			dashboard_city:item.city,
			component_name:item.name,
			city_component:`${item.city}-${item.name}`,
			time: Date.now(),
  		})
	}

	if (authStore.isMobileDevice && authStore.isNarrowDevice) {
		router.push({
			name: "component-info",
			params: { index: item.index },
		});
	} else {
		dialogStore.showMoreInfo(item);
	}
}
</script>

<template>
  <!-- 1. If the dashboard is map-layers -->
  <div
    v-if="contentStore.currentDashboard.index?.includes('map-layers')"
    class="dashboard"
  >
    <DashboardComponent
      v-for="item in contentStore.currentDashboard.components"
      :key="`${item.index}-${item.city}`"
      :config="item"
      mode="half"
      :info-btn="true"
      :active-city="item.city"
      :select-btn="true"
      :select-btn-disabled="contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city).length === 1"
      :select-btn-list="contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city)"
      :city-tag="contentStore.cityManager.getTagList(contentStore.currentDashboard?.city)"
      :favorite-btn="authStore.token ? true : false"
      :is-favorite="contentStore.favorites?.components.includes(item.id)"
      @favorite="
        (id) => {
          toggleFavorite(id,item.name,item.city);
        }
      "
      @info="
        (item) => {
          handleMoreInfo(item);
        }
      "
      @change-city="(city)=> {
        const selectedData = contentStore.cityDashboard.components.find((data) => {
          if (data.index === item.index && data.city === city) {
            return data
          }
        });

        const componentIndex = contentStore.currentDashboard.components.findIndex(
          (item) => item.id === selectedData.id
        );

        if (selectedData) {
          contentStore.setComponentData(componentIndex, selectedData);
        }
      }"
    />
    <MoreInfo />
    <ReportIssue />
  </div>
  <!-- 2. Dashboards that have components -->
  <div
    v-else-if="contentStore.currentDashboard.components?.length !== 0 || contentStore.cityDashboard.components?.length !== 0"
    class="dashboard"
  >
    <DashboardComponent
      v-for="item in contentStore.currentDashboard.components"
      :key="`${item.index}-${activeCityMap[item.index] ?? item.city}`"
      :config="item"
      :info-btn="true"
      :active-city="isEcoDiet ? (activeCityMap[item.index] ?? item.city) : item.city"
      :ai-chat-btn="isEcoDiet"
      :select-btn="true"
      :select-btn-disabled="isEcoDiet ? false : (contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city).length === 1 || contentStore.currentDashboardExcluded.components.filter((data) => data.index === item.index).length === 0)"
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
      :delete-btn="
        contentStore.personalDashboards
          .map((item) => item.index)
          .includes(contentStore.currentDashboard.index)
      "
      :favorite-btn="
        authStore.token &&
          contentStore.currentDashboard.icon !== 'favorite'
      "
      :is-favorite="contentStore.favorites?.components.includes(item.id)"
      @favorite="
        (id) => {
          toggleFavorite(id,item.name,item.city);
        }
      "
      @info="
        (item) => {
          handleMoreInfo(item);
        }
      "
      @delete="
        (id) => {
          contentStore.deleteComponent(id);
        }
      "
      @ai-chat="(config, event) => handleAiChat(config, event)"
      @change-city="(city) => {
        if (isEcoDiet) {
          handleEcoDietChangeCity(item, city);
        } else {
          const selectedData = contentStore.cityDashboard.components.find((data) => {
            if (data.index === item.index && data.city === city) {
              return data;
            }
          });
          const componentIndex = contentStore.currentDashboard.components.findIndex(
            (item) => item.id === selectedData.id
          );
          if (selectedData) {
            contentStore.setComponentData(componentIndex, selectedData);
          }
        }
      }"
    />
    <MoreInfo />
    <ReportIssue />
    <EcoDietExtras
      v-if="isEcoDiet"
      ref="ecoDietExtrasRef"
    />
  </div>
  <!-- 3. If dashboard is still loading -->
  <div
    v-else-if="contentStore.loading"
    class="dashboard dashboard-nodashboard"
  >
    <div class="dashboard-nodashboard-content">
      <div />
    </div>
  </div>
  <!-- 4. If dashboard failed to load -->
  <div
    v-else-if="contentStore.error"
    class="dashboard dashboard-nodashboard"
  >
    <div class="dashboard-nodashboard-content">
      <span>sentiment_very_dissatisfied</span>
      <h2>發生錯誤，無法載入儀表板</h2>
    </div>
  </div>
  <!-- 5. Dashboards that don't have components -->
  <div
    v-else
    class="dashboard dashboard-nodashboard"
  >
    <div class="dashboard-nodashboard-content">
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
</template>

<style scoped lang="scss">
.dashboard {
	max-height: calc(100vh - 127px);
	max-height: calc(var(--vh) * 100 - 127px);
	display: grid;
	row-gap: var(--font-s);
	column-gap: var(--font-s);
	margin: var(--font-m) var(--font-m);
	overflow-y: scroll;

	@media (min-width: 720px) {
		grid-template-columns: 1fr 1fr;
	}

	@media (min-width: 1296px) {
		grid-template-columns: 1fr 1fr 1fr;
	}

	@media (min-width: 1800px) {
		grid-template-columns: 1fr 1fr 1fr 1fr;
	}

	@media (min-width: 2200px) {
		grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
	}

	&-nodashboard {
		grid-template-columns: 1fr;

		&-content {
			width: 100%;
			height: calc(100vh - 127px);
			height: calc(var(--vh) * 100 - 127px);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;

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
