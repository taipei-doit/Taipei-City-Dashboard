<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from "vue";

const props = defineProps(["chart_config", "series", "history_data_color"]);

const chartOptions = ref({
	chart: {
		toolbar: {
			tools: {
				download: false,
				pan: false,
				reset: "<p>" + "重置" + "</p>",
				zoomin: false,
				zoomout: false,
			},
		},
	},
	colors: props.history_data_color
		? props.history_data_color
		: props.chart_config.color,
	dataLabels: {
		enabled: false,
	},
	grid: {
		show: false,
	},
	legend: {
		show: props.series.length > 1 ? true : false,
	},
	markers: {
		hover: {
			size: 5,
		},
		size: 3,
		strokeWidth: 0,
	},
	stroke: {
		colors: props.history_data_color
			? props.history_data_color
			: props.chart_config.color,
		curve: "smooth",
		show: true,
		width: 2,
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				`${parseTime(
					w.config.series[seriesIndex].data[dataPointIndex].x
				)}` +
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
			color: "#555",
			height: "0.8",
		},
		axisTicks: {
			color: "#555",
		},
		crosshairs: {
			show: false,
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
});

function parseTime(time) {
	return time.replace("T", " ").replace("+08:00", " ");
}
</script>

<template>
	<div>
		<apexchart
			width="100%"
			height="140px"
			type="area"
			:options="chartOptions"
			:series="series"
		></apexchart>
	</div>
</template>
