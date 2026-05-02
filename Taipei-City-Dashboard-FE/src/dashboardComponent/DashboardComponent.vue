<script setup>
import { computed, nextTick, ref, watch } from "vue";
// import "./styles/chartStyles.css";
// import "./styles/toggleswitch.css";
import "material-icons/iconfont/material-icons.css";
import { getComponentDataTimeframe } from "./utilities/dataTimeframe";
import { timeTerms } from "./utilities/AllTimes";
import { chartTypes } from "./utilities/chartTypes";
import { useAuthStore } from "../store/authStore";

import ComponentTag from "./components/ComponentTag.vue";
import TagTooltip from "./components/TagTooltip.vue";
import DistrictChart from "./components/DistrictChart.vue";
import DonutChart from "./components/DonutChart.vue";
import BarChart from "./components/BarChart.vue";
import TreemapChart from "./components/TreemapChart.vue";
import ColumnChart from "./components/ColumnChart.vue";
import BarPercentChart from "./components/BarPercentChart.vue";
import GuageChart from "./components/GuageChart.vue";
import RadarChart from "./components/RadarChart.vue";
import TimelineSeparateChart from "./components/TimelineSeparateChart.vue";
import TimelineStackedChart from "./components/TimelineStackedChart.vue";
import MapLegend from "./components/MapLegend.vue";
import MetroChart from "./components/MetroChart.vue";
import HeatmapChart from "./components/HeatmapChart.vue";
import PolarAreaChart from "./components/PolarAreaChart.vue";
import ColumnLineChart from "./components/ColumnLineChart.vue";
import BarChartWithGoal from "./components/BarChartWithGoal.vue";
import IconPercentChart from "./components/IconPercentChart.vue";
import IndicatorChart from "./components/IndicatorChart.vue";
import TextUnitChart from "./components/TextUnitChart.vue";

import MapLegendSvg from "./assets/chart/MapLegend.svg";
import DistrictChartSvg from "./assets/chart/DistrictChart.svg";
import TimelineStackedChartSvg from "./assets/chart/TimelineStackedChart.svg";
import BarChartSvg from "./assets/chart/BarChart.svg";
import BarPercentChartSvg from "./assets/chart/BarPercentChart.svg";
import ColumnChartSvg from "./assets/chart/ColumnChart.svg";
import ColumnLineChartSvg from "./assets/chart/ColumnLineChart.svg";
import DonutChartSvg from "./assets/chart/DonutChart.svg";
import GuageChartSvg from "./assets/chart/GuageChart.svg";
import HeatmapChartSvg from "./assets/chart/HeatmapChart.svg";
import IconPercentChartSvg from "./assets/chart/IconPercentChart.svg";
import MetroChartSvg from "./assets/chart/MetroChart.svg";
import PolarAreaChartSvg from "./assets/chart/PolarAreaChart.svg";
import RadarChartSvg from "./assets/chart/RadarChart.svg";
import TimelineSeparateChartSvg from "./assets/chart/TimelineSeparateChart.svg";
import BarChartWithGoalSvg from "./assets/chart/BarChartWithGoal.svg";
import TreemapChartSvg from "./assets/chart/TreemapChart.svg";
import IndicatorChartSvg from "./assets/chart/IndicatorChart.svg";
import TextUnitChartSvg from "./assets/chart/TextUnitChart.svg";


const AI_COMMENT_DEFAULT = "AI 圖表評論待生成";
const AI_COMMENT_LOADING = "AI 圖表評論生成中...";
const AI_COMMENT_ERROR = "AI 評論暫時無法生成";
const CHART_CHAT_CONTEXT_LIMIT = 7000;
const CHART_CHAT_HISTORY_LIMIT = 3;
const CHART_CHAT_DEFAULT_ANSWER = "AI 未回傳內容";
const CHART_CHAT_ERROR = "AI 問答暫時無法回應";

const props = defineProps({
	style: { type: Object, default: () => ({}) },
	mode: {
		type: String,
		default: "default",
		validator: (value) =>
			["default", "large", "map", "half", "halfmap", "preview"].includes(
				value
			),
	},
	config: { type: Object, required: true },
	selectBtn: { type: Boolean, default: false },
	selectBtnDisabled: { type: Boolean, default: false },
	selectBtnList: { type: Array, default: () => ([])  },
	cityTag: { type: Array, default: () => ([]) },
	favoriteBtn: { type: Boolean, default: false },
	isFavorite: { type: Boolean, default: false },
	deleteBtn: { type: Boolean, default: false },
	addBtn: { type: Boolean, default: false },
	infoBtn: { type: Boolean, default: false },
	infoBtnText: { type: String, default: "組件資訊" },
	toggleDisable: { type: Boolean, default: false },
	footer: { type: Boolean, default: true },
	activeCity: { type: String, default: '' },
	toggleOn: { type: Boolean, default: false },
});

const emits = defineEmits([
	"favorite",
	"delete",
	"add",
	"info",
	"toggle",
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"fly",
	"changeCity",
	"refreshAiComment"
]);

const activeChart = ref(props.config.chart_config.types[0]);
const authStore = useAuthStore();
const activeCity = computed({
	get: () => props.activeCity,
	set: (value) => {
		if (toggleOn.value === false) {
			toggleOn.value = true;
		}
		emits("changeCity", value);
	},
});

const toggleOn = computed({
	get: () => props.toggleOn,
	set: (value) => {
		emits("toggle", value, props.config.map_config);
	},
});

const mousePosition = ref({ x: null, y: null });
const showTagTooltip = ref(false);
const chartChatQuestion = ref("");
const chartChatMessages = ref([]);
const chartChatStatus = ref("idle");
const chartChatSession = ref("");
const chartChatRoom = ref(null);

