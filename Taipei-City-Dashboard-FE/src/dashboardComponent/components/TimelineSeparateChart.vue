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
		// chart_config.markerSize 可傳 number 或 number[]：傳陣列時逐 series 對應，
		// 0 代表該 series 不顯示 marker（用於虛線示意參考線，避免點點干擾視覺）
		size: props.chart_config?.markerSize ?? 3,
		strokeWidth: 0,
	},
	stroke: {
		colors: [...props.chart_config.color],
		curve: "smooth",
		show: true,
		width: 2,
		// 每條 series 各別的虛線樣式（0 = 實線，>0 = 虛線間隔）。例如「實際 / 目標 / 預測」
		// 三線並陳時可傳 [0, 6, 4]：實線 + 兩種虛線
		...(props.chart_config?.dashArray
			? { dashArray: props.chart_config.dashArray }
			: {}),
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
	// 預設 min:0；若 chart_config.yAxis 有給就 passthrough（如 c5b 碳足跡此類大基數小變化的 series 需 auto-scale）
	yaxis: props.chart_config?.yAxis ?? {
		min: 0,
	},
	// chart_config.yAxisAnnotations 可注入 y 軸 annotation band（如 c5b 雙城時用波浪帶遮中段空白）
	...(props.chart_config?.yAxisAnnotations
		? { annotations: { yaxis: props.chart_config.yAxisAnnotations } }
		: {}),
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
					// split("-")[0] 同時涵蓋 4 位西元（"2024-01-01" → "2024"）
					// 與 3 位民國（"113-01-01" → "113"）；slice(0,4) 對民國會誤抓 dash
					x: a.x.split("-")[0],
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

