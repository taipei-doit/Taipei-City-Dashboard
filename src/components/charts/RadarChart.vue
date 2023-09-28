<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';

const props = defineProps(['chart_config', 'activeChart', 'series']);

const chartOptions = ref({
	chart: {
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: props.chart_config.color,
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
				connectorColors: '#444',
				strokeColors: '#555',
			},
		},
	},
	stroke: {
		show: true,
		width: 2,
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
		categories: props.chart_config.categories ? props.chart_config.categories : [],
		labels: {
			offsetY: 5,
			formatter: function (value) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			}
		},
		type: 'category',
	},
	yaxis: {
		axisBorder: {
			color: '#000',
		},
		labels: {
			formatter: (value) => { return ''; },
		},
		// To fix a bug when there is more than 1 series
		// Orginal behavior: max will default to the max sum of each series
		max: function (max) {
			if (!props.chart_config.categories) {
				return max;
			}
			let adjustedMax = 0;
			props.series.forEach((element) => {
				const maxOfSeries = Math.max.apply(null, element.data);
				if (maxOfSeries > adjustedMax) {
					adjustedMax = maxOfSeries;
				}
			});
			return adjustedMax * 1.1;
		},
	}
});
</script>

<template>
	<div v-if="activeChart === 'RadarChart'">
		<apexchart width="100%" height="270px" type="radar" :options="chartOptions" :series="series"></apexchart>
	</div>
</template>