// Parses time data into display format
const dataTime = computed(() => {
	if (props.config.time_from === "static") {
		return "固定資料";
	} else if (props.config.time_from === "current") {
		return "即時資料";
	} else if (props.config.time_from === "demo") {
		return "示範靜態資料";
	} else if (props.config.time_from === "maintain") {
		return "維護修復中";
	}
	const { timefrom, timeto } = getComponentDataTimeframe(
		props.config.time_from,
		props.config.time_to,
		true
	);
	if (props.config.time_from === "day_start") {
		return `${timefrom.slice(0, 16)} ~ ${timeto.slice(11, 14)}00`;
	}
	return `${timefrom.slice(0, 10)} ~ ${timeto.slice(0, 10)}`;
});
// Parses update frequency data into display format
const updateFreq = computed(() => {
	if (props.config.update_freq && props.config.update_freq_unit) {
		return `每${props.config.update_freq}${
			timeTerms[props.config.update_freq_unit]
		}更新`;
	} else {
		return "不定期更新";
	}
});

// The style for the tag tooltip
const tooltipPosition = computed(() => {
	if (!mousePosition.value.x || !mousePosition.value.y) {
		return {
			left: "-1000px",
			top: "-1000px",
		};
	}
	return {
		left: `${mousePosition.value.x - 40}px`,
		top: `${mousePosition.value.y - 110}px`,
	};
});

const aiCommentStatus = computed(() => {
	if (props.config.ai_comment_status) {
		return props.config.ai_comment_status;
	}
	return props.config.ai_comment ? "success" : "idle";
});

const aiComment = computed(() => {
	if (aiCommentStatus.value === "loading") {
		return AI_COMMENT_LOADING;
	}
	if (aiCommentStatus.value === "error") {
		return props.config.ai_comment || AI_COMMENT_ERROR;
	}
	return props.config.ai_comment || AI_COMMENT_DEFAULT;
});

const aiCommentStatusLabel = computed(() => {
	if (aiCommentStatus.value === "loading") {
		return "生成中";
	}
	if (aiCommentStatus.value === "error") {
		return "需重試";
	}
	if (aiCommentStatus.value === "success") {
		return "已生成";
	}
	return "待生成";
});

const hasChartChatData = computed(() => {
	if (Array.isArray(props.config.chart_data)) {
		return props.config.chart_data.length > 0;
	}
	return (
		props.config.chart_data &&
		typeof props.config.chart_data === "object" &&
		Object.keys(props.config.chart_data).length > 0
	);
});

const chartChatInputDisabled = computed(
	() =>
		chartChatStatus.value === "loading" ||
		!authStore.token ||
		!hasChartChatData.value,
);

const chartChatSendDisabled = computed(
	() => chartChatInputDisabled.value || chartChatQuestion.value.trim() === "",
);

const chartChatEmptyText = computed(() => {
	if (!authStore.token) {
		return "登入後可提問";
	}
	if (!hasChartChatData.value) {
		return "目前沒有可分析資料";
	}
	return "等待提問";
});

const chartChatPlaceholder = computed(() =>
	chartChatInputDisabled.value ? chartChatEmptyText.value : "輸入圖表問題",
);

watch(
	() => [
		props.config.id,
		props.config.index,
		props.config.city,
		props.config.chart_data,
	],
	() => {
		chartChatQuestion.value = "";
		chartChatMessages.value = [];
		chartChatStatus.value = "idle";
		chartChatSession.value = "";
	},
);

