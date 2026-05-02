<script setup>
import { computed, ref } from "vue";

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
	"clearByParamFilter",
]);

const selectedCenter = ref(null);

const rows = computed(() => {
	const categories = props.chart_config.categories || [];
	const byMetric = {};
	for (const item of props.series || []) {
		byMetric[item.name] = item.data || [];
	}

	return categories.map((center, index) => {
		const swimCurrent = Number(byMetric["泳池目前人數"]?.[index] || 0);
		const swimCapacity = Number(byMetric["泳池容留人數"]?.[index] || 0);
		const gymCurrent = Number(byMetric["健身房目前人數"]?.[index] || 0);
		const gymCapacity = Number(byMetric["健身房容留人數"]?.[index] || 0);
		const swimRate = swimCapacity ? swimCurrent / swimCapacity : 0;
		const gymRate = gymCapacity ? gymCurrent / gymCapacity : 0;

		return {
			center,
			swimCurrent,
			swimCapacity,
			gymCurrent,
			gymCapacity,
			swimRate,
			gymRate,
			totalCurrent: swimCurrent + gymCurrent,
			totalCapacity: swimCapacity + gymCapacity,
		};
	});
});

const sortedRows = computed(() => {
	return [...rows.value].sort((a, b) => {
		const aRate = Math.max(a.swimRate, a.gymRate);
		const bRate = Math.max(b.swimRate, b.gymRate);
		return bRate - aRate || b.totalCurrent - a.totalCurrent;
	});
});

const totals = computed(() => {
	return rows.value.reduce(
		(sum, row) => ({
			swimCurrent: sum.swimCurrent + row.swimCurrent,
			swimCapacity: sum.swimCapacity + row.swimCapacity,
			gymCurrent: sum.gymCurrent + row.gymCurrent,
			gymCapacity: sum.gymCapacity + row.gymCapacity,
		}),
		{
			swimCurrent: 0,
			swimCapacity: 0,
			gymCurrent: 0,
			gymCapacity: 0,
		},
	);
});

function percent(value) {
	return `${Math.min(100, Math.max(0, value * 100)).toFixed(0)}%`;
}

function status(rate, capacity) {
	if (!capacity) return "未提供";
	if (rate >= 0.85) return "接近滿載";
	if (rate >= 0.6) return "人流偏高";
	return "可使用";
}

function statusClass(rate, capacity) {
	if (!capacity) return "is-muted";
	if (rate >= 0.85) return "is-high";
	if (rate >= 0.6) return "is-medium";
	return "is-low";
}

function handleSelect(center) {
	if (!props.map_filter || !props.map_filter_on) return;
	if (selectedCenter.value === center) {
		selectedCenter.value = null;
		emits("clearByParamFilter", props.map_config);
		return;
	}
	selectedCenter.value = center;
	emits("filterByParam", props.map_filter, props.map_config, center, null);
}
</script>

<template>
  <div
    v-if="activeChart === 'SportsVenueCapacityChart'"
    class="sports-capacity-chart"
  >
    <div class="sports-capacity-chart__summary">
      <div>
        <span>泳池</span>
        <strong>{{ totals.swimCurrent }}</strong>
        <small>/ {{ totals.swimCapacity }} 人</small>
      </div>
      <div>
        <span>健身房</span>
        <strong>{{ totals.gymCurrent }}</strong>
        <small>/ {{ totals.gymCapacity }} 人</small>
      </div>
    </div>

    <div class="sports-capacity-chart__list">
      <button
        v-for="row in sortedRows"
        :key="row.center"
        class="sports-capacity-chart__row"
        :class="{ 'is-selected': selectedCenter === row.center }"
        @click="handleSelect(row.center)"
      >
        <div class="sports-capacity-chart__row-head">
          <strong>{{ row.center }}</strong>
          <span>{{ row.totalCurrent }} / {{ row.totalCapacity }} 人</span>
        </div>

        <div class="sports-capacity-chart__metric">
          <div>
            <span>泳池</span>
            <small :class="statusClass(row.swimRate, row.swimCapacity)">
              {{ status(row.swimRate, row.swimCapacity) }}
            </small>
            <em>{{ row.swimCurrent }} / {{ row.swimCapacity }}</em>
          </div>
          <div class="sports-capacity-chart__track">
            <i
              class="is-swim"
              :style="{ width: percent(row.swimRate) }"
            />
          </div>
        </div>

        <div class="sports-capacity-chart__metric">
          <div>
            <span>健身房</span>
            <small :class="statusClass(row.gymRate, row.gymCapacity)">
              {{ status(row.gymRate, row.gymCapacity) }}
            </small>
            <em>{{ row.gymCurrent }} / {{ row.gymCapacity }}</em>
          </div>
          <div class="sports-capacity-chart__track">
            <i
              class="is-gym"
              :style="{ width: percent(row.gymRate) }"
            />
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.sports-capacity-chart {
	display: flex;
	flex-direction: column;
	gap: 0.65rem;
	height: 100%;
	overflow: visible;
	color: var(--color-normal-text);

	&__summary {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.5rem;
		flex: 0 0 auto;

		div {
			min-width: 0;
			padding: 0.55rem 0.65rem;
			border: 1px solid var(--color-border);
			border-radius: 5px;
			background: rgba(255, 255, 255, 0.04);
		}

		span,
		small {
			display: block;
			color: var(--color-complement-text);
			font-size: var(--font-s);
			line-height: 1.2;
		}

		strong {
			display: inline-block;
			margin-top: 0.2rem;
			font-size: 1.35rem;
			line-height: 1;
		}
	}

	&__list {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		min-height: 0;
		overflow-y: auto;
		padding-right: 0.15rem;
	}

	&__row {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		width: 100%;
		padding: 0.55rem 0.65rem;
		border: 1px solid var(--color-border);
		border-radius: 5px;
		background: rgba(255, 255, 255, 0.03);
		color: inherit;
		text-align: left;
		overflow: visible;

		&.is-selected,
		&:hover {
			border-color: rgba(36, 176, 221, 0.75);
			background: rgba(36, 176, 221, 0.08);
		}
	}

	&__row-head,
	&__metric > div:first-child {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		min-width: 0;
	}

	&__row-head {
		overflow: visible;

		strong {
			font-size: var(--font-s);
			line-height: 1.2;
			white-space: nowrap;
			text-overflow: ellipsis;
			overflow: hidden;
			min-width: 0;
			flex: 1 1 auto;
		}

		span {
			flex: 0 0 auto;
			color: var(--color-complement-text);
			font-size: var(--font-s);
		}
	}

	&__metric {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;

		span,
		em,
		small {
			font-size: 0.75rem;
			line-height: 1.15;
			font-style: normal;
		}

		span {
			color: var(--color-complement-text);
		}

		em {
			color: var(--color-normal-text);
		}

		small {
			margin-left: auto;
			padding: 0.08rem 0.32rem;
			border-radius: 3px;
			color: #ffffff;

			&.is-low {
				background: rgba(86, 185, 109, 0.42);
			}

			&.is-medium {
				background: rgba(248, 207, 88, 0.42);
			}

			&.is-high {
				background: rgba(237, 106, 69, 0.5);
			}

			&.is-muted {
				background: rgba(143, 152, 163, 0.45);
			}
		}
	}

	&__track {
		position: relative;
		height: 0.42rem;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.12);

		i {
			position: absolute;
			inset: 0 auto 0 0;
			border-radius: inherit;

			&.is-swim {
				background: #24b0dd;
			}

			&.is-gym {
				background: #ed6a45;
			}
		}
	}
}
</style>
