<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, defineProps, watch, computed, onBeforeUnmount } from "vue";
import { storeToRefs } from "pinia";
import DashboardComponent from "../../../dashboardComponent/DashboardComponent.vue";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";
import { useContentStore } from "../../../store/contentStore";
import { useAuthStore } from "../../../store/authStore.js";

import DialogContainer from "../DialogContainer.vue";
import InputTags from "../../utilities/forms/InputTags.vue";
import SelectButtons from "../../utilities/forms/SelectButtons.vue";
import HistoryChart from "../../charts/HistoryChart.vue";

import { chartsPerDataType } from "../../../assets/configs/apexcharts/chartTypes";
import { timeTerms } from "../../../assets/configs/AllTimes";
import { mapTypes } from "../../../assets/configs/mapbox/mapConfig";
import {
	buildMapSummaryPromptPayload,
	summarizeGeoJsonForAi,
} from "../../../assets/utilityFunctions/summarizeGeoJsonForAi";
import http from "../../../router/axios";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();
const contentStore = useContentStore();
const authStore = useAuthStore();

const props = defineProps(["searchParams"]);

const allowedDomains = [
	"citydashboard.taipei",
	"test-citydashboard.taipei",
];

const isCloudEnv = allowedDomains.includes(
	window.location.hostname,
);

const promptForChart = ref("你是台北市城市儀表板的資料分析助理。請根據提供的組件資訊與圖表資料，使用繁體中文撰寫一段 150 到 220 字的分析摘要。摘要應先簡要說明圖表的用途與指標意義，再分析資料中值得關注的趨勢、高低差異、排名、變化幅度、異常值、轉折點或群組差異，並說明這些現象可能代表的城市治理意義或使用者可以如何解讀。請優先引用資料中的具體期間、分類、區域與數值，使洞察具有依據。若資料不足以判斷原因，只能描述觀察到的現象，不可自行推測因果關係；若資料沒有明顯趨勢或差異，應如實說明資料分布相對穩定。只需輸出一段完整摘要，不要條列、不要加標題、不要描述分析步驟。");
const promptForMap = ref("你是台北市城市儀表板的空間資料分析助理。請根據提供的地圖圖層資訊、欄位說明與實際圖層資料，使用繁體中文撰寫一段 150 到 220 字的分析摘要。摘要應先簡要說明圖層呈現的空間資料內容與主要欄位意義；若提供了地圖顏色或樣式對照，也要說明不同顏色或樣式在地圖上分別代表什麼分類或狀態，並附上對應的色碼。再分析地圖中值得關注的空間分布現象，例如集中區域、稀疏區域、群聚、熱點、區域差異、鄰近關係、覆蓋範圍或異常點位，並說明使用者可以如何解讀這些空間特徵及其可能的城市治理意義。請優先引用資料中的行政區、地點、分類、數量或指標數值，使洞察具有依據。不得僅依點位數量直接推論事件風險或需求程度，也不可在資料不足時推測因果關係；若無法辨識明顯空間特徵，應如實說明目前分布較為平均或資訊不足。只需輸出一段完整摘要，不要條列、不要加標題、不要描述分析步驟。");
const updateMapSummaryLoading = ref(false);
const updateChartSummaryLoading = ref(false);

const { currentComponent } = storeToRefs(adminStore);
const currentSettings = ref("all");
const tempInputStorage = ref({
	link: "",
	contributor: "",
	chartColor: "#000000",
	historyColor: "#000000",
});

const pendingJobs = ref(loadPendingJobs());
const pollingIntervals = {};

function loadPendingJobs() {
	try {
		return JSON.parse(
			localStorage.getItem("ai_summary_pending_jobs") || "{}",
		);
	} catch {
		return {};
	}
}

function persistPendingJobs() {
	localStorage.setItem(
		"ai_summary_pending_jobs",
		JSON.stringify(pendingJobs.value),
	);
}

function getJobKey(city, index, type) {
	return `${city}-${index}-${type}`;
}

