<script setup>
import { computed } from "vue";

const props = defineProps({
	layout: { type: Object, required: true },
	svgH: { type: Number, required: true },
	nodeW: { type: Number, required: true },
	nc: { type: String, required: true },
});

const emit = defineEmits([
	"path-mousemove",
	"path-mouseleave",
	"node-mousemove",
	"node-mouseleave",
]);

function trunc(str, max = 13) {
	return str.length > max ? str.slice(0, max) + "…" : str;
}

const isMobile =
  typeof window !== "undefined" &&
  window.matchMedia?.("(max-width: 770px)").matches;
const MIN_LABEL_GAP = isMobile ? 22 : 16;
const LEADER_THRESHOLD = 1.5;
const NODE_LABEL_FONT_SIZE = isMobile ? 18 : 14;
const NODE_LABEL_BOUNDS_PAD = Math.ceil(NODE_LABEL_FONT_SIZE * 0.8);

// 階層大標籤預留的獨立頂部高度
const HEADER_HEIGHT = isMobile ? 36 : 28;

function declutter(nodes, minGap) {
	if (!nodes.length) return [];

	const firstNode = nodes[0];
	const lastNode = nodes[nodes.length - 1];
	const totalTop = firstNode.y;
	const totalBottom = lastNode.y + lastNode.h;
	const layerCenterY = (totalTop + totalBottom) / 2;

	const items = nodes.map((nd) => ({
		nd,
		origY: nd.y + nd.h / 2,
		y: nd.y + nd.h / 2,
	}));

	const n = items.length;
	if (n === 1) return [{ ...items[0].nd, labelY: items[0].y }];

	let pivotIdx = 0;
	let minDiff = Infinity;
	for (let i = 0; i < n; i++) {
		const diff = Math.abs(items[i].origY - layerCenterY);
		if (diff < minDiff) {
			minDiff = diff;
			pivotIdx = i;
		}
	}

	// 從中間向「上」推開
	for (let i = pivotIdx - 1; i >= 0; i--) {
		if (items[i + 1].y - items[i].y < minGap) {
			items[i].y = items[i + 1].y - minGap;
		}
	}

	// 從中間向「下」推開
	for (let i = pivotIdx + 1; i < n; i++) {
		if (items[i].y - items[i - 1].y < minGap) {
			items[i].y = items[i - 1].y + minGap;
		}
	}

	// 計算對稱質心校正
	const currentCenterY = (items[0].y + items[n - 1].y) / 2;
	const offset = layerCenterY - currentCenterY;

	for (let i = 0; i < n; i++) {
		items[i].y += offset;
	}

	return items.map((it) => ({ ...it.nd, labelY: it.y }));
}

const labeledLayers = computed(() =>
	props.layout?.nodesPerLayer
		? props.layout.nodesPerLayer.map((nodes) => declutter(nodes, MIN_LABEL_GAP))
		: [],
);

const verticalPad = computed(() => {
	let minY = 0;
	let maxY = props.svgH;

	for (const nodes of labeledLayers.value) {
		for (const nd of nodes) {
			minY = Math.min(minY, nd.labelY - NODE_LABEL_BOUNDS_PAD);
			maxY = Math.max(maxY, nd.labelY + NODE_LABEL_BOUNDS_PAD);
		}
	}

	const topOverflow = Math.max(0, -minY);
	const bottomOverflow = Math.max(0, maxY - props.svgH);

	return Math.max(topOverflow, bottomOverflow);
});

// ViewBox 總高度 = 獨立 Header 高度 + 圖表高 + 上下擴充 Margin
const viewBoxHeight = computed(() =>
	Math.ceil(HEADER_HEIGHT + props.svgH + verticalPad.value * 2),
);

function onNodeMouseMove(event, nd) {
	emit("node-mousemove", { event, tip: nd.tip });
}
</script>

