<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, watch } from "vue";
// import { MapConfig, MapFilter } from "../utilities/componentConfig";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps(["chart_config", "activeChart", "series"]);

// const emits = defineEmits([
// 	"filterByParam",
// 	"filterByLayer",
// 	"clearByParamFilter",
// 	"clearByLayerFilter",
// 	"fly"
// ]);

// 原始資料拷貝避免更改原始資料
const localSeries = ref(JSON.parse(JSON.stringify(props.series)));

const chartOptions = ref({
	chart: {
		toolbar: {
			show: false,
			tools: {
				zoom: false,
			},
		},
	},
	colors: [...props.chart_config.color],
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
		colors: [...props.chart_config.color],
		curve: "smooth",
		show: true,
		width: 2,
	},
	tooltip: {
		custom: function ({
			series,
			seriesIndex,
			dataPointIndex,
			w,
		}) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				`${parseTime(
					w.config.series[seriesIndex].data[dataPointIndex].x
				)}` +
				` - ${w.globals.seriesNames[seriesIndex]}` +
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
			show: false,
		},
		crosshairs: {
			show: false,
		},
		labels: {
			datetimeUTC: false,
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
	yaxis: {
		min: 0,
	},
});


function parseTime(time) {
	return time.replace("T", " ").replace("+08:00", " ");
}

watch(
  () => props.series,
  (newVal) => {
    localSeries.value = JSON.parse(JSON.stringify(newVal || []));

    const timestamps = newVal?.[0]?.data?.map((p) => new Date(p.x).getTime()) || [];
    if (timestamps.length < 2) return;

    const newDiff = Math.max(...timestamps) - Math.min(...timestamps);

    // 跨度超過三年改成年份類別
    if (newDiff >= 3 * 31536000000) {
      localSeries.value.forEach((item) => {
        item.data = item.data.map((a) => ({
          ...a,
          x: a.x.slice(0, 4),
        }));
      });
      chartOptions.value = {
        ...chartOptions.value,
        xaxis: {
          ...chartOptions.value.xaxis,
          type: "category",
          tickAmount: Math.floor(newDiff / 31536000000),
        },
      };
    } else {
      chartOptions.value = {
        ...chartOptions.value,
        xaxis: {
          ...chartOptions.value.xaxis,
          type: "datetime",
          labels: { datetimeUTC: false },
        },
      };
    }
  },
  { deep: true, immediate: true }
);

</script>

<template>
  <div v-if="activeChart === 'TimelineSeparateChart'">
    <VueApexCharts
      width="100%"
      height="260px"
      type="line"
      :options="chartOptions"
      :series="localSeries"
    />
  </div>
</template>

