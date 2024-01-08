<script setup>
import { defineProps, ref } from "vue";

const draggedItem = ref(null);

const props = defineProps(["tags", "colorData"]);

const emit = defineEmits({
	deletetag: { index: Number },
	updatetagorder: { updatedTags: Array },
});

const handleDragStart = (event, index) => {
	event.dataTransfer.setData("text/plain", index);
	event.dataTransfer.dropEffect = "move";
	draggedItem.value = index;
};

const handleDragOver = (event, index) => {
	event.preventDefault();
	const draggingOverItem = index;

	if (
		draggedItem.value === null ||
		draggingOverItem === null ||
		draggedItem.value === draggingOverItem
	) {
		return;
	}

	const updatedTags = [...props.tags];
	const [draggedTag] = updatedTags.splice(draggedItem.value, 1);
	updatedTags.splice(draggingOverItem, 0, draggedTag);

	draggedItem.value = draggingOverItem;

	emit("updatetagorder", updatedTags);
};

const handleDragEnd = () => {
	draggedItem.value = null;
};
</script>

<template>
	<div
		v-for="(tag, index) in tags"
		:key="`${tag.index}`"
		:class="{
			componentdragtag: true,
			'componentdragtag-dragging': index === draggedItem,
		}"
		:style="{
			backgroundColor: colorData ? tag : '',
			textShadow: colorData ? '0 0 2px black' : '',
		}"
		:draggable="true"
		@dragstart="(event) => handleDragStart(event, index)"
		@dragover="(event) => handleDragOver(event, index)"
		@dragend="handleDragEnd"
	>
		<h3>{{ tag.id }}</h3>
		<p>{{ tag.name }}</p>
		<button
			@click="$emit('deletetag', index)"
			:style="{ backgroundColor: colorData ? tag : '' }"
		>
			<span
				:style="{
					textShadow: colorData ? '0 0 2px black' : '',
				}"
				>cancel</span
			>
		</button>
	</div>
</template>

<style scoped lang="scss">
.componentdragtag {
	max-width: 100%;
	height: 40px;
	position: relative;
	display: flex;
	flex-direction: column;
	justify-content: center;
	background-color: var(--color-complement-text);
	border-radius: 5px;
	padding: 4px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: clip;

	h3 {
		margin-bottom: 2px;
	}

	button {
		background-color: var(--color-complement-text);
		position: absolute;
		top: 3px;
		right: 2px;
		padding: 2px 2px 0;
		span {
			font-family: var(--font-icon);
		}
	}

	&-dragging {
		background-color: var(--color-component-background);
		border: dashed 1px var(--color-border);
		padding: 2px 4px;

		button {
			display: none;
		}
	}
}
</style>
