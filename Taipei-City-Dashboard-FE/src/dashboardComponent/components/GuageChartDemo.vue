<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, computed } from "vue";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

const emits = defineEmits([
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"fly"
]);

// 重新解析資料：維持提取絕對數值，以供 polarArea 使用
const parseSeries = computed(() => {
	let output = {
		series: [],
		labels: [],
		totalSum: 0,
	};
	let totalSum = 0;

	if (props.series && props.series.length > 0) {
		// 判斷資料結構：如果是多個 series，每個 series 只有一筆資料 (如 YouBike 範例)
		if (props.series[0].data.length === 1) {
			for (let i = 0; i < props.series.length; i++) {
				let val = props.series[i].data[0];
				output.series.push(val);
				output.labels.push(props.series[i].name);
				totalSum += val;
			}
		} else {
			// 如果是單一 series 有多筆資料
			for (let i = 0; i < props.series[0].data.length; i++) {
				let val = props.series[0].data[i];
				output.series.push(val);
				output.labels.push(props.chart_config.categories ? props.chart_config.categories[i] : `Item ${i}`);
				totalSum += val;
			}
		}
	}

	output.totalSum = Math.round(totalSum * 100) / 100;
	return output;
});

// 使用 computed 動態產生 chartOptions，確保設定更新
const chartOptions = computed(() => {
	return {
		chart: {
			offsetY: 10,
			animations: {
				enabled: true,
				easing: 'easeinout',
				speed: 800,
			}
		},
		// 支援動態主題顏色
		colors: props.chart_config.color ? props.chart_config.color : ["#4A90E2", "#50E3C2", "#F5A623"],
		labels: parseSeries.value.labels,
		legend: {
			show: false, // 隱藏下方圖例，因為 polarArea 在外側已經有標籤了
		},
		dataLabels: {
			formatter: function (_val, { seriesIndex, w }) {
				// 顯示標籤名稱，過長則加上省略號
				let value = w.globals.labels[seriesIndex];
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
		plotOptions: {
			polarArea: {
				rings: {
					strokeWidth: 1,
					strokeColor: 'var(--color-border, #3c4043)',
				},
				spines: {
					strokeWidth: 1,
					connectorColors: 'var(--color-border, #3c4043)',
				}
			}
		},
		stroke: {
			colors: ["#282a2c"], // 加上深色邊框區分區塊
			show: true,
			width: 2
		},
		fill: {
			opacity: 0.8
		},
		theme: {
			monochrome: {
				enabled: false, // 確保吃到我們設定的色彩
			}
		},
		tooltip: {
			followCursor: false,
			custom: function ({ seriesIndex, w }) {
				return (
					'<div class="chart-tooltip">' +
					"<h6>" +
					w.globals.labels[seriesIndex] +
					"</h6>" +
					"<span>" +
					w.globals.series[seriesIndex] + (props.chart_config.unit ? ` ${props.chart_config.unit}` : '') +
					"</span>" +
					"</div>"
				);
			},
		},
	};
});

const selectedIndex = ref(null);

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				props.series[0].name
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits(
				"filterByLayer",
				props.map_config,
				config.w.globals.labels[config.dataPointIndex]
			);
		}
		selectedIndex.value = `${config.dataPointIndex}-${config.seriesIndex}`;
	} else {
		if (props.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
}
</script>

<template>
  <div v-if="activeChart === 'GuageChartDemo'" class="polararea-chart">
    <VueApexCharts
      width="100%"
      type="polarArea"
      :options="chartOptions"
      :series="parseSeries.series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>

<style scoped lang="scss">
.polararea-chart {
	height: 100%;
	width: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
	position: relative;
	overflow-y: visible;

	:deep(.vue-apexcharts) {
		z-index: 1;
		
		/* 確保 tooltip 不會被裁切 */
		.apexcharts-tooltip {
			z-index: 99;
		}
	}
}
</style>
