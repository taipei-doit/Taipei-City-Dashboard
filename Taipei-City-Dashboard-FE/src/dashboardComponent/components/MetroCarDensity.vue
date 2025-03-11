<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
// import { PropType } from "vue";

defineProps({
	direction: { type: String },
	weight: { type: Object },
});

const numToColor = {
	1: "#acc22a",
	2: "#fcd100",
	3: "#ed8502",
	4: "#ce161a",
};
</script>

<template>
  <div class="metrocardensity">
    <div
      v-if="weight"
      class="metrocardensity-container"
    >
      <div
        v-for="(item, index) in weight.y"
        :key="`${item}-${index}`"
        class="metrocardensity-item"
        :style="{ backgroundColor: numToColor[+item] }"
      >
        {{ index + 1 }}
      </div>
    </div>
    <span v-else>{{ direction === "desc" ? "north" : "south" }}</span>
  </div>
</template>

<style scoped lang="scss">
.metrocardensity {
	display: flex;
	align-items: center;
	justify-content: center;

	span {
		color: var(--color-complement-text);
		font-family: var(--font-icon);
		pointer-events: none;
		user-select: none;
	}

	&-container {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
		column-gap: 2px;
	}

	&-item {
		width: var(--font-ms);
		height: var(--font-ms);
		border-radius: 2px;
		color: black;
		font-size: 0.8rem;
		line-height: var(--font-ms);
		text-align: center;
		pointer-events: none;
		user-select: none;
	}
}
</style>
