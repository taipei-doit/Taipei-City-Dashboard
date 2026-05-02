<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { ref, computed, watch } from "vue";
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
	"fly"
]);

const hasCategories = !!props.chart_config.categories;
const enableSeriesFilter = ref(false);
const selectedIndex = ref(null);

const showStacked = computed(() => hasCategories && enableSeriesFilter.value);
const singleColor = props.chart_config.color[Math.floor(props.chart_config.color.length / 2)];

const distributedColors = computed(() => {
	if (!props.series || !props.series[0]) return [singleColor];
	const dataLen = props.series[0].data.length;
	if (props.chart_config.color.length >= dataLen) {
		return props.chart_config.color.slice(0, dataLen);
	}
	return [singleColor];
});

const displaySeries = computed(() => {
	if (!hasCategories || enableSeriesFilter.value) {
		return props.series;
	}
	const aggregated = props.chart_config.categories.map((_, i) => {
		return props.series.reduce((sum, s) => sum + (s.data[i] || 0), 0);
	});
	return [{ data: aggregated }];
});

const chartOptions = computed(() => ({
	chart: {
		offsetY: hasCategories ? 0 : 15,
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: showStacked.value
		? [...props.chart_config.color]
		: hasCategories
			? [singleColor]
			: distributedColors.value,
	dataLabels: {
		offsetX: 20,
		textAnchor: "start",
		enabled: !showStacked.value,
	},
	grid: {
		show: false,
	},
	legend: {
		show: showStacked.value,
	},
	plotOptions: {
		bar: {
			borderRadius: 2,
			distributed: !showStacked.value,
			horizontal: true,
			dataLabels: {
				hideOverflowingLabels: false,
				total: {
					enabled: showStacked.value,
					offsetX: 10,
				},
			},
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 0,
	},
	tooltip: {
		custom: function ({
			series,
			seriesIndex,
			dataPointIndex,
			w,
		}) {
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				w.globals.labels[dataPointIndex] +
				(showStacked.value
					? "-" + w.globals.seriesNames[seriesIndex]
					: "") +
				"</h6>" +
				"<span>" +
				series[seriesIndex][dataPointIndex] +
				` ${props.chart_config.unit}` +
				"</span>" +
				"</div>"
			);
		},
		followCursor: true,
	},
	xaxis: {
		axisBorder: {
			show: false,
		},
		axisTicks: {
			show: false,
		},
		labels: {
			show: false,
		},
		categories: hasCategories ? props.chart_config.categories : [],
		type: "category",
	},
	yaxis: {
		labels: {
			formatter: function (value) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
	},
}));

const chartHeight = computed(() => {
	const dataLen = hasCategories
		? props.chart_config.categories.length
		: props.series[0].data.length;
	return `${40 + dataLen * 30}`;
});

watch(enableSeriesFilter, () => {
	if (selectedIndex.value !== null) {
		if (props.map_filter?.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
});

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (
		`${config.dataPointIndex}-${config.seriesIndex}` !== selectedIndex.value
	) {
		// Supports filtering by xAxis + yAxis
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				enableSeriesFilter.value
					? config.w.globals.seriesNames[config.seriesIndex]
					: null
			);
		}
		// Supports filtering by xAxis
		else if (props.map_filter.mode === "byLayer") {
			emits(
				"filterByLayer",
				props.map_config,
				config.w.globals.labels[config.dataPointIndex]
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
    v-if="activeChart === 'BarChart'"
    class="barchart-wrapper"
  >
    <label
      v-if="hasCategories"
      class="barchart-series-filter"
    >
      <input
        v-model="enableSeriesFilter"
        type="checkbox"
      >
      <span>顯示星級</span>
    </label>
    <VueApexCharts
      :key="`bar-${enableSeriesFilter}`"
      width="100%"
      :height="chartHeight"
      type="bar"
      :options="chartOptions"
      :series="displaySeries"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>

<style scoped>
.barchart-wrapper {
  display: flex;
  flex-direction: column;
}

.barchart-series-filter {
  display: flex;
  align-items: center;
  gap: 4px;
  order: 1;
  margin-top: -8px;
  cursor: pointer;
  user-select: none;
}

.barchart-series-filter input {
  cursor: pointer;
}

.barchart-series-filter span {
  font-size: var(--font-s, 12px);
  color: var(--color-complement-text, #888);
}
</style>
