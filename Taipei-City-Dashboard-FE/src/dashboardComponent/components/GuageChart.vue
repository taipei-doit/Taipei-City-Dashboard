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

// Guage charts in apexcharts uses a slightly different data format from other chart types
// As such, the following parsing function are required
const parseSeries = computed(() => {
	let output = {
		series: [],
		tooltipText: [],
	};
	let parsedSeries = [];
	let parsedTooltip = [];
	for (let i = 0; i < props.series[0].data.length; i++) {
		let total = props.series[0].data[i] + props.series[1].data[i];
		parsedSeries.push(Math.round((props.series[0].data[i] / total) * 100));
		parsedTooltip.push(`${props.series[0].data[i]} / ${total}`);
	}
	output.series = parsedSeries;
	output.tooltipText = parsedTooltip;
	return output;
});

// chartOptions needs to be in the bottom since it uses computed data
const chartOptions = ref({
	chart: {
		toolbar: {
			show: false,
		},
	},
	colors: [...props.chart_config.color],
	labels: props.chart_config.categories ? props.chart_config.categories : [],
	legend: {
		offsetY: -10,
		onItemClick: {
			toggleDataSeries: false,
		},
		position: "bottom",
		show: parseSeries.value.series.length > 1 ? true : false,
	},
	plotOptions: {
		radialBar: {
			dataLabels: {
				name: {
					color: "#888787",
					fontSize: "0.8rem",
				},
				// total: {
				// 	color: "#888787",
				// 	fontSize: "0.8rem",
				// 	label: "平均",
				// 	show: true,
				// },
				value: {
					color: "#888787",
					fontSize: "16px",
					offsetY: 5,
				},
			},
			track: {
				background: "#777",
			},
		},
	},
	tooltip: {
		custom: function ({ seriesIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				w.globals.seriesNames[seriesIndex] +
				"</h6>" +
				"<span>" +
				`${parseSeries.value.tooltipText[seriesIndex]}` +
				"</span>" +
				"</div>"
			);
		},
		enabled: true,
	},
});

const selectedIndex = ref(null);

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		// Supports filtering by xAxis and yAxis
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				props.series[0].name // You can only click on the first series in ApexCharts
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
  <div v-if="activeChart === 'GuageChart'">
    <VueApexCharts
      width="80%"
      height="300px"
      type="radialBar"
      :options="chartOptions"
      :series="parseSeries.series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>
