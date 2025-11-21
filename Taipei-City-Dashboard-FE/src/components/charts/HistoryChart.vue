<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { timeTerms } from "../../assets/configs/AllTimes";

const props = defineProps(["chart_config", "series", "history_config"]);

const currentSeries = ref(0);

const chartOptions = ref({
	chart: {
		toolbar: {
			tools: {
				download: false,
				pan: false,
				reset: "<p>" + "重置" + "</p>",
				zoomin: false,
				zoomout: false,
			},
		},
	},
	colors: props.history_config.color[0]
		? props.history_config.color
		: props.chart_config.color,
	dataLabels: {
		enabled: false,
	},
	grid: {
		show: false,
	},
	legend: {
		show: true,
	},
	labels: {
		datetimeUTC: false,
	},
	markers: {
		hover: {
			size: 5,
		},
		size: 3,
		strokeWidth: 0,
	},
	stroke: {
		colors: props.history_config.color[0]
			? props.history_config.color
			: props.chart_config.color,
		curve: "smooth",
		show: true,
		width: 2,
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			// The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css
			return (
				'<div class="chart-tooltip">' +
				"<h6>" +
				`${parseTime(
					w.config.series[seriesIndex].data[dataPointIndex].x
				)}` +
				"</h6>" +
				"<span>" +
				series[seriesIndex][dataPointIndex] +
				` ${
					props.history_config.unit
						? props.history_config.unit
						: props.chart_config.unit
				}` +
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
			color: "#555",
		},
		crosshairs: {
			show: false,
		},
		tooltip: {
			enabled: false,
		},
		type: "datetime",
	},
});

function parseTime(time) {
	return time.replace("T", " ").replace("+08:00", " ");
}
</script>

<template>
  <div class="historychart">
    <div class="historychart-control">
      <button
        v-for="(key, index) in history_config.range"
        :key="key"
        :class="{ active: currentSeries === index }"
        @click="currentSeries = index"
      >
        {{ timeTerms[key] }}
      </button>
    </div>
    <div
      v-if="!props.series || !props.series[currentSeries]"
      class="historychart-error"
    >
      <span>error</span>
      <p>歷史資料異常</p>
    </div>
    <div
      v-else-if="props.series[currentSeries]"
      :style="{ width: '100%' }"
    >
      <apexchart
        width="100%"
        height="155px"
        type="area"
        :options="chartOptions"
        :series="series[currentSeries]"
      />
    </div>
    <div
      v-else
      class="historychart-error"
    >
      <span>error</span>
      <p>歷史資料異常</p>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.historychart {
	height: 200px;
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;

	&-control {
		width: 100%;
		display: flex;
		align-items: center;
		margin: 0.5rem 0;

		button {
			margin: 0 2px;
			padding: 4px 4px;
			border-radius: 5px;
			background-color: rgb(77, 77, 77);
			opacity: 0.6;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			text-align: center;
			transition: color 0.2s, opacity 0.2s;
			user-select: none;

			&:hover {
				opacity: 1;
				color: white;
			}
		}

		.active {
			background-color: var(--color-complement-text);
			color: white;
		}
	}

	&-error {
		height: 155px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;

		span {
			color: var(--color-complement-text);
			margin-bottom: 0.5rem;
			font-family: var(--font-icon);
			font-size: 2rem;
		}

		p {
			color: var(--color-complement-text);
		}
	}
}
</style>
