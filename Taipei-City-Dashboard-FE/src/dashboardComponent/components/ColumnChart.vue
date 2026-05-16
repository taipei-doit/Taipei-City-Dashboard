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

// 線圖才會用 dashArray 標目標／參考線；柱狀圖呈現「目標」毫無意義（會變成 4 排無意義的 bar），
// 所以這裡用 dashArray > 0 作為過濾條件，保留 actual series、丟掉 reference 線。
// chart_config.color 也須同步過濾，避免色階對不上 series index。
const filteredSeries = computed(() => {
	const dashArr = props.chart_config?.dashArray;
	if (!Array.isArray(dashArr)) return props.series;
	return props.series.filter((_, i) => !dashArr[i]);
});
const filteredColors = (() => {
	const dashArr = props.chart_config?.dashArray;
	if (!Array.isArray(dashArr)) return [...props.chart_config.color];
	return props.chart_config.color.filter((_, i) => !dashArr[i]);
})();

const isLargeDataSet = computed(() => {
	return (filteredSeries.value?.[0]?.data?.length ?? 0) > 12;
})

// Calculate initial width for large datasets only
// 多 series（如雙北 grouped 模式）每個 category 槽位要塞下 N 條 bar + 間距，
// 寬度依 series 數縮放，否則年份標籤會擠在一起（C5 雙北 14 年 × 2 城就會發生）。
const initialWidth = computed(() => {
	const WIDTH_PER_ITEM = 32;
	const seriesCount = Math.max(1, filteredSeries.value?.length ?? 1);
	const itemCount = filteredSeries.value?.[0]?.data?.length ?? 0;
	return itemCount * WIDTH_PER_ITEM * seriesCount;
});

const widthValue = ref(initialWidth.value);

// Convert to a string with unit for ApexCharts
const chartWidth = computed(() => {
	return isLargeDataSet.value ? `${widthValue.value}px` : "100%";
});


const chartOptions = ref({
	chart: {
		// 預設 stacked；c5b 碳足跡這類雙城獨立量值需 grouped（並排）才看得出單城起伏
		stacked: props.chart_config?.stacked ?? true,
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
	colors: filteredColors,
	dataLabels: {
		enabled: props.chart_config.categories ? false : true,
		offsetY: 20,
	},
	grid: {
		show: false,
	},
	// 改回預設 bottom（不浮動）— floating 會壓到 x 軸年份標籤上，
	// 雙北兩條 series 並陳時會把「新北市-碳足跡」字疊在年份上看不清；
	// 對齊 TimelineSeparateChart 的左下角錨定，避免大圖捲動時 legend 飄到中段看不見。
	// showForSingleSeries: ApexCharts 預設單 series bar chart 不顯 legend，
	// 但 C5 切到單城時 filter 完只剩 1 條，仍需要顯「{city}-碳足跡」標籤
	legend: {
		show: props.chart_config.categories ? true : false,
		position: "bottom",
		horizontalAlign: "left",
		showForSingleSeries: true,
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
	// chart_config.yAxis 未設則交給 ApexCharts 預設（從 0 起）；c5b 大基數小變化要 auto-scale
	...(props.chart_config?.yAxis ? { yaxis: props.chart_config.yAxis } : {}),
	// chart_config.yAxisAnnotations 可注入 y 軸 annotation band（如 c5b 雙城時遮中段空白）
	...(props.chart_config?.yAxisAnnotations
		? { annotations: { yaxis: props.chart_config.yAxisAnnotations } }
		: {}),
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
      :series="filteredSeries"
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

