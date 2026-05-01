<script setup>
import { ref, computed } from "vue";
import BarChart from "./BarChart.vue";
import ColumnChart from "./ColumnChart.vue";
import DonutChart from "./DonutChart.vue";
import TreemapChart from "./TreemapChart.vue";
import PolarAreaChart from "./PolarAreaChart.vue";

/*
 * Data contract (map_legend query_type):
 *   props.series = [{ name, type, icon, value }, ...]
 *
 * Config:
 *   chart_config.types      = ["CascadeBarChart", "BarChart", ...]
 *   chart_config.categories = ["篩選一標籤", "篩選二標籤", "篩選三標籤"]
 *
 * Compatible sub-chart types (all use [{data:[{x,y}]}] format):
 *   ColumnChart, BarChart, DonutChart, TreemapChart, PolarAreaChart
 */
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
]);

// ── Normalize series ──────────────────────────────────────────────────────────
const normalizedSeries = computed(() =>
	(props.series || []).map((d) => ({
		name:  d.name  ?? d["縣市"] ?? "",
		type:  d.type  ?? d.x_axis  ?? "",
		icon:  d.icon  ?? "",
		value: d.value ?? d.y_axis  ?? 0,
	}))
);

// ── Filter labels ─────────────────────────────────────────────────────────────
const labels = computed(
	() => props.chart_config.categories ?? ["篩選一", "篩選二", "篩選三"]
);

// ── Filter state ──────────────────────────────────────────────────────────────
const sel1 = ref("");
const sel2 = ref("");
const sel3 = ref("");

// ── Option lists ──────────────────────────────────────────────────────────────
const opts1 = computed(() => [
	...new Set(normalizedSeries.value.map((d) => d.name).filter(Boolean)),
]);

const opts2 = computed(() => {
	const base = sel1.value
		? normalizedSeries.value.filter((d) => d.name === sel1.value)
		: normalizedSeries.value;
	return [...new Set(base.map((d) => d.type).filter(Boolean))];
});

const opts3 = computed(() => [
	...new Set(normalizedSeries.value.map((d) => d.icon).filter(Boolean)),
]);

const sel1Model = computed({
	get: () => sel1.value,
	set: (val) => {
		sel1.value = val;
		sel2.value = "";
	},
});

// ── Core filter ───────────────────────────────────────────────────────────────
const filteredData = computed(() =>
	normalizedSeries.value.filter((d) => {
		if (sel1.value && d.name !== sel1.value) return false;
		if (sel2.value && d.type !== sel2.value) return false;
		if (sel3.value && d.icon !== sel3.value) return false;
		return true;
	})
);

// ── Grouping ──────────────────────────────────────────────────────────────────
const groupKey = computed(() => {
	if (sel1.value && sel2.value) return "icon";
	if (sel1.value && opts2.value.length > 0) return "type";
	if (sel1.value) return "icon";
	return "name";
});

// ── Aggregated chart data [{x, y}] ────────────────────────────────────────────
const chartData = computed(() => {
	const totals = {};
	filteredData.value.forEach((d) => {
		const key = d[groupKey.value];
		totals[key] = (totals[key] || 0) + Number(d.value);
	});
	return Object.entries(totals).map(([label, total]) => ({
		x: label,
		y: total,
	}));
});

const subSeries = computed(() => [{ data: chartData.value }]);

// Strip categories so sub-charts use data's own x-axis labels, not the filter labels
const subChartConfig = computed(() => ({
	...props.chart_config,
	categories: undefined,
}));

// ── Sub-chart type selector ───────────────────────────────────────────────────
const COMPATIBLE = ["ColumnChart", "BarChart", "DonutChart", "TreemapChart", "PolarAreaChart"];
const chartLabelMap = {
	ColumnChart:   "縱向長條圖",
	BarChart:      "橫向長條圖",
	DonutChart:    "圓餅圖",
	TreemapChart:  "矩形圖",
	PolarAreaChart:"極座標圖",
};
const chartMap = { ColumnChart, BarChart, DonutChart, TreemapChart, PolarAreaChart };

