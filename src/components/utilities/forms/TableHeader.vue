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
			class="tableheader"
			:style="{ cursor: 'pointer' }"
			@click="$emit('sort')"
			v-if="sort"
		>
			<p>
				<slot></slot>
			</p>
			<div class="tableheader-sort">
				<span
					:style="{
						color:
							mode === 'asc' ? 'var(--color-highlight)' : 'white',
					}"
					>arrow_drop_up</span
				>
				<span
					:style="{
						color:
							mode === 'desc'
								? 'var(--color-highlight)'
								: 'white',
					}"
					>arrow_drop_down</span
				>
			</div>
		</div>
		<div class="tableheader" v-else>
			<p><slot></slot></p>
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
		font-size: var(--font-m);
		margin: 0 8px;
	}

	&-sort {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		cursor: pointer;

		span {
			font-family: var(--font-icon);
			font-size: var(--font-l);
			transition: color 0.2s;
			margin-left: -6px;
		}
		span:first-child {
			margin-bottom: -12px;
		}
	}
}
</style>
