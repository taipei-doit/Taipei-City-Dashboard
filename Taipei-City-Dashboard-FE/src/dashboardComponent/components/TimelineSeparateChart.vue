<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup lang="ts">
import { ref } from "vue";
import { MapConfig, MapFilter } from "../utilities/componentConfig";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps(["chart_config", "activeChart", "series"]);

const emits = defineEmits<{
	(
		e: "filterByParam",
		map_filter: MapFilter,
		map_config: MapConfig[],
		x: string | null,
		y: string | null
	): void;
	(e: "filterByLayer", map_config: MapConfig[], x: string): void;
	(e: "clearByParamFilter", map_config: MapConfig[]): void;
	(e: "clearByLayerFilter", map_config: MapConfig[]): void;
	(e: "fly", location: any): void;
}>();

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
		}: {
			series: any;
			seriesIndex: any;
			dataPointIndex: any;
			w: any;
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

function parseTime(time: string) {
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
		></VueApexCharts>
	</div>
</template>

