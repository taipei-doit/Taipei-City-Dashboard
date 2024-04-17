<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- Draggable tags to be used in conjunction with an input element -->
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
    class="inputtags"
    :style="{ marginBottom: props.tags.length > 0 ? '5px' : 0 }"
  >
    <div
      v-for="(tag, index) in tags"
      :key="`${tag}`"
      :class="{
        'inputtags-tag': true,
        'inputtags-tag-dragging': index === draggedItem,
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
      {{ tag }}
      <button
        :style="{ backgroundColor: colorData ? tag : '' }"
        @click="$emit('deletetag', index)"
      >
        <span
          :style="{
            textShadow: colorData ? '0 0 2px black' : '',
          }"
        >cancel</span>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.inputtags {
	display: flex;
	flex-wrap: wrap;
	gap: 5px;

	&-tag {
		max-width: 100%;
		position: relative;
		display: flex;
		align-items: center;
		padding: 2px 18px 2px 4px;
		border-radius: 5px;
		background-color: var(--color-complement-text);
		font-size: var(--font-s);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;

		button {
			position: absolute;
			right: 0;
			padding: 2px 2px 0;
			background-color: var(--color-complement-text);

			span {
				font-family: var(--font-icon);
			}
		}

		&-dragging {
			padding: 2px 4px;
			border: dashed 1px var(--color-border);
			background-color: var(--color-component-background);

			button {
				display: none;
			}
		}
	}
}
</style>
