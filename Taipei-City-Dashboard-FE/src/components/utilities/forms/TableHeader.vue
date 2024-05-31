<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { defineProps, defineEmits } from "vue";

defineProps({
	sort: {
		type: Boolean,
		default: false,
	},
	mode: {
		type: String,
		default: "",
	},
	minWidth: { type: String, default: "100px" },
	style: { type: Object, default: () => ({}) },
});
defineEmits(["sort"]);
</script>

<template>
  <th :style="{ minWidth, ...style }">
    <div
      v-if="sort"
      class="tableheader"
      :style="{ cursor: 'pointer' }"
      @click="$emit('sort')"
    >
      <p>
        <slot />
      </p>
      <div class="tableheader-sort">
        <span
          :style="{
            color:
              mode === 'asc' ? 'var(--color-highlight)' : 'white',
          }"
        >arrow_drop_up</span>
        <span
          :style="{
            color:
              mode === 'desc'
                ? 'var(--color-highlight)'
                : 'white',
          }"
        >arrow_drop_down</span>
      </div>
    </div>
    <div
      v-else
      class="tableheader"
    >
      <p><slot /></p>
    </div>
  </th>
</template>

<style scoped lang="scss">
.tableheader {
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: default;

	p {
		margin: 0 8px;
		font-size: var(--font-m);
	}

	&-sort {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		cursor: pointer;

		span {
			margin-left: -6px;
			font-family: var(--font-icon);
			font-size: var(--font-l);
			transition: color 0.2s;
		}
		span:first-child {
			margin-bottom: -12px;
		}
	}
}
</style>