const isSuperAd = computed(() => {
	return authStore.user.is_admin && !authStore.isso_token && authStore.token;
});

// 個別判斷 chart / map 是否正在更新中
function isTypeUpdating(type) {
	if (!currentComponent.value) return false;
	const key = getJobKey(
		currentComponent.value.city,
		currentComponent.value.index,
		type,
	);
	return !!pendingJobs.value[key];
}

function handleConfirm() {
	adminStore.updateComponent(props.searchParams);
	handleClose();
}

function handleClose() {
	currentSettings.value = "all";
	dialogStore.hideAllDialogs();
	adminStore.currentComponent = null;
}

async function handleRenewAiSummary(type) {
	if (isCloudEnv) {
		await handleRenewAiSummaryCloud(type);
	} else {
		await handleRenewAiSummaryLocal(type);
	}
}

// 雲端環境 AI 摘要刷新機制
async function handleRenewAiSummaryCloud(type) {
	const { city } = currentComponent.value;
	const { index } = currentComponent.value;
	const key = getJobKey(city, index, type);

	if (pendingJobs.value[key]) return; // 已經在跑，防重複點擊

	try {
		const res = await http.post("/component/ai-summary/trigger", {
			index,
			city,
			type,
		});

		if (res?.data) {
			pendingJobs.value[key] = {
				dag_run_id: res.data.dag_run_id,
				conf: { ...res.data.conf, type },
			};
			persistPendingJobs();
			startPolling(key);
		}
	} catch (e) {
		dialogStore.showNotification('fail', '觸發 AI 摘要更新任務失敗，請稍後再試');
		console.error("觸發 AI 摘要更新任務失敗", e);
	}
}

// 地端 AI 摘要刷新機制
async function handleRenewAiSummaryLocal(type) {
	if (type === "chart") {
		updateChartSummaryLoading.value = true;
		try {
			const userContent = buildPrompt(currentComponent.value);
			const res = await http.post("/component/ai-summary/generate", {
				index: currentComponent.value.index,
				city: currentComponent.value.city,
				type: "chart",
				messages: [
					{ role: "system", content: promptForChart.value },
					{ role: "user", content: userContent },
				],
				max_new_tokens: 512,
				temperature: 0.7,
			});
			if (res?.data?.data?.summary?.result) {
				refreshSummaries(currentComponent.value.city, currentComponent.value.index);
			} else {
				dialogStore.showNotification('fail', '圖表摘要更新失敗，AI 回傳內容為空');
				console.warn("圖表摘要更新失敗，AI 回傳內容為空");
			}
		} catch (e) {
			dialogStore.showNotification('fail', '圖表摘要更新失敗，請稍後再試');
			console.error("圖表摘要更新失敗", e);
		} finally {
			updateChartSummaryLoading.value = false;
		}
	} else if (type === "map") {
		updateMapSummaryLoading.value = true;

		try {
			if (currentComponent.value.map_config.length === 0) {
				dialogStore.showNotification('fail', '地圖配置為空，無法生成摘要');
				console.warn("地圖配置為空，無法生成摘要");
				return;
			}

			const layerSummaries = [];

			for (const mapConfig of currentComponent.value.map_config) {
				if (!mapConfig?.index) {
					continue;
				}
				if (mapConfig.source !== "geojson") continue;

				try {
					const response = await fetch(
						`/mapData/${mapConfig.index}.geojson`,
					);
					if (!response.ok) {
						throw new Error(`HTTP ${response.status}`);
					}
					const data = await response.json();
					layerSummaries.push(summarizeGeoJsonForAi(data, mapConfig));
				} catch (error) {
					console.error(`取得 ${mapConfig.index} GeoJSON 失敗`, error);
				}
			}

			if (layerSummaries.length === 0) {
				dialogStore.showNotification('fail', '未有可解析之地圖圖層，無法生成摘要');
				console.warn("未有可解析之地圖圖層，無法生成摘要");
				return;
			}

			const userContent = JSON.stringify(
				buildMapSummaryPromptPayload(
					currentComponent.value,
					layerSummaries,
				),
			);

			const res = await http.post("/component/ai-summary/generate", {
				index: currentComponent.value.index,
				city: currentComponent.value.city,
				type: "map",
				messages: [
					{ role: "system", content: promptForMap.value },
					{ role: "user", content: userContent },
				],
				max_new_tokens: 512,
				temperature: 0.7,
			});
			if (res?.data?.data?.summary?.result) {
				refreshSummaries(currentComponent.value.city, currentComponent.value.index);
			} else {
				dialogStore.showNotification('fail', '地圖摘要更新失敗，AI 回傳內容為空');
				console.warn("地圖摘要更新失敗，AI 回傳內容為空");
			}
		} catch (e) {
			dialogStore.showNotification('fail', '地圖摘要更新失敗，請稍後再試');
			console.error("地圖摘要更新失敗", e);
		} finally {
			updateMapSummaryLoading.value = false;
		}
	}
}

