<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, watch } from "vue";
import router from "../../../router";
import { useMapStore } from "../../../store/mapStore";
import { useContentStore } from "../../../store/contentStore";
import { useThemeStore } from "../../../store/themeStore";
import {
	extractNewsInsight,
	fetchCrawledNewsRecommendations,
} from "../../../api/ai";

const mapStore = useMapStore();
const contentStore = useContentStore();
const themeStore = useThemeStore();

const RECOMMEND_SIDEBAR_EXPANDED_KEY = "isRecommendSidebarExpanded";
const MODE_STORAGE_KEY = "recommendSidebarAiMode";
/** 自行貼上網址並解析 */
const MODE_MANUAL_URL = "manual_url";
/** 伺服器自動抓取新聞並配對組件 */
const MODE_AUTO_NEWS = "auto_news";

/** 展開寬度略大於左側 SideBar，收合 45px */
const isExpanded = ref(true);

const recommendMode = ref(MODE_AUTO_NEWS);

const aiNewsUrl = ref("");
const aiInsightResult = ref(null);
const loadingAiInsight = ref(false);
const aiInsightError = ref(null);

/** 自動新聞：null = 尚未請求，[] = 已成功但無項目 */
const autoNewsItems = ref(null);
const loadingAutoNews = ref(false);
const autoNewsError = ref(null);

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

function switchRecommendMode(mode) {
	if (mode !== MODE_MANUAL_URL && mode !== MODE_AUTO_NEWS) {
		return;
	}
	recommendMode.value = mode;
	localStorage.setItem(MODE_STORAGE_KEY, mode);
}

function readRecommendModeFromStorage() {
	const stored = localStorage.getItem(MODE_STORAGE_KEY);
	if (stored === MODE_AUTO_NEWS || stored === MODE_MANUAL_URL) {
		recommendMode.value = stored;
	}
}

async function handleLoadAutoNews() {
	if (loadingAutoNews.value) {
		return;
	}
	loadingAutoNews.value = true;
	autoNewsError.value = null;

	try {
		autoNewsItems.value = await fetchCrawledNewsRecommendations({});
	} catch {
		autoNewsError.value =
			"無法載入新聞推薦。請稍後再試，或請管理員檢查伺服器 RSS（環境變數 NEWS_RSS_FEEDS）是否可連線。";
		autoNewsItems.value = null;
	} finally {
		loadingAutoNews.value = false;
	}
}

function openExternalNewsUrl(url) {
	if (!url || typeof url !== "string") return;
	globalThis.open(url, "_blank", "noopener,noreferrer");
}

readExpandedFromStorage();
readRecommendModeFromStorage();

watch(
	[recommendMode, isExpanded],
	([mode, expanded]) => {
		if (mode === MODE_AUTO_NEWS && expanded) {
			handleLoadAutoNews();
		}
	},
	{ immediate: true },
);

watch(
	() => themeStore.theme,
	() => {
		if (recommendMode.value === MODE_AUTO_NEWS && isExpanded.value) {
			handleLoadAutoNews();
		}
	},
);

/**
 * 導向儀表板總覽中該組件所在版面（保留右側推薦側欄，避免 component-info 卸載側欄）
 */
