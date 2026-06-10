<!-- Sankey Chart -->
<!--
  Generic Sankey chart type. Domain text/filters/colors driven by chart_config:
    chart_config.sankey_columns       string[3]  optional column header labels
    chart_config.sankey_filters       [{field,label}]  data-field-driven dropdowns
    chart_config.sankey_layer_labels  {raw: pretty}  pretty layer toggle labels
    chart_config.sankey_color_by      string  field name to color links by
    chart_config.sankey_color_map     {value: color}  explicit color override
    chart_config.color                string[]  fallback palette indexed by unique values
    chart_config.unit                 string  tooltip number suffix
  Each link in series requires: source, target, value, layer (string).
  Any extra fields can be referenced by sankey_filters / sankey_color_by.
  Layout assumes <= 2 distinct layer values forming a chain (col0 → col1 → col2).
-->
<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from "vue";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
	"mode",
]);

defineEmits([
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"fly",
]);

const NODE_W = 18;
const GAP = 4;
const PAD_TOP = 38;
const PAD_BOTTOM = 6;
const SVG_W_MIN = 1000;
const SVG_H_BASE = 420;
const DEFAULT_MAX_NODES = 25;
const FALLBACK_COLOR = "#888888";
const DEFAULT_PALETTE = ["#5b9fe8", "#f59e0b", "#22c55e", "#a855f7", "#ec4899", "#06b6d4"];

const containerRef = ref(null);
const containerWidth = ref(SVG_W_MIN);

let resizeObserver = null;
onMounted(() => {
	if (!containerRef.value || typeof ResizeObserver === "undefined") return;
	resizeObserver = new ResizeObserver((entries) => {
		for (const e of entries) {
			containerWidth.value = e.contentRect.width;
		}
	});
	resizeObserver.observe(containerRef.value);
});
onUnmounted(() => {
	resizeObserver?.disconnect();
	resizeObserver = null;
});

const svgWidth = computed(() => Math.max(containerWidth.value, SVG_W_MIN));
const X = computed(() => {
	const w = svgWidth.value;
	return [
		Math.round(w * 0.121),
		Math.round(w * 0.4375),
		Math.round(w * 0.863),
	];
});

const rawLinks = computed(() => {
	const s = props.series;
	if (!s) return [];
	if (Array.isArray(s)) {
		if (s.length && s[0]?.data && Array.isArray(s[0].data)) return s[0].data;
		return s;
	}
	if (s.links && Array.isArray(s.links)) return s.links;
	return [];
});

const sankeyColumns = computed(() => props.chart_config?.sankey_columns || []);
const filterFields = computed(() => props.chart_config?.sankey_filters || []);
const layerLabelMap = computed(() => props.chart_config?.sankey_layer_labels || {});
const unit = computed(() => props.chart_config?.unit || "");

function layerLabel(raw) {
	return layerLabelMap.value[raw] || raw;
}

const allLayerValues = computed(() => {
	const seen = new Set();
	const out = [];
	for (const l of rawLinks.value) {
		if (l.layer && !seen.has(l.layer)) {
			seen.add(l.layer);
			out.push(l.layer);
		}
	}
	return out;
});

const colorMap = computed(() => {
	const field = props.chart_config?.sankey_color_by;
	if (!field) return null;
	const explicit = props.chart_config?.sankey_color_map || {};
	const palette = props.chart_config?.color?.length
		? props.chart_config.color
		: DEFAULT_PALETTE;
	const seen = [];
	for (const l of rawLinks.value) {
		const v = l[field];
		if (v && !seen.includes(v)) seen.push(v);
	}
	const m = new Map();
	seen.forEach((v, i) => {
		m.set(v, explicit[v] || palette[i % palette.length] || FALLBACK_COLOR);
	});
	return m;
});

function getLinkColor(l) {
	const m = colorMap.value;
	if (!m) return FALLBACK_COLOR;
	const field = props.chart_config?.sankey_color_by;
	return m.get(l[field]) || FALLBACK_COLOR;
}

const filterValues = ref({});

watch(
	filterFields,
	(fields) => {
		for (const f of fields) {
			if (!(f.field in filterValues.value)) {
				filterValues.value[f.field] = "全部";
			}
		}
	},
	{ immediate: true, deep: true }
);

