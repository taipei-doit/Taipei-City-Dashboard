<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { computed, ref } from 'vue';

const props = defineProps(['chart_config', 'activeChart', 'series']);

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
			for (let i = 0; i < 12; i++) {
				if (!output[props.chart_config.categories[i]]) {
					output[props.chart_config.categories[i]] = 0;
				}
				output[props.chart_config.categories[i]] += +serie.data[i];
			}
		});
		highest = Object.values(output).sort(function (a, b) { return b - a; })[0];
		sum = Object.values(output).reduce((partialSum, a) => partialSum + a, 0);
	}

	output.highest = highest;
	output.sum = sum;
	return output;
});

const colorScale = computed(() => {
	const ranges = props.chart_config.color.map((el, index) => (
		{
			to: Math.round((heatmapData.value.highest / props.chart_config.color.length) * (props.chart_config.color.length - index)),
			from: Math.round((heatmapData.value.highest / props.chart_config.color.length) * (props.chart_config.color.length - index - 1)) + 1,
			color: el
		}
	)
	);
	ranges.unshift({
		to: 0,
		from: 0,
		color: "#444444"
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
			}
		},
	},
	stroke: {
		show: true,
		width: 2,
		colors: ['#282a2c'],
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return '<div class="chart-tooltip">' +
				'<h6>' + w.globals.labels[dataPointIndex] + `${props.chart_config.categories ? '-' + w.globals.seriesNames[seriesIndex] : ''}` + '</h6>' +
				'<span>' + series[seriesIndex][dataPointIndex] + ` ${props.chart_config.unit}` + '</span>' +
				'</div>';
		},
	},
	xaxis: {
		axisBorder: {
			show: false,
		},
		axisTicks: {
			show: false,
		},
		categories: props.chart_config.categories ? props.chart_config.categories : [],
		labels: {
			offsetY: 5,
			formatter: function (value) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			}
		},
		tooltip: {
			enabled: false
		},
		type: 'category',
	},
	yaxis: {
		max: function (max) {
			if (!props.chart_config.categories) {
				return max;
			}
			return heatmapData.value.highest;
		},
	}
});
</script>

<template>
	<div v-if="activeChart === 'HeatmapChart'" class="heatmapchart">
		<div class="heatmapchart-title">
			<h5>總合</h5>
			<h6>{{ heatmapData.sum }} {{ chart_config.unit }}</h6>
		</div>
		<apexchart width="100%" height="360px" type="heatmap" :options="chartOptions" :series="series"></apexchart>
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