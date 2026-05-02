<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref } from "vue";
import router from "../../../router";
import { useMapStore } from "../../../store/mapStore";
import { extractNewsInsight } from "../../../api/ai";

const mapStore = useMapStore();

const RECOMMEND_SIDEBAR_EXPANDED_KEY = "isRecommendSidebarExpanded";

/** 展開寬度略大於左側 SideBar，收合 45px */
const isExpanded = ref(true);

const aiNewsUrl = ref("");
const aiInsightResult = ref(null);
const loadingAiInsight = ref(false);
const aiInsightError = ref(null);

async function handleAiInsight() {
	if (!aiNewsUrl.value) return;

	loadingAiInsight.value = true;
	aiInsightError.value = null;
	aiInsightResult.value = null;

	try {
		const result = await extractNewsInsight(aiNewsUrl.value);
		aiInsightResult.value = result;
	} catch {
		aiInsightError.value = "無法載入主題。";
	} finally {
		loadingAiInsight.value = false;
	}
}

function readExpandedFromStorage() {
	const stored = localStorage.getItem(RECOMMEND_SIDEBAR_EXPANDED_KEY);
	if (stored === "false") {
		isExpanded.value = false;
	} else {
		isExpanded.value = true;
	}
}

function toggleExpand() {
	isExpanded.value = !isExpanded.value;
	localStorage.setItem(
		RECOMMEND_SIDEBAR_EXPANDED_KEY,
		String(isExpanded.value)
	);
	mapStore.resizeMap();
}

onMounted(() => {
	readExpandedFromStorage();
});

/**
 * 前往組件詳情頁（與 DashboardView 手機版「組件資訊」行為一致）
 */
function openStorylineRecommendedComponent(comp) {
	const idx = comp?.index;
	if (idx === undefined || idx === null || idx === "") {
		return;
	}
	const payload = {
		name: "component-info",
		params: { index: String(idx) },
	};
	if (comp.city) {
		payload.query = { city: comp.city };
	}
	router.push(payload);
}
</script>

