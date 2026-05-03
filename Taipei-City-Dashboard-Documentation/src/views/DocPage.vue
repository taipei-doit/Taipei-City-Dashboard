<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAppStore } from '../store/appStore';

import SideBar from '../components/SideBar.vue';
import DocPageContent from '../components/DocPageContent.vue';
import { docsList } from '../assets/docsList';
import { videoList } from '../assets/videoList';

const route = useRoute();
const { t } = useI18n();
const appStore = useAppStore();
const props = defineProps(['id']);

const currentPageIndex = computed(() => {
	if (props.id[0] === '#') return null;
	return docsList[route.name].findIndex((item) => item === props.id);
});
const previousPageIndex = computed(() => {
	if (currentPageIndex.value === -1 || currentPageIndex.value === 1) return null;
	if (docsList[route.name][currentPageIndex.value - 1][0] === "#") return currentPageIndex.value - 2;
	return currentPageIndex.value - 1;
});
const nextPageIndex = computed(() => {
	if (currentPageIndex.value === -1 || currentPageIndex.value === docsList[route.name].length - 1) return null;
	if (docsList[route.name][currentPageIndex.value + 1][0] === "#") return currentPageIndex.value + 2;
	return currentPageIndex.value + 1;
});
const githubEditLink = computed(() => {
	return `https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/${route.name}-${appStore.lang}/${props.id}.md`;
});
const associatedVideos = computed(() => {
	if (route.name === 'data-end') return [];
	return videoList[props.id];
});
</script>

<template>
	<div class="docpage">
		<div class="docpage-positioner">
			<button class="docpage-menu-button show-if-mobile" @click="appStore.toggleSidebar(true)">
				<span>menu</span>{{ t('menu') }}
			</button>
			<SideBar :docs="route.name" :docslist="docsList[route.name]" />
			<div v-if="currentPageIndex === -1" class="docpage-notfound">
				<h1>404</h1>
				<h2>{{ t('404-desc') }}</h2>
				<p>{{ t('404-message') }}</p>
			</div>
			<div v-else class="docpage-content" @click="appStore.toggleSidebar(false)">
				<h1>{{ t(`${route.name}.${id}`) }}</h1>
				<div v-if="associatedVideos" class="docpage-content-video">
					<a v-for="video in associatedVideos" :href="video.url" :key="`video-${video.titleEn}`"
						target="_blank" rel="noreferrer">
						<span>play_circle</span>
						<div>
							<h5>{{ video.titleCh }}</h5>
							<h6>{{ video.titleEn }}</h6>
						</div>
					</a>
				</div>
				<DocPageContent :docs="route.name" :id="id" :key="id" />
				<a class="docpage-edit" :href="githubEditLink" target="_blank"
					rel="noreferrer"><span>auto_fix_high</span>{{
				t('edit-github') }}</a>
				<div class="docpage-nav">
					<div>
						<router-link v-if="previousPageIndex"
							:to="`/${route.name}/${docsList[route.name][previousPageIndex]}`" class="prev">
							<h5><span>keyboard_arrow_left</span>{{ t('previous') }}</h5>
							<h6>{{ t(`${route.name}.${docsList[route.name][previousPageIndex]}`) }}</h6>
						</router-link>
					</div>
					<router-link v-if="nextPageIndex" :to="`/${route.name}/${docsList[route.name][nextPageIndex]}`"
						class="next">
						<h5>{{ t('next') }}<span>keyboard_arrow_right</span></h5>
						<h6>{{ t(`${route.name}.${docsList[route.name][nextPageIndex]}`) }}</h6>
					</router-link>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.docpage {
	display: flex;
	justify-content: center;
	width: 100%;
	height: calc(100vh - 60px);
	height: calc(var(--vh) * 100 - 60px);

	@media screen and (max-width: 850px) {
		height: calc(100% - 60px);
	}

	&-positioner {
		width: 100%;
		height: 100%;
		display: grid;
		grid-template-columns: 224px 1fr;

		@media screen and (max-width: 850px) {
			display: grid;
			grid-template-columns: 1fr;
			grid-template-rows: 2.5rem 1fr;
		}

		@media screen and (min-width: 1200px) {
			width: 1200px
		}
	}

	&-menu-button {
		display: flex;
		align-items: center;
		font-size: var(--font-m);
		padding: 0.5rem 0 0 1.5rem;
		color: var(--color-complement-text);
		cursor: pointer;
		width: fit-content;

		span {
			margin-right: 4px;
			font-family: var(--font-icon);
			color: var(--color-complement-text);
		}
	}

	&-notfound {
		margin-top: 4rem;
		text-align: center;

		h1 {
			font-size: 5rem;
			font-weight: 400;
		}

		h2 {
			font-size: 1.2rem;
		}
	}

	&-content {
		padding: 2rem 1.5rem 3rem 3rem;
		height: calc(100vh - 120px);
		height: calc(var(--vh) * 100 - 120px);
		overflow-y: scroll;

		h1 {
			margin-bottom: 1rem;
			font-size: 2rem;
		}

		@media screen and (max-width: 850px) {
			padding: 0 1.5rem 3rem 1.5rem;
		}

		&-video {
			display: flex;
			flex-wrap: wrap;
			margin: var(--font-m) 0 var(--font-s);
			column-gap: var(--font-s);
			row-gap: var(--font-s);

			a {
				display: flex;
				align-items: center;
				padding: 0.5rem 0.75rem;
				border-radius: 5px;
				background-color: var(--color-component-background);
				color: var(--color-complement-text);
				text-decoration: none;
				transition: opacity 0.3s;

				&:hover {
					opacity: 0.7;
				}

				span {
					font-family: var(--font-icon);
					color: var(--color-complement-text);
					font-size: var(--font-l);
					margin-right: 0.5rem;
				}

				div {
					h5 {
						font-size: var(--font-m);
						font-weight: 400;
					}

					h6 {
						font-size: var(--font-s);
						font-weight: 400;
						color: var(--color-complement-text);
					}
				}
			}

		}
	}

	&-edit {
		display: flex;
		padding: 0.5rem 0 1.5rem;
		color: var(--color-highlight);
		font-size: var(--font-ms);
		border-bottom: solid 1px var(--color-border);

		span {
			align-self: flex-start;
			color: var(--color-highlight);
			font-family: var(--font-icon);
			margin-right: 0.5rem;
		}
	}

	&-nav {
		display: flex;
		justify-content: space-between;
		margin-top: 1.5rem;

		h5 {
			display: flex;
			align-items: center;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			user-select: none;
		}

		span {
			font-family: var(--font-icon);
			color: var(--color-complement-text);
			font-size: var(--font-m);
		}

		h6 {
			margin-top: 4px;
			font-size: var(--font-m);
			font-weight: 400;
		}

		.next {
			text-align: right;

			h5 {
				justify-content: right;
			}
		}

	}
}
</style>import { videoList } from '../assets/videoList';
