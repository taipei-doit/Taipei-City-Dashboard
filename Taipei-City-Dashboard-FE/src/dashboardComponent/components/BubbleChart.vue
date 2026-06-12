<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps([
	"series",
	"chart_config",
	"activeChart",
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

const chartRef = ref(null);
const tooltip = ref({
	visible: false,
	x: 0,
	y: 0,
	placement: "right",
	name: "",
	point: null,
	categories: {},
});

const parsedUnit = JSON.parse(props.chart_config.unit);

function showTooltip({ name, point, categories }) {
	tooltip.value.visible = true;
	tooltip.value.name = name;
	tooltip.value.point = point;
	tooltip.value.categories = categories;
}

function hideTooltip() {
	tooltip.value.visible = false;
	tooltip.value.name = "";
	tooltip.value.point = null;
	tooltip.value.categories = {};
}

function onMouseMove(e) {
	if (tooltip.value.visible) {
		const chartRect = chartRef.value?.getBoundingClientRect();
		const chartCenterX = chartRect
			? chartRect.left + chartRect.width / 2
			: window.innerWidth / 2;
		const isRightSide = e.clientX > chartCenterX;

		tooltip.value.placement = isRightSide ? "left" : "right";
		tooltip.value.x = isRightSide ? e.clientX - 12 : e.clientX + 12;
		tooltip.value.y = e.clientY + 12;
	}
}

function onChartMouseMove(e) {
	if (!tooltip.value.visible) return;

	const { target } = e;
	const isBubblePoint =
		target instanceof Element && target.closest(".apexcharts-series");

	if (!isBubblePoint) {
		hideTooltip();
	}
}

function onWindowLeave() {
	hideTooltip();
}

onMounted(() => {
	window.addEventListener("mousemove", onMouseMove);
	window.addEventListener("blur", onWindowLeave);
});

onBeforeUnmount(() => {
	window.removeEventListener("mousemove", onMouseMove);
	window.removeEventListener("blur", onWindowLeave);
});

const chartOptions = ref({
	chart: {
		type: "bubble",
		zoom: { allowMouseWheelZoom: false },
		toolbar: { show: false },
		events: {
			mouseLeave: () => {
				hideTooltip();
			},
			dataPointMouseLeave: () => {
				hideTooltip();
			},
		},
	},

	plotOptions: {
		bubble: {
			minBubbleRadius: 5,
			maxBubbleRadius: 30,
		},
	},

	colors: props.map_config.color,
	dataLabels: { enabled: false },
	fill: { opacity: 0.7 },
	grid: { show: false },
	legend: { show: false },

	tooltip: {
		custom: ({ seriesIndex, dataPointIndex, w }) => {
			const { series } = w.config;
			const { name, data } = series[seriesIndex];
			const point = data[dataPointIndex];
			const categories = props.chart_config.categories ?? {};

			showTooltip({
				name: name ?? "",
				point,
				categories,
			});

			return `<div style="display:none;"></div>`;
		},
	},

	xaxis: {
		axisBorder: { show: true, color: "#666", height: 1 },
		axisTicks: { show: false },
		type: "numeric",
		tickAmount: 5,
		labels: {
			offsetY: 2,
			formatter: (val) => Number(val).toLocaleString(),
		},
	},

	yaxis: {
		axisBorder: { show: true, color: "#666" },
		labels: {
			formatter: (val) =>
				val >= 1000 ? `${(val / 1000).toFixed(0)}k` : `${val}`,
		},
	},
});

const allX = props.series.flatMap((s) => s.data.map((d) => d.x));
const allY = props.series.flatMap((s) => s.data.map((d) => d.y));

chartOptions.value.xaxis.min = Math.min(...allX) * 0.9;
chartOptions.value.xaxis.max = Math.max(...allX) * 1.1;
chartOptions.value.yaxis.min = Math.min(...allY) * 0.9;
chartOptions.value.yaxis.max = Math.max(...allY) * 1.1;

const selectedIndex = ref(null);

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) return;

	const key = `${config.dataPointIndex}-${config.seriesIndex}`;

	if (key !== selectedIndex.value) {
		const point =
			config.w.config.series[config.seriesIndex].data[
				config.dataPointIndex
			];

		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				point.x,
				config.w.globals.seriesNames[config.seriesIndex],
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits("filterByLayer", props.map_config, point.x);
		}

		selectedIndex.value = key;
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
		v-if="activeChart === 'BubbleChart'"
		ref="chartRef"
		class="bubbleChart"
		@mousemove="onChartMouseMove"
		@mouseleave="hideTooltip"
	>
		<VueApexCharts
			type="bubble"
			width="100%"
			height="100%"
			:options="chartOptions"
			:series="props.series"
			@data-point-selection="handleDataSelection"
		/>

		<Teleport to="body">
			<div
				v-if="tooltip.visible && tooltip.point"
				class="chart-tooltip"
				:style="{
					top: tooltip.y + 'px',
					left: tooltip.x + 'px',
					transform:
						tooltip.placement === 'left'
							? 'translateX(-100%)'
							: 'none',
				}"
			>
				<h6>{{ tooltip.name }}</h6>
				<div>
					{{ tooltip.categories[0] ?? "X" }}：{{ tooltip.point.x }}
					{{ parsedUnit.x ?? "" }}
				</div>
				<div>
					{{ tooltip.categories[1] ?? "Y" }}：{{ tooltip.point.y }}
					{{ parsedUnit.y ?? "" }}
				</div>
				<div>
					{{ tooltip.categories[2] ?? "Z" }}：{{ tooltip.point.z }}
					{{ parsedUnit.z ?? "" }}
				</div>
			</div>
		</Teleport>
	</div>
</template>

<style lang="scss" scoped>
.bubbleChart {
	position: relative;
	height: 90%;

	:deep(.apexcharts-tooltip) {
		display: none !important;
	}

	:deep(.apexcharts-tooltip-marker) {
		display: none !important;
	}
}
</style>

<style lang="scss">
.chart-tooltip {
	position: fixed;
	z-index: 9999;
	pointer-events: none;
	background: var(--color-background, #1e1e1e);
	color: var(--color-text, #ffffff);
	border: 1px solid var(--color-border, #444);
	border-radius: 4px;
	padding: 8px 12px;
	font-size: 0.85rem;
	line-height: 1.6;
	white-space: nowrap;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);

	h6 {
		margin: 0 0 4px 0;
		font-size: 0.9rem;
		font-weight: 600;
	}

	div {
		margin: 0;
	}
}
</style>
