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
	legend: {
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
			if (isLargeDataSet.value) {
				return (
					'<div class="chart-tooltip">' +
						"<h6>" +
							w.globals.categoryLabels[dataPointIndex] +
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
			} else {
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
			}
		},
	},
	xaxis: {
		...(isLargeDataSet.value && { tickPlacement: 'on' }),
		...(isLargeDataSet.value && { tickAmount: 12 }),
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
</script>

<template>
  <div
    v-if="activeChart === 'ColumnChart'"
  >
    <VueApexCharts
      type="bar"
      width="100%"
      height="250px"
      :options="chartOptions"
      :series="series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>

