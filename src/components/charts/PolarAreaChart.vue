<!-- Developed by 00:21, Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<!-- eslint-disable no-mixed-spaces-and-tabs -->
<script setup>
import { computed, ref } from "vue";
import { useMapStore } from "../../store/mapStore";

// register the five required props
const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
]);
const mapStore = useMapStore();

const mousePosition = ref({ x: null, y: null });
const tooltipPosition = computed(() => {
	return {
		left: `${mousePosition.value.x - 20}px`,
		top: `${mousePosition.value.y - 74}px`,
	};
});

const parseSeries = computed(() => {
	let output = {};
	let series = [];
	let max = -1;

	// 2D Data
	if (!props.chart_config.categories) {
		props.series[0].data.forEach((element) => {
			series.push({
				a: element.x,
				data: [
					{
						r: "",
						value: element.y,
					},
				],
			});
			max = max < element.y ? element.y : max;
		});
	}
	// 3D Data
	else {
		for (let i = 0; i < props.series[0].data.length; i++) {
			series.push({
				a: props.chart_config["categories"][i],
				data: [],
			});
			for (let j = 0; j < props.series.length; j++) {
				series[i].data.push({
					r: props.series[j].name,
					value: props.series[j].data[i],
				});
				max =
					max < props.series[j].data[i]
						? props.series[j].data[i]
						: max;
			}
			series[i].data.sort((a, b) => b.value - a.value);
		}
	}
	output.series = series;
	output.max = max;
	return output;
});

// a refers to the number of categories (xAxis)
// r refers to the number of series (yAxis)
const anumTotal = computed(() => {
	return parseSeries.value.series.length;
});
const rnumTotal = computed(() => {
	return parseSeries.value.series[0].data.length;
});
const showedData = ref(parseSeries.value.series);
const showedMax = ref(parseSeries.value.max);
const rShow = ref(Array(rnumTotal.value).fill(true));
const aHovered = ref(-1);
const rHovered = ref(-1);
const rtext = 105; // xAxis label position radius

const aspc = (2 * Math.PI) / 180;
const agap = (6 * Math.PI) / 180;
const rmin = 10; // sector radius adder
const rmax = 75; // sector radius multiplier
const rselected = 80; // selected sector radius multiplier

const cx = 180;
const cy = 115;

// index: a
const labels = Array.from({ length: anumTotal.value }, (_, index) => {
	return {
		name: parseSeries.value.series[index].a,
		x:
			cx +
			rtext * Math.sin(((index + 0.5) * 2 * Math.PI) / anumTotal.value),
		y:
			cy -
			rtext * Math.cos(((index + 0.5) * 2 * Math.PI) / anumTotal.value),
	};
});

// max: showedMax.value, return {radius, startAngle, endAngle}
function calcSector(a, r) {
	let awid =
		(Math.PI * 2) / anumTotal.value - aspc - (rnumTotal.value - 1) * agap;
	let astart = (a * Math.PI * 2) / anumTotal.value + aspc / 2 + r * agap;
	let aend = astart + awid;
	let rend =
		aHovered.value === a
			? (parseSeries.value.series[a].data[r].value / showedMax.value) *
					rselected +
			  rmin
			: (showedData.value[a].data[r].value / showedMax.value) * rmax +
			  rmin;
	for (let i = 0; i < props.series.length; i++) {
		if (props.series[i].name === showedData.value[a].data[r].r) {
			if (!rShow.value[i]) {
				rend = 0;
				break;
			}
		}
	}
	return {
		radius: rend,
		startAngle: astart,
		endAngle: aend,
	};
}
function getSectorPath(cx, cy, radius, startAngle, endAngle) {
	const x1 = cx + radius * Math.sin(startAngle);
	const y1 = cy - radius * Math.cos(startAngle);
	const x2 = cx + radius * Math.sin(endAngle);
	const y2 = cy - radius * Math.cos(endAngle);
	const largeArcFlag = endAngle - startAngle <= Math.PI ? "0" : "1";
	return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
}

const sectors = Array.from(
	{ length: anumTotal.value * rnumTotal.value },
	(_, index) => {
		const a = index % anumTotal.value;
		const r = (index / anumTotal.value) | 0;
		let rname = -1;
		for (let i = 0; i < props.series.length; i++) {
			if (showedData.value[a].data[r].r === props.series[i].name) {
				rname = i;
			}
		}
		return {
			show: true,
			r: r,
			a: a,
			fill: props.chart_config.color[rname],
			stroke_width: 1,
		};
	}
);

function sectorD(index) {
	const a = index % anumTotal.value;
	const r = (index / anumTotal.value) | 0;
	const posFac = calcSector(a, r);
	return getSectorPath(
		cx,
		cy,
		posFac.radius,
		posFac.startAngle,
		posFac.endAngle
	);
}

function toggleActive(i) {
	aHovered.value = i % anumTotal.value;
	rHovered.value = (i / anumTotal.value) | 0;
}
function toggleActiveToNull() {
	aHovered.value = -1;
	rHovered.value = -1;
}
function updateMouseLocation(e) {
	mousePosition.value.x = e.pageX;
	mousePosition.value.y = e.pageY;
}

const selectedIndex = ref(null);