function changeActiveChart(chartName) {
	if (
		props.mode === "map" &&
		props.config.map_config &&
		props.config.map_config[0] &&
		props.config.map_filter
	) {
		if (props.config.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.config.map_config);
		} else if (props.config.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.config.map_config);
		}
	}
	activeChart.value = chartName;
}
// Updates the location for the tag tooltip
function updateMouseLocation(e) {
	mousePosition.value.x = e.pageX;
	mousePosition.value.y = e.pageY;
}
// Updates whether to show the tag tooltip
function changeShowTagTooltipState(state) {
	showTagTooltip.value = state;
}
function retryAIComment() {
	emits("refreshAiComment", props.config);
}
function getAIChatEndpoint() {
	const apiUrl = import.meta.env.VITE_API_URL || "";
	return `${apiUrl.replace(/\/$/, "")}/ai/chat/twai`;
}
function getChartChatSession() {
	if (!chartChatSession.value) {
		const identity = props.config.id || props.config.index || "component";
		chartChatSession.value = `dashboard-chart-${identity}-${Math.random()
			.toString(36)
			.slice(2, 10)}`;
	}
	return chartChatSession.value;
}
function truncateChartChatContext(value) {
	const runes = Array.from(value);
	if (runes.length <= CHART_CHAT_CONTEXT_LIMIT) {
		return value;
	}
	return `${runes.slice(0, CHART_CHAT_CONTEXT_LIMIT).join("")}\n...（資料已截斷）`;
}
function stringifyChartChatPayload(payload) {
	try {
		return truncateChartChatContext(JSON.stringify(payload, null, 2));
	} catch (error) {
		console.error("Failed to build chart chat context:", error);
		return "{}";
	}
}
function buildChartChatContext() {
	return stringifyChartChatPayload({
		component: {
			id: props.config.id,
			index: props.config.index,
			city: props.config.city,
			name: props.config.name,
			source: props.config.source,
			time_from: props.config.time_from,
			time_to: props.config.time_to,
			display_time: dataTime.value,
			update_freq: props.config.update_freq,
			update_freq_unit: props.config.update_freq_unit,
			description: props.config.short_desc || props.config.long_desc,
		},
		active_chart: activeChart.value,
		chart_config: props.config.chart_config,
		chart_data: props.config.chart_data,
		ai_comment: aiComment.value,
	});
}
function buildChartChatMessages(question) {
	const historyMessages = chartChatMessages.value
		.slice(-CHART_CHAT_HISTORY_LIMIT)
		.flatMap((message) => [
			{
				role: "user",
				content: message.question,
			},
			{
				role: "assistant",
				content: message.answer,
			},
		]);

	return [
		{
			role: "system",
			content:
				"你是臺北城市儀表板的圖表問答助理。請只根據提供的圖表上下文回答，使用繁體中文，回答要精簡、具體；若資料不足，請明確說明不能判斷，不要編造數字。",
		},
		{
			role: "user",
			content: `以下是目前圖表上下文，後續問題都要以此為依據：\n${buildChartChatContext()}`,
		},
		...historyMessages,
		{
			role: "user",
			content: question,
		},
	];
}
async function scrollChartChatToBottom() {
	await nextTick();
	const room = chartChatRoom.value;
	if (!room) {
		return;
	}
	room.scrollTo({
		top: room.scrollHeight,
		behavior: "smooth",
	});
}
async function submitChartQuestion() {
	const question = chartChatQuestion.value.trim();
	if (chartChatSendDisabled.value || !question) {
		return;
	}

	const pendingMessage = {
		id: `${Date.now()}-${chartChatMessages.value.length}`,
		question,
		answer: "回答生成中...",
		status: "loading",
	};

	chartChatQuestion.value = "";
	chartChatStatus.value = "loading";
	chartChatMessages.value.push(pendingMessage);
	scrollChartChatToBottom();

	try {
		const response = await fetch(getAIChatEndpoint(), {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${authStore.token}`,
			},
			body: JSON.stringify({
				session: getChartChatSession(),
				stream: false,
				max_new_tokens: 420,
				temperature: 0.2,
				top_p: 0.9,
				messages: buildChartChatMessages(question),
			}),
		});
		const payload = await response.json().catch(() => ({}));
		if (!response.ok) {
			throw new Error(payload?.message || `HTTP ${response.status}`);
		}
		const answer = payload?.data?.content || CHART_CHAT_DEFAULT_ANSWER;
		pendingMessage.answer = answer;
		pendingMessage.status = "success";
		chartChatSession.value = payload?.data?.session || chartChatSession.value;
		chartChatStatus.value = "success";
		scrollChartChatToBottom();
	} catch (error) {
		console.error(
			`Failed to ask AI chart question for component ${props.config.id}:`,
			error,
		);
		pendingMessage.answer = CHART_CHAT_ERROR;
		pendingMessage.status = "error";
		chartChatStatus.value = "error";
		scrollChartChatToBottom();
	}
}
function returnChartComponent(name, svg) {
	switch (name) {
	case "DistrictChart":
		return svg ? DistrictChartSvg : DistrictChart;
	case "BarChart":
		return svg ? BarChartSvg : BarChart;
	case "MapLegend":
		return svg ? MapLegendSvg : MapLegend;
	case "MetroChart":
		return svg ? MetroChartSvg : MetroChart;
	case "TimelineSeparateChart":
		return svg ? TimelineSeparateChartSvg : TimelineSeparateChart;
	case "TimelineStackedChart":
		return svg ? TimelineStackedChartSvg : TimelineStackedChart;
	case "PolarAreaChart":
		return svg ? PolarAreaChartSvg : PolarAreaChart;
	case "IconPercentChart":
		return svg ? IconPercentChartSvg : IconPercentChart;
	case "ColumnChart":
		return svg ? ColumnChartSvg : ColumnChart;
	case "DonutChart":
		return svg ? DonutChartSvg : DonutChart;
	case "TreemapChart":
		return svg ? TreemapChartSvg : TreemapChart;
	case "BarPercentChart":
		return svg ? BarPercentChartSvg : BarPercentChart;
	case "GuageChart":
		return svg ? GuageChartSvg : GuageChart;
	case "RadarChart":
		return svg ? RadarChartSvg : RadarChart;
	case "HeatmapChart":
		return svg ? HeatmapChartSvg : HeatmapChart;
	case "ColumnLineChart":
		return svg ? ColumnLineChartSvg : ColumnLineChart;
	case "BarChartWithGoal":
		return svg ? BarChartWithGoalSvg : BarChartWithGoal;
	case "IndicatorChart":
		return svg ? IndicatorChartSvg : IndicatorChart;
	case "TextUnitChart":
		return svg ? TextUnitChartSvg : TextUnitChart;
	default:
		return svg ? MapLegendSvg : MapLegend;
	}
}
</script>

<template>
  <div
    :class="[
      {
        dashboardcomponent: true,
        mapclosed: mode.includes('map') && !toggleOn,
        mapopen: mode === 'map' && toggleOn,
        halfmapopen: mode === 'halfmap' && toggleOn,
        half: mode === 'half',
        large: mode === 'large',
        preview: mode === 'preview',
      },
    ]"
    :style="style"
  >
    <!-- Header -->
    <div class="dashboardcomponent-header">
      <!-- Upper Left Corner -->
      <div>
        <h3>
          {{ config.name }}
          <ComponentTag
            v-if="!mode.includes('map')"
            icon=""
            :text="updateFreq"
            mode="small"
          />
          <div
            v-else
            @mouseenter="changeShowTagTooltipState(true)"
            @mousemove="updateMouseLocation"
            @mouseleave="changeShowTagTooltipState(false)"
          >
            <span v-if="config.map_filter && config.map_config">tune</span>
            <span v-if="config.map_config && config.map_config[0]">map</span>
            <span v-if="config.history_config?.range">insights</span>
          </div>
        </h3>
        <p v-if="mode === 'preview'">
          {{ props.config.short_desc }}
        </p>
        <div v-if="!mode.includes('map') || toggleOn">
          <h4 v-if="dataTime === '維護修復中'">
            {{ `${config.source} | ` }}<span>warning</span>
            <h4>{{ `${dataTime}` }}</h4>
            <span>warning</span>
          </h4>
          <h4 v-else>
            {{ `${config.source} | ${dataTime}` }}
          </h4>
          <div
            v-if="mode !== 'preview'"
            class="city-tag-container"
          >
            <ComponentTag
              v-for=" city in props.cityTag"
              :key="city"
              :icon="''"
              :text="city.name"
              :mode="'small'"
              :class="`city-tag-item ${city.value}`"
            />
          </div>
        </div>
      </div>
      <!-- Upper Right Corner -->
      <div
        v-if="['default', 'half', 'preview'].includes(mode)"
        class="dashboardcomponent-header-button"
      >
        <button
          v-if="addBtn"
          @click="$emit('add', config.id, config.name)"
        >
          <span>add_circle</span>
        </button>
        <button
          v-if="favoriteBtn"
          :class="{
            isfavorite: isFavorite,
          }"
          @click="$emit('favorite', config.id)"
        >
          <span>favorite</span>
        </button>
        <button
          v-if="deleteBtn"
          class="isDelete"
          @click="$emit('delete', config.id)"
        >
          <span>delete</span>
        </button>
      </div>
      <div
        v-else-if="mode.includes('map')"
        class="dashboardcomponent-header-toggle"
      >
        <label class="toggleswitch">
          <input
            v-model="toggleOn"
            type="checkbox"
            :disabled="toggleDisable"
          >
          <span class="toggleswitch-slider" />
        </label>
      </div>
    </div>
    <!-- Control Buttons -->
    <div
      v-if="
        (!mode.includes('map') || toggleOn) &&
          mode !== 'preview'
      "
      class="dashboardcomponent-control"
    >
      <select
        v-if="selectBtn && !selectBtnDisabled"
        v-model="activeCity"
        name="city"
        class="selectBtn"
        :class="{'selectBtn-disabled': selectBtnDisabled}"
      >
        <template
          v-for="city in props.selectBtnList"
          :key="city.value"
        >
          <option :value="city.value">
            {{ city.name }}
          </option>
        </template>
      </select>
      <div
        v-if="config.chart_config.types.length > 1"
        class="dashboardcomponent-control-group"
      >
        <button
          v-for="item in config.chart_config.types"
          :key="`${config.index}-${item}-button`"
          :class="{
            'dashboardcomponent-control-group-button': true,
            'dashboardcomponent-control-group-active': activeChart === item,
          }"
          @click="changeActiveChart(item)"
        >
          {{ chartTypes[item] }}
        </button>
      </div>
    </div>
    <!-- Main Content -->
    <div
      v-if="mode === 'preview'"
      class="preview-content"
    >
      <div
        class="preview-content-id"
      >
        <div
          v-if="mode === 'preview'"
          class="city-tag-container-preview"
        >
          <ComponentTag
            v-for="city in props.cityTag"
            :key="city.value"
            :icon="''"
            :text="city.name"
            :mode="'small'"
            :class="`city-tag-item ${city.value}`"
          />
        </div>
        <p :title="props.config.index">
          Index: {{ props.config.index }}
        </p>
      </div>
      <div class="preview-content-charts">
        <img
          v-for="chart in props.config.chart_config.types"
          :key="`${props.config.index} - ${chart}`"
          :src="returnChartComponent(chart, true).toString()"
        >
      </div>
    </div>
    <div
      v-else-if="config.chart_data && (toggleOn || !mode.includes('map'))"
      :class="{
        'dashboardcomponent-chart': true,
        'half-chart': mode === 'half',
        'mapopen-chart': mode === 'map',
        'halfmapopen-chart': mode === 'halfmap',
      }"
    >
      <component
        :is="returnChartComponent(item)"
        v-for="item in config.chart_config.types"
        :key="`${props.config.index}-${item}-chart-${item.city}`"
        :active-chart="activeChart"
        :active-city="activeCity"
        :chart_config="config.chart_config"
        :series="config.chart_data"
        :map_config="config.map_config"
        :map_filter="config.map_filter"
        :map_filter_on="mode.includes('map')"
        @filter-by-param="
          (map_filter, map_config, x, y) =>
            $emit('filterByParam', map_filter, map_config, x, y)
        "
        @filter-by-layer="
          (map_config, x) => $emit('filterByLayer', map_config, x)
        "
        @clear-by-param-filter="
          (map_config) => $emit('clearByParamFilter', map_config)
        "
        @clear-by-layer-filter="
          (map_config) => $emit('clearByLayerFilter', map_config)
        "
        @fly="(location) => $emit('fly', location)"
      />
    </div>
    <div
      v-else-if="
        config.chart_data === null &&
          (toggleOn || !mode.includes('map'))
      "
      :class="{
        'dashboardcomponent-error': true,
        'half-loading': mode === 'half',
        'mapopen-loading': mode.includes('map'),
      }"
    >
      <span>error</span>
      <p>組件資料異常</p>
    </div>
    <div
      v-else-if="toggleOn || !mode.includes('map')"
      :class="{
        'dashboardcomponent-loading': true,
        'mapopen-loading': mode.includes('map'),
        'half-loading': mode === 'half',
      }"
    >
      <div />
    </div>
    <section
      v-if="mode !== 'preview' && (!mode.includes('map') || toggleOn)"
      :class="[
        'dashboardcomponent-ai-section',
        `dashboardcomponent-ai-section-comment-${aiCommentStatus}`,
        `dashboardcomponent-ai-section-chat-${chartChatStatus}`,
      ]"
    >
      <div
        ref="chartChatRoom"
        class="dashboardcomponent-ai-room"
      >
        <div
          :class="[
            'dashboardcomponent-ai-message',
            'dashboardcomponent-ai-message-ai',
            `dashboardcomponent-ai-message-${aiCommentStatus}`,
          ]"
        >
          <div class="dashboardcomponent-ai-bubble">
            <div class="dashboardcomponent-ai-bubble-heading">
              <strong>AI 圖表評論</strong>
              <span>{{ aiCommentStatusLabel }}</span>
            </div>
            <p :title="aiComment">
              {{ aiComment }}
            </p>
          </div>
          <button
            v-if="aiCommentStatus === 'error'"
            type="button"
            class="dashboardcomponent-ai-message-action"
            title="重新生成"
            @click="retryAIComment"
          >
            <span>refresh</span>
          </button>
        </div>
        <template v-if="chartChatMessages.length > 0">
          <template
            v-for="message in chartChatMessages"
            :key="message.id"
          >
            <div class="dashboardcomponent-ai-message dashboardcomponent-ai-message-user">
              <div class="dashboardcomponent-ai-bubble">
                <p>{{ message.question }}</p>
              </div>
            </div>
            <div
              :class="[
                'dashboardcomponent-ai-message',
                'dashboardcomponent-ai-message-ai',
                `dashboardcomponent-ai-message-${message.status}`,
              ]"
            >
              <div class="dashboardcomponent-ai-bubble">
                <p>{{ message.answer }}</p>
              </div>
            </div>
          </template>
        </template>
      </div>
      <form
        class="dashboardcomponent-chart-chat-form dashboardcomponent-ai-room-form"
        @submit.prevent="submitChartQuestion"
      >
        <input
          v-model="chartChatQuestion"
          type="text"
          maxlength="160"
          :placeholder="chartChatPlaceholder"
          :disabled="chartChatInputDisabled"
        >
        <button
          type="submit"
          title="送出問題"
          :disabled="chartChatSendDisabled"
        >
          <span>{{ chartChatStatus === 'loading' ? 'hourglass_top' : 'send' }}</span>
        </button>
      </form>
    </section>
    <!-- Footer -->
    <div
      v-if="footer && (!mode.includes('map') || toggleOn)"
      class="dashboardcomponent-footer"
    >
      <div
        v-if="!mode.includes('map')"
        @mouseenter="changeShowTagTooltipState(true)"
        @mousemove="updateMouseLocation"
        @mouseleave="changeShowTagTooltipState(false)"
      >
        <ComponentTag
          v-if="config.map_filter && config.map_config?.length > 0"
          :icon="mode === 'preview' ? '' : 'tune'"
          text="篩選地圖"
          class="hide-if-mobile"
        />
        <ComponentTag
          v-if="config.map_config && config.map_config[0] !== null && config.map_config?.length > 0"
          :icon="mode === 'preview' ? '' : 'map'"
          text="空間資料"
          class="hide-if-mobile"
        />
        <ComponentTag
          v-if="config.history_config?.range"
          :icon="mode === 'preview' ? '' : 'insights'"
          text="歷史資料"
          class="history-tag"
        />
      </div>
      <div v-else />
      <button
        v-if="infoBtn"
        @click="$emit('info', config)"
      >
        <p>{{ infoBtnText }}</p>
        <span>arrow_circle_right</span>
      </button>
    </div>
    <div
      v-else-if="!mode.includes('map')"
      class="dashboardcomponent-footer"
    />
  </div>
  <Teleport to="body">
    <!-- The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css -->
    <TagTooltip
      v-if="showTagTooltip"
      :position="tooltipPosition"
      :has-filter="config.map_filter ? true : false"
      :has-map-layer="
        config.map_config && config.map_config[0] ? true : false
      "
      :has-history="config.history_config?.range ? true : false"
    />
  </Teleport>
</template>

<style scoped lang="scss">
* {
	box-sizing: border-box;
	margin: 0;
	padding: 0;
	font-family: "微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans",
		"Helvetica";
	overflow: hidden;
}

button {
	border: none;
	background-color: transparent;
}

button:hover {
	cursor: pointer;
}

::-webkit-scrollbar {
	width: 0px;
}

.dashboardcomponent {
	height: 560px;
	max-height: 560px;
	width: calc(100% - var(--font-m) * 2);
	max-width: calc(100% - var(--font-m) * 2);
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	position: relative;
	padding: var(--font-m);
	border-radius: 5px;
	background-color: var(--color-component-background);

	@media (min-width: 1050px) {
		height: 570px;
		max-height: 570px;
	}

	@media (min-width: 1650px) {
		height: 590px;
		max-height: 590px;
	}

	@media (min-width: 2200px) {
		height: 700px;
		max-height: 700px;
	}

	&-header {
		display: flex;
		justify-content: space-between;
		overflow: visible;

		h3 {
			display: flex;
			font-size: var(--font-m);
			color: var(--color-normal-text);

			.componenttag {
				flex-shrink: 0;
				margin-top: 4px;
			}
		}

		h4 {
			display: flex;
			align-items: center;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			font-weight: 400;
			overflow: visible;

			span {
				margin-left: 4px !important;
				margin: 0 4px;
				color: rgb(237, 90, 90) !important;
				font-size: 1rem;
				font-family: var(--font-icon);
				user-select: none;
			}

			h4 {
				color: rgb(237, 90, 90);
			}
		}

		p {
			color: var(--color-normal-text);
			font-size: var(--font-s);
			font-weight: 400;
		}

		div:first-child {
			div {
				display: flex;
				align-items: center;
			}

			span {
				margin-left: 8px;
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				user-select: none;
			}
		}
		&-button {
			min-width: 48px;
			display: flex;
			justify-content: flex-end;
			align-items: flex-start;

			button span {
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				font-size: calc(
					var(--font-l) *
						var(--font-to-icon)
				);
				transition: color 0.2s;

				&:hover {
					color: white;
				}
			}

			button.isfavorite span {
				color: rgb(255, 65, 44);

				&:hover {
					color: rgb(160, 112, 106);
				}
			}
		}

		&-toggle {
			min-height: var(--font-ms);
			min-width: 2rem;
			margin-top: 4px;
		}

		@media (max-width: 760px) {
			button.isDelete {
				display: none !important;
			}
		}

		@media (min-width: 760px) {
			button.isFlag {
				display: none !important;
			}
		}

		@media (min-width: 759px) {
			button.isUnfavorite {
				display: none !important;
			}
		}
	}

	&-control {
		width: 100%;
		display: flex;
		// justify-content: center;
		align-items: center;
		// position: absolute;
		top: 4.2rem;
		left: 0;
		z-index: 8;
		padding: 4px 0;

		&-group {
			display: flex;
			justify-content: center;
			align-items: center;
			margin: 0 auto;
			transform: translateX(-15%);

			&-button {
				margin: 0 2px;
				padding: 3px 5px;
				border-radius: 5px;
				background-color: rgb(77, 77, 77);
				opacity: 0.6;
				color: var(--color-complement-text);
				font-size: var(--font-s);
				text-align: center;
				transition: color 0.2s, opacity 0.2s;
				user-select: none;
	
				&:hover {
					opacity: 1;
					color: white;
				}
			}
	
			&-active {
				background-color: var(--color-complement-text);
				color: white;
			}
		}

		.selectBtn {
			background-color: var(--color-component-background);
			padding: 3px;

			&-disabled {
				cursor: not-allowed;
			}
		}
	}

	&-chart,
	&-loading,
	&-error {
		flex: 1 1 auto;
		height: auto;
		min-height: 230px;
		position: relative;
		padding-top: 0.5%;
		overflow-y: scroll;

		p {
			color: var(--color-border);
		}
	}

	&-ai-comment {
		flex: 0 0 auto;
		height: 74px;
		min-height: 74px;
		max-height: 74px;
		display: grid;
		grid-template-columns: 28px minmax(0, 1fr) auto;
		align-items: flex-start;
		gap: 8px;
		margin-top: 6px;
		padding: 8px 10px;
		border: 1px solid rgba(255, 255, 255, 0.14);
		border-radius: 8px;
		background:
			linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(0, 0, 0, 0.18)),
			rgba(0, 0, 0, 0.16);
		box-shadow:
			inset 0 1px 0 rgba(255, 255, 255, 0.08),
			0 12px 28px rgba(0, 0, 0, 0.18);
		opacity: 1;
		overflow: hidden;

		&-icon {
			width: 28px;
			height: 28px;
			display: grid;
			place-items: center;
			border-radius: 8px;
			background:
				linear-gradient(135deg, rgba(78, 149, 255, 0.32), rgba(122, 78, 255, 0.18)),
				rgba(255, 255, 255, 0.05);
			color: var(--color-highlight);
			font-family: var(--font-icon);
			font-size: var(--font-ms);
			box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
			user-select: none;
		}

		&-content {
			min-width: 0;
			overflow: hidden;
		}

		&-heading {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 8px;
			margin-bottom: 4px;
			overflow: visible;

			strong {
				color: var(--color-normal-text);
				font-size: var(--font-s);
				font-weight: 700;
				line-height: 1.2;
			}
		}

		&-status {
			flex: 0 0 auto;
			padding: 2px 7px;
			border-radius: 999px;
			background-color: rgba(255, 255, 255, 0.08);
			color: var(--color-complement-text);
			font-size: 0.72rem;
			line-height: 1.35;
			letter-spacing: 0;
		}

		p {
			flex: 1 1 auto;
			min-width: 0;
			max-height: 34px;
			padding-right: 6px;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			line-height: 1.45;
			overflow-y: auto;
			scrollbar-width: thin;
			scrollbar-color: rgba(255, 255, 255, 0.24) transparent;
			white-space: normal;
			text-overflow: clip;
		}

		p::-webkit-scrollbar {
			width: 4px;
		}

		p::-webkit-scrollbar-thumb {
			border-radius: 999px;
			background-color: rgba(255, 255, 255, 0.24);
		}

		button {
			flex: 0 0 auto;
			width: 28px;
			height: 28px;
			display: grid;
			align-items: center;
			justify-content: center;
			border-radius: 8px;
			background-color: rgba(255, 255, 255, 0.06);
			color: var(--color-highlight);
			transition: background-color 0.2s, color 0.2s;

			&:hover {
				background-color: rgba(255, 255, 255, 0.12);
				color: white;
			}

			span {
				margin: 0;
				font-family: var(--font-icon);
				font-size: var(--font-ms);
				user-select: none;
			}
		}

		&-loading .dashboardcomponent-ai-comment-icon {
			animation: pulse 1.2s ease-in-out infinite;
		}

		&-error {
			border-color: rgba(237, 90, 90, 0.8);

			.dashboardcomponent-ai-comment-icon,
			.dashboardcomponent-ai-comment-status,
			p {
				color: rgb(237, 90, 90);
			}
		}
	}

	&-chart-chat {
		flex: 0 0 auto;
		height: 90px;
		min-height: 90px;
		max-height: 90px;
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-top: 6px;
		padding: 8px 10px;
		border: 1px solid rgba(255, 255, 255, 0.12);
		border-radius: 8px;
		background:
			linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(0, 0, 0, 0.18)),
			rgba(0, 0, 0, 0.14);
		box-shadow:
			inset 0 1px 0 rgba(255, 255, 255, 0.08),
			0 10px 24px rgba(0, 0, 0, 0.16);

		&-heading {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 8px;
			overflow: visible;

			div {
				min-width: 0;
				display: flex;
				align-items: center;
				gap: 6px;
			}

			span {
				margin: 0;
				color: var(--color-highlight);
				font-family: var(--font-icon);
				font-size: var(--font-ms);
				user-select: none;
			}

			strong {
				color: var(--color-normal-text);
				font-size: var(--font-s);
				font-weight: 700;
				line-height: 1.2;
			}
		}

		&-status {
			flex: 0 0 auto;
			padding: 2px 7px;
			border-radius: 999px;
			background-color: rgba(255, 255, 255, 0.08);
			color: var(--color-complement-text) !important;
			font-family: "微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans",
				"Helvetica" !important;
			font-size: 0.72rem !important;
			line-height: 1.35;
			letter-spacing: 0;
		}

		&-thread {
			flex: 1 1 auto;
			min-height: 20px;
			max-height: 22px;
			padding-right: 4px;
			overflow-y: auto;
			scrollbar-width: thin;
			scrollbar-color: rgba(255, 255, 255, 0.24) transparent;

			&-empty {
				display: flex;
				align-items: center;
			}

			p {
				color: var(--color-complement-text);
				font-size: var(--font-s);
				line-height: 1.35;
				white-space: normal;
			}
		}

		&-thread::-webkit-scrollbar {
			width: 4px;
		}

		&-thread::-webkit-scrollbar-thumb {
			border-radius: 999px;
			background-color: rgba(255, 255, 255, 0.24);
		}

		&-message {
			display: flex;
			flex-direction: column;
			gap: 3px;
			margin-bottom: 5px;
			overflow: visible;

			&:last-child {
				margin-bottom: 0;
			}

			strong {
				display: inline-grid;
				place-items: center;
				width: 18px;
				height: 18px;
				margin-right: 5px;
				border-radius: 5px;
				background-color: rgba(255, 255, 255, 0.08);
				color: var(--color-highlight);
				font-size: 0.7rem;
				line-height: 1;
			}

			&-loading .dashboardcomponent-chart-chat-answer {
				animation: pulse 1.2s ease-in-out infinite;
			}

			&-error .dashboardcomponent-chart-chat-answer,
			&-error strong {
				color: rgb(237, 90, 90);
			}
		}

		&-question {
			color: var(--color-normal-text) !important;
			font-weight: 700;
		}

		&-answer {
			color: var(--color-complement-text);
		}

		&-form {
			flex: 0 0 auto;
			display: grid;
			grid-template-columns: minmax(0, 1fr) 28px;
			gap: 6px;
			overflow: visible;

			input {
				min-width: 0;
				height: 28px;
				padding: 0 10px;
				border: 1px solid rgba(255, 255, 255, 0.12);
				border-radius: 8px;
				background-color: rgba(0, 0, 0, 0.16);
				color: var(--color-normal-text);
				font-size: var(--font-s);
				outline: none;
				transition: border-color 0.2s, background-color 0.2s;

				&::placeholder {
					color: var(--color-complement-text);
					opacity: 0.75;
				}

				&:focus {
					border-color: rgba(255, 255, 255, 0.28);
					background-color: rgba(20, 22, 26, 0.96);
				}

				&:disabled {
					cursor: not-allowed;
					opacity: 0.58;
				}
			}

			button {
				width: 28px;
				height: 28px;
				display: grid;
				place-items: center;
				border-radius: 8px;
				background:
					linear-gradient(135deg, rgba(78, 149, 255, 0.32), rgba(122, 78, 255, 0.18)),
					rgba(255, 255, 255, 0.05);
				color: var(--color-highlight);
				transition: background-color 0.2s, color 0.2s, opacity 0.2s;

				&:hover:not(:disabled) {
					background-color: rgba(255, 255, 255, 0.12);
					color: white;
				}

				&:disabled {
					cursor: not-allowed;
					opacity: 0.52;
				}

				span {
					margin: 0;
					font-family: var(--font-icon);
					font-size: var(--font-ms);
					user-select: none;
				}
			}
		}

		&-loading .dashboardcomponent-chart-chat-heading > div span {
			animation: pulse 1.2s ease-in-out infinite;
		}

		&-error {
			border-color: rgba(237, 90, 90, 0.58);

			.dashboardcomponent-chart-chat-status {
				color: rgb(237, 90, 90) !important;
			}
		}
	}

	&-ai-section {
		flex: 0 0 auto;
		height: 152px;
		min-height: 152px;
		max-height: 152px;
		position: relative;
		display: flex;
		flex-direction: column;
		margin-top: 6px;
		padding: 8px 10px;
		border: 1px solid rgba(255, 255, 255, 0.14);
		border-radius: 8px;
		background:
			linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(0, 0, 0, 0.18)),
			rgba(0, 0, 0, 0.16);
		box-shadow:
			inset 0 1px 0 rgba(255, 255, 255, 0.08),
			0 12px 28px rgba(0, 0, 0, 0.18);
		overflow: hidden;

		&-comment-error,
		&-chat-error {
			border-color: rgba(237, 90, 90, 0.68);
		}

		&:hover,
		&:focus-within {
			.dashboardcomponent-ai-room-form {
				opacity: 1;
				pointer-events: auto;
				transform: translateY(0);
				background:
					linear-gradient(180deg, rgba(36, 38, 40, 0), rgba(36, 38, 40, 0.94) 32%),
					transparent;
			}
		}
	}

	&-ai-room {
		flex: 1 1 auto;
		min-height: 0;
		display: flex;
		flex-direction: column;
		gap: 7px;
		padding-right: 4px;
		padding-bottom: 42px;
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(255, 255, 255, 0.24) transparent;

		&::-webkit-scrollbar {
			width: 4px;
		}

		&::-webkit-scrollbar-thumb {
			border-radius: 999px;
			background-color: rgba(255, 255, 255, 0.24);
		}

		&-form {
			position: absolute;
			right: 10px;
			bottom: 8px;
			left: 10px;
			z-index: 1;
			opacity: 0;
			pointer-events: none;
			transform: translateY(6px);
			background:
				linear-gradient(180deg, rgba(36, 38, 40, 0), rgba(36, 38, 40, 0.78) 36%),
				transparent;
			transition: opacity 0.18s ease, transform 0.18s ease;
		}
	}

	&-ai-message {
		width: 100%;
		display: flex;
		align-items: flex-start;
		gap: 7px;
		overflow: visible;

		&-ai {
			justify-content: flex-start;
		}

		&-user {
			justify-content: flex-end;

			.dashboardcomponent-ai-bubble {
				border-radius: 12px 12px 3px 12px;
				background:
					linear-gradient(135deg, rgba(78, 149, 255, 0.36), rgba(122, 78, 255, 0.22)),
					rgba(255, 255, 255, 0.08);
				color: var(--color-normal-text);
			}
		}

		&-action {
			flex: 0 0 auto;
			width: 28px;
			height: 28px;
			display: grid;
			place-items: center;
			border-radius: 8px;
			background:
				linear-gradient(135deg, rgba(78, 149, 255, 0.32), rgba(122, 78, 255, 0.18)),
				rgba(255, 255, 255, 0.05);
			color: var(--color-highlight);
			font-family: var(--font-icon);
			font-size: var(--font-ms);
			box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
			user-select: none;
		}

		&-action {
			background-color: rgba(255, 255, 255, 0.06);
			transition: background-color 0.2s, color 0.2s;

			&:hover {
				background-color: rgba(255, 255, 255, 0.12);
				color: white;
			}

			span {
				margin: 0;
				font-family: var(--font-icon);
				font-size: var(--font-ms);
			}
		}

		&-loading .dashboardcomponent-ai-bubble {
			animation: pulse 1.2s ease-in-out infinite;
		}

		&-error {
			.dashboardcomponent-ai-bubble,
			.dashboardcomponent-ai-bubble-heading span {
				color: rgb(237, 90, 90);
			}
		}
	}

	&-ai-bubble {
		min-width: 0;
		max-width: 88%;
		padding: 7px 9px;
		border-radius: 12px 12px 12px 3px;
		background-color: rgba(255, 255, 255, 0.07);
		color: var(--color-complement-text);
		overflow: visible;

		&-heading {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 8px;
			margin-bottom: 3px;
			overflow: visible;

			strong {
				color: var(--color-normal-text);
				font-size: var(--font-s);
				font-weight: 700;
				line-height: 1.2;
			}

			span {
				flex: 0 0 auto;
				padding: 1px 6px;
				border-radius: 999px;
				background-color: rgba(255, 255, 255, 0.08);
				color: var(--color-complement-text);
				font-size: 0.72rem;
				line-height: 1.35;
			}
		}

		p {
			color: inherit;
			font-size: var(--font-s);
			line-height: 1.45;
			white-space: normal;
		}
	}

	&-loading {
		display: flex;
		align-items: center;
		justify-content: center;

		div {
			width: 2rem;
			height: 2rem;
			border-radius: 50%;
			border: solid 4px var(--color-border);
			border-top: solid 4px var(--color-highlight);
			animation: spin 0.7s ease-in-out infinite;
		}
	}

	&-error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;

		span {
			color: var(--color-complement-text);
			margin-bottom: 0.5rem;
			font-family: var(--font-icon);
			font-size: 2rem;
		}

		p {
			color: var(--color-complement-text);
		}
	}

	&-footer {
		height: 26px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		overflow: visible;

		div {
			display: flex;
			align-items: center;
		}

		button,
		a {
			display: flex;
			align-items: center;
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}

			span {
				margin-left: 4px;
				color: var(--color-highlight);
				font-family: var(--font-icon);
				user-select: none;
			}

			p {
				max-height: 1.2rem;
				color: var(--color-highlight);
				user-select: none;
			}
		}
	}
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}

@keyframes pulse {
	50% {
		opacity: 0.4;
	}
}

.large {
	height: 640px;
	max-height: 640px;

	@media (min-width: 820px) {
		height: 660px;
		max-height: 660px;
	}

	@media (min-width: 1200px) {
		height: 700px;
		max-height: 700px;
	}

	@media (min-width: 2200px) {
		height: 800px;
		max-height: 800px;
	}

	.dashboardcomponent-chart,
	.dashboardcomponent-loading,
	.dashboardcomponent-error {
		min-height: 300px;
	}
}

.mapclosed {
	max-height: none;
	height: fit-content;
}

.mapopen {
	max-height: 500px;
	height: 500px;

	&-chart,
	&-loading {
		padding-top: 0%;
		height: auto;
		min-height: 210px;
		position: relative;
		overflow-y: scroll;

		p {
			color: var(--color-border);
		}
	}

	.dashboardcomponent-ai-comment {
		height: 64px;
		min-height: 64px;
		max-height: 64px;
		padding: 7px 9px;

		p {
			max-height: 28px;
		}
	}

	.dashboardcomponent-chart-chat {
		height: 78px;
		min-height: 78px;
		max-height: 78px;
		padding: 7px 9px;

		&-thread {
			max-height: 18px;
		}
	}
}

.half {
	height: 450px;
	max-height: 450px;

	@media (min-width: 1050px) {
		height: 470px;
		max-height: 470px;
	}

	@media (min-width: 1650px) {
		height: 490px;
		max-height: 490px;
	}

	@media (min-width: 2200px) {
		height: 580px;
		max-height: 580px;
	}

	&-chart,
	&-loading {
		height: auto;
		min-height: 160px;
	}

	.dashboardcomponent-ai-comment {
		height: 64px;
		min-height: 64px;
		max-height: 64px;
		padding: 7px 9px;

		p {
			max-height: 28px;
		}
	}

	.dashboardcomponent-chart-chat {
		height: 78px;
		min-height: 78px;
		max-height: 78px;
		padding: 7px 9px;

		&-thread {
			max-height: 18px;
		}
	}
}

.halfmapopen {
	height: 470px;
	max-height: 470px;

	&-chart {
		padding-top: 0;
		height: auto;
		min-height: 170px;
	}

	.dashboardcomponent-ai-comment {
		height: 64px;
		min-height: 64px;
		max-height: 64px;
		padding: 7px 9px;

		p {
			max-height: 28px;
		}
	}

	.dashboardcomponent-chart-chat {
		height: 78px;
		min-height: 78px;
		max-height: 78px;
		padding: 7px 9px;

		&-thread {
			max-height: 18px;
		}
	}
}

.preview {
	height: 170px;
	max-height: 170px;

	&-content {
		display: flex;
		justify-content: space-between;

		&-id {
			height: calc(100% - 2px);
			display: flex;
			flex-direction: column;
			justify-content: center;
			padding: 0 4px;
			border-radius: 5px;
			border: 1px dashed var(--color-complement-text);
			white-space: nowrap;
			margin-right: 4px;

			p {
				font-size: var(--font-s);
				color: var(--color-complement-text);
				text-overflow: ellipsis;
			}
		}

		&-charts {
			display: flex;
			column-gap: 4px;
			img {
				width: 40px;
				height: 40px;
				border-radius: 5px;
				background-color: var(
					--color-complement-text
				);
			}
		}
	}
}

.city {
	&-tag {
		&-container {
			margin: 4px 0;
			display: flex;
			gap: 5px;
	
			div:first-child {
				margin-left: 5px;
			}

			&-preview {
				display: flex;
				gap: 4px;
			}
		}
	}
}
</style>
