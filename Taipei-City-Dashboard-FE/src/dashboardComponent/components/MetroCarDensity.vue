<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup lang="ts">
import { PropType } from "vue";

defineProps({
	direction: { type: String },
	weight: { type: Object as PropType<{ x: string; y: string }> },
});

const numToColor: { [index: number]: string } = {
	1: "#acc22a",
	2: "#fcd100",
	3: "#ed8502",
	4: "#ce161a",
};
</script>

<template>
	<div class="metrocardensity">
		<div v-if="weight" class="metrocardensity-container">
			<div
				class="metrocardensity-item"
				v-for="(item, index) in weight.y"
				:style="{ backgroundColor: numToColor[+item] }"
				:key="`${item}-${index}`"
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
		color: var(--dashboardcomponent-color-complement-text);
		font-family: var(--dashboardcomponent-font-icon);
		pointer-events: none;
		user-select: none;
	}

	&-container {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
		column-gap: 2px;
	}

	&-item {
		width: var(--dashboardcomponent-font-ms);
		height: var(--dashboardcomponent-font-ms);
		border-radius: 2px;
		color: black;
		font-size: 0.8rem;
		line-height: var(--dashboardcomponent-font-ms);
		text-align: center;
		pointer-events: none;
		user-select: none;
	}
}
</style>