function startPolling(key) {
	if (pollingIntervals[key]) return;

	pollingIntervals[key] = setInterval(async () => {
		const job = pendingJobs.value[key];
		if (!job) return stopPolling(key); // 資料被清掉了(例如另一個分頁清除)，保險起見停止

		try {
			const statusRes = await http.get(
				`/component/ai-summary/status/${encodeURIComponent(job.dag_run_id)}`,
			);
			const state = statusRes?.data?.state;

			if (state === "success" || state === "failed") {
				stopPolling(key);
				delete pendingJobs.value[key];
				persistPendingJobs();

				if (state === "success") {
					const isCurrent =
						currentComponent.value &&
						getJobKey(
							currentComponent.value.city,
							currentComponent.value.index,
							job.conf.type,
						) === key;
					if (isCurrent) {
						refreshSummaries(job.conf.city, job.conf.index);
					}
				}
			}
		} catch (e) {
			console.error("查詢 AI 摘要任務狀態失敗", e);
		}
	}, 5000);
}

function stopPolling(key) {
	clearInterval(pollingIntervals[key]);
	delete pollingIntervals[key];
}

let responseForChart = ref(null);
let responseForMap = ref(null);

async function refreshSummaries(city, index) {
	// 先清空，避免短暫顯示或錯誤時殘留上一個組件的內容
	responseForChart.value = null;
	responseForMap.value = null;

	try {
		responseForChart.value = await http.get("/component/ai-summary", {
			params: { index, city, type: "chart" },
		});
	} catch (e) {
		console.error("取得圖表 AI 摘要失敗", e);
		responseForChart.value = null;
	}

	try {
		responseForMap.value = await http.get("/component/ai-summary", {
			params: { index, city, type: "map" },
		});
	} catch (e) {
		console.error("取得地圖 AI 摘要失敗", e);
		responseForMap.value = null;
	}
}

function buildPrompt(component) {
	const { name, city, short_desc, long_desc, chart_data, updated_at } =
		component;

	// TextUnitChart: 每個指標只有一個數值，直接攤平成 key-value
	const kpis = chart_data.map((d) => {
		const value = Array.isArray(d.data) ? d.data[0] : d.data;
		return `${d.name}：${value}${d.icon ?? ""}`;
	});

	return [
		`圖表名稱：${name}`,
		`所屬城市：${city}`,
		`圖表說明：${short_desc}`,
		`指標定義與脈絡：${long_desc}`,
		`資料時間：${component.time_from === "static" ? "靜態資料（無特定期間）" : component.time_from}`,
		`資料更新時間：${updated_at}`,
		`本次數據：\n${kpis.join("\n")}`,
	].join("\n\n");
}

watch(
	() => currentComponent.value,
	async (newVal) => {
		if (!newVal) return;

		["chart", "map"].forEach((type) => {
			const key = getJobKey(newVal.city, newVal.index, type);
			if (pendingJobs.value[key]) {
				startPolling(key);
			}
		});

		await refreshSummaries(newVal.city, newVal.index);
	},
	{ immediate: true },
);

