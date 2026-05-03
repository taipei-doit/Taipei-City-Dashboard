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

// multi_chart 載入後才會帶入 categories_by_type → effectiveChartConfig.categories；
// 必須用 computed，否則 xaxis.categories 會卡在初次 mount 的空陣列，圖表無法渲染。
const chartOptions = computed(() => {
	const unit = props.chart_config?.unit ?? "";
	const cats = props.chart_config?.categories?.length
		? props.chart_config.categories
		: [];
	const nSeries = props.series?.length ?? 0;
	return {
		chart: {
			stacked: true,
			stackType: "100%",
			toolbar: {
				show: false,
			},
		},
		colors: props.chart_config.types.includes("GuageChart")
			? [props.chart_config.color[0], "#777"]
			: props.chart_config.color,
		dataLabels: {
			textAnchor: "start",
		},
		grid: {
			show: false,
		},
		legend: {
			offsetY: 20,
			position: "top",
			show: nSeries > 2,
		},
		plotOptions: {
			bar: {
				borderRadius: 5,
				horizontal: true,
			},
		},
		stroke: {
			colors: ["#282a2c"],
			show: true,
			width: 2,
		},
		tooltip: {
			custom: function ({
				series,
				seriesIndex,
				dataPointIndex,
				w,
			}) {
				return (
					'<div class="chart-tooltip">' +
					"<h6>" +
					w.globals.seriesNames[seriesIndex] +
					"</h6>" +
					"<span>" +
					series[seriesIndex][dataPointIndex] +
					` ${unit}` +
					"</span>" +
					"</div>"
				);
			},
		},
		xaxis: {
			axisBorder: {
				show: false,
			},
			axisTicks: {
				show: false,
			},
			categories: cats,
			labels: {
				show: false,
			},
			type: "category",
		},
	};
});

const chartHeight = computed(() => {
	const n = props.series?.[0]?.data?.length ?? 0;
	return `${50 + n * 30}`;
});

const selectedIndex = ref(null);

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		// Supports filtering by xAxis + yAxis
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				config.w.globals.seriesNames[config.seriesIndex]
			);
		}
		// Supports filtering by xAxis
		else if (props.map_filter.mode === "byLayer") {
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
  <div
    v-if="activeChart === 'BarPercentChart'"
  >
    <VueApexCharts
      type="bar"
      width="100%"
      :height="chartHeight"
      :options="chartOptions"
      :series="series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>
