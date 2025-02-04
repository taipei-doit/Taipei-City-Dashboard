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
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: [...props.chart_config.color],
	grid: {
		show: false,
	},
	legend: {
		show: props.chart_config.categories ? true : false,
	},
	markers: {
		size: 3,
		strokeWidth: 0,
	},
	plotOptions: {
		radar: {
			polygons: {
				connectorColors: "#444",
				strokeColors: "#555",
			},
		},
	},
	stroke: {
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
	},
	xaxis: {
		categories: props.chart_config.categories
			? props.chart_config.categories
			: [],
		labels: {
			offsetY: 5,
			formatter: function (value: string) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
		type: "category",
	},
	yaxis: {
		axisBorder: {
			color: "#000",
		},
		labels: {
			formatter: (_value: string) => {
				return "";
			},
		},
		// To fix a bug when there is more than 1 series
		// Orginal behavior: max will default to the max sum of each series
		max: function (max: number) {
			if (!props.chart_config.categories) {
				return max;
			}
			let adjustedMax = 0;
			props.series.forEach((element: { data: number[] }) => {
				const maxOfSeries = Math.max.apply(null, element.data);
				if (maxOfSeries > adjustedMax) {
					adjustedMax = maxOfSeries;
				}
			});
			return adjustedMax * 1.1;
		},
	},
});
</script>

<template>
	<div v-if="activeChart === 'RadarChart'">
		<VueApexCharts
			width="100%"
			height="270px"
			type="radar"
			:options="chartOptions"
			:series="series"
		></VueApexCharts>
	</div>
</template>
