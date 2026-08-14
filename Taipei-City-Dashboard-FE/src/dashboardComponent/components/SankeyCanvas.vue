<script setup>
import { computed, ref } from "vue";

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

const hoveredNodeKey = ref(null);
const hoveredPathKey = ref(null);
const selectedNodeKey = ref(null);
const selectedPathKey = ref(null);

function trunc(str, max = 13) {
	return str.length > max ? str.slice(0, max) + "…" : str;
}

const isMobile =
  typeof window !== "undefined" &&
  window.matchMedia?.("(max-width: 770px)").matches;
const MIN_LABEL_GAP = isMobile ? 22 : 16;
const NODE_LABEL_FONT_SIZE = isMobile ? 18 : 14;
const NODE_LABEL_BOUNDS_PAD = Math.ceil(NODE_LABEL_FONT_SIZE * 0.8);
const CANVAS_BOTTOM_PAD = isMobile ? 20 : 16;

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

function getRenderedLabelY(nd) {
	return nd.y + nd.h / 2;
}

const verticalPad = computed(() => {
	let maxY = props.svgH + CANVAS_BOTTOM_PAD;

	for (const nodes of labeledLayers.value) {
		for (const nd of nodes) {
			const renderedLabelY = getRenderedLabelY(nd);
			maxY = Math.max(maxY, renderedLabelY + NODE_LABEL_BOUNDS_PAD);
			maxY = Math.max(maxY, nd.y + nd.h + CANVAS_BOTTOM_PAD);
		}
	}

	const bottomOverflow = Math.max(0, maxY - props.svgH);

	return bottomOverflow;
});

// ViewBox 總高度 = 獨立 Header 高度 + 圖表高 + 上下擴充 Margin
const viewBoxHeight = computed(() =>
	Math.ceil(HEADER_HEIGHT + props.svgH + verticalPad.value),
);

function onNodeMouseMove(event, layerIndex, nd) {
	hoveredPathKey.value = null;
	hoveredNodeKey.value = getNodeKey(layerIndex, nd.name);
	emit("node-mousemove", { event, tip: nd.tip });
}

function onNodeMouseLeave() {
	hoveredNodeKey.value = null;
	emit("node-mouseleave");
}

function onNodeClick(event, layerIndex, nd) {
	event.stopPropagation();
	const nodeKey = getNodeKey(layerIndex, nd.name);
	const isSameSelection =
		selectedNodeKey.value === nodeKey && selectedPathKey.value === null;

	selectedPathKey.value = null;
	selectedNodeKey.value = isSameSelection ? null : nodeKey;
}

function onPathMouseMove(event, path) {
	hoveredNodeKey.value = null;
	hoveredPathKey.value = path.key;
	emit("path-mousemove", { event, tip: path.tip });
}

function onPathMouseLeave() {
	hoveredPathKey.value = null;
	emit("path-mouseleave");
}

function onPathClick(event, path) {
	event.stopPropagation();
	const isSameSelection =
		selectedPathKey.value === path.key && selectedNodeKey.value === null;

	selectedNodeKey.value = null;
	selectedPathKey.value = isSameSelection ? null : path.key;
}

function getNodeKey(layerIndex, name) {
	return `${layerIndex}|${name}`;
}

function clearSelection() {
	selectedNodeKey.value = null;
	selectedPathKey.value = null;
}

const graph = computed(() => {
	const links = (props.layout?.paths ?? []).filter((path) => !path.hidden);
	const outgoing = new Map();
	const incoming = new Map();
	const pathByKey = new Map();

	for (const path of links) {
		const sourceKey = getNodeKey(path.source_layer, path.source);
		const targetKey = getNodeKey(path.target_layer, path.target);
		const edge = { key: path.key, sourceKey, targetKey };

		pathByKey.set(path.key, edge);

		if (!outgoing.has(sourceKey)) outgoing.set(sourceKey, []);
		outgoing.get(sourceKey).push(edge);

		if (!incoming.has(targetKey)) incoming.set(targetKey, []);
		incoming.get(targetKey).push(edge);
	}

	return { outgoing, incoming, pathByKey };
});

const activeState = computed(() => {
	const activeNodeKey = hoveredNodeKey.value || selectedNodeKey.value;
	const activePathKey = hoveredPathKey.value || selectedPathKey.value;
	const hasTransientHover = Boolean(hoveredNodeKey.value || hoveredPathKey.value);
	const hasSelection = Boolean(selectedNodeKey.value || selectedPathKey.value);

	if (activeNodeKey) {
		const nodeKeys = new Set([activeNodeKey]);
		const pathKeys = new Set();

		for (const edge of graph.value.outgoing.get(activeNodeKey) ?? []) {
			nodeKeys.add(edge.targetKey);
			pathKeys.add(edge.key);
		}

		for (const edge of graph.value.incoming.get(activeNodeKey) ?? []) {
			nodeKeys.add(edge.sourceKey);
			pathKeys.add(edge.key);
		}

		return {
			nodeKeys,
			pathKeys,
			hasActiveState: hasTransientHover || hasSelection,
		};
	}

	if (activePathKey) {
		const edge = graph.value.pathByKey.get(activePathKey);
		if (!edge) {
			return {
				nodeKeys: new Set(),
				pathKeys: new Set(),
				hasActiveState: false,
			};
		}

		return {
			nodeKeys: new Set([edge.sourceKey, edge.targetKey]),
			pathKeys: new Set([edge.key]),
			hasActiveState: hasTransientHover || hasSelection,
		};
	}

	return { nodeKeys: new Set(), pathKeys: new Set(), hasActiveState: false };
});

