<!-- Developed by Open Possible (台灣大哥大), Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<script setup lang="ts">
import { ref, computed } from "vue";
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

const parseSeries = computed(() => {
	return props.series.map(
		(
			serie: { name: string; data: { x: string; y: number }[] },
			index: number
		) => ({
			...serie,
			type: index === 0 ? "column" : "line",
		})
	);
});

const totalMax = computed(() => {
	if (props.series[0].name.slice(-2) === props.series[1].name.slice(-2)) {
		let max = Math.max(
			...props.series[0].data.map((d: { x: string; y: number }) => d.y),
			...props.series[1].data.map((d: { x: string; y: number }) => d.y)
		);

		// add 10% then round up to the nearest 100
		return Math.ceil((max * 1.1) / 100) * 100;
	}
	return null;
});

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
		show: true,
		markers: {
			radius: [0, 20],
		},
	},
	markers: {
		hover: {
			size: 4,
		},
		shape: "circle",
		size: 4,
		strokeWidth: 0,
	},
	stroke: {
		colors: [...props.chart_config.color],
		curve: "smooth",
		show: true,
		width: 2,
	},
	plotOptions: {
		column: {
			stacked: false,
			grouping: false,
		},
	},
	tooltip: {
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
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
			return (
				`<div class="chart-tooltip">` +
				`<h6>` +
				`${parseTime(w.config.series[0].data[dataPointIndex].x)} - ${
					w.globals.seriesNames[seriesIndex]
				}` +
				`</h6>` +
				`<span>${series[seriesIndex][dataPointIndex]} ${props.chart_config.unit}</span>` +
				`</div>`
			);
		},
		enabled: true,
		followCursor: true,
		intersect: true,
		shared: false,
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
			stroke: {
				color: "var(--dashboardcomponent-color-complement-text)",
			},
		},
		labels: {
			datetimeUTC: false,
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
	yaxis: [
		{
			min: 0,
			max: function (max: number) {
				if (totalMax.value) {
					return totalMax.value;
				}
				return max;
			},
			labels: {
				formatter: function (val: number) {
					return val.toFixed(0);
				},
			},
			title: {
				text: props.series[0].name,
				style: {
					color: "var(--dashboardcomponent-color-complement-text)",
				},
			},
		},
		{
			min: 0,
			max: function (max: string) {
				if (totalMax.value) {
					return totalMax.value;
				}
				return max;
			},
			labels: {
				formatter: function (val: number) {
					return val.toFixed(0);
				},
			},
			opposite: true,
			title: {
				text: props.series?.[1]?.name ?? "",
				style: {
					color: "var(--dashboardcomponent-color-complement-text)",
				},
			},
		},
	],
});

function parseTime(time: string) {
	return time.replace("T00:00:00+08:00", " ");
}
</script>

<template>
	<div v-if="activeChart === 'ColumnLineChart'">
		<VueApexCharts
			width="100%"
			height="260px"
			type="line"
			:options="chartOptions"
			:series="parseSeries"
		></VueApexCharts>
	</div>
</template>
