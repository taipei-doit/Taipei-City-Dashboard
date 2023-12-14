<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref, computed } from "vue";
import { useMapStore } from "../../store/mapStore";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
]);
const mapStore = useMapStore();

const chartOptions = ref({
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
		show: props.series.length > 2 ? true : false,
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
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				w.globals.seriesNames[seriesIndex] +
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
});

const chartHeight = computed(() => {
	return `${50 + props.series[0].data.length * 30}`;
});

const selectedIndex = ref(null);

function handleDataSelection(e, chartContext, config) {
	if (!props.map_filter) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		// Supports filtering by xAxis + yAxis
		if (props.map_filter.mode === "byParam") {
			mapStore.filterByParam(
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				config.w.globals.seriesNames[config.seriesIndex]
			);
		}
		// Supports filtering by xAxis
		else if (props.map_filter.mode === "byLayer") {
			mapStore.filterByLayer(
				props.map_config,
				config.w.globals.labels[config.dataPointIndex]
			);
		}
		selectedIndex.value = `${config.dataPointIndex}-${config.seriesIndex}`;
	} else {
		if (props.map_filter.mode === "byParam") {
			mapStore.clearByParamFilter(props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			mapStore.clearByLayerFilter(props.map_config);
		}
		selectedIndex.value = null;
	}
}
</script>

<template>
	<div v-if="activeChart === 'BarPercentChart'">
		<apexchart
			width="100%"
			:height="chartHeight"
			type="bar"
			:options="chartOptions"
			:series="series"
			@dataPointSelection="handleDataSelection"
		></apexchart>
	</div>
</template>
