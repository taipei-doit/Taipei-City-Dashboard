<!-- Developed by Open Possible (台灣大哥大), Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<script setup>
import { computed, ref } from "vue";

const props = defineProps(["chart_config", "activeChart", "series"]);

const targetItem = ref(null);
const mousePosition = ref({ x: null, y: null });

let targetData = { status: null };

// init active index
const activeIndex = ref(0);
const chartIconTotal = 50;

// calculate active sum
const activeSum = computed(() => {
	return props.series.reduce(
		(acc, entry) => acc + entry.data[activeIndex.value],
		0
	);
});

// calculate primary percentage
const primaryPercentage = computed(() => {
	return Math.round(
		(props.series[0].data[activeIndex.value] / activeSum.value) * 100
	);
});

// calculate primary icon number
const primaryIconNumber = computed(() => {
	return Math.round((primaryPercentage.value * chartIconTotal) / 100);
});

const tooltipPosition = computed(() => {
	return {
		left: `${mousePosition.value.x - 10}px`,
		top: `${mousePosition.value.y - 54}px`,
	};
});

function updateChartData(index) {
	activeIndex.value = index;
}

function toggleActive(e) {
	targetItem.value = e.target.dataset.name;
	targetData.name = e.target.dataset.name;
	targetData.value = e.target.dataset.value;
}

function initActiveToNull() {
	targetItem.value = null;
}

function updateMouseLocation(e) {
	mousePosition.value.x = e.pageX;
	mousePosition.value.y = e.pageY;
}
</script>

<template>
	<div v-if="activeChart === 'IconPercentChart'" class="iconPercentageChart">
		<!-- chart data -->
		<div class="iconPercentageChart__title">
			<div
				v-for="(item, index) in series"
				:key="item.name"
				class="iconPercentageChart__content"
			>
				<h2>
					{{ item.name
					}}<span
						class="iconPercentageChart__percentage"
						:style="{
							color:
								index === 0
									? chart_config.color[0]
									: chart_config.color[1],
						}"
						>{{
							index === 0
								? primaryPercentage
								: 100 - primaryPercentage
						}}</span
					>
					％
				</h2>
				<p>總數：{{ item.data[activeIndex] }}{{ chart_config.unit }}</p>
			</div>
		</div>
		<!-- year buttons -->
		<div class="iconPercentageChart__buttons">
			<button
				v-for="(item, index) in chart_config.categories"
				:key="item"
				:class="{
					iconPercentageChart__button: true,
					active: activeIndex === index,
				}"
				@click="updateChartData(index)"
			>
				{{ item }}
			</button>
		</div>
		<!-- chart icon -->
		<div class="iconPercentageChart__chart">
			<span
				v-for="(item, index) in chartIconTotal"
				:key="item"
				:class="`iconPercentageChart__chart-item initial-animation-${item}`"
				:style="{
					color:
						index < primaryIconNumber
							? chart_config.color[0]
							: chart_config.color[1],
				}"
				@mouseenter="toggleActive"
				@mouseleave="initActiveToNull"
				@mousemove="updateMouseLocation"
				:data-value="
					index < primaryIconNumber
						? primaryPercentage
						: 100 - primaryPercentage
				"
				:data-name="
					index < primaryIconNumber ? series[0].name : series[1].name
				"
			>
				{{
					index < primaryIconNumber ? series[0].icon : series[1].icon
				}}
			</span>
			<!-- tooltip -->
			<Teleport to="body">
				<div
					v-if="targetItem"
					class="iconPercentageChart__chart-info chart-tooltip"
					:style="tooltipPosition"
				>
					<h6>{{ targetData.name }}比例</h6>
					<span>{{ targetData.value }}％</span>
				</div>
			</Teleport>
		</div>
	</div>
</template>

<style scoped lang="scss">
.iconPercentageChart {
	position: relative;
	max-height: 100%;
	color: var(--color-normal-text);
	overflow-y: scroll;

	&__chart {
		display: grid;
		grid-template-columns: repeat(10, 1fr);
		row-gap: 4px;
		margin: 0 2rem;
	}
	&__chart-item {
		opacity: 0;
		font-family: var(--font-icon);
		font-size: 2rem;
		user-select: none;
		cursor: default;
	}
	&__chart-info {
		position: fixed;
		z-index: 20;
	}
	&__title {
		display: flex;
		justify-content: space-around;
		margin: 1rem 1rem;
	}
	&__percentage {
		padding: 0 0.3em;
		font-size: 1.3rem;
	}
	&__content {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		p {
			margin-top: 0.2 rem;
			color: var(--color-complement-text);
		}
	}
	&__buttons {
		display: flex;
		justify-content: space-around;
		margin: 0 2rem;
		margin-bottom: 0.5rem;
		color: var(--color-complement-text);
	}
	&__button {
		padding: 2px 6px;
		border: solid 1px var(--color-complement-text);
		border-radius: 5px;
		color: var(--color-complement-text);
		transition: all 0.2s ease;
	}
	&__button.active {
		color: var(--color-normal-text);
		background-color: var(--color-border);
	}
}

@keyframes ease-in {
	0% {
		opacity: 0;
	}

	100% {
		opacity: 1;
	}
}

@for $i from 1 through 50 {
	.initial-animation-#{$i} {
		animation-name: ease-in;
		animation-duration: 0.1s;
		animation-delay: 0.02s * ($i - 1);
		animation-timing-function: linear;
		animation-fill-mode: forwards;
	}
}
</style>
