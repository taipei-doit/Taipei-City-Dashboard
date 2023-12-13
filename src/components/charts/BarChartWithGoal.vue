<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { computed, ref } from "vue";
import { useMapStore } from "../../store/mapStore";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
]);
const mapStore = useMapStore();

const goalColor = "#fff";
const defaultLabels = ["實際數值", "期望數值"];

const parseSeries = computed(() => {
	if (props.series[0].data[0].goal) {
		let parsedSeries = [];
		let colors = [];
		let allGoalsNotMet = true;
		const inputData = props.series[0].data;
		for (let i = 0; i < inputData.length; i++) {
			const item = inputData[i];
			const goalItem = {
				name: "目標",
				value: item.goal,
				strokeWidth: 4,
				strokeColor: goalColor,
			};

			const parsedItem = {
				x: item.x,
				y: item.y,
				goals: [goalItem],
			};
			parsedSeries.push(parsedItem);
			if (item.y > item.goal) {
				allGoalsNotMet = false;
				colors.push(props.chart_config.color[1]);
			} else {
				colors.push(props.chart_config.color[0]);
			}
		}
		if (allGoalsNotMet) {
			colors = props.chart_config.color;
		}
		return {
			colors,
			series: [{ name: "", data: parsedSeries }],
		};
	} else {
		return { series: props.series };
	}
});

const chartOptions = ref({
	chart: {
		stacked: true,
		toolbar: {
			show: false,
		},
	},
	colors: parseSeries.value.colors ?? props.chart_config.color,
	dataLabels: {
		enabled: false,
	},
	grid: {
		show: false,
	},
	legend: {
		show: true,
		showForSingleSeries: true,
		customLegendItems: props.chart_config.categories ?? defaultLabels,
		markers: {
			fillColors: [props.chart_config.color[1], goalColor],
			radius: 0,
			height: [12, 4],
		},
	},
	plotOptions: {
		bar: {
			borderRadius: 4,
			distributed: true,
			horizontal: true,
		},
	},
	fill: {
		opacity: 1,
	},
	// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			const label = w.globals.labels[dataPointIndex];
			const category1 =
				props.chart_config.categories?.[0] ?? defaultLabels[0];
			const category2 =
				props.chart_config.categories?.[1] ?? defaultLabels[1];
			const value = series[seriesIndex][dataPointIndex];
			const goalValue =
				w.globals.seriesGoals[seriesIndex][dataPointIndex]?.[0]?.value;

			const goalHtml = goalValue
				? `<td><span>${goalValue} ${props.chart_config.unit}</span></td>`
				: "";

			return `
			<div class="chart-tooltip">
				<h6>${label}</h6>
				<table>
					<tr>
						<td><h6>${category1}</h6></td>
						<td><span>${value} ${props.chart_config.unit}</span></td>
					</tr>
					<tr>
						<td><h6>${category2}</h6></td>
						${goalHtml}
					</tr>
				</table>
			</div>`;
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
			show: true,
		},
		type: "category",
	},
	yaxis: {
		labels: {
			formatter: function (value) {
				return value.length > 7 ? value.slice(0, 6) + "..." : value;
			},
		},
	},
});

const chartHeight = computed(() => {
	const height = 80 + props.series[0].data.length * 36;
	return `${Math.min(height, 260)}`;
});
const selectedIndex = ref(null);

function handleDataSelection(e, chartContext, config) {
	if (!props.chart_config.map_filter) {
		return;
	}
	if (config.dataPointIndex !== selectedIndex.value) {
		mapStore.addLayerFilter(
			`${props.map_config[0].index}-${props.map_config[0].type}`,
			props.chart_config.map_filter[0],
			props.chart_config.map_filter[1][config.dataPointIndex]
		);
		selectedIndex.value = config.dataPointIndex;
	} else {
		mapStore.clearLayerFilter(
			`${props.map_config[0].index}-${props.map_config[0].type}`
		);
		selectedIndex.value = null;
	}
}
</script>

<template>
	<div v-if="activeChart === 'BarChartWithGoal'">
		<apexchart
			width="100%"
			:height="chartHeight"
			type="bar"
			:options="chartOptions"
			:series="parseSeries.series"
			@dataPointSelection="handleDataSelection"
		></apexchart>
	</div>
</template>
