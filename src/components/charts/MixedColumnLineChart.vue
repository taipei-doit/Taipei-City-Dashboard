<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref, computed } from "vue";

const props = defineProps(["chart_config", "activeChart", "series"]);

const parseSeries = computed(() => {
	return props.series.map((serie, index) => ({
		...serie,
		type: index === 0 ? "column" : index === 1 ? "line" : serie.type,
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
		// enabledOnSeries: [0],
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
		custom: function ({ series, dataPointIndex, w }) {
			const categoryLabel = w.globals.categoryLabels[dataPointIndex];
			let tooltipContent = "";

			for (let i = 0; i < w.globals.seriesNames.length; i++) {
				const seriesName = w.globals.seriesNames[i];
				const value = series[i][dataPointIndex];
				const unit = props.chart_config.units[i];

				if (series[i].length > 0) {
					tooltipContent += `<tr><td><h6>${seriesName}</h6></td><td>${value} ${unit}</td></tr>`;
				}
			}

			return `<div class="chart-tooltip">
				<h6>${categoryLabel}</h6>
				<table>${tooltipContent}</table>
			</div>`;
		},
	},
	states: {
		hover: {
			filter: {
				type: "none",
			},
		},
		active: {
			filter: {
				type: "none",
			},
		},
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
			// 	show: false,
			stroke: {
				color: "var(--color-complement-text)",
			},
		},
		tooltip: {
			enabled: false,
		},
	},
	yaxis: [
		{
			title: {
				text: props.series[0].name,
				style: {
					color: "var(--color-complement-text)",
				},
			},
			labels: {
				formatter: function (val) {
					return val.toFixed(0);
				},
			},
		},
		{
			opposite: true,
			title: {
				text: props.series?.[1]?.name ?? "",
				style: {
					color: "var(--color-complement-text)",
				},
			},
			labels: {
				formatter: function (val) {
					return val.toFixed(0);
				},
			},
		},
	],
});
</script>

<template>
	<div v-if="activeChart === 'MixedColumnLineChart'">
		<apexchart
			width="100%"
			height="260px"
			type="line"
			:options="chartOptions"
			:series="parseSeries"
		></apexchart>
	</div>
</template>
