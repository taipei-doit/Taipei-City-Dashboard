<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- This component has two modes "outline" and "fill" which is controlled via the prop "mode" -->

<script setup>
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
	border: solid 1px var(--dashboardcomponent-color-complement-text);
	border-radius: 5px;
	overflow-x: hidden;
	user-select: none;

	span {
		margin-right: 4px;
		color: var(--dashboardcomponent-color-complement-text);
		font-family: var(--dashboardcomponent-font-icon);
	}

	p {
		max-height: var(--dashboardcomponent-font-ms);
		color: var(--dashboardcomponent-color-complement-text);
		font-size: var(--dashboardcomponent-font-s);
	}

	&-fill {
		background-color: var(--dashboardcomponent-color-complement-text);

		span,
		p {
			color: white;
		}
	}

	&-small {
		min-height: var(--dashboardcomponent-font-ms);
		max-height: var(--dashboardcomponent-font-ms);
		padding: 0 2px;
		margin-left: 8px;

		p {
			font-weight: 400;
		}

		&.city-tag-item {
			margin: 0;

			p {
				color: white;
			}

			&.taipei {
				background-color: #1411AC;
			}
			&.metrotaipei {
				background-color: #11AC33;
			}
		}
	}
}
</style>