const filterOptionsByField = computed(() => {
	const out = {};
	for (const f of filterFields.value) {
		const seen = new Set();
		const list = [];
		for (const l of rawLinks.value) {
			const v = l[f.field];
			if (v !== undefined && v !== null && v !== "" && !seen.has(v)) {
				seen.add(v);
				list.push(v);
			}
		}
		list.sort();
		out[f.field] = ["全部", ...list];
	}
	return out;
});

const selectedLayer = ref("全部");
const tableLayer = ref("");
const hoveredTooltip = ref(null);

watch(
	allLayerValues,
	(layers) => {
		if (!tableLayer.value && layers.length) tableLayer.value = layers[0];
	},
	{ immediate: true }
);

const filteredLinks = computed(() => {
	let links = rawLinks.value;
	// Per-field filter: only drop links where field is present AND non-matching.
	// Links lacking the field are kept (filter is silent for them) so a field
	// that only exists on one layer doesn't wipe out the other layer.
	for (const f of filterFields.value) {
		const v = filterValues.value[f.field];
		if (!v || v === "全部") continue;
		links = links.filter((l) => {
			const lv = l[f.field];
			if (lv === undefined || lv === null || lv === "") return true;
			return lv === v;
		});
	}
	// Cascade across the 2-layer chain so the unfiltered layer narrows to
	// only links that connect to the filtered layer's surviving nodes.
	const layers = allLayerValues.value;
	if (layers.length === 2) {
		const [lA, lB] = layers;
		const aLinks = links.filter((l) => l.layer === lA);
		const bLinks = links.filter((l) => l.layer === lB);
		const aTargets = new Set(aLinks.map((l) => l.target));
		const bSources = new Set(bLinks.map((l) => l.source));
		const cascadedA = bLinks.length > 0
			? aLinks.filter((l) => bSources.has(l.target))
			: aLinks;
		const cascadedB = aLinks.length > 0
			? bLinks.filter((l) => aTargets.has(l.source))
			: bLinks;
		return [...cascadedA, ...cascadedB];
	}
	return links;
});

const tableRows = computed(() => {
	const links = filteredLinks.value.filter((l) => l.layer === tableLayer.value);
	return links
		.filter((l) => (l.value || 0) > 0)
		.sort((a, b) => (b.value || 0) - (a.value || 0))
		.slice(0, 200);
});

const layout = computed(() =>
	buildLayout(filteredLinks.value, selectedLayer.value, X.value, allLayerValues.value)
);

const svgHeight = computed(() => {
	const maxNodes = Math.max(
		layout.value.nodes0.length,
		layout.value.nodes1.length,
		layout.value.nodes2.length,
		1
	);
	return Math.max(SVG_H_BASE, maxNodes * 30 + 80);
});