onBeforeUnmount(() => {
	Object.keys(pollingIntervals).forEach(stopPolling);
});
</script>

<template>
  <DialogContainer
    :dialog="`adminComponentSettings`"
    @on-close="handleClose"
  >
    <div class="admincomponentsettings">
      <div class="admincomponentsettings-header">
        <h2>組件設定</h2>
        <button @click="handleConfirm">
          確定更改
        </button>
      </div>
      <div class="admincomponentsettings-tabs">
        <button
          :class="{ active: currentSettings === 'all' }"
          @click="currentSettings = 'all'"
        >
          整體
        </button>
        <button
          :class="{ active: currentSettings === 'chart' }"
          @click="currentSettings = 'chart'"
        >
          圖表
        </button>
        <button
          v-if="currentComponent.history_config !== null"
          :class="{ active: currentSettings === 'history' }"
          @click="currentSettings = 'history'"
        >
          歷史軸
        </button>
        <button
          v-if="currentComponent.map_config[0] !== null"
          :class="{ active: currentSettings === 'map' }"
          @click="currentSettings = 'map'"
        >
          地圖
        </button>
      </div>
      <div class="admincomponentsettings-content">
        <div class="admincomponentsettings-settings">
          <div
            v-if="currentSettings === 'all'"
            class="admincomponentsettings-settings-items"
          >
            <label>組件名稱* ({{
              currentComponent.name.length
            }}/10)</label>
            <input
              v-model="currentComponent.name"
              type="text"
              :minlength="1"
              :maxlength="15"
              required
              disabled
            >
            <div class="two-block">
              <label>組件 ID</label>
              <label>組件 Index</label>
            </div>
            <div class="two-block">
              <input
                type="text"
                :value="currentComponent.id"
                disabled
              >
              <input
                type="text"
                :value="currentComponent.index"
                disabled
              >
            </div>
            <label>資料來源*</label>
            <input
              v-model="currentComponent.source"
              type="text"
              :minlength="1"
              :maxlength="12"
              required
            >
            <label>更新頻率* (0 = 不定期更新)</label>
            <div class="two-block">
              <input
                v-model="currentComponent.update_freq"
                type="number"
                :min="0"
                :max="31"
                required
              >
              <select v-model="currentComponent.update_freq_unit">
                <option value="minute" />
                <option value="hour">
                  時
                </option>
                <option value="day">
                  天
                </option>
                <option value="week">
                  週
                </option>
                <option value="month">
                  月
                </option>
                <option value="year">
                  年
                </option>
              </select>
            </div>
            <label>資料區間</label>
            <!-- eslint-disable no-mixed-spaces-and-tabs -->
            <div class="three-block">
              <select
                v-model="currentComponent.time_from"
                @change="
                  () => {
                    if (
                      [
                        'current',
                        'static',
                        'demo',
                        'maintain',
                      ].includes(
                        currentComponent.time_from,
                      )
                    ) {
                      currentComponent.time_to = '';
                    } else {
                      currentComponent.time_to = 'now';
                    }
                  }
                "
              >
                <option
                  v-for="time in [
                    'current',
                    'static',
                    'demo',
                    'maintain',
                    'day_start',
                    'week_start',
                    'month_start',
                    'quarter_start',
                    'year_start',
                    'day_ago',
                    'week_ago',
                    'month_ago',
                    'quarter_ago',
                    'halfyear_ago',
                    'year_ago',
                  ]"
                  :key="time"
                  :value="time"
                >
                  {{ timeTerms[time] }}
                </option>
              </select>
              <div
                :style="{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }"
              >
                至
              </div>
              <input
                :value="
                  currentComponent.time_to === 'now'
                    ? '現在'
                    : 'N/A'
                "
                :disabled="true"
              >
            </div>
            <label required>組件簡述* ({{
              currentComponent.short_desc.length
            }}/50)</label>
            <textarea
              v-model="currentComponent.short_desc"
              :minlength="1"
              :maxlength="50"
              required
            />
            <label>組件詳述* ({{
              currentComponent.long_desc.length
            }}/100)</label>
            <textarea
              v-model="currentComponent.long_desc"
              :minlength="1"
              :maxlength="100"
              required
            />
            <label>範例情境* ({{
              currentComponent.use_case.length
            }}/100)</label>
            <textarea
              v-model="currentComponent.use_case"
              :minlength="1"
              :maxlength="100"
              required
            />
            <label>資料連結</label>
            <InputTags
              :tags="currentComponent.links"
              @deletetag="
                (index) => {
                  currentComponent.links.splice(index, 1);
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.links = updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.link"
              type="text"
              :minlength="1"
              @keypress.enter="
                () => {
                  if (tempInputStorage.link.length > 0) {
                    currentComponent.links.push(
                      tempInputStorage.link,
                    );
                    tempInputStorage.link = '';
                  }
                }
              "
            >
            <label>貢獻者</label>
            <InputTags
              :tags="currentComponent.contributors"
              @deletetag="
                (index) => {
                  currentComponent.contributors.splice(
                    index,
                    1,
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.contributors = updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.contributor"
              type="text"
              @keypress.enter="
                () => {
                  if (
                    tempInputStorage.contributor.length > 0
                  ) {
                    currentComponent.contributors.push(
                      tempInputStorage.contributor,
                    );
                    tempInputStorage.contributor = '';
                  }
                }
              "
            >
            <div class="enable_ai_summary">
              <label>是否開啟 AI 摘要功能</label>
              <label class="toggle-switch">
                <input
                  v-model="currentComponent.enable_ai_summary"
                  type="checkbox"
                >
                <span class="toggle-switch-slider" />
              </label>
            </div>
            <div
              v-if="isSuperAd"
              class="refresh_ai_summary"
            >
              <label>組件圖表 AI 摘要刷新</label>
              <div class="ai_summary-btns">
                <button
                  :disabled="isTypeUpdating('chart') || updateChartSummaryLoading"
                  @click="handleRenewAiSummary('chart')"
                >
                  {{
                    isTypeUpdating("chart") || updateChartSummaryLoading
                      ? "更新中…"
                      : "點擊刷新"
                  }}
                </button>
              </div>
              <div
                v-if="!isCloudEnv"
                class="ai_summary-settings"
              >
                <label>組件圖表 AI 摘要刷新 prompt 設定</label>
                <textarea
                  v-model="promptForChart"
                  type="text"
                  rows="5"
                />
              </div>
            </div>
            <div class="ai_summary_preview">
              <label>目前組件圖表 AI 摘要內容</label>
              <div class="ai_summary_preview-content">
                {{
                  responseForChart?.data.data.result ||
                    "無資料"
                }}
              </div>
            </div>
            <div
              v-if="isSuperAd"
              class="refresh_ai_summary"
            >
              <label>組件地圖 AI 摘要刷新</label>
              <div class="ai_summary-btns">
                <button
                  :disabled="isTypeUpdating('map') || updateMapSummaryLoading"
                  @click="handleRenewAiSummary('map')"
                >
                  {{
                    isTypeUpdating("map") || updateMapSummaryLoading
                      ? "更新中…"
                      : "點擊刷新"
                  }}
                </button>
              </div>
              <div
                v-if="!isCloudEnv"
                class="ai_summary-settings"
              >
                <label>組件地圖 AI 摘要刷新 prompt 設定</label>
                <textarea
                  v-model="promptForMap"
                  type="text"
                  rows="5"
                />
              </div>
            </div>
            <div class="ai_summary_preview">
              <label>目前組件地圖 AI 摘要內容</label>
              <div class="ai_summary_preview-content">
                {{
                  responseForMap?.data.data.result || "無資料"
                }}
              </div>
            </div>
          </div>
          <div
            v-else-if="currentSettings === 'chart'"
            class="admincomponentsettings-settings-items"
          >
            <label>圖表資料型態</label>
            <select
              :value="currentComponent.query_type"
              disabled
            >
              <option value="two_d">
                二維資料
              </option>
              <option value="three_d">
                三維資料
              </option>
              <option value="time">
                時間序列資料
              </option>
              <option value="percent">
                百分比資料
              </option>
              <option value="map_legend">
                圖例資料
              </option>
            </select>
            <label>資料單位*</label>
            <input
              v-model="currentComponent.chart_config.unit"
              type="text"
              :minlength="1"
              :maxlength="6"
              required
            >
            <label>圖表類型*（限3種，依點擊順序排列）</label>
            <SelectButtons
              :tags="
                chartsPerDataType[currentComponent.query_type]
              "
              :selected="currentComponent.chart_config.types"
              :limit="3"
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.chart_config.types =
                    updatedTags;
                }
              "
            />
            <label>圖表顏色</label>
            <InputTags
              :tags="currentComponent.chart_config.color"
              :color-data="true"
              @deletetag="
                (index) => {
                  currentComponent.chart_config.color.splice(
                    index,
                    1,
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.chart_config.color =
                    updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.chartColor"
              type="color"
              class="admincomponentsettings-settings-inputcolor"
              @focusout="
                () => {
                  if (
                    tempInputStorage.chartColor.length === 7
                  ) {
                    currentComponent.chart_config.color.push(
                      tempInputStorage.chartColor,
                    );
                    tempInputStorage.chartColor = '#000000';
                  }
                }
              "
            >
            <div v-if="currentComponent.map_config[0] !== null">
              <label>地圖篩選</label>
              <textarea v-model="currentComponent.map_filter" />
            </div>
          </div>
          <div
            v-else-if="currentSettings === 'history'"
            class="admincomponentsettings-settings-items"
          >
            <label>歷史軸時間區間
              (依點擊順序排列，資料無法預覽)</label>
            <SelectButtons
              :tags="[
                'month_ago',
                'quarter_ago',
                'halfyear_ago',
                'year_ago',
                'twoyear_ago',
                'fiveyear_ago',
                'tenyear_ago',
              ]"
              :selected="currentComponent.history_config.range"
              :limit="5"
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.history_config.range =
                    updatedTags;
                }
              "
            />
            <label>歷史軸顏色 (若無提供沿用圖表顏色)</label>
            <InputTags
              :tags="currentComponent.history_config.color"
              :color-data="true"
              @deletetag="
                (index) => {
                  currentComponent.history_config.color.splice(
                    index,
                    1,
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.history_config.color =
                    updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.historyColor"
              type="color"
              class="admincomponentsettings-settings-inputcolor"
              @focusout="
                () => {
                  if (
                    tempInputStorage.historyColor.length ===
                    7
                  ) {
                    currentComponent.history_config.color.push(
                      tempInputStorage.historyColor,
                    );
                    tempInputStorage.historyColor =
                      '#000000';
                  }
                }
              "
            >
          </div>
          <div v-else-if="currentSettings === 'map'">
            <div
              v-for="(
                map_config, index
              ) in currentComponent.map_config"
              :key="map_config.index"
              class="admincomponentsettings-settings-items"
            >
              <hr v-if="index > 0">
              <label>地圖{{ index + 1 }} ID / Index</label>
              <div class="two-block">
                <input
                  :value="
                    currentComponent.map_config[index].id
                  "
                  disabled
                >
                <input
                  v-model="
                    currentComponent.map_config[index].index
                  "
                  :maxlength="30"
                  :minlength="1"
                  required
                >
              </div>

              <label>地圖{{ index + 1 }} 名稱* ({{
                currentComponent.map_config[index].title
                  .length
              }}/10)</label>
              <input
                v-model="
                  currentComponent.map_config[index].title
                "
                type="text"
                :minlength="1"
                :maxlength="10"
                required
              >
              <label>地圖{{ index + 1 }} 類型*</label>
              <select
                v-model="
                  currentComponent.map_config[index].type
                "
              >
                <option
                  v-for="(value, key) in mapTypes"
                  :key="key"
                  :value="key"
                >
                  {{ value }}
                </option>
              </select>
              <label>地圖{{
                index + 1
              }}
                預設變形（大小/圖示）</label>
              <div class="two-block">
                <select
                  v-model="
                    currentComponent.map_config[index].size
                  "
                  :disabled="
                    currentComponent.map_config[index]
                      .type === 'symbol-3d'
                  "
                >
                  <option :value="''">
                    無
                  </option>
                  <option value="small">
                    small (點圖)
                  </option>
                  <option value="big">
                    big (點圖)
                  </option>
                  <option value="wide">
                    wide (線圖)
                  </option>
                </select>
                <select
                  v-model="
                    currentComponent.map_config[index].icon
                  "
                  :disabled="
                    currentComponent.map_config[index]
                      .type === 'symbol-3d'
                  "
                >
                  <option :value="''">
                    無
                  </option>
                  <option value="heatmap">
                    heatmap (點圖)
                  </option>
                  <option value="dash">
                    dash (線圖)
                  </option>
                  <option value="metro">
                    metro (符號圖)
                  </option>
                  <option value="metro-density">
                    metro-density (符號圖)
                  </option>
                  <option value="triangle_green">
                    triangle_green (符號圖)
                  </option>
                  <option value="triangle_white">
                    triangle_white (符號圖)
                  </option>
                  <option value="youbike">
                    youbike (符號圖)
                  </option>
                  <option value="bus">
                    bus (符號圖)
                  </option>
                  <option value="cctv">
                    cctv (符號圖)
                  </option>
                </select>
              </div>
              <label>地圖{{ index + 1 }} Paint屬性</label>
              <textarea
                v-model="
                  currentComponent.map_config[index].paint
                "
              />
              <label>地圖{{ index + 1 }} Popup標籤</label>
              <textarea
                v-model="
                  currentComponent.map_config[index].property
                "
              />
            </div>
          </div>
        </div>
        <div class="admincomponentsettings-preview">
          <DashboardComponent
            v-if="
              currentSettings === 'all' ||
                currentSettings === 'chart'
            "
            :key="`${currentComponent.index}-${currentComponent.chart_config.color}-${currentComponent.chart_config.types}`"
            :config="JSON.parse(JSON.stringify(currentComponent))"
            :active-city="currentComponent.city"
            :city-tag="
              contentStore.cityManager.getTagList(
                currentComponent.city,
              )
            "
            mode="large"
          />
          <div
            v-else-if="currentSettings === 'history'"
            :style="{ width: '300px' }"
          >
            <HistoryChart
              :key="`${currentComponent.index}-${currentComponent.history_config.color}`"
              :chart_config="currentComponent.chart_config"
              :series="currentComponent.history_data"
              :history_config="
                JSON.parse(
                  JSON.stringify(
                    currentComponent.history_config,
                  ),
                )
              "
            />
          </div>
          <div
            v-else-if="currentSettings === 'map'"
            index="componentsettings"
          >
            預覽功能 Coming Soon
          </div>
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admincomponentsettings {
	width: 750px;
	height: 500px;

	@media (max-width: 770px) {
		display: none;
	}
	@media (max-height: 520px) {
		display: none;
	}

	&-header {
		display: flex;
		justify-content: space-between;

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-ms);
		}
	}

	&-content {
		height: calc(100% - 70px);
		display: grid;
		grid-template-columns: 1fr 350px;
	}

	&-tabs {
		height: 30px;
		display: flex;
		align-items: center;
		margin-top: var(--font-s);

		button {
			width: 70px;
			height: 30px;
			border-radius: 5px 5px 0px 0px;
			background-color: var(--color-border);
			font-size: var(--font-m);
			color: var(--color-text);
			cursor: pointer;
			transition: background-color 0.2s;

			&:hover {
				background-color: var(--color-complement-text);
			}
		}
		.active {
			background-color: var(--color-complement-text);
		}
	}

	&-settings {
		padding: 0 0.5rem 0.5rem 0.5rem;
		margin-right: var(--font-ms);
		border-radius: 0px 5px 5px 5px;
		border: solid 1px var(--color-border);
		overflow-y: scroll;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		.two-block {
			display: grid;
			grid-template-columns: 1fr 1fr;
			column-gap: 0.5rem;
		}
		.three-block {
			display: grid;
			grid-template-columns: 1fr 2rem 1fr;
			column-gap: 0.5rem;
		}

		&-items {
			display: flex;
			flex-direction: column;

			hr {
				margin: var(--font-ms) 0 0.5rem;
				border: none;
				border-bottom: dashed 1px var(--color-complement-text);
			}
		}

		&-inputcolor {
			width: 140px;
			height: 40px;
			appearance: none;
			display: flex;
			justify-content: center;
			align-items: center;
			padding: 0;
			outline: none;
			cursor: pointer;

			&::-webkit-color-swatch {
				border: none;
				border-radius: 5px;
			}
			&::-moz-color-swatch {
				border: none;
			}
			&:before {
				content: "選擇顏色";
				position: absolute;
				display: block;
				border-radius: 5px;
				font-size: var(--font-ms);
				color: var(--color-complement-text);
			}
			&:focus:before {
				content: "點擊空白處確認";
				text-shadow: 0px 0px 1px black;
			}
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}

	&-preview {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		border-radius: 5px;
		border: solid 1px var(--color-border);
	}
}

.enable_ai_summary {
	margin-top: 0.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	label {
		margin: 0;
	}
}

.toggle-switch {
	position: relative;
	display: inline-block;
	width: 40px;
	height: 22px;
	flex-shrink: 0;

	input {
		opacity: 0;
		width: 0;
		height: 0;

		&:checked + .toggle-switch-slider {
			background-color: var(--color-highlight);
		}

		&:checked + .toggle-switch-slider:before {
			transform: translateX(18px);
		}

		&:focus-visible + .toggle-switch-slider {
			outline: 2px solid var(--color-highlight);
			outline-offset: 2px;
		}
	}

	&-slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: var(--color-border);
		transition: background-color 0.2s;
		border-radius: 22px;

		&:before {
			position: absolute;
			content: "";
			height: 16px;
			width: 16px;
			left: 3px;
			bottom: 3px;
			background-color: white;
			transition: transform 0.2s;
			border-radius: 50%;
		}
	}
}

.refresh_ai_summary {
	margin: 0.5rem 0;
	display: flex;
	flex-direction: column;
	gap: 0.5rem;
	button {
		width: fit-content;
		padding: 2px 6px;
		border-radius: 5px;
		background-color: var(--color-highlight);

		&:disabled {
			background-color: var(--color-border);
			color: var(--color-complement-text);
			cursor: not-allowed;
			opacity: 0.6;
		}
	}
	.ai_summary-btns {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.ai_summary-setting {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		background-color: transparent;
		&:hover {
			color: var(--color-border);
		}
	}
}

.ai_summary-settings {
	margin-top: 0.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.25rem;

	label {
		margin: 0;
	}

	textarea {
	overflow-y: auto;

	&::-webkit-scrollbar {
		width: 4px;
	}
	&::-webkit-scrollbar-thumb {
		background-color: rgba(136, 135, 135, 0.5);
		border-radius: 4px;
	}
	&::-webkit-scrollbar-thumb:hover {
		background-color: rgba(136, 135, 135, 1);
	}
}
}

.ai_summary_preview {
	margin-top: 0.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.25rem;

	label {
		margin: 0;
	}

	&-content {
		max-height: 120px;
		overflow-y: auto;
		padding: 0.5rem;
		border-radius: 5px;
		background-color: var(--color-border);
		font-size: var(--font-ms);
		color: darken(white, 30%);
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
	}
}
</style>
