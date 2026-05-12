<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, computed } from "vue";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps(["chart_config", "activeChart", "series"]);

// const emits = defineEmits([
// 	"filterByParam",
// 	"filterByLayer",
// 	"clearByParamFilter",
// 	"clearByLayerFilter",
// 	"fly"
// ]);

// 資料格式：series = [{ name, data: [{ x, y, z }, ...] }]
// x 為類別／數值（依 chart_config.xType 決定），y 為主數值，z 為 bubble 半徑大小
const bubbleSeries = computed(() => {
	const cats = props.chart_config.categories || [];
	return props.series.map((s) => ({
		name: s.name,
		data: (s.data || []).map((y, i) => ({
			x: cats[i] ?? i,
			y: y,
			z: Math.max(2, Math.sqrt(Math.abs(y)) / 30),
		})),
	}));
});

const chartOptions = ref({
	chart: {
		type: "bubble",
		toolbar: { show: false },
	},
	colors: [...props.chart_config.color],
	dataLabels: {
		enabled: false,
	},
	fill: {
		opacity: 0.8,
	},
	grid: {
		show: true,
		borderColor: "#444",
	},
	legend: {
		show: props.series.length > 1,
		labels: { colors: "var(--color-complement-text)" },
	},
	stroke: {
		colors: ["#282a2c"],
		width: 1,
	},
	tooltip: {
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			const xValue = w.globals.seriesX[seriesIndex][dataPointIndex];
			const yValue = series[seriesIndex][dataPointIndex];
			const zValue = w.globals.seriesZ[seriesIndex][dataPointIndex];
			const seriesName = w.globals.seriesNames[seriesIndex] || "";
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				seriesName +
				"</h6>" +
				"<span>" +
				`x: ${xValue} ／ y: ${yValue}` +
				"</span>" +
				"<span>" +
				`${props.chart_config.unit || "size"}: ${zValue}` +
				"</span>" +
				"</div>"
			);
		},
	},
	xaxis: {
		tickAmount: props.chart_config.xTickAmount || 12,
		type: props.chart_config.xType || "category",
		labels: {
			style: { colors: "var(--color-complement-text)" },
		},
	},
	yaxis: {
		max: props.chart_config.yMax || undefined,
		labels: {
			style: { colors: "var(--color-complement-text)" },
		},
	},
});
</script>

<template>
  <div v-if="activeChart === 'BubbleChart'">
    <VueApexCharts
      width="100%"
      height="270px"
      type="bubble"
      :options="chartOptions"
      :series="bubbleSeries"
    />
  </div>
</template>
