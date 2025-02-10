<!-- Developed by Open Possible (台灣大哥大), Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<script setup lang="ts">
import { computed, ref } from "vue";
import { MapConfig, MapFilter } from "../utilities/componentConfig";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

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
	let parsedSeries = [];

	for (let i = 0; i < props.chart_config.categories.length; i++) {
		const goalItem = {
			name: "目標",
			value: props.series[0].data[i] + props.series[1].data[i],
			strokeWidth: 4,
			strokeColor: props.chart_config.color[1] || "#fff",
		};

		const parsedItem = {
			x: props.chart_config.categories[i],
			y: props.series[0].data[i],
			goals: [goalItem],
		};
		parsedSeries.push(parsedItem);
	}
	return [{ data: parsedSeries }];
});

const chartOptions = ref({
	chart: {
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: [props.chart_config.color[0]],
	dataLabels: {
		enabled: false,
	},
	grid: {
		show: false,
	},
	legend: {
		show: true,
		showForSingleSeries: true,
		customLegendItems: ["實際數值", "期望數值"],
		markers: {
			fillColors: [
				props.chart_config.color[0],
				props.chart_config.color[1] || "#fff",
			],
			radius: 0,
			height: [12, 4],
		},
	},
	plotOptions: {
		bar: {
			borderRadius: 4,
			distributed: true,
			horizontal: true,
		},
	},
	fill: {
		opacity: 1,
	},
	// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
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
			const label = w.globals.labels[dataPointIndex];
			const value = series[seriesIndex][dataPointIndex];
			const goalValue =
				w.globals.seriesGoals[seriesIndex][dataPointIndex]?.[0]?.value;

			return `
			<div class="chart-tooltip">
				<h6>${label}-實際數值</h6>
				<span>${value} ${props.chart_config.unit}</span>
				<h6>${label}-目標數值</h6>
				<span>${goalValue} ${props.chart_config.unit}</span>
			</div>`;
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
		labels: {
			show: true,
		},
		type: "category",
	},
	yaxis: {
		labels: {
			formatter: function (value: string) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
	},
});

const chartHeight = computed(() => {
	const height = 80 + props.series[0].data.length * 60;
	return height;
});
const selectedIndex = ref<null | string>(null);

function handleDataSelection(_e: any, _chartContext: any, config: any) {
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
				props.series[0].name // Only the first series can be clicked in apexcharts
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
		v-if="activeChart === 'BarChartWithGoal'"
		:style="{
			marginTop: `${
				chart_config.categories.length < 3
					? 90 - chart_config.categories.length * 30
					: 0
			}px`,
		}"
	>
		<VueApexCharts
			type="bar"
			width="100%"
			:height="chartHeight"
			:options="chartOptions"
			:series="parseSeries"
			@dataPointSelection="handleDataSelection"
		></VueApexCharts>
	</div>
</template>
