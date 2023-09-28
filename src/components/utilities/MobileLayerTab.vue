<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';
import { useMapStore } from '../../store/mapStore';

const { BASE_URL } = import.meta.env;

const mapStore = useMapStore();

const props = defineProps(['content']);

const checked = ref(false);

// Communicates with the mapStore to open and close map layers on mobile
function handleToggle() {
	if (!props.content.map_config) {
		return;
	}
	if (checked.value) {
		mapStore.addToMapLayerList(props.content.map_config);
	} else {
		mapStore.turnOffMapLayerVisibility(props.content.map_config);
	}
}
</script>

<template>
	<div class="mobilelayertab">
		<input :id="content.index" type="checkbox" v-model="checked" @change="handleToggle" />
		<label :for="content.index" :class="{ checked: checked }">
			<img :src="`${BASE_URL}/images/thumbnails/${content.chart_config.types[0]}.svg`" />
		</label>
		<p>{{ content.name.length > 6 ? `${content.name.slice(0, 5)}...` : content.name }}</p>
	</div>
</template>

<style scoped lang="scss">
.mobilelayertab {
	input {
		width: 0;
		height: 0;
		opacity: 0;
	}

	label {
		width: 73px;
		height: 73px;
		display: inline-block;
		border: solid 1px transparent;
		border-radius: 5px;
		background-color: var(--color-complement-text);
		transition: border 0.2s;
		cursor: pointer;

		img {
			width: 100%;
		}
	}

	input:checked+label {
		border: solid 1px var(--color-highlight);
	}

	p {
		margin-top: 4px;
		color: var(--color-complement-text);
		font-size: 0.75rem;
		text-align: center;
	}

	margin-bottom: 8px
}

.checked {
	border: solid 1px var(--color-highlight);
}
</style>