function handleDataSelection(xParam, yParam) {
	if (!props.map_filter) {
		return;
	}
	if (`${xParam}-${yParam}` !== selectedIndex.value) {
		// Supports filtering by xAxis
		if (props.map_filter.mode === "byParam") {
			mapStore.filterByParam(
				props.map_filter,
				props.map_config,
				xParam,
				yParam
			);
		}
		// Supports filtering by xAxis
		else if (props.map_filter.mode === "byLayer") {
			mapStore.filterByLayer(props.map_config, xParam);
		}
		selectedIndex.value = `${xParam}-${yParam}`;
	} else {
		if (props.map_filter.mode === "byParam") {
			mapStore.clearByParamFilter(props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			mapStore.clearByLayerFilter(props.map_config);
		}
		selectedIndex.value = null;
	}
}

function handleLegendSelection(index) {
	rShow.value[index] = !rShow.value[index];
	let newData = [];
	let newMax = -1;
	for (let a = 0; a < anumTotal.value; a++) {
		newData = [
			...newData,
			{
				a: parseSeries.value.series[a].a,
				data: [],
			},
		];
		for (let r = 0; r < parseSeries.value.series[a].data.length; r++) {
			let index = -1;
			for (let i = 0; i < props.series.length; i++) {
				if (showedData.value[a].data[r].r === props.series[i].name) {
					index = i;
				}
			}
			if (rShow.value[index]) {
				newData[a]["data"] = [
					...newData[a]["data"],
					{
						r: props.series[index].name,
						value: props.series[index].data[a],
					},
				];
				if (newMax < parseSeries.value.series[a].data[r].value)
					newMax = parseSeries.value.series[a].data[r].value;
			} else {
				newData[a]["data"] = [
					...newData[a]["data"],
					{
						r: props.series[index].name,
						value: 0,
					},
				];
			}
		}
	}
	showedMax.value = newMax;
	showedData.value = newData;
}
</script>

<template>
	<!-- conditionally render the chart -->
	<div v-if="activeChart === 'PolarAreaChart'" class="polarareachart">
		<!-- The layout of the chart Vue component -->
		<!-- Utilize the @click event listener to enable map filtering by data selection -->
		<svg class="polarareachart-chart" xmlns="http://www.w3.org/2000/svg">
			<g v-for="(sector, index) in sectors" :key="index">
				<path
					:class="{
						[`initial-animation-sector-${sector.a}-${sector.r}`]: true,
						sector: true,
					}"
					v-if="sector.show"
					:d="sectorD(index)"
					:fill="sector.fill"
					:stroke-width="sector.stroke_width"
					@mouseenter="toggleActive(index)"
					@mousemove="updateMouseLocation"
					@mouseleave="toggleActiveToNull"
					@click="
						handleDataSelection(
							chart_config.categories[aHovered],
							showedData[aHovered].data[rHovered].r
						)
					"
				/>
			</g>
			<g v-for="(label, index) in labels" :key="index">
				<text
					:x="label.x"
					:y="label.y"
					text-anchor="middle"
					alignment-baseline="middle"
					fill="#888787"
					font-size="12"
				>
					{{ label.name }}
				</text>
			</g>
			<circle :cx="cx" :cy="cy" :r="10" :stroke="null" />
		</svg>
		<div class="polarareachart-legend" v-if="chart_config.categories">
			<div
				:class="{
					'polarareachart-legend-item': true,
					selected: !rShow[index],
				}"
				v-for="(serie, index) in props.series"
				:key="serie.name"
				@click="handleLegendSelection(index)"
			>
				<div
					:style="{
						backgroundColor: props.chart_config.color[index],
					}"
				></div>
				<p>{{ serie.name }}</p>
			</div>
		</div>
		<Teleport to="body">
			<!-- The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css -->
			<div
				v-if="aHovered !== -1"
				class="polarareachart-tooltip chart-tooltip"
				:style="tooltipPosition"
			>
				<h6>
					{{ showedData[aHovered].a
					}}{{ props.chart_config.categories && "-"
					}}{{ showedData[aHovered].data[rHovered].r }}
				</h6>
				<span
					>{{ showedData[aHovered].data[rHovered].value
					}}{{ chart_config.unit }}</span
				>
			</div>
		</Teleport>
	</div>
</template>

<style scoped lang="scss">
.polarareachart {
	/* styles for the chart Vue component */
	overflow: scroll;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;

	&-chart {
		min-height: 230px;
		width: 360px;
		overflow: scroll;
		margin-top: 1.5rem;

		circle {
			fill: var(--color-component-background);
		}
		.sector {
			stroke: var(--color-component-background);
			transition: all 0.3s ease;
			cursor: pointer;
		}
	}
	&-legend {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		justify-content: center;
		column-gap: var(--font-s);
		row-gap: 4px;
		margin-top: var(--font-s);

		&-item {
			display: flex;
			flex-direction: row;
			align-items: center;
			gap: 4px;

			cursor: pointer;
			transition: opacity 0.2s ease;

			& > div {
				width: 12px;
				height: 12px;
				border-radius: 2px;
			}
			& > p {
				color: var(--color-complement-text);
			}
		}
		.selected {
			opacity: 0.5;
		}
	}

	&-tooltip {
		position: fixed;
		z-index: 20;
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
@for $a from 0 through 100 {
	@for $r from 0 through 100 {
		.initial-animation-sector-#{$a}-#{$r} {
			animation-name: ease-in;
			animation-duration: 0.25s;
			animation-delay: 0.01s * ($a * 5 + $r);
			animation-timing-function: linear;
			animation-fill-mode: forwards;
			opacity: 0;
		}
	}
}
</style>
