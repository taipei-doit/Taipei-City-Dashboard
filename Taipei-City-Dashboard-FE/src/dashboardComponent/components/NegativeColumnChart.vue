<!-- Developed by Bombs King, Taipei Codefest 2026 -->

<script setup>
import { computed, ref } from "vue";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

const emits = defineEmits([
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"fly",
]);

const categories = computed(() => {
	const data = props.series?.[0]?.data || [];
	return data.map((point) => point.x);
});

const values = computed(() => {
	const data = props.series?.[0]?.data || [];
	return data.map((point) => point.y);
});

const positiveColor = computed(() => {
	return props.chart_config?.color?.[0] || "#5a9cf8";
});

const negativeColor = computed(() => {
	return props.chart_config?.color?.[1] || "#e05a5a";
});

const perPointColors = computed(() => {
	return values.value.map((value) =>
		value < 0 ? negativeColor.value : positiveColor.value,
	);
});

const isLargeDataSet = computed(() => {
	return values.value.length > 12;
});

const yAxisMin = computed(() => {
	if (!values.value.length) return 0;
	return Math.min(0, ...values.value);
});

const yAxisMax = computed(() => {
	if (!values.value.length) return 0;
	return Math.max(0, ...values.value);
});

const yAxisTickAmount = computed(() => {
	const range = yAxisMax.value - yAxisMin.value;
	if (!Number.isFinite(range) || range <= 0) return 2;
	return Math.max(2, Math.ceil(range / 20000));
});

const baseWidth = computed(() => {
	const itemCount = values.value.length || 1;
	return itemCount * 20;
});

const scaleValue = ref(1);

const chartWidth = computed(() => {
	return isLargeDataSet.value
		? `${Math.max(1, baseWidth.value * scaleValue.value)}px`
		: "100%";
});

const chartSeries = computed(() => {
	return [
		{
			name: props.chart_config?.unit || "",
			data: values.value,
		},
	];
});

const chartOptions = computed(() => ({
	chart: {
		offsetY: 10,
		toolbar: {
			show: isLargeDataSet.value,
			tools: {
				download: false,
				pan: false,
				reset: "<p>重置</p>",
				zoomin: false,
				zoomout: false,
			},
		},
	},
	colors: perPointColors.value,
	dataLabels: {
		enabled: !isLargeDataSet.value || scaleValue.value >= 2,
		formatter: (val) => {
			if (val >= -4000 && val <= 4000) {
				return `${Math.round(val)}`;
			}
			return "";
		},
	},
	grid: {
		show: false,
	},
	annotations: {
		yaxis: [
			{
				y: 0,
				borderColor: "#8a8a8a",
				strokeWidth: 2,
				strokeDashArray: 0,
				opacity: 1,
			},
		],
	},
	legend: {
		show: false,
	},
	plotOptions: {
		bar: {
			horizontal: false,
			borderRadius: 2,
			distributed: true,
			dataLabels: {
				position: "top",
			},
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 1,
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex }) {
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				categories.value[dataPointIndex] +
				"</h6>" +
				"<span>" +
				series[seriesIndex][dataPointIndex] +
				` ${props.chart_config?.unit || ""}` +
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
		categories: categories.value,
		type: "category",
	},
	yaxis: {
		min: yAxisMin.value,
		max: yAxisMax.value,
		tickAmount: yAxisTickAmount.value,
		labels: {
			formatter: (value) => `${Math.round(value)}`,
		},
	},
}));

const selectedIndex = ref(null);

function increaseWidth() {
	scaleValue.value = Math.min(4, scaleValue.value + 0.25);
}

function decreaseWidth() {
	scaleValue.value = Math.max(0.5, scaleValue.value - 0.25);
}

function resetWidth() {
	scaleValue.value = 1;
}

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				categories.value[config.dataPointIndex],
				null,
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits(
				"filterByLayer",
				props.map_config,
				categories.value[config.dataPointIndex],
			);
		}
		selectedIndex.value = `${config.dataPointIndex}-${config.seriesIndex}`;
	} else {
		if (props.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
}
</script>

<template>
	<div
		v-if="activeChart === 'NegativeColumnChart'"
		class="negativeColumnChart"
	>
		<div v-if="isLargeDataSet" class="negativeColumnChart-toolbar">
			<p class="negativeColumnChart-toolbar-item" @click="increaseWidth">
				<span>add</span>
			</p>
			<p class="negativeColumnChart-toolbar-item" @click="decreaseWidth">
				<span>remove</span>
			</p>
			<p
				class="negativeColumnChart-toolbar-item reset"
				@click="resetWidth"
			>
				重置
			</p>
		</div>
		<VueApexCharts
			:key="chartWidth"
			:width="chartWidth"
			height="330"
			type="bar"
			:options="chartOptions"
			:series="chartSeries"
			@data-point-selection="handleDataSelection"
		/>
	</div>
</template>

<style scoped>
:deep(.apexcharts-yaxis-annotation line) {
	stroke-linecap: round;
}

.negativeColumnChart {
	overflow-x: auto;
	overflow-y: auto;
	position: relative;
	height: 100%;
}

.negativeColumnChart :deep(.vue-apexcharts) {
	justify-content: unset !important;
}

.negativeColumnChart-toolbar {
	position: sticky;
	top: 0;
	left: 0;
	z-index: 1;
	background-color: var(--color-component-background);
	display: flex;
	justify-content: flex-end;
	align-items: center;
	gap: 4px;
}

.negativeColumnChart-toolbar-item {
	cursor: pointer;
	font-size: var(--font-s);
	display: flex;
	justify-content: center;
	align-items: center;
}

.negativeColumnChart-toolbar-item span {
	text-align: center;
	font-family: var(--font-icon);
	font-size: var(--font-ms);
	padding: 2px;
}

.negativeColumnChart-toolbar-item.reset {
	color: var(--color-highlight);
}
</style>
