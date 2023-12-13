<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { computed, ref } from "vue";
import { useMapStore } from "../../store/mapStore";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
]);

const mapStore = useMapStore();

const heatmapData = computed(() => {
	let output = {};
	let highest = 0;
	let sum = 0;
	if (props.series.length === 1) {
		props.series[0].data.forEach((item) => {
			output[item.x] = item.y;
			if (item.y > highest) {
				highest = item.y;
			}
			sum += item.y;
		});
	} else {
		props.series.forEach((serie) => {
			for (let i = 0; i < props.chart_config.categories.length; i++) {
				if (!output[props.chart_config.categories[i]]) {
					output[props.chart_config.categories[i]] = 0;
				}
				output[props.chart_config.categories[i]] += +serie.data[i];

				if (+serie.data[i] > highest) highest = +serie.data[i];
			}
		});
		sum = Object.values(output).reduce(
			(partialSum, a) => partialSum + a,
			0
		);
	}

	output.highest = highest;
	output.sum = sum;
	return output;
});

const colorScale = computed(() => {
	const ranges = props.chart_config.color.map((el, index) => ({
		to: Math.floor(
			(heatmapData.value.highest / props.chart_config.color.length) *
				(props.chart_config.color.length - index)
		),
		from:
			Math.floor(
				(heatmapData.value.highest / props.chart_config.color.length) *
					(props.chart_config.color.length - index - 1)
			) + 1,
		color: el,
	}));
	ranges.unshift({
		to: 0,
		from: 0,
		color: "#444444",
	});
	return ranges;
});

const chartOptions = ref({
	chart: {
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	dataLabels: {
		distributed: true,
		style: {
			fontSize: "12px",
			fontWeight: "normal",
		},
	},
	grid: {
		show: false,
	},
	legend: {
		show: false,
	},
	markers: {
		size: 3,
		strokeWidth: 0,
	},
	plotOptions: {
		heatmap: {
			enableShades: false,
			radius: 4,
			colorScale: {
				ranges: colorScale.value,
			},
		},
	},
	stroke: {
		show: true,
		width: 2,
		colors: ["#282a2c"],
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				`${w.globals.seriesNames[seriesIndex]}-${w.globals.labels[dataPointIndex]}` +
				"</h6>" +
				"<span>" +
				`${series[seriesIndex][dataPointIndex]}` +
				`${props.chart_config.unit}` +
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
			offsetY: 5,
			formatter: function (value) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
		tooltip: {
			enabled: false,
		},
		type: "category",
	},
	yaxis: {
		max: function (max) {
			if (!props.chart_config.categories) {
				return max;
			}
			return heatmapData.value.highest;
		},
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
	<div v-if="activeChart === 'HeatmapChart'" class="heatmapchart">
		<div class="heatmapchart-title">
			<h5>總合</h5>
			<h6>{{ heatmapData.sum }} {{ chart_config.unit }}</h6>
		</div>
		<apexchart
			width="100%"
			height="360px"
			type="heatmap"
			:options="chartOptions"
			:series="series"
			@dataPointSelection="handleDataSelection"
		></apexchart>
	</div>
</template>

<style scoped lang="scss">
.heatmapchart {
	&-title {
		display: flex;
		justify-content: center;
		flex-direction: column;
		margin: -0.2rem 0 -1.5rem;

		h5 {
			color: var(--color-complement-text);
		}

		h6 {
			color: var(--color-complement-text);
			font-size: var(--font-m);
			font-weight: 400;
		}
	}
}
</style>
