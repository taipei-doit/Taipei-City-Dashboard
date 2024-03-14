<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed, ref } from "vue";
import { useContentStore } from "../../store/contentStore";

import ComponentTag from "../utilities/miscellaneous/ComponentTag.vue";
import TagTooltip from "../utilities/miscellaneous/TagTooltip.vue";
import { timeTerms } from "../../assets/configs/AllTimes";
import { getComponentDataTimeframe } from "../../assets/utilityFunctions/dataTimeframe";

const contentStore = useContentStore();

const props = defineProps({
	// The complete config (incl. chart data) of a dashboard component will be passed in
	content: { type: Object },
	isStatic: { type: Boolean, default: false },
	style: { type: Object, default: () => ({}) },
});

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
	<div class="componentpreview" :style="style">
		<div class="componentpreview-header">
			<div>
				<h3>
					{{ content.name }}
					<ComponentTag icon="" :text="updateFreq" mode="small" />
				</h3>
				<p>{{ props.content.short_desc }}</p>
				<h4 v-if="dataTime === '維護修復中'">
					{{ `${content.source} | ` }}<span>warning</span>
					<h4>{{ `${dataTime}` }}</h4>
					<span>warning</span>
				</h4>
				<h4 v-else>{{ `${content.source} | ${dataTime}` }}</h4>
			</div>
			<div class="componentpreview-header-buttons" v-if="!isStatic">
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
		<div class="componentpreview-content">
			<div class="componentpreview-content-id">
				<p>ID: {{ props.content.id }}</p>
				<p>Index: {{ props.content.index }}</p>
			</div>
			<div class="componentpreview-content-charts">
				<img
					v-for="chart in props.content.chart_config.types"
					:key="`${props.content.index} - ${chart}`"
					:src="`/images/thumbnails/${chart}.svg`"
				/>
			</div>
		</div>
		<div class="componentpreview-footer">
			<div
				@mouseenter="changeShowTagTooltipState(true)"
				@mousemove="updateMouseLocation"
				@mouseleave="changeShowTagTooltipState(false)"
			>
				<ComponentTag
					v-if="content.map_filter && content.map_config"
					text="篩選地圖"
					class="hide-if-mobile"
				/>
				<ComponentTag
					v-if="content.map_config && content.map_config[0] !== null"
					text="空間資料"
				/>
				<ComponentTag
					v-if="content.history_data || content.history_config"
					text="歷史資料"
					class="history-tag"
				/>
			</div>
			<!-- The content in the target component should be passed into the "showMoreInfo" function of the mapStore to show more info -->
			<RouterLink :to="`/component/${content.index}`" v-if="!isStatic">
				<p>資訊頁面</p>
				<span>arrow_circle_right</span>
			</RouterLink>
		</div>
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
.componentpreview {
	height: 170px;
	max-height: 170px;
	width: calc(100% - var(--font-m) * 2);
	max-width: calc(100% - var(--font-m) * 2);
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	position: relative;
	padding: var(--font-m);
	border-radius: 5px;
	background-color: var(--color-component-background);

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

		p {
			margin: 4px 0;
		}

		&-buttons {
			min-width: 48px;
			display: flex;
			align-items: baseline;
			justify-content: flex-end;
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
		@media (min-width: 759px) {
			button.isUnfavorite {
				display: none !important;
			}
		}
	}

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

			p {
				font-size: var(--font-s);
				color: var(--color-complement-text);
			}
		}

		&-charts {
			display: flex;
			column-gap: 4px;
			img {
				width: 40px;
				height: 40px;
				border-radius: 5px;
				background-color: var(--color-complement-text);
			}
		}
	}

	&-footer {
		height: 26px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		overflow: visible;

		@media (max-width: 760px) {
			.history-tag {
				display: none !important;
			}
		}

		div {
			display: flex;
			align-items: center;
		}

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
</style>