<template>
  <svg
    :viewBox="`0 0 ${layout.svgW} ${viewBoxHeight}`"
    preserveAspectRatio="xMidYMid meet"
    v-bind="$attrs"
  >
    <!-- 1. 獨立的階層大標籤區塊 (固定在頂部，不受 verticalPad 移動影響) -->
    <g class="header-layer">
      <text
        v-for="(label, i) in layout.layerLabels"
        :key="`label-${i}`"
        :x="layout.xPositions[i] + nodeW / 2"
        :y="HEADER_HEIGHT"
        class="layer-label"
      >
        {{ label }}
      </text>
    </g>

    <!-- 2. 圖表主體區塊 (下移 HEADER_HEIGHT + verticalPad，提供充足的安全防撞空間) -->
    <g :transform="`translate(0, ${HEADER_HEIGHT + verticalPad})`">
      <!-- Flow paths -->
      <path
        v-for="(p, i) in layout.paths"
        :key="`p-${i}`"
        :d="p.d"
        :fill="p.fill"
        :style="{ opacity: p.hidden ? 0 : p.opacity }"
        class="sankey-link"
        :class="{ 'sankey-link--hidden': p.hidden }"
        @mouseenter="emit('path-mousemove', { event: $event, tip: p.tip })"
        @mousemove="emit('path-mousemove', { event: $event, tip: p.tip })"
        @mouseleave="emit('path-mouseleave')"
      />

      <!-- Nodes -->
      <template
        v-for="(nodes, li) in layout.nodesPerLayer"
        :key="`layer-${li}`"
      >
        <g
          v-for="nd in nodes"
          :key="`n${li}-${nd.name}`"
        >
          <rect
            :x="nd.x"
            :y="nd.y"
            :width="nodeW"
            :height="nd.h"
            :fill="nc"
            rx="2"
            class="sankey-node"
            @mouseenter="onNodeMouseMove($event, nd)"
            @mousemove="onNodeMouseMove($event, nd)"
            @mouseleave="emit('node-mouseleave')"
          />
        </g>
      </template>

      <!-- Labels (向上下對稱展開，不再壓迫頂部標籤) -->
      <template
        v-for="(nodes, li) in labeledLayers"
        :key="`label-layer-${li}`"
      >
        <g
          v-for="nd in nodes"
          :key="`label-${li}-${nd.name}`"
        >
          <line
            v-if="Math.abs(nd.labelY - (nd.y + nd.h / 2)) > LEADER_THRESHOLD"
            :x1="li === 0 ? nd.x - 4 : nd.x + nodeW + 4"
            :y1="nd.y + nd.h / 2"
            :x2="li === 0 ? nd.x - 8 : nd.x + nodeW + 8"
            :y2="nd.labelY"
            class="label-leader"
          />
          <text
            :x="li === 0 ? nd.x - 8 : nd.x + nodeW + 8"
            :y="nd.labelY"
            :text-anchor="li === 0 ? 'end' : 'start'"
            dominant-baseline="middle"
            class="node-label"
          >
            {{ trunc(nd.name, li === 0 ? 13 : 16) }}
          </text>
        </g>
      </template>
    </g>
  </svg>
</template>

<style scoped lang="scss">
.sankey-link {
	transition: opacity 0.15s;
	cursor: pointer;

	&--hidden {
		pointer-events: none;
	}

	&:hover {
		opacity: 1 !important;
	}
}

.sankey-node {
	cursor: pointer;
	transition: filter 0.15s;
	&:hover {
		filter: brightness(1.25);
	}
}

.layer-label {
	fill: var(--color-text-secondary, #aaa);
	font-size: 20px;
	text-anchor: middle;
	font-weight: 600;
	letter-spacing: 0.5px;
}

.node-label {
	fill: var(--color-text, #ddd);
	font-size: 14px;
	pointer-events: none;
}

.label-leader {
	stroke: var(--color-text-secondary, #aaa);
	stroke-width: 1;
	opacity: 0.5;
	pointer-events: none;
}

@media (max-width: 770px) {
	.layer-label {
		font-size: 24px;
	}

	.node-label {
		font-size: 18px;
	}
}
</style>