const subChartOptions = computed(() =>
	(props.chart_config.types || [])
		.filter((t) => COMPATIBLE.includes(t))
		.map((t) => ({ key: t, label: chartLabelMap[t] }))
);

// Default: ColumnChart (縱向長條圖)
const selectedChart = ref("ColumnChart");
</script>

<template>
  <div
    v-if="activeChart === 'CascadeBarChart'"
    class="cascadebarchart"
  >
    <!-- 三層篩選器 -->
    <div class="cascadebarchart-filters">
      <label class="cascadebarchart-filter">
        <span>{{ labels[0] }}</span>
        <select v-model="sel1Model">
          <option value="">全部</option>
          <option
            v-for="opt in opts1"
            :key="opt"
            :value="opt"
          >
            {{ opt }}
          </option>
        </select>
      </label>

      <label class="cascadebarchart-filter">
        <span>{{ labels[1] }}</span>
        <select
          v-model="sel2"
          :disabled="!sel1 || opts2.length === 0"
        >
          <option value="">全部</option>
          <option
            v-for="opt in opts2"
            :key="opt"
            :value="opt"
          >
            {{ opt }}
          </option>
        </select>
      </label>

      <label class="cascadebarchart-filter">
        <span>{{ labels[2] }}</span>
        <select v-model="sel3">
          <option value="">全部</option>
          <option
            v-for="opt in opts3"
            :key="opt"
            :value="opt"
          >
            {{ opt }}
          </option>
        </select>
      </label>
    </div>

    <!-- 圖表類型切換（資料庫設定多個相容類型時才顯示） -->
    <div
      v-if="subChartOptions.length > 1"
      class="cascadebarchart-charttype"
    >
      <button
        v-for="opt in subChartOptions"
        :key="opt.key"
        :class="{ active: selectedChart === opt.key }"
        @click="selectedChart = opt.key"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- 圖表（委派給對應子元件，地圖事件往上轉發） -->
    <component
      :is="chartMap[selectedChart] ?? chartMap['ColumnChart']"
      v-if="chartData.length > 0"
      :active-chart="selectedChart"
      :chart_config="subChartConfig"
      :series="subSeries"
      :map_config="map_config"
      :map_filter="map_filter"
      :map_filter_on="map_filter_on"
      @filter-by-param="(...args) => emits('filterByParam', ...args)"
      @filter-by-layer="(...args) => emits('filterByLayer', ...args)"
      @clear-by-param-filter="(...args) => emits('clearByParamFilter', ...args)"
      @clear-by-layer-filter="(...args) => emits('clearByLayerFilter', ...args)"
    />
    <p
      v-else
      class="cascadebarchart-empty"
    >
      無符合條件的資料
    </p>
  </div>
</template>

<style scoped>
.cascadebarchart {
  padding: 0 0.5rem;
  overflow-x: auto;
}

.cascadebarchart-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.cascadebarchart-filter {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 100px;
}

.cascadebarchart-filter span {
  font-size: 0.7rem;
  color: var(--color-complement-text);
  letter-spacing: 0.5px;
}

.cascadebarchart-filter select {
  padding: 4px 8px;
  background: var(--color-component-background);
  color: var(--color-normal-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  width: 100%;
}

.cascadebarchart-filter select:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.cascadebarchart-charttype {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.cascadebarchart-charttype button {
  padding: 3px 8px;
  border-radius: 4px;
  background-color: rgb(77, 77, 77);
  color: var(--color-complement-text);
  font-size: var(--font-s);
  opacity: 0.6;
  cursor: pointer;
  border: none;
  transition: color 0.2s, opacity 0.2s;
}

.cascadebarchart-charttype button:hover {
  opacity: 1;
  color: white;
}

.cascadebarchart-charttype button.active {
  background-color: var(--color-complement-text);
  color: white;
  opacity: 1;
}

.cascadebarchart-empty {
  text-align: center;
  color: var(--color-complement-text);
  padding: 24px 0;
  font-size: 0.85rem;
}
</style>
