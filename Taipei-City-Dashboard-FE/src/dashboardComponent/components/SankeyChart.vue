<script setup>
import { computed, ref } from "vue";
import { hexToRGB } from "../../assets/utilityFunctions/colorConvert";
import SankeyCanvas from "./SankeyCanvas.vue";
// import { useDialogStore } from "../../store/dialogStore.js";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	// "map_filter",
	// "map_filter_on",
]);

// const dialogStore = useDialogStore();

// ── parsed series data ──────────────────────────────────────────────────────────────
const parsed_series = {
	categories: props.chart_config?.categories,
	data: props.series,
};

// ── Constants ──────────────────────────────────────────────────────────────
const NODE_W = 16;
const GAP = 4;
const PAD_TOP = 36;
const PAD_BOT = 6;
const PAD_L = 160;
const PAD_R = 180;
const SVG_H = 420;
const AVAIL_H = SVG_H - PAD_TOP - PAD_BOT;
const TOP_N = 14;
const NC = "#6b8fa3";

const COLOR_LOW = hexToRGB(props.chart_config.color?.[0]);
const COLOR_HIGH = hexToRGB(props.chart_config.color?.[1]);
const colorLowCss = `rgb(${+COLOR_LOW.r},${+COLOR_LOW.g},${+COLOR_LOW.b})`;
const colorHighCss = `rgb(${+COLOR_HIGH.r},${+COLOR_HIGH.g},${+COLOR_HIGH.b})`;

// ── State ──────────────────────────────────────────────────────────────────
const wrapperRef = ref(null);
const hoveredTip = ref(null);
const tipX = ref(0);
const tipY = ref(0);
const tipOnLeft = ref(false);
const isExpanded = ref(false);

// ── Helpers ────────────────────────────────────────────────────────────────
function flowColor(t) {
	const r = Math.round(+COLOR_LOW.r + (+COLOR_HIGH.r - +COLOR_LOW.r) * t);
	const g = Math.round(+COLOR_LOW.g + (+COLOR_HIGH.g - +COLOR_LOW.g) * t);
	const b = Math.round(+COLOR_LOW.b + (+COLOR_HIGH.b - +COLOR_LOW.b) * t);
	return `rgb(${r},${g},${b})`;
}

function positionNodes(topList, xPos) {
	if (!topList.length) return [];
	const total = topList.reduce((s, [, v]) => s + v, 0);
	const fillH = AVAIL_H - GAP * (topList.length - 1);
	let y = PAD_TOP;
	return topList.map(([name, flow]) => {
		const h = Math.max(3, (flow / total) * fillH);
		const node = { name, flow, x: xPos, y, h };
		y += h + GAP;
		return node;
	});
}

function onPathMouseMove({ event, tip }) {
	hoveredTip.value = tip;
	tipX.value = event.clientX;
	tipY.value = event.clientY;
	const rect = wrapperRef.value?.getBoundingClientRect();
	tipOnLeft.value = rect ? event.clientX > rect.left + rect.width / 2 : false;
}

function onPathMouseLeave() {
	hoveredTip.value = null;
}

function handleExpand() {
	// if (window.innerWidth < 770) {
	// 	dialogStore.showNotification("fail","放大檢視僅限電腦版！");
	// 	return;
	// }
	isExpanded.value = true;
}

