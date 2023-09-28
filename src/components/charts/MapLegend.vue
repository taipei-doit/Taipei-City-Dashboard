<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';
import { useMapStore } from '../../store/mapStore';

const { BASE_URL } = import.meta.env;

const props = defineProps(['chart_config', 'series', 'map_config']);
const mapStore = useMapStore();

const selectedIndex = ref(null);

function handleDataSelection(index) {
	if (!props.chart_config.map_filter) {
		return;
	}
	if (index !== selectedIndex.value) {
		mapStore.addLayerFilter(`${props.map_config[0].index}-${props.map_config[0].type}`, props.chart_config.map_filter[0], props.chart_config.map_filter[1][index]);
		selectedIndex.value = index;
	} else {
		mapStore.clearLayerFilter(`${props.map_config[0].index}-${props.map_config[0].type}`);
		selectedIndex.value = null;
	}
}
</script>

<template>
	<div class="maplegend">
		<div class="maplegend-legend">
			<button v-for="(item, index) in series" :key="item.name" @click="handleDataSelection(index)"
				:class="{ 'maplegend-legend-item': true, 'maplegend-selected': selectedIndex === index }">
				<!-- Show different icons for different map types -->
				<div v-if="item.type !== 'symbol'"
					:style="{ backgroundColor: `${item.color}`, height: item.type === 'line' ? '0.4rem' : '1rem', borderRadius: item.type === 'circle' ? '50%' : '2px' }">
				</div>
				<img v-else :src="`${BASE_URL}/images/map/${item.icon}.png`" />
				<!-- If there is a value attached, show the value -->
				<div v-if="item.value">
					<h5>{{ item.name }}</h5>
					<h6>{{ item.value }} {{ chart_config.unit }}</h6>
				</div>
				<div v-else>
					<h6>{{ item.name }}</h6>
				</div>
			</button>
		</div>
	</div>
</template>

<style scoped lang="scss">
.maplegend {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-top: -1rem;
	overflow: visible;

	&-legend {
		width: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		column-gap: 1rem;
		row-gap: 1rem;
		overflow: visible;

		&-item {
			display: flex;
			align-items: center;
			padding: 5px 10px 5px 5px;
			border: 1px solid var(--color-border);
			border-radius: 5px;
			transition: box-shadow 0.2s;

			div:first-child,
			img {
				width: 1rem;
				margin-right: 0.75rem;
			}

			h5 {
				color: var(--color-complement-text);
				font-size: 0.75rem;
				text-align: left;
			}

			h6 {
				font-size: 1rem;
				font-weight: 400;
				text-align: left;
			}

			&:hover {
				box-shadow: 0px 0px 5px black;
			}
		}
	}

	&-selected {
		box-shadow: 0px 0px 5px black;
	}
}
</style>