async function openStorylineRecommendedComponent(comp) {
	const compId = comp?.id;
	if (compId === undefined || compId === null || compId === "") {
		const idx = comp?.index;
		if (idx === undefined || idx === null || idx === "") return;
		router.push({
			name: "component-info",
			params: { index: String(idx) },
			query: comp.city ? { city: comp.city } : {},
		});
		return;
	}

	if (
		contentStore.dashboards.size === 0 &&
		(!contentStore.personalDashboards?.length)
	) {
		await contentStore.setDashboards(true);
	}

	const loc = contentStore.findDashboardLocationForComponent(
		compId,
		comp?.city || null,
	);
	if (!loc) {
		const idx = comp?.index;
		if (idx === undefined || idx === null || idx === "") return;
		router.push({
			name: "component-info",
			params: { index: String(idx) },
			query: comp.city ? { city: comp.city } : {},
		});
		return;
	}

	contentStore.pendingScrollToComponentId = compId;
	const query = { index: loc.index };
	if (loc.city != null && loc.city !== "") {
		query.city = loc.city;
	}

	const rt = router.currentRoute.value;
	const sameDashboard =
		rt.path === "/dashboard" &&
		String(rt.query.index || "") === String(loc.index || "") &&
		String(rt.query.city || "") === String(loc.city || "");

	if (sameDashboard) {
		return;
	}

	await router.push({ path: "/dashboard", query });
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
          <p
            v-if="recommendMode === MODE_MANUAL_URL"
            class="recommendsidebar-lead"
          >
            貼上新聞網址取得洞察與推薦主題。
          </p>
          <p
            v-else
            class="recommendsidebar-lead"
          >
            由系統擷取近期新聞，推薦與儀表板組件相關的 2–3 則報導。
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
      <div
        class="recommendsidebar-modes"
        role="tablist"
        aria-label="今日推薦模式"
      >
        <button
          type="button"
          role="tab"
          class="recommendsidebar-mode-btn"
          :class="{
            'recommendsidebar-mode-btn--active':
              recommendMode === MODE_AUTO_NEWS,
          }"
          :aria-selected="recommendMode === MODE_AUTO_NEWS"
          @click="switchRecommendMode(MODE_AUTO_NEWS)"
        >
          自動新聞
        </button>
        <button
          type="button"
          role="tab"
          class="recommendsidebar-mode-btn"
          :class="{
            'recommendsidebar-mode-btn--active':
              recommendMode === MODE_MANUAL_URL,
          }"
          :aria-selected="recommendMode === MODE_MANUAL_URL"
          @click="switchRecommendMode(MODE_MANUAL_URL)"
        >
          網址分析
        </button>
      </div>

      <div v-show="recommendMode === MODE_MANUAL_URL">
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

          <h2 class="recommendsidebar-subtitle">
            AI 數據洞察
          </h2>
          <div class="recommendsidebar-storyline">
            {{ aiInsightResult.storyline }}
          </div>
        </div>
      </div>

      <div
        v-show="recommendMode === MODE_AUTO_NEWS"
        class="recommendsidebar-auto-news"
      >
        <button
          type="button"
          class="recommendsidebar-crawl-btn"
          :disabled="loadingAutoNews"
          @click="handleLoadAutoNews"
        >
          <span v-if="!loadingAutoNews">newspaper</span>
          <span
            v-else
            class="is-spinning"
          >sync</span>
          <span class="recommendsidebar-crawl-btn-label">
            {{ loadingAutoNews ? "載入中…" : "取得新聞推薦" }}
          </span>
        </button>
        <p
          v-if="autoNewsError"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ autoNewsError }}
        </p>
        <p
          v-else-if="
            autoNewsItems !== null &&
              autoNewsItems.length === 0 &&
              !loadingAutoNews
          "
          class="recommendsidebar-msg"
        >
          目前沒有可推薦的新聞項目。
        </p>
        <ul
          v-if="autoNewsItems?.length"
          class="recommendsidebar-newslist"
        >
          <li
            v-for="(item, idx) in autoNewsItems"
            :key="`${item.url || item.title}-${idx}`"
          >
            <article class="recommendsidebar-news-card">
              <h3 class="recommendsidebar-news-title">
                <a
                  v-if="item.url"
                  :href="item.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="recommendsidebar-news-link"
                >
                  {{ item.title }}
                </a>
                <template v-else>
                  {{ item.title }}
                </template>
              </h3>
              <p
                v-if="item.source || item.published_at"
                class="recommendsidebar-news-meta"
              >
                <span v-if="item.source">
                  {{ item.source }}
                </span>
                <span v-if="item.source && item.published_at"> · </span>
                <span v-if="item.published_at">
                  {{ item.published_at }}
                </span>
              </p>
              <p
                v-if="item.summary"
                class="recommendsidebar-news-summary"
              >
                {{ item.summary }}
              </p>
              <p
                v-if="item.component?.name"
                class="recommendsidebar-news-related"
              >
                關聯組件：{{ item.component.name }}
              </p>
              <div class="recommendsidebar-news-actions">
                <button
                  v-if="item.url"
                  type="button"
                  class="recommendsidebar-news-action recommendsidebar-news-action--ghost"
                  @click="openExternalNewsUrl(item.url)"
                >
                  <span class="recommendsidebar-news-action-icon">open_in_new</span>
                  開啟全文
                </button>
                <button
                  type="button"
                  class="recommendsidebar-news-action recommendsidebar-news-action--primary"
                  :disabled="!item.component"
                  @click="openStorylineRecommendedComponent(item.component)"
                >
                  查看組件
                </button>
              </div>
            </article>
          </li>
        </ul>
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

	&-modes {
		display: flex;
		margin-bottom: 12px;
		border-radius: 8px;
		border: 1px solid var(--color-border);
		overflow: hidden;
		background: var(--color-component-background);
	}

	&-mode-btn {
		flex: 1;
		padding: 8px 10px;
		font-size: var(--font-m);
		color: var(--color-complement-text);
		transition:
			background-color 0.2s,
			color 0.2s;
		text-wrap: nowrap;

		&:hover {
			color: var(--color-normal-text);
			background: var(--color-background);
		}

		&--active {
			background: var(--color-highlight);
			color: #fff;
			font-weight: 600;

			&:hover {
				color: #fff;
			}
		}
	}

	&-auto-news {
		margin-bottom: 16px;
	}

	&-crawl-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		width: 100%;
		padding: 8px 10px;
		margin-bottom: 10px;
		border-radius: 6px;
		background: var(--color-highlight);
		color: #fff;
		font-size: var(--font-m);
		transition: opacity 0.2s;

		&:disabled {
			opacity: 0.55;
			cursor: not-allowed;
		}

		span:first-of-type {
			font-family: var(--font-icon);
			font-size: var(--font-m);
		}
	}

	&-crawl-btn-label {
		font-weight: 500;
	}

	&-newslist {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	&-news-card {
		border: 1px solid var(--color-border);
		border-radius: 8px;
		padding: 10px;
		background: var(--color-background);
	}

	&-news-title {
		margin: 0 0 4px;
		font-size: var(--font-ms);
		font-weight: 600;
		line-height: 1.35;
	}

	&-news-link {
		color: var(--color-highlight);
		text-decoration: none;
		word-break: break-word;

		&:hover {
			text-decoration: underline;
		}
	}

	&-news-meta {
		margin: 0 0 6px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		line-height: 1.3;
	}

	&-news-summary {
		margin: 0 0 8px;
		font-size: var(--font-s);
		color: var(--color-normal-text);
		line-height: 1.45;
		word-break: break-word;
		line-clamp: 5;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 5;
		overflow: hidden;
	}

	&-news-related {
		margin: 0 0 10px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		line-height: 1.35;
	}

	&-news-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		align-items: center;
	}

	&-news-action {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 6px 8px;
		border-radius: 5px;
		font-size: var(--font-s);
		cursor: pointer;
		transition:
			filter 0.15s,
			border-color 0.2s;

		&--primary {
			flex: 1;
			min-width: 0;
			justify-content: center;
			border: none;
			background: var(--color-highlight);
			color: #fff;

			&:disabled {
				opacity: 0.45;
				cursor: not-allowed;
				filter: none;
			}
		}

		&--ghost {
			border: 1px solid var(--color-border);
			background: var(--color-component-background);
			color: var(--color-normal-text);
		}

		&:not(:disabled):hover {
			filter: brightness(1.08);
		}
	}

	&-news-action-icon {
		font-family: var(--font-icon);
		font-size: var(--font-m);
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

		> .recommendsidebar-subtitle:first-of-type {
			margin-top: 0;
		}
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
		font-weight: 700;
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
		font-weight: 700;
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