// ── Layout ─────────────────────────────────────────────────────────────────
const layout = computed(() => {
	const raw = parsed_series;

	const layerLabels = raw.categories ?? [];
	const links = (raw.data ?? []).filter(
		(l) => l.source_layer != null && l.target_layer != null && l.source_layer !== l.target_layer,
	);

	const n =
		layerLabels.length ||
		links.reduce((m, l) => Math.max(m, l.source_layer, l.target_layer), 0) + 1;

	if (n < 2)
		return { svgW: 800, xPositions: [], nodesPerLayer: [], layerLabels, paths: [], n, padTop: PAD_TOP };

	const svgW = Math.max(800, PAD_L + PAD_R + n * 180);
	const usableW = svgW - PAD_L - PAD_R - NODE_W;
	const xPositions = Array.from({ length: n }, (_, i) =>
		Math.round(PAD_L + (n === 1 ? 0 : (i / (n - 1)) * usableW)),
	);

	const nodeFlow = Array.from({ length: n }, () => new Map());
	for (const l of links) {
		nodeFlow[l.source_layer].set(l.source, (nodeFlow[l.source_layer].get(l.source) || 0) + l.value);
		nodeFlow[l.target_layer].set(l.target, (nodeFlow[l.target_layer].get(l.target) || 0) + l.value);
	}

	const topPerLayer = nodeFlow.map((m) =>
		[...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, TOP_N),
	);
	const setPerLayer = topPerLayer.map((t) => new Set(t.map(([name]) => name)));

	const nodesPerLayer = topPerLayer.map((top, i) => positionNodes(top, xPositions[i]));
	const mapPerLayer = nodesPerLayer.map((nodes) => new Map(nodes.map((nd) => [nd.name, nd])));

	const aggMap = new Map();
	for (const l of links) {
		const sl = l.source_layer, tl = l.target_layer;
		if (!setPerLayer[sl].has(l.source) || !setPerLayer[tl].has(l.target)) continue;
		const key = `${sl}|${l.source}||${tl}|${l.target}`;
		const e = aggMap.get(key) ?? { source: l.source, source_layer: sl, target: l.target, target_layer: tl, value: 0 };
		e.value += l.value;
		aggMap.set(key, e);
	}
	const aggLinks = [...aggMap.values()].sort((a, b) => b.value - a.value);

	const allValues = aggLinks.map((l) => l.value);
	const minV = allValues.length ? Math.min(...allValues) : 0;
	const maxV = allValues.length ? Math.max(...allValues) : 1;
	const normalize = (v) => (maxV === minV ? 0.5 : (v - minV) / (maxV - minV));

	const usedRight = nodesPerLayer.map((nodes) => new Map(nodes.map((nd) => [nd.name, 0])));
	const usedLeft = nodesPerLayer.map((nodes) => new Map(nodes.map((nd) => [nd.name, 0])));

	const paths = [];
	for (const l of aggLinks) {
		const src = mapPerLayer[l.source_layer].get(l.source);
		const tgt = mapPerLayer[l.target_layer].get(l.target);
		if (!src || !tgt) continue;

		const lh = Math.min(
			Math.max(1, (l.value / (nodeFlow[l.source_layer].get(l.source) || l.value)) * src.h),
			Math.max(1, (l.value / (nodeFlow[l.target_layer].get(l.target) || l.value)) * tgt.h),
		);

		const sOff = usedRight[l.source_layer].get(l.source);
		const tOff = usedLeft[l.target_layer].get(l.target);
		const x1 = src.x + NODE_W, y1 = src.y + sOff;
		const x2 = tgt.x, y2 = tgt.y + tOff;
		const mx = (x1 + x2) / 2;

		paths.push({
			d: [
				`M ${x1} ${y1}`,
				`C ${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`,
				`L ${x2} ${y2 + lh}`,
				`C ${mx} ${y2 + lh} ${mx} ${y1 + lh} ${x1} ${y1 + lh}`,
				"Z",
			].join(" "),
			fill: flowColor(normalize(l.value)),
			opacity: 0.35 + normalize(l.value) * 0.35,
			tip:
				l.target_layer - l.source_layer > 1
					? `${l.source} → ${l.target}（跨 ${l.target_layer - l.source_layer} 層）：${l.value.toLocaleString()} 次`
					: `${l.source} → ${l.target}：${l.value.toLocaleString()} 次`,
		});

		usedRight[l.source_layer].set(l.source, sOff + lh);
		usedLeft[l.target_layer].set(l.target, tOff + lh);
	}

	return { svgW, xPositions, nodesPerLayer, layerLabels, paths, n, padTop: PAD_TOP };
});
</script>

