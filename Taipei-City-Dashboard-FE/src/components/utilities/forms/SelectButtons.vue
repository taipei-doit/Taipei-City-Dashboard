<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- Used by admin settings forms to select items from a predetermined list -->
<script setup>
import { defineProps, defineEmits, ref, computed } from "vue";
import { chartTypes } from "../../../assets/configs/apexcharts/chartTypes";
import { timeTerms } from "../../../assets/configs/AllTimes";

const props = defineProps(["tags", "selected", "limit", "disable"]);

const selectedTagList = ref([...props.selected]);

const emit = defineEmits({
	updatetagorder: { updatedTags: Array },
});

const selectLabels = computed(() => {
	return {
		...chartTypes,
		...timeTerms,
	};
});

function handleClick(tag) {
	if (selectedTagList.value.includes(tag)) {
		selectedTagList.value = selectedTagList.value.filter(
			(item) => item !== tag
		);
	} else {
		if (props.limit && selectedTagList.value.length >= props.limit) {
			return;
		}
		selectedTagList.value.push(tag);
	}
	emit("updatetagorder", selectedTagList.value);
}
</script>

<template>
  <div class="selectbuttons">
    <button
      v-for="tag in tags"
      :key="`chart-${tag}`"
      :class="{
        'selectbuttons-button': true,
        'selectbuttons-active': selectedTagList.includes(tag),
      }"
      :disabled="disable"
      @click="
        () => {
          handleClick(tag);
        }
      "
    >
      {{ selectLabels[tag] }}
    </button>
  </div>
</template>

<style scoped lang="scss">
.selectbuttons {
	display: flex;
	flex-wrap: wrap;
	gap: 4px;

	&-button {
		max-width: 100%;
		position: relative;
		display: flex;
		align-items: center;
		background-color: var(--color-border);
		border-radius: 5px;
		padding: 2px 4px;
		font-size: var(--font-s);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		transition: opacity 0.2s;

		&:hover {
			opacity: 0.7;
		}
	}
	&-active {
		background-color: var(--color-complement-text);
	}
}
</style>
