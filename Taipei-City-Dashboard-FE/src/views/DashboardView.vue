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
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import router from "../router";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useAuthStore } from "../store/authStore";
import { ref, watch } from "vue";

import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const authStore = useAuthStore();

// Dashboard AI Summary
const dashboardAISummary = ref("");
const dashboardAILoading = ref(false);
const dashboardAIError = ref(false);
const dashboardAICollapsed = ref(false);
let dashboardAIAbortController = null;

const dashboardIntros = {
	"防災都市": "這個儀表板整合雙北市防災相關資訊，涵蓋淹水潛勢、土石流警戒、避難所分佈與容量、以及各行政區災害風險等級，協助市民與決策者掌握城市韌性現況。",
	"健康守護": "這個儀表板彙整雙北市公共衛生指標，包含急診室壅塞狀況、腸病毒與登革熱疫情分佈、醫療資源配置，以及各行政區健康風險概況，支援即時公衛決策。",
	"長照關懷": "這個儀表板呈現雙北市高齡化相關統計，涵蓋扶養比、老化指數、高齡就業結構，以及長照服務資源分佈，協助了解高齡社會的挑戰與政策需求。",
	"捷運系統": "這個儀表板展示雙北市捷運路網的運量、班距、轉乘人次與各站進出站統計，協助掌握大眾運輸使用趨勢與路網效能。",
	"道路交通": "這個儀表板整合雙北市道路交通資料，包含路段壅塞指數、號誌時制、事故統計與車流量分析，協助了解城市道路使用狀況。",
	"共享單車": "這個儀表板追蹤雙北市 YouBike 即時狀況，包含各站可借還車輛數、熱門站點分佈與使用趨勢，協助市民規劃最後一哩路。",
	"務實交通": "這個儀表板整合雙北市跨運具交通資訊，涵蓋 YouBike 使用率、電動公車普及度與自行車道路網，呈現永續交通發展現況。",
	"都市規劃": "這個儀表板展示雙北市土地使用分區、建築許可核發與都市更新進度，協助掌握城市空間發展與規劃政策執行情況。",
	"城市建設": "這個儀表板追蹤雙北市重大公共建設進度，包含工程施工狀態、預算執行率與建設分佈，協助了解城市基礎設施投資概況。",
	"婦幼資源": "這個儀表板整合雙北市婦女與兒童相關服務資源，涵蓋托嬰中心、托育補助、婦女館及相關福利設施分佈，支援家庭政策規劃。",
	"為民服務": "這個儀表板彙整雙北市政府各類市民服務資訊，包含行政申辦量、服務據點分佈與民眾滿意度，協助評估政府服務效能。",
	"氣候變遷": "這個儀表板監測雙北市氣候與環境指標，涵蓋碳排放、空氣品質、熱島效應與極端氣候事件，支援城市氣候調適策略制定。",
	"商圈活化": "這個儀表板分析雙北市各商圈的人流動態、消費指數、店家密度與空置率，協助評估商業活力並支援地方經濟振興政策。",
	"圖資資訊": "這個儀表板提供雙北市地理資訊圖層，涵蓋行政區界、地形、設施位置等空間資料，支援城市管理與地理分析應用。",
	"食安健康": "這個儀表板整合雙北市食品安全與餐飲衛生資訊，涵蓋食品稽查紀錄、違規商家統計、餐飲衛生評級分佈，以及近期食安事件通報，協助市民掌握飲食安全現況與政府稽查動態。",
};

function getDashboardPrompt(name) {
	const intro = dashboardIntros[name];
	if (intro) return `不需使用工具，直接回答：${intro}請用一段話重新表達，限80字。`;
	return `不需使用工具，直接用一段話介紹「${name}」儀表板的功能與涵蓋的主要資料主題，限80字。`;
}

