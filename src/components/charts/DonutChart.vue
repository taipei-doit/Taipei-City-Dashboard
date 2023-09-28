<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { computed, defineProps, ref } from 'vue';
import { useMapStore } from '../../store/mapStore';

const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config']);
const mapStore = useMapStore();

// How many data points to show before summing all remaining points into "other"
const steps = ref(6);

// Donut charts in apexcharts uses a slightly different data format from other chart types
// As such, the following parsing functions are required
const parsedSeries = computed(() => {
	const toParse = [...props.series[0].data];
	if (toParse.length <= steps.value) {
		return toParse.map((item) => item.y);
	}
	let output = [];
	for (let i = 0; i < steps.value; i++) {
		output.push(toParse[i].y);
	}
	const toSum = toParse.splice(steps.value, toParse.length - steps.value);
	let sum = 0;
	toSum.forEach(element => sum += element.y);
	output.push(sum);
	return output;
});
const parsedLabels = computed(() => {
	const toParse = [...props.series[0].data];
	if (toParse.length <= steps.value) {
		return toParse.map((item) => item.x);
	}
	let output = [];
	for (let i = 0; i < steps.value; i++) {
		output.push(toParse[i].x);
	}
	output.push('其他');
	return output;
});
const sum = computed(() => {
	return Math.round(parsedSeries.value.reduce((a, b) => a + b) * 100) / 100;
});

// chartOptions needs to be in the bottom since it uses computed data
const chartOptions = ref({
	chart: {
		offsetY: 10,
	},
	colors: props.series.length >= steps.value ? [...props.chart_config.color, '#848c94'] : props.chart_config.color,
	dataLabels: {
		formatter: function (val, { seriesIndex, w }) {
			let value = w.globals.labels[seriesIndex];
			return value.length > 7 ? value.slice(0, 6) + "..." : value;
		},
	},
	labels: parsedLabels,
	legend: {
		show: false,
	},
	plotOptions: {
		pie: {
			dataLabels: {
				offset: 15,
			},
			donut: {
				size: '77.5%',
			},
		}
	},
	stroke: {
		colors: ['#282a2c'],
		show: true,
		width: 3,
	},
	tooltip: {
		followCursor: false,
		custom: function ({ series, seriesIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return '<div class="chart-tooltip">' +
				'<h6>' + w.globals.labels[seriesIndex] + '</h6>' +
				'<span>' + series[seriesIndex] + ` ${props.chart_config.unit}` + '</span>' +
				'</div>';
		},
	},
});

const selectedIndex = ref(null);

function handleDataSelection(e, chartContext, config) {
	if (!props.chart_config.map_filter) {
		return;
	}
	if (config.dataPointIndex !== selectedIndex.value) {
		mapStore.addLayerFilter(`${props.map_config[0].index}-${props.map_config[0].type}`, props.chart_config.map_filter[0], props.chart_config.map_filter[1][config.dataPointIndex]);
		selectedIndex.value = config.dataPointIndex;
	} else {
		mapStore.clearLayerFilter(`${props.map_config[0].index}-${props.map_config[0].type}`);
		selectedIndex.value = null;
	}
}
</script>

<template>
	<div v-if="activeChart === 'DonutChart'" class="donutchart">
		<apexchart width="100%" type="donut" :options="chartOptions" :series="parsedSeries"
			@dataPointSelection="handleDataSelection">
		</apexchart>
		<div class="donutchart-title">
			<h5>總合</h5>
			<h6>{{ sum }}</h6>
		</div>
	</div>
</template>

<style scoped lang="scss">
.donutchart {
	height: 100%;
	width: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
	position: relative;
	overflow-y: visible;

	&-title {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-direction: column;
		position: absolute;

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