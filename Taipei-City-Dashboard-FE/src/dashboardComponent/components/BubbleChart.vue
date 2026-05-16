<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed } from "vue";
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

const yCategories = computed(() => {
	let categories = [];

	if (props.chart_config?.categories?.length) {
		categories = props.chart_config.categories;
	} else if ((props.series || []).some((item) => item.name)) {
		categories = (props.series || []).map((item) => item.name);
	} else {
		categories = (props.series?.[0]?.data || []).map((point) => point.x);
	}

	return [...new Set(categories.filter(Boolean))];
});

const chartOptions = computed(() => ({
	chart: {
		type: "bubble",
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
		padding: {
			left: 20,
			right: 20,
		},
	},
	legend: {
		show: true,
		labels: { colors: "var(--color-complement-text)" },
	},
	plotOptions: {
		bubble: {
			minBubbleRadius: 5,
			maxBubbleRadius: 5,
		},
	},
	stroke: {
		colors: ["#282a2c"],
		width: 1,
	},
	tooltip: {
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			const xValue = w.globals.seriesX[seriesIndex][dataPointIndex];
			const seriesName = w.globals.seriesNames[seriesIndex] || "";
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				seriesName +
				"</h6>" +
				"<span>" +
				`${xValue}` +
				"</span>" +
				"<span>" +
				`${props.chart_config.unit || "size"}` +
				"</span>" +
				"</div>"
			);
		},
	},
	...(props.chart_config?.yAxis ? { xaxis: props.chart_config.yAxis } : {}),
	yaxis: {

		categories: yCategories.value,
		tickAmount: yCategories.value.length - 1,
		labels: {
			style: { colors: "var(--color-complement-text)" },
			formatter: (val) => {
				const index = Math.round(val);
				return yCategories.value[index] ?? "";
			}
		},
	}
}));

function parseNumber(value) {
	const number = Number(value);
	return Number.isFinite(number) ? number : null;
}

function getYIndex(label, fallbackIndex) {
	const index = yCategories.value.indexOf(label);
	return index >= 0 ? index : fallbackIndex;
}

const localSeries = computed(() => {
	const hasChartCategories = props.chart_config?.categories?.length;

	return (props.series || []).flatMap((item, seriesIndex) => {
		if (item.name) {
			return [{
				name: item.name,
				data: (item.data || [])
					.map((point, pointIndex) => {
						const yLabel = hasChartCategories
							? props.chart_config.categories[pointIndex]
							: item.name;
						const x = parseNumber(typeof point === "object" ? point.y : point);
						if (x === null) return null;
						return {
							x,
							y: getYIndex(yLabel, seriesIndex),
							z: parseNumber(point?.z) ?? 10,
						};
					})
					.filter(Boolean),
			}];
		}
		return (item.data || []).map((point, index) => {
			const x = parseNumber(point.y);
			if (x === null) return null;
			return {
				name: point.x,
				data: [{
					x,
					y: getYIndex(point.x, index),
					z: parseNumber(point.z) ?? 10,
				}],
			};
		}).filter(Boolean);
	});
});
</script>

<template>
	<div v-if="activeChart === 'BubbleChart'">
		<VueApexCharts width="100%" height="250px" type="bubble" :options="chartOptions" :series="localSeries" />
	</div>
</template>