async function fetchDashboardSummary(dashboardName) {
	if (!dashboardName || !authStore.token) return;
	// 取消前一個進行中的請求
	if (dashboardAIAbortController) dashboardAIAbortController.abort();
	dashboardAIAbortController = new AbortController();
	dashboardAILoading.value = true;
	dashboardAIError.value = false;
	dashboardAISummary.value = "";
	dashboardAICollapsed.value = false;
	try {
		const baseUrl = import.meta.env.VITE_API_URL || "";
		const res = await fetch(`${baseUrl}/ai/chat/twai`, {
			method: "POST",
			headers: { "Content-Type": "application/json",
				Authorization: `Bearer ${authStore.token}`
			 },
			signal: dashboardAIAbortController.signal,
			body: JSON.stringify({
				stream: true,
				messages: [{
					role: "user",
					content: getDashboardPrompt(dashboardName),
				}],
			}),
		});
		if (!res.ok) throw new Error(res.status);
		const reader = res.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";
		dashboardAILoading.value = false;
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split("\n");
			buffer = lines.pop();
			for (const line of lines) {
				if (!line.startsWith("data:")) continue;
				try {
					const json = JSON.parse(line.slice(5).trim());
					if (json.generated_text) {
						// 過濾掉 tool call XML
						const text = json.generated_text.replace(/<tool[^>]*>[\s\S]*?<\/function>/g, "").replace(/<[^>]+>/g, "");
						dashboardAISummary.value += text;
					}
				} catch { /* skip */ }
			}
		}
	} catch(e) {
		if (e?.name === 'AbortError') return;
		dashboardAIError.value = true;
		dashboardAILoading.value = false;
	}
}

watch(
	() => contentStore.currentDashboard?.name,
	(name) => { if (name) fetchDashboardSummary(name); },
	{ immediate: true }
);

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
    <div class="db-ai-banner">
      <div class="db-ai-banner-header" @click="dashboardAICollapsed = !dashboardAICollapsed">
        <span class="material-icons">auto_awesome</span>
        <p>{{ contentStore.currentDashboard.name }} — AI 整體摘要</p>
        <span class="material-icons">{{ dashboardAICollapsed ? 'expand_more' : 'expand_less' }}</span>
      </div>
      <div v-show="!dashboardAICollapsed" class="db-ai-banner-body">
        <p v-if="dashboardAILoading" class="db-ai-loading">查詢中，請稍候...</p>
        <p v-else-if="dashboardAIError" class="db-ai-error">AI 摘要服務暫時無法使用。</p>
        <p v-else>{{ dashboardAISummary }}</p>
      </div>
    </div>
    <DashboardComponent
      v-for="item in contentStore.currentDashboard.components"
      :key="`${item.index}-${item.city}`"
      :config="item"
      mode="half"
      :info-btn="true"
      :ai-summary-btn="true"
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
    <!-- Dashboard AI Summary Banner -->
    <div class="db-ai-banner">
      <div class="db-ai-banner-header" @click="dashboardAICollapsed = !dashboardAICollapsed">
        <span class="material-icons">auto_awesome</span>
        <p>{{ contentStore.currentDashboard.name }} — AI 整體摘要</p>
        <span class="material-icons">{{ dashboardAICollapsed ? 'expand_more' : 'expand_less' }}</span>
      </div>
      <div v-show="!dashboardAICollapsed" class="db-ai-banner-body">
        <p v-if="dashboardAILoading" class="db-ai-loading">查詢中，請稍候...</p>
        <p v-else-if="dashboardAIError" class="db-ai-error">AI 摘要服務暫時無法使用。</p>
        <p v-else>{{ dashboardAISummary }}</p>
      </div>
    </div>
    <DashboardComponent
      v-for="item in contentStore.currentDashboard.components"
      :key="`${item.index}-${item.city}`"
      :config="item"
      :info-btn="true"
      :ai-summary-btn="true"
      :active-city="item.city"
      :select-btn="true"
      :select-btn-disabled="contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city).length === 1 || contentStore.currentDashboardExcluded.components.filter((data) => data.index === item.index).length === 0"
      :select-btn-list="contentStore.currentDashboard?.city
        ? contentStore.cityManager.getSelectList(contentStore.currentDashboard?.city)
        : contentStore.cityManager.getCities(contentStore.cityManager.activeCities)
      "
      :city-tag="contentStore.currentDashboard?.city
        ? contentStore.cityManager.getTagList(contentStore.currentDashboard?.city)
        : contentStore.cityManager.getTagList(item.city)
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
      }
      "
    />
    <MoreInfo />
    <ReportIssue />
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

.db-ai-banner {
	grid-column: 1 / -1;
	background-color: var(--color-component-background);
	border-radius: 5px;
}

.db-ai-banner-header {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 10px 16px;
	cursor: pointer;
	user-select: none;

	span {
		font-family: var(--font-icon);
		color: var(--color-highlight);
		font-size: 18px;
	}

	p {
		flex: 1;
		color: var(--color-highlight);
		font-size: var(--font-s);
		font-weight: 500;
	}
}

.db-ai-banner-body {
	padding: 0 16px 12px;

	p {
		color: var(--color-complement-text);
		font-size: var(--font-s);
		line-height: 1.7;
	}

	.db-ai-loading,
	.db-ai-error {
		color: var(--color-border);
	}
}
</style>
