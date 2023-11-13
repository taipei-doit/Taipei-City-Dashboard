<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component has two modes "outline" and "fill" which is controlled via the prop "mode" -->

<script setup>
import { useDialogStore } from "../../store/dialogStore";

const dialogStore = useDialogStore();

defineProps({
	icon: String,
	text: String,
	mode: {
		type: String,
		default: "outline",
	},
});
</script>

<template>
	<div
		:class="{
			componenttag: true,
			'componenttag-fill': mode === 'fill',
			'componenttag-small': mode === 'small',
		}"
		@click="
			dialogStore.showNotification(
				'info',
				'為內部版本更新頻率，本展示站台均為靜態資料'
			)
		"
	>
		<span v-if="icon">{{ icon }}</span>
		<p>{{ text }}</p>
	</div>
</template>

<style scoped lang="scss">
.componenttag {
	min-height: 1.5rem;
	max-height: 1.5rem;
	width: fit-content;
	max-width: 88px;
	display: flex;
	align-items: center;
	margin-right: 4px;
	padding: 0 4px;
	border: solid 1px var(--color-complement-text);
	border-radius: 5px;
	overflow-x: hidden;
	user-select: none;

	span {
		margin-right: 4px;
		color: var(--color-complement-text);
		font-family: var(--font-icon);
	}

	p {
		max-height: 1rem;
		color: var(--color-complement-text);
	}

	&-fill {
		background-color: var(--color-complement-text);

		span,
		p {
			color: white;
		}
	}

	&-small {
		min-height: 1.1rem;
		max-height: 1.1rem;
		padding: 0 2px;
		margin-left: 8px;

		p {
			font-weight: 400;
		}
	}
}
</style>
