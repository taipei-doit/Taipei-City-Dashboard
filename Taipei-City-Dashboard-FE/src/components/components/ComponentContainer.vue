<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- This component has three modes 'normal dashboard' / 'more info' / 'basic map layers' -->
<!-- The different modes are controlled by the props "notMoreInfo" (default true) and "isMapLayer" (default false) -->

<script setup>
import { computed, ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";
import { useAuthStore } from "../../store/authStore";

import ComponentTag from "../utilities/miscellaneous/ComponentTag.vue";
import TagTooltip from "../utilities/miscellaneous/TagTooltip.vue";
import { chartTypes } from "../../assets/configs/apexcharts/chartTypes";
import { timeTerms } from "../../assets/configs/AllTimes";
import { getComponentDataTimeframe } from "../../assets/utilityFunctions/dataTimeframe";

const dialogStore = useDialogStore();
const contentStore = useContentStore();
const authStore = useAuthStore();

const props = defineProps({
	// The complete config (incl. chart data) of a dashboard component will be passed in
	content: { type: Object },
	notMoreInfo: { type: Boolean, default: true },
	isMapLayer: { type: Boolean, default: false },
	isComponentView: { type: Boolean, default: false },
	embed: { type: Boolean, default: false },
	style: { type: Object, default: () => ({}) },
});

// The default active chart is the first one in the list defined in the dashboard component
const activeChart = ref(props.content.chart_config.types[0]);
// stores the location of the mouse when tags are hovered over
const mousePosition = ref({ x: null, y: null });
const showTagTooltip = ref(false);

// Parses time data into display format
const dataTime = computed(() => {
	if (props.content.time_from === "static") {
		return "固定資料";
	} else if (props.content.time_from === "current") {
		return "即時資料";
	} else if (props.content.time_from === "demo") {
		return "示範靜態資料";
	} else if (props.content.time_from === "maintain") {
		return "維護修復中";
	}
	const { parsedTimeFrom, parsedTimeTo } = getComponentDataTimeframe(
		props.content.time_from,
		props.content.time_to
	);
	if (props.content.time_from === "day_start") {
		return `${parsedTimeFrom.slice(0, 16)} ~ ${parsedTimeTo.slice(
			11,
			14
		)}00`;
	}
	return `${parsedTimeFrom.slice(0, 10)} ~ ${parsedTimeTo.slice(0, 10)}`;
});
// Parses update frequency data into display format
const updateFreq = computed(() => {
	if (!props.content.update_freq) {
		return "不定期更新";
	}
	return `每${props.content.update_freq}${
		timeTerms[props.content.update_freq_unit]
	}更新`;
});
// The style for the tag tooltip
const tooltipPosition = computed(() => {
	return {
		left: `${mousePosition.value.x - 40}px`,
		top: `${mousePosition.value.y - 110}px`,
	};
});

// Toggles between chart types defined in the dashboard component
function changeActiveChart(chartName) {
	activeChart.value = chartName;
}
function toggleFavorite() {
	if (contentStore.favorites.components.includes(props.content.id)) {
		contentStore.unfavoriteComponent(props.content.id);
	} else {
		contentStore.favoriteComponent(props.content.id);
	}
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
</script>

<template>
	<div
		:class="{
			componentcontainer: true,
			moreinfostyle: !notMoreInfo,
			maplayer: isMapLayer,
		}"
		:style="style"
	>
		<div class="componentcontainer-header">
			<div>
				<h3>
					{{ content.name }}
					<ComponentTag icon="" :text="updateFreq" mode="small" />
				</h3>
				<h4 v-if="dataTime === '維護修復中'">
					{{ `${content.source} | ` }}<span>warning</span>
					<h4>{{ `${dataTime}` }}</h4>
					<span>warning</span>
				</h4>
				<h4 v-else>{{ `${content.source} | ${dataTime}` }}</h4>
			</div>
			<div v-if="notMoreInfo && authStore.token && !embed">
				<button
					v-if="
						contentStore.currentDashboard.icon !== 'favorite' &&
						contentStore.favorites
					"
					:class="{
						isfavorite: contentStore.favorites.components.includes(
							content.id
						),
					}"
					@click="toggleFavorite"
				>
					<span>favorite</span>
				</button>
				<!-- Change @click to a report issue function to implement functionality -->
				<button
					title="回報問題"
					class="isFlag"
					@click="
						dialogStore.showReportIssue(
							content.id,
							content.index,
							content.name
						)
					"
				>
					<span>flag</span>
				</button>
				<button
					v-if="
						contentStore.personalDashboards
							.map((item) => item.index)
							.includes(contentStore.currentDashboard.index)
					"
					@click="contentStore.deleteComponent(content.id)"
					class="isDelete"
				>
					<span>delete</span>
				</button>
			</div>
			<div v-else-if="isComponentView">
				<button
					v-if="
						!contentStore.editDashboard.components
							.map((item) => item.id)
							.includes(props.content.id)
					"
					@click="
						contentStore.editDashboard.components.push({
							id: props.content.id,
							name: props.content.name,
						})
					"
					class="hide-if-mobile"
				>
					<span>add_circle</span>
				</button>
				<button
					v-if="
						!authStore.isNarrowDevice || !authStore.isMobileDevice
					"
					:class="{
						isfavorite: contentStore.favorites.components.includes(
							content.id
						),
					}"
					@click="toggleFavorite"
				>
					<span>favorite</span>
				</button>
			</div>
		</div>
		<div
			class="componentcontainer-control"
			v-if="props.content.chart_config.types.length > 1"
		>
			<button
				:class="{
					'componentcontainer-control-button': true,
					'componentcontainer-control-active': activeChart === item,
				}"
				v-for="item in props.content.chart_config.types"
				@click="changeActiveChart(item)"
				:key="`${props.content.index}-${item}-button`"
			>
				{{ chartTypes[item] }}
			</button>
		</div>
		<div
			:class="{
				'componentcontainer-chart': true,
				'maplayer-chart': isMapLayer,
			}"
			v-if="content.chart_data"
		>
			<!-- The components referenced here can be edited in /components/charts -->
			<component
				v-for="item in content.chart_config.types"
				:activeChart="activeChart"
				:is="item"
				:chart_config="content.chart_config"
				:series="content.chart_data"
				:map_config="content.map_config"
				:map_filter="content.map_filter"
				:key="`${props.content.index}-${item}-chart`"
			>
			</component>
		</div>
		<div
			v-else-if="content.chart_data === null"
			:class="{
				'componentcontainer-error': true,
				'maplayer-loading': isMapLayer,
			}"
		>
			<span>error</span>
			<p>組件資料異常</p>
		</div>
		<div
			v-else
			:class="{
				'componentcontainer-loading': true,
				'maplayer-loading': isMapLayer,
			}"
		>
			<div></div>
		</div>
		<div class="componentcontainer-footer" v-if="!embed">
			<div
				@mouseenter="changeShowTagTooltipState(true)"
				@mousemove="updateMouseLocation"
				@mouseleave="changeShowTagTooltipState(false)"
			>
				<ComponentTag
					v-if="content.map_filter && content.map_config"
					icon="tune"
					text="篩選地圖"
					class="hide-if-mobile"
				/>
				<ComponentTag
					v-if="content.map_config && content.map_config[0] !== null"
					icon="map"
					text="空間資料"
					class="hide-if-mobile"
				/>
				<ComponentTag
					v-if="content.history_data || content.history_config"
					icon="insights"
					text="歷史資料"
					class="history-tag"
				/>
			</div>
			<!-- The content in the target component should be passed into the "showMoreInfo" function of the mapStore to show more info -->
			<button
				v-if="notMoreInfo"
				@click="dialogStore.showMoreInfo(content)"
			>
				<p>組件資訊</p>
				<span>arrow_circle_right</span>
			</button>
			<RouterLink
				:to="`/component/${content.index}`"
				v-if="
					authStore.isMobileDevice &&
					authStore.isNarrowDevice &&
					authStore.currentPath !== 'component-info'
				"
			>
				<p>資訊頁面</p>
				<span>arrow_circle_right</span>
			</RouterLink>
		</div>
		<div v-else class="componentcontainer-footer"></div>
		<Teleport to="body">
			<!-- The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css -->
			<TagTooltip
				v-if="showTagTooltip"
				:position="tooltipPosition"
				:hasFilter="content.map_filter ? true : false"
				:hasMapLayer="content.map_config[0] ? true : false"
				:hasHistory="content.history_config ? true : false"
			/>
		</Teleport>
	</div>
