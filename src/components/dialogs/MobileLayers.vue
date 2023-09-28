<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component controls map layers in the mobile version. To preserve state, the dialog is only hidden but not removed when disabled -->

<script setup>
import { computed } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import { useContentStore } from '../../store/contentStore';

import MobileLayerTab from '../utilities/MobileLayerTab.vue';

const dialogStore = useDialogStore();
const contentStore = useContentStore();

// Filter out components without maps
const filteredMapLayers = computed(() => {
	if (!contentStore.currentDashboard.content) {
		return [];
	}
	return contentStore.currentDashboard.content.filter((element) => element.map_config);
});
</script>

<template>
	<Teleport to="body">
		<div :class="{ dialogcontainer: true, 'show-dialog-animation': dialogStore.dialogs.mobileLayers === true }">
			<div class="dialogcontainer-background" @click="dialogStore.hideAllDialogs"></div>
			<div class="dialogcontainer-dialog">
				<div class="mobilelayers">
					<!-- Map Layers Dashboard -->
					<div v-if="contentStore.currentDashboard.index === 'map-layers'">
						<MobileLayerTab v-for="item in contentStore.currentDashboard.content" :content="item"
							:key="`map-layer-${item.index}`" />
					</div>
					<!-- other dashboards with components -->
					<div v-else-if="filteredMapLayers.length !== 0">
						<MobileLayerTab v-for="item in filteredMapLayers" :content="item" :key="item.index" />
						<h2>基本圖層</h2>
						<MobileLayerTab v-for="item in contentStore.mapLayers" :content="item"
							:key="`map-layer-${item.index}`" />
					</div>
					<!-- Other dashboards without components -->
					<div v-else>
						<h2>基本圖層</h2>
						<MobileLayerTab v-for="item in contentStore.mapLayers" :content="item"
							:key="`map-layer-${item.index}`" />
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<style scoped lang="scss">
.dialogcontainer {
	width: 100vw;
	height: 100vh;
	height: calc(var(--vh) * 100);
	position: fixed;
	top: 0;
	left: 0;
	opacity: 0;
	z-index: -1;

	&-dialog {
		width: fit-content;
		height: fit-content;
		position: absolute;
		left: 16px;
		top: 135px;
		padding: var(--font-m) 11px var(--font-m) var(--font-m);
		border: solid 1px var(--color-border);
		border-radius: 5px;
		background-color: rgb(30, 30, 30);
		transform: translateY(0);
	}

	&-background {
		width: 100vw;
		height: 100vh;
		height: calc(var(--vh) * 100);
		position: absolute;
		top: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.5);
	}

}

.mobilelayers {
	width: 80px;
	max-height: 350px;
	padding: 0;
	overflow-y: scroll;

	div {
		display: grid;
	}

	h2 {
		margin-bottom: 8px;
	}
}

@keyframes opacity-transition {
	0% {
		opacity: 0
	}

	100% {
		opacity: 1
	}
}

@keyframes transform-transition {
	0% {
		transform: translateY(-2.25rem);
	}

	100% {
		transform: translateY(0);
	}
}

.show-dialog-animation {
	opacity: 1;
	animation: opacity-transition 0.3s ease;
	z-index: 10;

	.dialogcontainer-dialog {
		animation: transform-transition 0.3s ease;
	}
}
</style>