<script setup>
import { computed } from "vue";

const props = defineProps({
	layout: { type: Object, required: true },
	svgH: { type: Number, required: true },
	nodeW: { type: Number, required: true },
	nc: { type: String, required: true },
});

const emit = defineEmits(["path-mousemove", "path-mouseleave"]);

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

function declutter(nodes, minGap) {
	if (!nodes.length) return [];

	const items = nodes.map((nd) => ({ nd, y: nd.y + nd.h / 2 }));

	for (let i = 1; i < items.length; i++) {
		if (items[i].y - items[i - 1].y < minGap) {
			items[i].y = items[i - 1].y + minGap;
		}
	}
	for (let i = items.length - 2; i >= 0; i--) {
		if (items[i + 1].y - items[i].y < minGap) {
			items[i].y = items[i + 1].y - minGap;
		}
	}

	return items.map((it) => ({ ...it.nd, labelY: it.y }));
}

const labeledLayers = computed(() =>
	props.layout?.nodesPerLayer
		? props.layout.nodesPerLayer.map((nodes) => declutter(nodes, MIN_LABEL_GAP))
		: [],
);

const viewBoxHeight = computed(() => {
	const bottomMostLabelY = labeledLayers.value.reduce((maxY, nodes) => {
		for (const nd of nodes) {
			maxY = Math.max(maxY, nd.labelY);
		}
		return maxY;
	}, props.svgH);

	return Math.max(props.svgH, Math.ceil(bottomMostLabelY + NODE_LABEL_BOUNDS_PAD));
});
</script>

<template>
  <svg
    :viewBox="`0 0 ${layout.svgW} ${viewBoxHeight}`"
    preserveAspectRatio="xMidYMid meet"
    v-bind="$attrs"
  >
    <!-- Layer labels -->
    <text
      v-for="(label, i) in layout.layerLabels"
      :key="`label-${i}`"
      :x="layout.xPositions[i] + nodeW / 2"
      :y="layout.padTop - 14"
      class="layer-label"
    >
      {{ label }}
    </text>

    <!-- Flow paths -->
    <path
      v-for="(p, i) in layout.paths"
      :key="`p-${i}`"
      :d="p.d"
      :fill="p.fill"
      :style="{ opacity: p.opacity }"
      class="sankey-link"
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
        />
      </g>
    </template>

    <!-- Labels(防重疊後,獨立於節點迴圈外,只畫一次) -->
    <template
      v-for="(nodes, li) in labeledLayers"
      :key="`label-layer-${li}`"
    >
      <g
        v-for="nd in nodes"
        :key="`label-${li}-${nd.name}`"
      >
        <!-- 引導線:label 被推開時,畫一條細線連回節點原本位置 -->
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
  </svg>
</template>

<style scoped lang="scss">
.sankey-link {
	transition: opacity 0.15s;
	cursor: pointer;
	&:hover {
		opacity: 1 !important;
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
