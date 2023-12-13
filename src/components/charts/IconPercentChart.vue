<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { computed, ref } from "vue";
const targetItem = ref(null);
const mousePosition = ref({ x: null, y: null });

const props = defineProps(["chart_config", "activeChart", "series"]);
let targetData = { status: null };

const { color, categories, unit } = props.chart_config;

// init active index
const activeIndex = ref(0);

const chartIconTotal = 50;
let iconColorPrimary = color[0];
let iconColorSecondary = color[1];

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

// calculate secondary percentage
const secondaryPercentage = computed(() => {
	return 100 - primaryPercentage.value;
});

// calculate primary icon number
const primaryIconNumber = computed(() => {
	return Math.round((primaryPercentage.value * chartIconTotal) / 100);
});

// update active data
const updateChartData = (index) => {
	activeIndex.value = index;
};

// tooltip setting start

const toggleActive = (e) => {
	targetItem.value = e.target.dataset.name;
	targetData.name = e.target.dataset.name;
	targetData.value = e.target.dataset.value;
};

const initActiveToNull = () => {
	targetItem.value = null;
};

const tooltipPosition = computed(() => {
	return {
		left: `${mousePosition.value.x - 10}px`,
		top: `${mousePosition.value.y - 54}px`,
	};
});

const updateMouseLocation = (e) => {
	mousePosition.value.x = e.pageX;
	mousePosition.value.y = e.pageY;
};

// tooltip setting end
</script>

<template>
	<div
		v-if="activeChart === 'IconPercentageChart'"
		class="iconPercentageChart"
	>
		<!-- chart data -->
		<div class="iconPercentageChart__title">
			<div
				class="iconPercentageChart__content"
				v-for="(item, index) in series"
				:key="item.name"
			>
				<h2>
					{{ item.name
					}}<span
						class="iconPercentageChart__percentage"
						:style="{
							color:
								index === 0
									? iconColorPrimary
									: iconColorSecondary,
						}"
						>{{
							index === 0
								? primaryPercentage
								: secondaryPercentage
						}}</span
					>
					{{ unit }}
				</h2>
				<p>總人數：{{ item.data[activeIndex] }}</p>
			</div>
		</div>
		<!-- year buttons -->
		<div class="iconPercentageChart__buttons">
			<button
				@click="updateChartData(index)"
				class="iconPercentageChart__button"
				:class="activeIndex === index ? 'active' : ''"
				type="button"
				v-for="(item, index) in categories"
				:key="item"
			>
				{{ item }}
			</button>
		</div>
		<!-- chart icon -->
		<div class="iconPercentageChart__chart">
			<div class="iconPercentageChart__chart-wrap">
				<span
					:data-name="
						index < primaryIconNumber
							? series[0].name
							: series[1].name
					"
					v-for="(item, index) in chartIconTotal"
					:key="item"
					:class="`initial-animation-${item} initial-animation`"
					:data-value="
						index < primaryIconNumber
							? primaryPercentage
							: secondaryPercentage
					"
					:style="{
						color:
							index < primaryIconNumber
								? iconColorPrimary
								: iconColorSecondary,
					}"
					@mouseenter="toggleActive"
					@mouseleave="initActiveToNull"
					@mousemove="updateMouseLocation"
					class="material-icons-round icon-item"
				>
					{{ index < primaryIconNumber ? "man" : "woman" }}
				</span>
			</div>
			<!-- tooltip -->
			<Teleport to="body">
				<div
					v-if="targetItem"
					class="iconPercentageChart__chart-info chart-tooltip"
					:style="tooltipPosition"
				>
					<h6>{{ targetData.name }}比例</h6>
					<span>{{ targetData.value }}{{ unit }}</span>
				</div>
			</Teleport>
		</div>
	</div>
</template>

<style scoped lang="scss">
:root {
	--iconPercentageChartFontColor: #fffffb;
}

.iconPercentageChart {
	max-height: 100%;
	position: relative;
	overflow-y: scroll;
	&__chart {
		margin: 0 2rem;
	}
	&__chart-info {
		position: fixed;
		z-index: 20;
	}
	color: var(--iconPercentageChartFontColor);
	&__title {
		margin-bottom: 1rem;
		display: flex;
		justify-content: space-around;
	}
	&__percentage {
		font-size: 1.3rem;
		padding: 0 0.3em;
	}
	&__content {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		p {
			color: var(--color-complement-text);
			margin-top: 0.2 rem;
		}
	}
	&__buttons {
		color: var(--color-complement-text);
		margin: 0 2rem;
		display: flex;
		justify-content: space-around;
		margin-bottom: 0.5rem;
		transition: all 0.3s ease;
	}
	&__button {
		color: var(--color-complement-text);
		border: solid 1px var(--color-complement-text);
		padding: 0 6px;
		border-radius: 5px;
	}
	&__button.active {
		color: #fff;
		background-color: #ffffff2e;
	}
}

.icon-item {
	font-size: 2rem;
	width: 10%;
}

.initial-animation {
	opacity: 0;
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