function buildLayout(links, layerFilter, Xpos, layerVals) {
	const layerA = layerVals[0];
	const layerB = layerVals[1];

	const includeA = layerA && (layerFilter === "全部" || layerFilter === layerA);
	const includeB = layerB && (layerFilter === "全部" || layerFilter === layerB);

	const upMid = includeA ? links.filter((l) => l.layer === layerA) : [];
	const midDown = includeB ? links.filter((l) => l.layer === layerB) : [];

	const flow0 = new Map();
	const flow1mid = new Map();
	const flow1down = new Map();
	const flow2 = new Map();

	for (const l of upMid) {
		const v = l.value || 0;
		if (v <= 0) continue;
		flow0.set(l.source, (flow0.get(l.source) || 0) + v);
		flow1mid.set(l.target, (flow1mid.get(l.target) || 0) + v);
	}
	for (const l of midDown) {
		const v = l.value || 0;
		if (v <= 0) continue;
		flow1down.set(l.source, (flow1down.get(l.source) || 0) + v);
		flow2.set(l.target, (flow2.get(l.target) || 0) + v);
	}

	const flow1 = new Map();
	for (const [k, v] of flow1mid) flow1.set(k, v);
	for (const [k, v] of flow1down) flow1.set(k, Math.max(flow1.get(k) || 0, v));

	const configured = Number(props.chart_config?.sankey_max_nodes);
	const topN = Number.isFinite(configured) && configured > 0 ? configured : DEFAULT_MAX_NODES;

	function topNodes(flowMap) {
		return [...flowMap.entries()]
			.sort((a, b) => b[1] - a[1])
			.slice(0, topN);
	}

	const top0 = topNodes(flow0);
	const top1 = topNodes(flow1);
	const top2 = topNodes(flow2);
	const set0 = new Set(top0.map(([n]) => n));
	const set1 = new Set(top1.map(([n]) => n));
	const set2 = new Set(top2.map(([n]) => n));

	const maxNodes = Math.max(top0.length, top1.length, top2.length, 1);
	const dynamicH = Math.max(SVG_H_BASE, maxNodes * 30 + 80);
	const availableH = dynamicH - PAD_TOP - PAD_BOTTOM;

	function positionNodes(topList, xPos) {
		if (topList.length === 0) return [];
		const total = topList.reduce((s, [, v]) => s + v, 0);
		const gaps = GAP * (topList.length - 1);
		const fillH = availableH - gaps;
		let y = PAD_TOP;
		return topList.map(([name, flow]) => {
			const h = Math.max(3, (flow / total) * fillH);
			const node = { name, flow, x: xPos, y, h };
			y += h + GAP;
			return node;
		});
	}

	const nodes0 = positionNodes(top0, Xpos[0]);
	const nodes1 = positionNodes(top1, Xpos[1]);
	const nodes2 = positionNodes(top2, Xpos[2]);
	const map0 = new Map(nodes0.map((n) => [n.name, n]));
	const map1 = new Map(nodes1.map((n) => [n.name, n]));
	const map2 = new Map(nodes2.map((n) => [n.name, n]));

	function aggLinks(rawLinksArg, srcSet, tgtSet) {
		const agg = new Map();
		for (const l of rawLinksArg) {
			if (!srcSet.has(l.source) || !tgtSet.has(l.target)) continue;
			const v = l.value || 0;
			if (v <= 0) continue;
			const key = `${l.source}|${l.target}`;
			const entry = agg.get(key) || {
				source: l.source,
				target: l.target,
				value: 0,
				_origin: l,
			};
			entry.value += v;
			agg.set(key, entry);
		}
		return [...agg.values()].sort((a, b) => b.value - a.value);
	}

	const linksUM = aggLinks(upMid, set0, set1);
	const linksMD = aggLinks(midDown, set1, set2);

	const usedR0 = new Map(nodes0.map((n) => [n.name, 0]));
	const usedL1 = new Map(nodes1.map((n) => [n.name, 0]));
	const usedR1 = new Map(nodes1.map((n) => [n.name, 0]));
	const usedL2 = new Map(nodes2.map((n) => [n.name, 0]));

	function linkPx(val, nodeFlow, nodeH) {
		return Math.max(1, (val / nodeFlow) * nodeH);
	}

	function bezierPath(srcNode, srcOff, tgtNode, tgtOff, lh, color, tip) {
		const x1 = srcNode.x + NODE_W;
		const y1 = srcNode.y + srcOff;
		const x2 = tgtNode.x;
		const y2 = tgtNode.y + tgtOff;
		const mx = (x1 + x2) / 2;
		return {
			d: [
				`M ${x1} ${y1}`,
				`C ${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`,
				`L ${x2} ${y2 + lh}`,
				`C ${mx} ${y2 + lh} ${mx} ${y1 + lh} ${x1} ${y1 + lh}`,
				"Z",
			].join(" "),
			fill: color,
			tip,
		};
	}

	function tipText(l) {
		const num = (l.value || 0).toLocaleString();
		const suffix = unit.value ? ` ${unit.value}` : "";
		return `${l.source} → ${l.target}：${num}${suffix}`;
	}

	const paths = [];
	for (const l of linksUM) {
		const src = map0.get(l.source);
		const tgt = map1.get(l.target);
		if (!src || !tgt) continue;
		const lh = Math.min(
			linkPx(l.value, flow0.get(l.source) || l.value, src.h),
			linkPx(l.value, flow1mid.get(l.target) || l.value, tgt.h)
		);
		const color = getLinkColor(l._origin || l);
		paths.push(
			bezierPath(src, usedR0.get(l.source), tgt, usedL1.get(l.target), lh, color, tipText(l))
		);
		usedR0.set(l.source, usedR0.get(l.source) + lh);
		usedL1.set(l.target, usedL1.get(l.target) + lh);
	}
	for (const l of linksMD) {
		const src = map1.get(l.source);
		const tgt = map2.get(l.target);
		if (!src || !tgt) continue;
		const lh = Math.min(
			linkPx(l.value, flow1down.get(l.source) || l.value, src.h),
			linkPx(l.value, flow2.get(l.target) || l.value, tgt.h)
		);
		const color = getLinkColor(l._origin || l);
		paths.push(
			bezierPath(src, usedR1.get(l.source), tgt, usedL2.get(l.target), lh, color, tipText(l))
		);
		usedR1.set(l.source, usedR1.get(l.source) + lh);
		usedL2.set(l.target, usedL2.get(l.target) + lh);
	}

	return { nodes0, nodes1, nodes2, paths };
}

