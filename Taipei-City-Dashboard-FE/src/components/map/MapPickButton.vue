<!-- Developed by Taipei Urban Intelligence Center 2026 -->

<script setup>
const props = defineProps({
	armed: { type: Boolean, default: false },
	disabled: { type: Boolean, default: false },
	icon: { type: String, default: "place" },
	title: { type: String, default: "在地圖上選取位置" },
	ariaLabel: { type: String, default: "在地圖上選取位置" },
});

const emit = defineEmits(["toggle"]);
</script>

<template>
	<button
		type="button"
		class="MapPickButton"
		:class="{ 'MapPickButton--armed': props.armed }"
		:title="props.title"
		:aria-label="props.ariaLabel"
		:disabled="props.disabled"
		@click="emit('toggle')"
	>
		<span
			class="MapPickButton__icon"
			aria-hidden="true"
		>
			{{ props.icon }}
		</span>
	</button>
</template>

<style scoped lang="scss">
.MapPickButton {
	flex-shrink: 0;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 4px 6px;
	min-width: 32px;
	min-height: 28px;
	border: 1px solid var(--color-border);
	border-radius: 4px;
	background: var(--color-component-background);
	color: var(--color-complement-text);
	cursor: pointer;

	&--armed {
		color: var(--color-highlight);
		border-color: var(--color-highlight);
	}

	&:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	&__icon {
		font-family: var(--font-icon);
		font-size: 1.15rem;
		line-height: 1;
		user-select: none;
	}
}
</style>
