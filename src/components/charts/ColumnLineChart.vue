<!-- Developed by Open Possible (台灣大哥大), Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<script setup>
import { ref, computed } from "vue";

const props = defineProps(["chart_config", "activeChart", "series"]);

const parseSeries = computed(() => {
	return props.series.map((serie, index) => ({
		...serie,
		type: index === 0 ? "column" : "line",
	}));
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
	colors: props.chart_config.color,
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
		colors: props.chart_config.color,
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
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
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
				color: "var(--color-complement-text)",
			},
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
	yaxis: [
		{
			labels: {
				formatter: function (val) {
					return val.toFixed(0);
				},
			},
			title: {
				text: props.series[0].name,
				style: {
					color: "var(--color-complement-text)",
				},
			},
		},
		{
			labels: {
				formatter: function (val) {
					return val.toFixed(0);
				},
			},
			opposite: true,
			title: {
				text: props.series?.[1]?.name ?? "",
				style: {
					color: "var(--color-complement-text)",
				},
			},
		},
	],
});

function parseTime(time) {
	return time.replace("T00:00:00+08:00", " ");
}
</script>

<template>
	<div v-if="activeChart === 'ColumnLineChart'">
		<apexchart
			width="100%"
			height="260px"
			type="line"
			:options="chartOptions"
			:series="parseSeries"
		></apexchart>
	</div>
</template>
