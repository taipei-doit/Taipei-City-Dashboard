<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
// import { MapConfig, MapFilter } from "../utilities/componentConfig";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps(["chart_config", "activeChart", "series"]);

// const emits = defineEmits([
// 	"filterByParam",
// 	"filterByLayer",
// 	"clearByParamFilter",
// 	"clearByLayerFilter",
// 	"fly"
// ]);

const chartOptions = ref({
	chart: {
		toolbar: {
			show: false,
			tools: {
				zoom: false,
			},
		},
	},
	colors: [...props.chart_config.color],
	dataLabels: {
		enabled: false,
	},
	grid: {
		show: false,
	},
	legend: {
		show: props.series.length > 1 ? true : false,
	},
	markers: {
		hover: {
			size: 5,
		},
		size: 3,
		strokeWidth: 0,
	},
	stroke: {
		colors: [...props.chart_config.color],
		curve: "smooth",
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
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				`${parseTime(
					w.config.series[seriesIndex].data[dataPointIndex].x
				)}` +
				` - ${w.globals.seriesNames[seriesIndex]}` +
				"</h6>" +
				"<span>" +
				series[seriesIndex][dataPointIndex] +
				` ${props.chart_config.unit}` +
				"</span>" +
				"</div>"
			);
		},
	},
	xaxis: {
		axisBorder: {
			color: "#555",
			height: "0.8",
		},
		axisTicks: {
			show: false,
		},
		crosshairs: {
			show: false,
		},
		labels: {
			datetimeUTC: false,
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
	yaxis: {
		min: 0,
	},
});

function parseTime(time) {
	return time.replace("T", " ").replace("+08:00", " ");
}
</script>

<template>
  <div v-if="activeChart === 'TimelineSeparateChart'">
    <VueApexCharts
      width="100%"
      height="260px"
      type="line"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