<template>
  <div
    v-if="activeChart === 'SankeyChart'"
    ref="wrapperRef"
    class="sankey-wrapper"
  >
    <!-- Tooltip -->
    <div
      v-if="hoveredTip"
      class="sankey-tooltip"
      :style="
        tipOnLeft
          ? { left: tipX - 14 + 'px', top: tipY - 10 + 'px', transform: 'translateX(-100%)' }
          : { left: tipX + 14 + 'px', top: tipY - 10 + 'px' }
      "
    >
      {{ hoveredTip }}
    </div>

    <!-- 放大按鈕 -->
    <button
      class="expand-btn"
      title="放大檢視"
      @click="handleExpand"
    >
      <span>⛶</span>
    </button>

    <!-- 一般檢視 -->
    <SankeyCanvas
      :layout="layout"
      :svg-h="SVG_H"
      :node-w="NODE_W"
      :nc="NC"
      class="sankey-svg"
      @path-mousemove="onPathMouseMove"
      @path-mouseleave="onPathMouseLeave"
    />

    <!-- Legend -->
    <div class="sankey-legend">
      <span class="legend-label">低流量</span>
      <div
        class="legend-gradient"
        :style="`background: linear-gradient(to right, ${colorLowCss}, ${colorHighCss})`"
      />
      <span class="legend-label">高流量</span>
    </div>

    <!-- Fullscreen overlay -->
    <Teleport to="body">
      <div
        v-if="isExpanded"
        class="sankey-overlay"
        @click.self="isExpanded = false"
      >
        <div class="sankey-modal">
          <button
            class="modal-close-btn"
            @click="isExpanded = false"
          >
            ✕
          </button>

          <!-- Tooltip（共用同一份 ref） -->
          <div
            v-if="hoveredTip"
            class="sankey-tooltip"
            :style="
              tipOnLeft
                ? { left: tipX - 14 + 'px', top: tipY - 10 + 'px', transform: 'translateX(-100%)' }
                : { left: tipX + 14 + 'px', top: tipY - 10 + 'px' }
            "
          >
            {{ hoveredTip }}
          </div>

          <!-- 放大檢視 -->
          <SankeyCanvas
            :layout="layout"
            :svg-h="SVG_H"
            :node-w="NODE_W"
            :nc="NC"
            class="sankey-svg-full"
            @path-mousemove="onPathMouseMove"
            @path-mouseleave="onPathMouseLeave"
          />

          <div class="sankey-legend">
            <span class="legend-label">低流量</span>
            <div
              class="legend-gradient"
              :style="`background: linear-gradient(to right, ${colorLowCss}, ${colorHighCss})`"
            />
            <span class="legend-label">高流量</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped lang="scss">
.sankey-wrapper {
	position: relative;
	width: 100%;
	height: 90%;
	display: flex;
	flex-direction: column;
	gap: 4px;
	background: transparent;
}

.expand-btn {
	position: absolute;
	top: 4px;
	right: 4px;
	z-index: 5;
	background: transparent;
	border: 1px solid #555;
	border-radius: 4px;
	color: var(--color-text-secondary, #aaa);
	width: 26px;
	height: 26px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 14px;
	line-height: 1;
	padding: 0;
	transition: border-color 0.15s, color 0.15s;

	&:hover {
		border-color: #aaa;
		color: #fff;
	}
}

.sankey-svg {
	flex: 1;
	width: 100%;
	min-height: 0;
	display: block;
}

.sankey-tooltip {
	position: fixed;
	background: #282a2c;
	box-shadow: 0px 0px 5px black;
	color: #fff;
	padding: 3px 12px;
	border: 1px solid #666;
	border-radius: 4px;
	font-size: 0.875rem;
	pointer-events: none;
	white-space: nowrap;
	z-index: 9999;
}

.sankey-legend {
	display: flex;
	align-items: center;
	gap: 8px;
	justify-content: center;
	font-size: 0.72rem;
	color: var(--color-text-secondary, #aaa);
	flex-shrink: 0;
	margin: 16px;
}

.legend-label {
	white-space: nowrap;
}

.legend-gradient {
	width: 80px;
	height: 10px;
	border-radius: 3px;
}

// ── Fullscreen overlay ─────────────────────────────────────────────────────
.sankey-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.75);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
}

.sankey-modal {
	position: relative;
	background: #1a1c1e;
	border: 1px solid #444;
	border-radius: 8px;
	width: 75vw;
	aspect-ratio: 4 / 3;
	max-height: 75vh;
	display: flex;
	flex-direction: column;
	padding: 6vh 16px;
	box-sizing: border-box;
}

.modal-close-btn {
	position: absolute;
	top: 10px;
	right: 12px;
	background: transparent;
	border: 1px solid #555;
	border-radius: 4px;
	color: #aaa;
	width: 28px;
	height: 28px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 14px;
	z-index: 1;
	transition: border-color 0.15s, color 0.15s;

	&:hover {
		border-color: #aaa;
		color: #fff;
	}
}

.sankey-svg-full {
	flex: 1;
	width: 100%;
	min-height: 0;
	display: block;
}

@media (max-width: 770px) {
	.sankey-modal {
		display: none;
	}

	.expand-btn {
		display: none;
	}
}
</style>