function truncate(str, max = 13) {
	if (!str) return "";
	return str.length > max ? str.slice(0, max) + "…" : str;
}

function tableHeaderSource(layerRaw) {
	const cols = sankeyColumns.value;
	if (!cols.length) return "Source";
	const idx = allLayerValues.value.indexOf(layerRaw);
	return cols[idx] || "Source";
}

function tableHeaderTarget(layerRaw) {
	const cols = sankeyColumns.value;
	if (!cols.length) return "Target";
	const idx = allLayerValues.value.indexOf(layerRaw);
	return cols[idx + 1] || "Target";
}

function nodeColor() {
	return "#6b8fa3";
}
</script>

<template>
  <div v-if="activeChart === 'SankeyChart'" class="sankey-wrapper">
    <!-- Table view (MoreInfo dialog) -->
    <template v-if="mode === 'large'">
      <div class="table-controls">
        <button
          v-for="lv in allLayerValues"
          :key="lv"
          :class="['layer-btn', { 'layer-btn-active': tableLayer === lv }]"
          @click="tableLayer = lv"
        >{{ layerLabel(lv) }}</button>
        <select
          v-for="f in filterFields"
          :key="`tbl-${f.field}`"
          v-model="filterValues[f.field]"
          class="sankey-select"
        >
          <option
            v-for="opt in filterOptionsByField[f.field] || []"
            :key="opt"
            :value="opt"
          >{{ opt === '全部' ? `${f.label || f.field}：全部` : opt }}</option>
        </select>
      </div>
      <div class="supply-table-wrap">
        <table class="supply-table">
          <thead>
            <tr>
              <th>{{ tableHeaderSource(tableLayer) }}</th>
              <th>{{ tableHeaderTarget(tableLayer) }}</th>
              <th>數值{{ unit ? `（${unit}）` : '' }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in tableRows" :key="i">
              <td>{{ row.source }}</td>
              <td>{{ row.target }}</td>
              <td class="count-cell">{{ (row.value || 0).toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Chart view (normal) -->
    <template v-else>
      <div class="sankey-controls">
        <div v-if="allLayerValues.length > 1" class="layer-btn-group">
          <button
            :class="['layer-btn', { 'layer-btn-active': selectedLayer === '全部' }]"
            @click="selectedLayer = '全部'"
          >全部</button>
          <button
            v-for="lv in allLayerValues"
            :key="lv"
            :class="['layer-btn', { 'layer-btn-active': selectedLayer === lv }]"
            @click="selectedLayer = lv"
          >{{ layerLabel(lv) }}</button>
        </div>
        <div class="sankey-selects">
          <select
            v-for="f in filterFields"
            :key="f.field"
            v-model="filterValues[f.field]"
            class="sankey-select"
          >
            <option
              v-for="opt in filterOptionsByField[f.field] || []"
              :key="opt"
              :value="opt"
            >{{ opt === '全部' ? `${f.label || f.field}：全部` : opt }}</option>
          </select>
        </div>
      </div>

      <div v-if="hoveredTooltip" class="sankey-tooltip">{{ hoveredTooltip }}</div>

      <div ref="containerRef" class="sankey-scroll">
        <svg
          :width="svgWidth"
          :height="svgHeight"
          :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
          class="sankey-svg"
        >
          <text
            v-if="sankeyColumns[0] && layout.nodes0.length"
            :x="X[0] + NODE_W / 2"
            :y="PAD_TOP - 14"
            class="layer-label"
          >{{ sankeyColumns[0] }}</text>
          <text
            v-if="sankeyColumns[1] && layout.nodes1.length"
            :x="X[1] + NODE_W / 2"
            :y="PAD_TOP - 14"
            class="layer-label"
          >{{ sankeyColumns[1] }}</text>
          <text
            v-if="sankeyColumns[2] && layout.nodes2.length"
            :x="X[2] + NODE_W / 2"
            :y="PAD_TOP - 14"
            class="layer-label"
          >{{ sankeyColumns[2] }}</text>

          <path
            v-for="(p, i) in layout.paths"
            :key="`p-${i}`"
            :d="p.d"
            :fill="p.fill"
            class="sankey-link"
            @mouseenter="hoveredTooltip = p.tip"
            @mouseleave="hoveredTooltip = null"
          />

          <g v-for="n in layout.nodes0" :key="`n0-${n.name}`">
            <rect :x="n.x" :y="n.y" :width="NODE_W" :height="n.h" :fill="nodeColor()" class="sankey-node" />
            <text :x="n.x - 5" :y="n.y + n.h / 2" text-anchor="end" dominant-baseline="middle" class="node-label">{{ truncate(n.name) }}</text>
          </g>
          <g v-for="n in layout.nodes1" :key="`n1-${n.name}`">
            <rect :x="n.x" :y="n.y" :width="NODE_W" :height="n.h" :fill="nodeColor()" class="sankey-node" />
            <text :x="n.x + NODE_W + 5" :y="n.y + n.h / 2" text-anchor="start" dominant-baseline="middle" class="node-label">{{ truncate(n.name) }}</text>
          </g>
          <g v-for="n in layout.nodes2" :key="`n2-${n.name}`">
            <rect :x="n.x" :y="n.y" :width="NODE_W" :height="n.h" :fill="nodeColor()" class="sankey-node" />
            <text :x="n.x + NODE_W + 5" :y="n.y + n.h / 2" text-anchor="start" dominant-baseline="middle" class="node-label">{{ truncate(n.name, 16) }}</text>
          </g>
        </svg>
      </div>

      <div v-if="colorMap && colorMap.size" class="sankey-legend">
        <span v-for="[val, color] in colorMap" :key="val">
          <i :style="`background:${color}`" />{{ val }}
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.sankey-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: transparent;
  overflow: visible;
}

.sankey-controls,
.table-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 0.5rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.layer-btn-group { display: flex; gap: 2px; }

.layer-btn {
  font-size: 0.72rem;
  padding: 2px 10px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #555);
  background: var(--color-component-background, #1e1e1e);
  color: var(--color-text-secondary, #aaa);
  cursor: pointer;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;

  &-active {
    background-color: var(--color-complement-text, #5b8db8);
    color: white;
    border-color: transparent;
  }
}

.sankey-selects { margin-left: auto; display: flex; gap: 6px; flex-wrap: wrap; }

.sankey-select {
  background-color: var(--color-component-background, #1e1e1e);
  color: var(--color-text, #eee);
  border: 1px solid var(--color-border, #555);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.72rem;
  cursor: pointer;
  &:focus { outline: none; }
}

.sankey-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;

  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--color-border, #555);
    border-radius: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.sankey-svg {
  display: block;
}

.sankey-link {
  opacity: 0.45;
  transition: opacity 0.15s;
  cursor: pointer;
  &:hover { opacity: 0.8; }
}

.sankey-node { rx: 2; }

.layer-label {
  fill: var(--color-text-secondary, #aaa);
  font-size: 13px;
  text-anchor: middle;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.node-label {
  fill: var(--color-text, #ddd);
  font-size: 11px;
  pointer-events: none;
}

.sankey-tooltip {
  position: absolute;
  top: 3.2rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.78rem;
  pointer-events: none;
  white-space: nowrap;
  z-index: 10;
}

.sankey-legend {
  display: flex;
  gap: 1rem;
  justify-content: center;
  font-size: 0.72rem;
  color: var(--color-text-secondary, #aaa);
  flex-shrink: 0;
  flex-wrap: wrap;

  span { display: flex; align-items: center; gap: 4px; }
  i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; }
}

.supply-table-wrap {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  padding: 0 0.5rem;
  min-height: 0;
}

.supply-table {
  min-width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;

  th {
    position: sticky;
    top: 0;
    background: var(--color-component-background, #1e1e1e);
    color: var(--color-text-secondary, #aaa);
    font-weight: 600;
    padding: 6px 10px;
    text-align: left;
    border-bottom: 1px solid var(--color-border, #444);
    white-space: nowrap;
  }

  td {
    padding: 5px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: var(--color-text, #ddd);
    vertical-align: middle;
    white-space: nowrap;
  }

  tr:hover td { background: rgba(255,255,255,0.04); }

  .count-cell {
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: var(--color-complement-text, #5b8db8);
  }
}
</style>