</template>

<style scoped lang="scss">
.componentcontainer {
	height: 330px;
	max-height: 330px;
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
		height: 370px;
		max-height: 370px;
	}

	@media (min-width: 1650px) {
		height: 400px;
		max-height: 400px;
	}

	@media (min-width: 2200px) {
		height: 500px;
		max-height: 500px;
	}

	&-header {
		display: flex;
		justify-content: space-between;

		h3 {
			display: flex;
			align-items: center;
			font-size: var(--font-m);
		}

		h4 {
			display: flex;
			align-items: center;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			font-weight: 400;

			span {
				margin: 0 4px;
				color: rgb(237, 90, 90);
				font-size: 1rem;
				font-family: var(--font-icon);
				user-select: none;
			}

			h4 {
				color: rgb(237, 90, 90);
			}
		}

		button span {
			color: var(--color-complement-text);
			font-family: var(--font-icon);
			font-size: calc(var(--font-l) * var(--font-to-icon));
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
		justify-content: center;
		align-items: center;
		position: absolute;
		top: 4.2rem;
		left: 0;
		z-index: 8;

		&-button {
			margin: 0 2px;
			padding: 4px 4px;
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

	&-chart,
	&-loading,
	&-error {
		height: 75%;
		position: relative;
		padding-top: 5%;
		overflow-y: scroll;

		p {
			color: var(--color-border);
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

		button {
			@media (max-width: 760px) {
				display: none !important;
			}
		}
	}
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}

.moreinfostyle {
	height: 350px;
	max-height: 350px;

	@media (min-width: 820px) {
		height: 380px;
		max-height: 380px;
	}

	@media (min-width: 1200px) {
		height: 420px;
		max-height: 420px;
	}

	@media (min-width: 2200px) {
		height: 520px;
		max-height: 520px;
	}
}

.maplayer {
	height: 180px;
	max-height: 180px;

	@media (min-width: 1050px) {
		height: 210px;
		max-height: 210px;
	}

	@media (min-width: 1650px) {
		height: 225px;
		max-height: 225px;
	}

	@media (min-width: 2200px) {
		height: 275px;
		max-height: 275px;
	}

	&-chart,
	&-loading {
		height: 60%;
	}
}
</style>
