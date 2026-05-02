<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useMapStore } from "../../../store/mapStore";
import { useTranslationStore } from "../../../store/translationStore";
import {
	fetchStorylineTopics,
	postStorylineRecommend,
	toStorylineApiLang,
	collectRelatedNewsFromSteps,
} from "../../../api/storyline";
import { extractNewsInsight } from "../../../api/ai";

const mapStore = useMapStore();
const translationStore = useTranslationStore();
const { locale } = storeToRefs(translationStore);

const RECOMMEND_SIDEBAR_EXPANDED_KEY = "isRecommendSidebarExpanded";

/** 展開寬度略大於左側 SideBar，收合 45px */
const isExpanded = ref(true);

const topics = ref([]);
const selectedTopicId = ref(null);
const relatedNews = ref([]);
const loadError = ref(null);
const recommendError = ref(null);
const loadingTopics = ref(false);
const loadingRecommend = ref(false);

// AI Insight State
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
		// 如果有推薦組件，也可以考慮自動選取或展開
	} catch (err) {
		aiInsightError.value = "AI 分析失敗，請檢查網址或稍後再試。";
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

async function loadTopics() {
	loadError.value = null;
	loadingTopics.value = true;
	topics.value = [];
	try {
		topics.value = await fetchStorylineTopics();
	} catch {
		loadError.value = "無法載入主題。";
	} finally {
		loadingTopics.value = false;
	}
}

async function selectTopic(topic) {
	selectedTopicId.value = topic.id;
	recommendError.value = null;
	relatedNews.value = [];
	loadingRecommend.value = true;
	const lang = toStorylineApiLang(locale.value);
	try {
		const { steps } = await postStorylineRecommend({
			lang,
			topic_id: String(topic.id),
			limit: 12,
		});
		relatedNews.value = collectRelatedNewsFromSteps(steps);
		if (!relatedNews.value.length) {
			recommendError.value = "此主題暫無摘要。";
		}
	} catch {
		recommendError.value = "無法載入新聞。";
	} finally {
		loadingRecommend.value = false;
	}
}

watch(locale, () => {
	if (selectedTopicId.value) {
		const t = topics.value.find((x) => x.id === selectedTopicId.value);
		if (t) {
			selectTopic(t);
		}
	}
});

onMounted(() => {
	readExpandedFromStorage();
	loadTopics();
});
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
            選擇主題或貼上新聞連結。
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
      <!-- AI Insight Input Section -->
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

      <!-- AI Result: Storyline -->
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
        
        <h2
          v-if="aiInsightResult.components?.length"
          class="recommendsidebar-subtitle"
        >
          推薦數據組件
        </h2>
        <ul
          v-if="aiInsightResult.components?.length"
          class="recommendsidebar-topiclist"
        >
          <li
            v-for="comp in aiInsightResult.components"
            :key="comp.id"
          >
            <button
              type="button"
              class="recommendsidebar-topic recommendsidebar-topic--ai"
              @click="mapStore.addComponentToDashboard(comp)"
            >
              <span class="recommendsidebar-topic-title">{{ comp.name }}</span>
              <span class="recommendsidebar-topic-summary">{{ comp.short_desc }}</span>
            </button>
          </li>
        </ul>
      </div>

      <div
        v-if="loadingTopics"
        class="recommendsidebar-status"
      >
        載入中…
      </div>
      <template v-else>
        <h2 class="recommendsidebar-subtitle">
          推薦主題
        </h2>
        <p
          v-if="loadError"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ loadError }}
        </p>
        <p
          v-else-if="!topics.length"
          class="recommendsidebar-msg"
        >
          尚無推薦主題。
        </p>
        <ul
          v-else
          class="recommendsidebar-topiclist"
        >
          <li
            v-for="t in topics"
            :key="t.id"
          >
            <button
              type="button"
              class="recommendsidebar-topic"
              :class="{ 'is-selected': selectedTopicId === t.id }"
              @click="selectTopic(t)"
            >
              <span class="recommendsidebar-topic-title">{{ t.title }}</span>
              <span
                v-if="t.summary"
                class="recommendsidebar-topic-summary"
              >{{ t.summary }}</span>
            </button>
          </li>
        </ul>

        <h2 class="recommendsidebar-subtitle recommendsidebar-subtitle--news">
          相關新聞
        </h2>
        <div
          v-if="!selectedTopicId"
          class="recommendsidebar-msg"
        >
          請先選擇主題。
        </div>
        <div
          v-else-if="loadingRecommend"
          class="recommendsidebar-status"
        >
          載入新聞…
        </div>
        <p
          v-else-if="recommendError"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ recommendError }}
        </p>
        <ul
          v-else
          class="recommendsidebar-newslist"
        >
          <li
            v-for="(n, idx) in relatedNews"
            :key="n.news_id ?? idx"
            class="recommendsidebar-newsitem"
          >
            <a
              v-if="n.url"
              :href="n.url"
              target="_blank"
              rel="noopener noreferrer"
              class="recommendsidebar-news-title"
            >{{ n.title }}</a>
            <span
              v-else
              class="recommendsidebar-news-title"
            >{{ n.title }}</span>
            <p
              v-if="n.summary"
              class="recommendsidebar-news-summary"
            >
              {{ n.summary }}
            </p>
          </li>
        </ul>
      </template>
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

	/* 與左側 SideBar：h1＝私人儀表板層級；h2／SideBarTab 儀表板名＝ var(--font-m) */
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

		&--news {
			margin-top: 14px;
			padding-top: 10px;
			border-top: 1px solid var(--color-border);
		}
	}

	&-status,
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

	&-newslist {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--font-s);
	}

	&-newsitem {
		padding-bottom: var(--font-s);
		border-bottom: 1px solid var(--color-border);

		&:last-child {
			border-bottom: none;
			padding-bottom: 0;
		}
	}

	&-news-title {
		font-size: var(--font-m);
		font-weight: 400;
		color: var(--color-highlight);
		text-decoration: none;
		word-break: break-word;

		&:hover {
			text-decoration: underline;
		}
	}

	&-news-summary {
		margin: 4px 0 0;
		font-size: var(--font-s);
		color: var(--color-normal-text);
		line-height: 1.45;
		word-break: break-word;
	}

	&-collapse {
		width: 45px;
		min-width: 45px;
		padding: 0 4px;
	}
}
</style>
