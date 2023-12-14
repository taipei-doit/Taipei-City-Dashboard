<!-- Developed by 00:21, Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<!-- eslint-disable no-mixed-spaces-and-tabs -->
<script setup>
import { computed, ref } from "vue";
import { useMapStore } from "../../store/mapStore";

const colorBG = "#282A2C";

// register the four required props
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

/* ==== To Be Refactored ==== */
/* ========================== */
// data
let data = [];
let dataMax = -1;
for (let j = 0; j < props.series[0].data.length; j++) {
	data = [
		...data,
		{
			a: props.chart_config["categories"][j],
			data: [],
		},
	];
	for (let i = 0; i < props.series.length; i++) {
		// i: a, j: r
		data[j].data = [
			...data[j].data,
			{
				r: props.series[i].name,
				value: props.series[i].data[j],
			},
		];
		if (dataMax < props.series[i].data[j])
			dataMax = props.series[i].data[j];
	}
	data[j].data.sort((a, b) => b.value - a.value);
}

const anumTotal = data.length;
const rnumTotal = data[0].data.length;
const showedData = ref(data);
const showedMax = ref(dataMax);
const rShow = ref(Array(data[0].data.length).fill(true));
const aHovered = ref(-1);
const rHovered = ref(-1);
const rtext = 100;
const aspc = (4 * Math.PI) / 180;
const agap = (5.5 * Math.PI) / 180;
const cr = 25;
const rmin = 50;
const rmax = 40;
const rselected = 50;
const cx = 180;
const cy = 115;

// index: a
const labels = Array.from({ length: anumTotal }, (_, index) => {
	return {
		name: data[index].a,
		x: cx + rtext * Math.sin(((index + 0.5) * 2 * Math.PI) / anumTotal),
		y: cy - rtext * Math.cos(((index + 0.5) * 2 * Math.PI) / anumTotal),
	};
});

// max: showedMax.value, return {radius, startAngle, endAngle}
function calcSector(a, r) {
	let awid = (Math.PI * 2) / anumTotal - aspc - (rnumTotal - 1) * agap;
	let astart = (a * Math.PI * 2) / anumTotal + aspc / 2 + r * agap;
	let aend = astart + awid;
	let maxDataInR = 0;
	for (let k = 0; k < showedData.value[a].data.length; k++) {
		if (maxDataInR < showedData.value[a].data[k].value)
			maxDataInR = showedData.value[a].data[k].value;
	}
	// console.log(a, r, maxDataInR)
	let rend =
		aHovered.value === a
			? (showedData.value[a].data[r].value / maxDataInR) * rselected +
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

const sectors = Array.from({ length: anumTotal * rnumTotal }, (_, index) => {
	const a = index % anumTotal;
	const r = (index / anumTotal) | 0;
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
		stroke: colorBG,
		stroke_width: 1.2,
	};
});

function sectorD(index) {
	const a = index % anumTotal;
	const r = (index / anumTotal) | 0;
	const posFac = calcSector(a, r);
	return getSectorPath(
		cx,
		cy,
		posFac.radius,
		posFac.startAngle,
		posFac.endAngle
	);
}

const legends = Array.from({ length: rnumTotal }, (_, index) => {
	// const { width, height } = textwrapper.value ? textwrapper.value.getBoundingClientRect() : { width: 0, height: 0 };
	return {
		color: props.chart_config.color[index],
		text: props.series[index].name,
	};
});
/* ========================== */
/* ==== To Be Refactored ==== */

function toggleActive(i) {
	aHovered.value = i % anumTotal;
	rHovered.value = (i / anumTotal) | 0;
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
	for (let a = 0; a < anumTotal; a++) {
		newData = [
			...newData,
			{
				a: data[a].a,
				data: [],
			},
		];
		for (let r = 0; r < data[a].data.length; r++) {
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
				if (newMax < data[a].data[r].value)
					newMax = data[a].data[r].value;
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
		<svg class="svg-container" xmlns="http://www.w3.org/2000/svg">
			<g v-for="(sector, index) in sectors" :key="index">
				<path
					:class="{
						[`initial-animation-sector-${sector.a}-${sector.r}`]: true,
						sector: true,
					}"
					v-if="sector.show"
					:d="sectorD(index)"
					:fill="sector.fill"
					:stroke="sector.stroke"
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
			<circle :cx="cx" :cy="cy" :r="cr" :stroke="null" :fill="colorBG" />
		</svg>
		<div class="textwrapper">
			<div
				class="legends"
				v-for="(legend, index) in legends"
				:key="index"
				@click="handleLegendSelection(index)"
			>
				<svg class="svg-legend" style="width: 15px; height: 15px">
					<rect
						width="15"
						height="15"
						:fill="legend.color"
						rx="4"
						ry="4"
					/>
					<rect
						class="legends-rect-top"
						width="15"
						height="15"
						:fill="colorBG"
						:opacity="!rShow[index] ? 0.65 : 0"
						rx="4"
						ry="4"
					/>
				</svg>
				<span> {{ legend.text }} </span>
			</div>
		</div>
		<Teleport to="body">
			<!-- The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css -->
			<div
				v-if="aHovered !== -1"
				class="polarareachart-chart-info chart-tooltip"
				:style="tooltipPosition"
			>
				<h6>
					{{ chart_config.categories[aHovered] }}-{{
						showedData[aHovered].data[rHovered].r
					}}
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
		display: flex;
		justify-content: center;
		svg {
			width: 50%;
			path {
				transition: transform 0.2s;
				opacity: 0;
			}
		}
		&-info {
			position: fixed;
			z-index: 20;
		}
	}
}
.textwrapper {
	display: flex;
	flex-wrap: wrap;
	gap: 8px 14px;
	padding: 12px 0;
	justify-content: center;
	align-items: center;
	align-content: flex-start;
}
.legends {
	height: 15px;
	display: flex;
	justify-content: center;
	align-items: center;
	font-size: small;
	gap: 6px;
	cursor: pointer;
	&-rect-top {
		transition: all 0.2s ease;
	}
}
.svg-container {
	min-height: 230px;
	width: 360px;
	overflow: scroll;
	margin-top: 1.5rem;
}
.sector {
	transition: all 0.3s ease;
	cursor: pointer;
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
/* Animation styles aren't required but recommended */
</style>
