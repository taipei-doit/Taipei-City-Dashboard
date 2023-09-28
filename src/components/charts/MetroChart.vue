<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';

import MetroCarDensity from '../utilities/MetroCarDensity.vue';
import { lineInfo } from '../../assets/configs/apexcharts/taipeiMetroLines';

const props = defineProps(['chart_config', 'activeChart', 'series']);

const color = ref(props.chart_config.color[0]);
const line = ref(props.series[0].name);
</script>

<template>
	<div v-if="activeChart === 'MetroChart'" class="metrochart">
		<div v-for="(item, index) in  lineInfo[line] " :class="`initial-animation-${index + 1}`" :key="`${line}-${index}`">
			<!-- Shows station name / station label / density level of each train car -->
			<div class="metrochart-block">
				<h5>{{ item.name }}</h5>
				<!-- Will show a different style if the station is a terminal station -->
				<div class="metrochart-block-tag"
					:style="{ borderColor: color, backgroundColor: (index === lineInfo[line].length - 1 || index === 0) ? color : 'white' }">
					<p :style="{ color: (index === lineInfo[line].length - 1 || index === 0) ? 'white' : 'black' }">{{ line
					}}</p>
					<p :style="{ color: (index === lineInfo[line].length - 1 || index === 0) ? 'white' : 'black' }">{{
						item.id }}</p>
				</div>
				<MetroCarDensity :weight="series[1].data.find(element => element.x === item.id)" direction="south" />
				<MetroCarDensity :weight="series[0].data.find(element => element.x === item.id)" direction="north" />
			</div>
			<!-- Just shows the line connecting stations -->
			<div class="metrochart-block">
				<div></div>
				<div class="metrochart-block-line"
					:style="{ backgroundColor: index === lineInfo[line].length - 1 ? 'transparent' : color }"></div>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.metrochart {
	width: 100%;

	h5 {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		margin-right: 0.4rem;
		font-size: 0.7rem;
		font-weight: 400;
		pointer-events: none;
		user-select: none;
	}

	p {
		color: black;
		font-size: 0.6rem;
		line-height: 0.6rem;
		pointer-events: none;
		user-select: none;
	}

	&-block {
		display: grid;
		grid-template-columns: 5rem 20px 1fr 1fr;

		&-tag {
			min-width: 1rem;
			min-height: 1.4rem;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			border-width: 2px;
			border-style: solid;
			border-radius: 4px;
			background-color: white;
		}

		&-line {
			width: 8px;
			height: 1rem;
			margin: 0px 6px;
		}
	}
}

@keyframes ease-in {
	0% {
		opacity: 0
	}

	;

	100% {
		opacity: 1
	}
}

@for $i from 1 through 40 {
	.initial-animation-#{$i} {
		animation-name: ease-in;
		animation-duration: 0.2s;
		animation-delay: 0.05s * ($i - 1);
		animation-timing-function: linear;
		animation-fill-mode: forwards;
		opacity: 0;
	}
}
</style>