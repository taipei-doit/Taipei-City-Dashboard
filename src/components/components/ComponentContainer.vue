<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component has three modes 'normal dashboard' / 'more info' / 'basic map layers' -->
<!-- The different modes are controlled by the props "notMoreInfo" (default true) and "isMapLayer" (default false) -->

<script setup>
import { computed, ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import ComponentTag from "../utilities/ComponentTag.vue";
import { chartTypes } from "../../assets/configs/apexcharts/chartTypes";

const dialogStore = useDialogStore();
const contentStore = useContentStore();

const props = defineProps({
	// The complete config (incl. chart data) of a dashboard component will be passed in
	content: { type: Object },
	notMoreInfo: { type: Boolean, default: true },
	isMapLayer: { type: Boolean, default: false },
});

// The default active chart is the first one in the list defined in the dashboard component
const activeChart = ref(props.content.chart_config.types[0]);

// Parses time data into display format
const dataTime = computed(() => {
	if (!props.content.time_from) {
		return "固定資料";
	}
	if (!props.content.time_to) {
		return props.content.time_from.slice(0, 10);
	}
	return `${props.content.time_from.slice(
		0,
		10
	)} ~ ${props.content.time_to.slice(0, 10)}`;
});
// Parses update frequency data into display format
const updateFreq = computed(() => {
	const unitRef = {
		minute: "分",
		hour: "時",
		day: "天",
		week: "週",
		month: "月",
		year: "年",
	};
	if (!props.content.update_freq) {
		return "不定期更新";
	}
	return `每${props.content.update_freq}${
		unitRef[props.content.update_freq_unit]
	}更新`;
});

// Toggles between chart types defined in the dashboard component
function changeActiveChart(chartName) {
	activeChart.value = chartName;
}
function toggleFavorite() {
	if (contentStore.favorites.includes(`${props.content.id}`)) {
		contentStore.unfavoriteComponent(props.content.id);
	} else {
		contentStore.favoriteComponent(props.content.id);
	}
}
</script>

<template>
	<div
		:class="{
			componentcontainer: true,
			moreinfostyle: !notMoreInfo,
			maplayer: isMapLayer,
		}"
	>
		<div class="componentcontainer-header">
			<div>
				<h3>
					{{ content.name }}
					<ComponentTag icon="" :text="updateFreq" mode="small" />
				</h3>
				<h4>{{ `${content.source} | ${dataTime}` }}</h4>
			</div>
			<div v-if="notMoreInfo">
				<button
					v-if="
						!isMapLayer &&
						contentStore.currentDashboard.index !== 'favorites'
					"
					:class="{
						isfavorite: contentStore.favorites.includes(
							`${content.id}`
						),
					}"
					@click="toggleFavorite"
				>
					<span>favorite</span>
				</button>
				<!-- Change @click to a report issue function to implement functionality -->
				<button
					title="回報問題"
					class="show-if-mobile"
					@click="
						dialogStore.showReportIssue(content.id, content.name)
					"
				>
					<span>flag</span>
				</button>
				<!-- deleteComponent is currently a dummy function to demonstrate what adding components may look like
                     Connect a backend to actually implement the function or remove altogether -->
				<button
					v-if="!isMapLayer"
					@click="contentStore.deleteComponent(content.id)"
					class="isDelete"
				>
					<span>delete</span>
				</button>
				<button
					v-if="
						!isMapLayer &&
						contentStore.currentDashboard.index === 'favorites'
					"
					@click="contentStore.deleteComponent(content.id)"
					class="isUnfavorite"
				>
					<span>delete</span>
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
				:key="`${props.content.index}-${item}-chart`"
			>
			</component>
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
		<div class="componentcontainer-footer">
			<div>
				<ComponentTag
					v-if="content.chart_config.map_filter && content.map_config"
					icon="tune"
					text="篩選地圖"
					@click="
						dialogStore.showNotification(
							'info',
							'本組件有篩選地圖功能，歡迎至地圖頁面嘗試'
						)
					"
					class="hide-if-mobile"
				/>
				<ComponentTag
					v-if="content.map_config"
					icon="map"
					text="空間資料"
					@click="
						dialogStore.showNotification(
							'info',
							'本組件有空間資料，歡迎至地圖頁面查看'
						)
					"
				/>
				<ComponentTag
					v-if="content.history_data"
					icon="insights"
					text="歷史資料"
					@click="
						dialogStore.showNotification(
							'info',
							'本組件有歷史資訊，點擊「組件資訊」以查看'
						)
					"
					class="history-tag"
				/>
			</div>
			<!-- The content in the target component should be passed into the "showMoreInfo" function of the mapStore to show more info -->
			<button
				v-if="notMoreInfo && !isMapLayer"
				@click="dialogStore.showMoreInfo(content)"
			>
				<p>組件資訊</p>
				<span>arrow_circle_right</span>
			</button>
		</div>
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
			color: var(--color-complement-text);
			font-size: var(--font-s);
			font-weight: 400;
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
	&-loading {
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

	&-footer {
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

		button {
			display: flex;
			align-items: center;
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}

			@media (max-width: 760px) {
				display: none !important;
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
