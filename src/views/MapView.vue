<!-- Developed By Taipei Urban Intelligence Center 2023 -->
<!-- 
Lead Developer:  Igor Ho (FE Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<!-- Map charts will be hidden in mobile mode and be replaced with the mobileLayers dialog -->

<script setup>
import { computed } from "vue";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";

import ComponentMapChart from "../components/components/ComponentMapChart.vue";
import MapContainer from "../components/map/MapContainer.vue";
import MoreInfo from "../components/dialogs/MoreInfo.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();

// Separate components with maps from those without
const parseMapLayers = computed(() => {
	const hasMap = contentStore.currentDashboard.content.filter(
		(item) => item.map_config
	);
	const noMap = contentStore.currentDashboard.content.filter(
		(item) => !item.map_config
	);

	return { hasMap: hasMap, noMap: noMap };
});
</script>

<template>
	<div class="map">
		<div class="hide-if-mobile">
			<!-- If the dashboard is map layers -->
			<div
				class="map-charts"
				v-if="contentStore.currentDashboard.index === 'map-layers'"
			>
				<ComponentMapChart
					v-for="item in contentStore.currentDashboard.content"
					:content="item"
					:key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
					:is-map-layer="true"
				/>
			</div>
			<!-- other dashboards that have components -->
			<div
				v-else-if="contentStore.currentDashboard.content.length !== 0"
				class="map-charts"
			>
				<ComponentMapChart
					v-for="item in parseMapLayers.hasMap"
					:content="item"
					:key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
				/>
				<h2>基本圖層</h2>
				<ComponentMapChart
					v-for="item in contentStore.mapLayers"
					:content="item"
					:key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
					:is-map-layer="true"
				/>
				<h2 v-if="parseMapLayers.noMap.length > 0">無空間資料組件</h2>
				<ComponentMapChart
					v-for="item in parseMapLayers.noMap"
					:content="item"
					:key="`map-layer-${item.index}-${contentStore.currentDashboard.index}`"
				/>
			</div>
			<!-- if dashboard is still loading -->
			<div
				v-else-if="contentStore.loading"
				class="map-charts-nodashboard"
			>
				<div></div>
			</div>
			<!-- if dashboard failed to load -->
			<div v-else-if="contentStore.error" class="map-charts-nodashboard">
				<span>sentiment_very_dissatisfied</span>
				<h2>發生錯誤，無法載入儀表板</h2>
			</div>
			<!-- other dashboards that don't have components -->
			<div v-else class="map-charts-nodashboard">
				<span>addchart</span>
				<h2>尚未加入組件</h2>
				<button
					@click="dialogStore.showDialog('addComponent')"
					class="hide-if-mobile"
					v-if="contentStore.currentDashboard.index !== 'favorites'"
				>
					加入您的第一個組件
				</button>
				<p v-else>點擊其他儀表板組件之愛心以新增至收藏組件</p>
			</div>
		</div>
		<MapContainer />
		<MoreInfo />
		<ReportIssue />
	</div>
</template>

<style scoped lang="scss">
.map {
	height: calc(100vh - 127px);
	height: calc(var(--vh) * 100 - 127px);
	display: flex;
	margin: var(--font-m) var(--font-m);

	&-charts {
		width: 360px;
		max-height: 100%;
		height: fit-content;
		display: grid;
		row-gap: var(--font-m);
		margin-right: var(--font-s);
		border-radius: 5px;
		overflow-y: scroll;

		@media (min-width: 1000px) {
			width: 370px;
		}

		@media (min-width: 2000px) {
			width: 400px;
		}

		&-nodashboard {
			width: 360px;
			height: calc(100vh - 127px);
			height: calc(var(--vh) * 100 - 127px);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;

			@media (min-width: 1000px) {
				width: 370px;
			}

			@media (min-width: 2000px) {
				width: 400px;
			}

			span {
				margin-bottom: 1rem;
				font-family: var(--font-icon);
				font-size: 2rem;
			}

			button {
				color: var(--color-highlight);
			}

			div {
				width: 2rem;
				height: 2rem;
				border-radius: 50%;
				border: solid 4px var(--color-border);
				border-top: solid 4px var(--color-highlight);
				animation: spin 0.7s ease-in-out infinite;
			}
		}
	}
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
</style>
