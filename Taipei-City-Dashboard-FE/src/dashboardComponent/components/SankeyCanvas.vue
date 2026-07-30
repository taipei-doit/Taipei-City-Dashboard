<script setup>
defineProps({
	layout: { type: Object, required: true },
	svgH: { type: Number, required: true },
	nodeW: { type: Number, required: true },
	nc: { type: String, required: true },
});

const emit = defineEmits(["path-mousemove", "path-mouseleave"]);

function trunc(str, max = 13) {
	return str.length > max ? str.slice(0, max) + "…" : str;
}
</script>

<template>
  <svg
    :viewBox="`0 0 ${layout.svgW} ${svgH}`"
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
      <!-- Labels 最後畫 -->
      <template
        v-for="(nodes, li) in layout.nodesPerLayer"
        :key="`label-layer-${li}`"
      >
        <text
          v-for="nd in nodes"
          :key="`label-${li}-${nd.name}`"
          :x="li === 0 ? nd.x - 8 : nd.x + nodeW + 8"
          :y="nd.y + nd.h / 2"
          :text-anchor="li === 0 ? 'end' : 'start'"
          dominant-baseline="middle"
          class="node-label"
        >
          {{ trunc(nd.name, li === 0 ? 13 : 16) }}
        </text>
      </template>
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

@media (max-width: 770px) {
	.layer-label {
		font-size: 24px;
	}

	.node-label {
		font-size: 18px;
	}
}
</style>
