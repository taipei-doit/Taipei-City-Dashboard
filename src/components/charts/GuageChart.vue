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

// Guage charts in apexcharts uses a slightly different data format from other chart types
// As such, the following parsing function are required
const parseSeries = computed(() => {
	let output = {};
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
	colors: props.chart_config.color,
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
				total: {
					color: "#888787",
					fontSize: "0.8rem",
					label: "平均",
					show: true,
				},
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

function handleDataSelection(e, chartContext, config) {
	if (!props.map_filter) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		// Supports filtering by xAxis
		if (props.map_filter.mode === "byParam") {
			mapStore.filterByParam(
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex]
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
	<div v-if="activeChart === 'GuageChart'">
		<apexchart
			width="80%"
			height="300px"
			type="radialBar"
			:options="chartOptions"
			:series="parseSeries.series"
			@dataPointSelection="handleDataSelection"
		>
		</apexchart>
	</div>
</template>
