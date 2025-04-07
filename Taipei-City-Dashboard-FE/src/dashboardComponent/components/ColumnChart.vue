<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

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
	"fly"
]);

const isLargeDataSet = computed(() => {
	return props.series[0].data.length > 12
})

// Calculate initial width for large datasets only
const initialWidth = computed(() => {
	const WIDTH_PER_ITEM = 32
	const itemCount = props.series[0].data.length;
	return itemCount * WIDTH_PER_ITEM;
});

const widthValue = ref(initialWidth.value);

// Convert to a string with unit for ApexCharts
const chartWidth = computed(() => {
	return isLargeDataSet.value ? `${widthValue.value}px` : "100%";
});


const chartOptions = ref({
	chart: {
		stacked: true,
		zoom: {
			allowMouseWheelZoom: false,
		},
		toolbar: isLargeDataSet.value 
			? {
				show: true,
				tools: {
					download: false,
					pan: false,
					reset: "<p>" + "重置" + "</p>",
					zoomin: false,
					zoomout: false,
				}
			  }
			: {
				show: false,
			}
	},
	colors: [...props.chart_config.color],
	dataLabels: {
		enabled: props.chart_config.categories ? false : true,
		offsetY: 20,
	},
	grid: {
		show: false,
	},
	legend: isLargeDataSet.value
		? {
			show: props.chart_config.categories ? true : false,
			horizontalAlign: "left",
			offsetX: 20,
			floating: true,
		  }
		: {
			show: props.chart_config.categories ? true : false,
		  },
	plotOptions: {
		bar: {
			borderRadius: 5,
			dataLabels: {
				hideOverflowingLabels: false
			},
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 2,
	},
	tooltip: {
		// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
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
						`${
							props.chart_config.categories
								? "-" + w.globals.seriesNames[seriesIndex]
								: ""
						}` +
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
			show: false,
		},
		axisTicks: {
			show: false,
		},
		categories: props.chart_config.categories
			? props.chart_config.categories
			: [],
		labels: {
			offsetY: 2,
		},
		type: "category",
	},
});

const selectedIndex = ref(null);

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
				config.w.globals.seriesNames[config.seriesIndex]
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

function increaseWidth() {
	widthValue.value += 50;
}

function decreaseWidth() {
	if (widthValue.value > 150) {
		widthValue.value -= 50;
	}
}

function resetWidth() {
	widthValue.value = initialWidth.value;
}
</script>

<template>
  <div
    v-if="activeChart === 'ColumnChart'"
    class="columnChart"
  >
    <div
      v-if="isLargeDataSet"
      class="columnChart-toolbar"
    >
      <p
        class="columnChart-toolbar-item"
        @click="increaseWidth"
      >
        <span>add</span>
      </p>
      <p
        class="columnChart-toolbar-item"
        @click="decreaseWidth"
      >
        <span>remove</span>
      </p>
      <p
        class="columnChart-toolbar-item reset"
        @click="resetWidth"
      >
        重置
      </p>
    </div>
    <VueApexCharts
      :key="chartWidth"
      type="bar"
      :width="chartWidth"
      height="250px"
      :options="chartOptions"
      :series="series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>

<style lang="scss" scoped>
.columnChart {
	overflow: auto;
	position: relative;
	height: 100%;

	.vue-apexcharts {
		justify-content: unset !important;
	}

	&-toolbar {
		position: sticky;
		top: 0;
		left: 0;
		z-index: 1;
		background-color: var(--color-component-background);
		display: flex;
		justify-content: flex-end;
		align-items: center;
		gap: 4px;

		&-item {
			cursor: pointer;
			font-size: var(--font-s);
			display: flex;
			justify-content: center;
			align-items: center;

			span {
				text-align: center;
				font-family: var(--font-icon);
				font-size: var(--font-ms);
				padding: 2px;
			}

			&.reset {
				color: var(--color-highlight)
			}
		}
	}
}
</style>