<template>
  <div
    :class="{
      recommendsidebar: true,
      'recommendsidebar-collapse': !isExpanded,
      'hide-if-mobile': true,
    }"
  >
    <div
      class="recommendsidebar-top"
      :class="{ 'recommendsidebar-top--collapsed': !isExpanded }"
    >
      <button
        type="button"
        class="recommendsidebar-toggle"
        :title="isExpanded ? '收合今日推薦' : '展開今日推薦'"
        @click="toggleExpand"
      >
        <span>{{
          isExpanded
            ? "keyboard_double_arrow_right"
            : "keyboard_double_arrow_left"
        }}</span>
      </button>
      <template v-if="isExpanded">
        <div class="recommendsidebar-headertext">
          <h1 class="recommendsidebar-title">
            今日推薦
          </h1>
          <p class="recommendsidebar-lead">
            貼上新聞網址取得洞察與推薦主題。
          </p>
        </div>
      </template>
      <span
        v-else
        class="recommendsidebar-collapsed-label-text"
        aria-hidden="true"
      >今日推薦</span>
    </div>

    <template v-if="isExpanded">
      <div class="recommendsidebar-ai-section">
        <div class="recommendsidebar-ai-input-group">
          <input
            v-model="aiNewsUrl"
            type="text"
            placeholder="貼上新聞網址擷取洞察..."
            class="recommendsidebar-ai-input"
            @keyup.enter="handleAiInsight"
          >
          <button
            type="button"
            class="recommendsidebar-ai-btn"
            :disabled="loadingAiInsight || !aiNewsUrl"
            @click="handleAiInsight"
          >
            <span v-if="!loadingAiInsight">auto_awesome</span>
            <span
              v-else
              class="is-spinning"
            >sync</span>
          </button>
        </div>
        <p
          v-if="aiInsightError"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ aiInsightError }}
        </p>
      </div>

      <div
        v-if="aiInsightResult"
        class="recommendsidebar-ai-result"
      >
        <h2 class="recommendsidebar-subtitle recommendsidebar-subtitle--ai">
          AI 數據洞察
        </h2>
        <div class="recommendsidebar-storyline">
          {{ aiInsightResult.storyline }}
        </div>

        <h2 class="recommendsidebar-subtitle">
          推薦主題
        </h2>
        <ul
          v-if="aiInsightResult.components?.length"
          class="recommendsidebar-topiclist"
        >
          <li
            v-for="comp in aiInsightResult.components"
            :key="`${comp.id}-${comp.city ?? ''}`"
          >
            <button
              type="button"
              class="recommendsidebar-topic recommendsidebar-topic--ai"
              @click="openStorylineRecommendedComponent(comp)"
            >
              <span class="recommendsidebar-topic-title">{{ comp.name }}</span>
              <span class="recommendsidebar-topic-summary">{{ comp.short_desc }}</span>
            </button>
          </li>
        </ul>
        <p
          v-else
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          無法載入主題。
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.recommendsidebar {
	width: 240px;
	min-width: 240px;
	height: calc(100vh - 80px);
	height: calc(var(--vh) * 100 - 80px);
	max-height: calc(100vh - 80px);
	max-height: calc(var(--vh) * 100 - 80px);
	position: relative;
	padding: 0 var(--font-m) 0 10px;
	margin-top: 20px;
	border-left: 1px solid var(--color-border);
	transition: min-width 0.2s ease-out, width 0.2s ease-out;
	overflow-x: visible;
	overflow-y: auto;
	user-select: none;
	flex-shrink: 0;

	&-top {
		display: flex;
		flex-direction: row;
		align-items: flex-start;
		gap: 8px;
		margin-bottom: 10px;
		flex-shrink: 0;
		min-width: 0;

		&--collapsed {
			flex-direction: column;
			align-items: center;
			gap: 12px;
			margin-bottom: 0;
			padding-bottom: 4px;
		}
	}

	&-toggle {
		flex-shrink: 0;
		margin-top: 0;
		padding: 5px;
		border-radius: 5px;
		background-color: var(--color-background);
		transition: background-color 0.2s;

		&:hover {
			background-color: var(--color-component-background);
		}

		span {
			font-family: var(--font-icon);
			font-size: var(--font-l);
		}
	}

	&-headertext {
		flex: 1;
		min-width: 0;
	}

	&-ai-section {
		margin-bottom: 16px;
	}

	&-ai-input-group {
		display: flex;
		gap: 4px;
		background: var(--color-component-background);
		padding: 4px;
		border-radius: 6px;
		border: 1px solid var(--color-border);

		&:focus-within {
			border-color: var(--color-highlight);
		}
	}

	&-ai-input {
		flex: 1;
		border: none;
		background: transparent;
		color: var(--color-normal-text);
		font-size: var(--font-s);
		padding: 4px 8px;
		outline: none;
		min-width: 0;

		&::placeholder {
			color: var(--color-complement-text);
		}
	}

	&-ai-btn {
		background: var(--color-highlight);
		color: #fff;
		border-radius: 4px;
		padding: 4px 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: opacity 0.2s;

		&:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}

		span {
			font-family: var(--font-icon);
			font-size: var(--font-m);
		}

		.is-spinning {
			animation: spin 1s linear infinite;
		}
	}

	&-ai-result {
		margin-bottom: 20px;
		padding-bottom: 16px;
		border-bottom: 1px dashed var(--color-border);
	}

	&-storyline {
		font-size: var(--font-m);
		line-height: 1.6;
		color: var(--color-normal-text);
		background: var(--color-menu-dropdown);
		padding: 12px;
		border-radius: 8px;
		margin-bottom: 12px;
		white-space: pre-wrap;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	&-title {
		cursor: default;
		margin: 0 0 6px;
		font-size: var(--font-l);
		font-weight: 400;
	}

	&-lead {
		margin: 0;
		font-size: var(--font-m);
		color: var(--color-complement-text);
		font-weight: 400;
		line-height: 1.4;
	}

	&-collapsed-label-text {
		display: block;
		writing-mode: vertical-rl;
		text-orientation: mixed;
		font-size: var(--font-m);
		font-weight: 400;
		color: var(--color-complement-text);
		letter-spacing: 0.12em;
		user-select: none;
		padding-top: 2px;
	}

	&-subtitle {
		color: var(--color-complement-text);
		font-weight: 400;
		font-size: var(--font-m);
		margin: 10px 0 6px;
		text-wrap: nowrap;

		&--ai {
			margin-top: 0;
		}
	}

	&-msg {
		margin: 0 0 8px;
		font-size: var(--font-m);
		font-weight: 400;
		color: var(--color-complement-text);
		line-height: 1.4;
	}

	&-msg--error {
		color: #c62828;
	}

	&-topiclist {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	&-topic {
		width: 100%;
		text-align: left;
		padding: 8px 8px;
		border-radius: 5px;
		border: 1px solid var(--color-border);
		background: var(--color-background);
		cursor: pointer;
		transition: border-color 0.2s;

		&:hover {
			border-color: var(--color-highlight);
		}

		&.is-selected {
			border-color: var(--color-highlight);
			background: var(--color-menu-dropdown);
		}
	}

	&-topic-title {
		display: block;
		font-size: var(--font-m);
		font-weight: 400;
		word-break: break-word;
	}

	&-topic-summary {
		display: block;
		margin-top: 4px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		line-height: 1.35;
		word-break: break-word;
	}

	&-collapse {
		width: 45px;
		min-width: 45px;
		padding: 0 4px;
	}
}
</style>
