<script setup>
import { computed } from "vue";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

const metricMeta = {
	"pH值": {
		key: "ph",
		label: "pH",
		unit: "",
		min: 6.5,
		max: 8.5,
		idealMin: 6.5,
		idealMax: 8.5,
		color: "#56B96D",
	},
	"濁度(NTU)": {
		key: "ntu",
		label: "濁度",
		unit: "NTU",
		min: 0,
		max: 2,
		idealMin: 0,
		idealMax: 2,
		color: "#24B0DD",
	},
	"餘氯(mg/L)": {
		key: "chlorine",
		label: "餘氯",
		unit: "mg/L",
		min: 0,
		max: 1,
		idealMin: 0.2,
		idealMax: 1,
		color: "#F8CF58",
	},
};

const metrics = computed(() => {
	const rows = props.series?.[0]?.data || [];
	return rows.map((row) => {
		const meta = metricMeta[row.x] || {
			label: row.x,
			unit: props.chart_config.unit || "",
			min: 0,
			max: Math.max(row.y, 1),
			idealMin: 0,
			idealMax: Math.max(row.y, 1),
			color: props.chart_config.color?.[0] || "#56B96D",
		};
		const value = Number(row.y || 0);
		const range = meta.max - meta.min || 1;
		const pct = Math.min(
			100,
			Math.max(0, ((value - meta.min) / range) * 100)
		);
		const idealLeft = Math.min(
			100,
			Math.max(0, ((meta.idealMin - meta.min) / range) * 100)
		);
		const idealWidth = Math.min(
			100 - idealLeft,
			Math.max(0, ((meta.idealMax - meta.idealMin) / range) * 100)
		);
		const status =
			value >= meta.idealMin && value <= meta.idealMax ? "正常" : "留意";

		return {
			...meta,
			value,
			formatted: Number.isInteger(value) ? value.toString() : value.toFixed(2),
			pct,
			idealLeft,
			idealWidth,
			status,
		};
	});
});
</script>

<template>
  <div
    v-if="activeChart === 'WaterQualityChart'"
    class="water-quality-chart"
  >
    <div
      v-for="metric in metrics"
      :key="metric.key"
      class="water-quality-chart__metric"
    >
      <div class="water-quality-chart__header">
        <div>
          <span class="water-quality-chart__label">{{ metric.label }}</span>
          <span class="water-quality-chart__status">{{ metric.status }}</span>
        </div>
        <div>
          <span
            class="water-quality-chart__value"
            :style="{ color: metric.color }"
          >{{ metric.formatted }}</span>
          <span class="water-quality-chart__unit">{{ metric.unit }}</span>
        </div>
      </div>
      <div class="water-quality-chart__track">
        <div
          class="water-quality-chart__ideal"
          :style="{
            left: `${metric.idealLeft}%`,
            width: `${metric.idealWidth}%`,
          }"
        />
        <div
          class="water-quality-chart__bar"
          :style="{
            width: `${metric.pct}%`,
            backgroundColor: metric.color,
          }"
        />
      </div>
      <div class="water-quality-chart__scale">
        <span>{{ metric.min }}</span>
        <span>{{ metric.max }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.water-quality-chart {
	display: grid;
	grid-template-columns: 1fr;
	gap: 0.75rem;
	height: 100%;
	padding: 0.25rem 0;
	color: var(--color-normal-text);

	&__metric {
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 0.45rem;
		min-height: 0;
		padding: 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: 5px;
		background: rgba(255, 255, 255, 0.03);
	}

	&__header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 0.5rem;
	}

	&__label {
		font-size: var(--font-s);
		color: var(--color-complement-text);
	}

	&__status {
		margin-left: 0.45rem;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		background: rgba(86, 185, 109, 0.14);
		color: #9dc56e;
		font-size: 0.72rem;
	}

	&__value {
		font-size: 1.55rem;
		font-weight: 700;
		line-height: 1;
	}

	&__unit {
		margin-left: 0.25rem;
		color: var(--color-complement-text);
		font-size: var(--font-s);
	}

	&__track {
		position: relative;
		height: 0.6rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.12);
	}

	&__ideal,
	&__bar {
		position: absolute;
		top: 0;
		bottom: 0;
		border-radius: 999px;
	}

	&__ideal {
		background: rgba(255, 255, 255, 0.18);
	}

	&__bar {
		left: 0;
	}

	&__scale {
		display: flex;
		justify-content: space-between;
		color: var(--color-complement-text);
		font-size: 0.75rem;
	}
}
</style>
