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

const hasCategories = computed(() => !!props.chart_config.categories);

const chartOptions = ref({
	chart: {
		offsetY: 15,
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: [...props.chart_config.color],
	dataLabels: {
		offsetX: 20,
		textAnchor: "start",
		enabled: !props.chart_config.categories,
	},
	grid: {
		show: false,
	},
	legend: {
		show: !!props.chart_config.categories,
	},
	plotOptions: {
		bar: {
			borderRadius: 2,
			distributed: !props.chart_config.categories,
			horizontal: true,
			dataLabels: {
				hideOverflowingLabels: false
			},
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 0,
	},
	// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
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
				w.globals.labels[dataPointIndex] +
				`${
					props.chart_config.categories
						? "-" + w.globals.seriesNames[seriesIndex]
						: ""
				}` +
				"</h6>" +
				"<span>" +
				series[seriesIndex][dataPointIndex] +
				` ${props.chart_config.unit}` +
				"</span>" +
				"</div>"
			);
		},
		followCursor: true,
	},
	xaxis: {
		axisBorder: {
			show: false,
		},
		axisTicks: {
			show: false,
		},
		categories: props.chart_config.categories
			? props.chart_config.categories
			: [],
		labels: {
			show: false,
		},
		type: "category",
	},
	yaxis: {
		labels: {
			formatter: function (value) {
				if (typeof value !== 'string') return value;
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
	},
});

const chartHeight = computed(() => {
	if (hasCategories.value) {
		return `${40 + props.chart_config.categories.length * 30}`;
	}
	return `${40 + props.series[0].data.length * 30}`;
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
  <div v-if="activeChart === 'BarChart'">
    <VueApexCharts
      width="100%"
      :height="chartHeight"
      type="bar"
      :options="chartOptions"
      :series="series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>