function isNodeActive(layerIndex, name) {
	return activeState.value.nodeKeys.has(getNodeKey(layerIndex, name));
}

function isPathActive(path) {
	return activeState.value.pathKeys.has(path.key);
}
</script>

<template>
  <svg
    :viewBox="`0 0 ${layout.svgW} ${viewBoxHeight}`"
    preserveAspectRatio="xMidYMid meet"
    v-bind="$attrs"
    @click="clearSelection"
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
    <g :transform="`translate(0, ${HEADER_HEIGHT})`">
      <!-- Flow paths -->
      <path
        v-for="(p, i) in layout.paths"
        :key="`p-${i}`"
        :d="p.d"
        :fill="p.fill"
        :style="{ opacity: p.hidden ? 0 : p.opacity }"
        class="sankey-link"
        :class="{
          'sankey-link--hidden': p.hidden,
          'sankey-link--active': !p.hidden && isPathActive(p),
          'sankey-link--dimmed':
            !p.hidden && activeState.hasActiveState && !isPathActive(p),
        }"
        @mouseenter="onPathMouseMove($event, p)"
        @mousemove="onPathMouseMove($event, p)"
        @mouseleave="onPathMouseLeave"
        @click="onPathClick($event, p)"
      />

      <!-- Nodes -->
      <template
        v-for="(nodes, li) in layout.nodesPerLayer"
        :key="`layer-${li}`"
      >
        <g
          v-for="nd in nodes"
          :key="`n${li}-${nd.name}`"
          :class="{
            'sankey-node-group--active': isNodeActive(li, nd.name),
            'sankey-node-group--dimmed':
              activeState.hasActiveState && !isNodeActive(li, nd.name),
          }"
        >
          <rect
            :x="nd.x"
            :y="nd.y"
            :width="nodeW"
            :height="nd.h"
            :fill="nc"
            rx="2"
            class="sankey-node"
            :class="{
              'sankey-node--active': isNodeActive(li, nd.name),
              'sankey-node--dimmed':
                activeState.hasActiveState && !isNodeActive(li, nd.name),
            }"
            @mouseenter="onNodeMouseMove($event, li, nd)"
            @mousemove="onNodeMouseMove($event, li, nd)"
            @mouseleave="onNodeMouseLeave"
            @click="onNodeClick($event, li, nd)"
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
          :class="{
            'sankey-node-group--active': isNodeActive(li, nd.name),
            'sankey-node-group--dimmed':
              activeState.hasActiveState && !isNodeActive(li, nd.name),
          }"
        >
          <line
            :x1="li === 0 ? nd.x : nd.x + nodeW"
            :y1="getRenderedLabelY(nd)"
            :x2="li === 0 ? nd.x - 8 : nd.x + nodeW + 8"
            :y2="getRenderedLabelY(nd)"
            class="label-leader"
            :class="{
              'label-leader--active': isNodeActive(li, nd.name),
              'label-leader--dimmed':
                activeState.hasActiveState && !isNodeActive(li, nd.name),
            }"
          />
          <text
            :x="li === 0 ? nd.x - 8 : nd.x + nodeW + 8"
            :y="getRenderedLabelY(nd)"
            :text-anchor="li === 0 ? 'end' : 'start'"
            dominant-baseline="middle"
            class="node-label"
            :class="{
              'node-label--active': isNodeActive(li, nd.name),
              'node-label--dimmed':
                activeState.hasActiveState && !isNodeActive(li, nd.name),
            }"
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
	transition:
		opacity 0.15s,
		filter 0.15s;
	cursor: pointer;

	&--hidden {
		opacity: 0 !important;
		pointer-events: none;
		filter: none !important;
	}

	&--active {
		opacity: 1 !important;
		filter: brightness(1.1);
	}

	&--dimmed {
		opacity: 0.08 !important;
	}
}

.sankey-node {
	cursor: pointer;
	transition:
		filter 0.15s,
		opacity 0.15s;

	&--active {
		filter: brightness(1.25);
	}

	&--dimmed {
		opacity: 0.22;
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
	transition:
		opacity 0.15s,
		fill 0.15s;

	&--active {
		fill: var(--color-text, #fff);
	}

	&--dimmed {
		opacity: 0.3;
	}
}

.label-leader {
	stroke: var(--color-text-secondary, #aaa);
	stroke-width: 1;
	opacity: 0.5;
	pointer-events: none;
	transition:
		opacity 0.15s,
		stroke 0.15s;

	&--active {
		stroke: var(--color-text, #fff);
		opacity: 0.8;
	}

	&--dimmed {
		opacity: 0.16;
	}
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
