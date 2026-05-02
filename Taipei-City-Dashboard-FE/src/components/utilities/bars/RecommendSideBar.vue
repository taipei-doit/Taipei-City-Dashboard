<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref, watch } from "vue";
import { useMapStore } from "../../../store/mapStore";
import { useBackendTranslation } from "../../../composables/useBackendTranslation";
import {
	fetchStorylineTopics,
	postStorylineRecommend,
	toStorylineApiLang,
	collectRelatedNewsFromSteps,
} from "../../../api/storyline";

const mapStore = useMapStore();
const { t, locale } = useBackendTranslation();

const RECOMMEND_SIDEBAR_EXPANDED_KEY = "isRecommendSidebarExpanded";

/** 展開寬度略大於左側 SideBar，收合 45px */
const isExpanded = ref(true);

const topics = ref([]);
const selectedTopicId = ref(null);
const relatedNews = ref([]);
/** @type {import('vue').Ref<string | null>} */
const loadErrorKey = ref(null);
/** @type {import('vue').Ref<string | null>} */
const recommendErrorKey = ref(null);
const loadingTopics = ref(false);
const loadingRecommend = ref(false);

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
	loadErrorKey.value = null;
	loadingTopics.value = true;
	topics.value = [];
	try {
		topics.value = await fetchStorylineTopics();
	} catch {
		loadErrorKey.value = "recommend.error_topics_load";
	} finally {
		loadingTopics.value = false;
	}
}

async function selectTopic(topic) {
	selectedTopicId.value = topic.id;
	recommendErrorKey.value = null;
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
			recommendErrorKey.value = "recommend.error_news_empty_summary";
		}
	} catch {
		recommendErrorKey.value = "recommend.error_news_load";
	} finally {
		loadingRecommend.value = false;
	}
}

watch(locale, () => {
	if (selectedTopicId.value) {
		const sel = topics.value.find((x) => x.id === selectedTopicId.value);
		if (sel) {
			selectTopic(sel);
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
        :title="isExpanded ? t('recommend.toggle_collapse_title') : t('recommend.toggle_expand_title')"
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
            {{ t('recommend.title') }}
          </h1>
          <p class="recommendsidebar-lead">
            {{ t('recommend.lead') }}
          </p>
        </div>
      </template>
      <span
        v-else
        class="recommendsidebar-collapsed-label-text"
        aria-hidden="true"
      >{{ t('recommend.title') }}</span>
    </div>

    <template v-if="isExpanded">
      <div
        v-if="loadingTopics"
        class="recommendsidebar-status"
      >
        {{ t('recommend.loading_topics') }}
      </div>
      <template v-else>
        <h2 class="recommendsidebar-subtitle">
          {{ t('recommend.section_topics') }}
        </h2>
        <p
          v-if="loadErrorKey"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ t(loadErrorKey) }}
        </p>
        <p
          v-else-if="!topics.length"
          class="recommendsidebar-msg"
        >
          {{ t('recommend.empty_topics') }}
        </p>
        <ul
          v-else
          class="recommendsidebar-topiclist"
        >
          <li
            v-for="top in topics"
            :key="top.id"
          >
            <button
              type="button"
              class="recommendsidebar-topic"
              :class="{ 'is-selected': selectedTopicId === top.id }"
              @click="selectTopic(top)"
            >
              <span class="recommendsidebar-topic-title">{{ top.title }}</span>
              <span
                v-if="top.summary"
                class="recommendsidebar-topic-summary"
              >{{ top.summary }}</span>
            </button>
          </li>
        </ul>

        <h2 class="recommendsidebar-subtitle recommendsidebar-subtitle--news">
          {{ t('recommend.section_news') }}
        </h2>
        <div
          v-if="!selectedTopicId"
          class="recommendsidebar-msg"
        >
          {{ t('recommend.pick_topic_hint') }}
        </div>
        <div
          v-else-if="loadingRecommend"
          class="recommendsidebar-status"
        >
          {{ t('recommend.loading_news') }}
        </div>
        <p
          v-else-if="recommendErrorKey"
          class="recommendsidebar-msg recommendsidebar-msg--error"
        >
          {{ t(recommendErrorKey) }}
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
