<script setup>
import { ref } from "vue";
// import { useMapStore } from '../../store/mapStore';

const colors = ["#7F3D82", "#7261BD", "#5683C1", "#5e9f8a"];
// function interpolateColor(color1, color2, weight) {
// 	const parseColor = (color) => {
// 		const hex = color.slice(1);
// 		return {
// 			r: parseInt(hex.slice(0, 2), 16),
// 			g: parseInt(hex.slice(2, 4), 16),
// 			b: parseInt(hex.slice(4, 6), 16),
// 		};
// 	};
// 	const interpolate = (c1, c2, weight) => {
// 		const interpolateChannel = (c1, c2, weight) =>
// 			Math.round(c1 + (c2 - c1) * weight);
// 		return {
// 			r: interpolateChannel(c1.r, c2.r, weight),
// 			g: interpolateChannel(c1.g, c2.g, weight),
// 			b: interpolateChannel(c1.b, c2.b, weight),
// 		};
// 	};
// 	const color1RGB = parseColor(color1);
// 	const color2RGB = parseColor(color2);
// 	const interpolatedColor = interpolate(color1RGB, color2RGB, weight);
// 	return `rgb(${interpolatedColor.r},${interpolatedColor.g},${interpolatedColor.b})`;
// }

// register the four required props
const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
]);
// const mapStore = useMapStore()

const num = props.series.length;
let lnum = 0;
for (let i = 0; i < num; i++) {
	if (lnum < props.series[i]["data"][1]) lnum = props.series[i]["data"][1];
}

// data: a tree
let data = {
	name: props.series[0].name,
	index: props.series[0].data[0],
	layer: props.series[0].data[1],
	parent: props.series[0].data[2],
	value: props.series[0].data[3],
	children: [],
	toggled: true,
};
function initialization(i, p) {
	if (p.index === props.series[i].data[2]) {
		p.children = [
			...p.children,
			{
				name: props.series[i].name,
				index: props.series[i].data[0],
				layer: props.series[i].data[1],
				parent: props.series[i].data[2],
				value: props.series[i].data[3],
				children: [],
				toggled: false,
			},
		];
		return true;
	}
	for (let j = 0; j < p["children"].length; j++) {
		initialization(i, p["children"][j]);
	}
}
for (let i = 1; i < num; i++) {
	initialization(i, data);
}
// console.log(data);

const showedData = ref(data);

const hei = 30;
const l = 15;
const trileft = 5;
const spcy = 13;
const spcx = 18;
function calcPos(data) {
	// console.log('calcPos called', data);
	let pos = [
		{
			index: 0,
			x: 0,
			y: 0,
			layer: 0,
			showed: true,
			toggled: data.toggled,
			childrenCount: data.children.length,
			name: data.name,
		},
	];
	let accy = hei + spcy;
	function dfsPos(parent, x) {
		if (parent["children"] && parent["children"].length > 0) {
			for (let i = 0; i < parent["children"].length; i++) {
				if (parent["toggled"]) {
					pos = [
						...pos,
						{
							index: parent["children"][i].index,
							x: x + spcx,
							y: accy,
							layer: parent["layer"] + 1,
							showed: true,
							toggled: parent["children"][i].toggled,
							childrenCount:
								parent["children"][i].children.length,
							name: parent["children"][i].name,
						},
					];
					accy += hei + spcy;
				} else {
					pos = [
						...pos,
						{
							index: parent["children"][i].index,
							x: x + spcx,
							y: accy - hei - spcy,
							layer: parent["layer"] + 1,
							showed: false,
							toggled: parent["children"][i].toggled,
							childrenCount:
								parent["children"][i].children.length,
							name: parent["children"][i].name,
						},
					];
				}
				dfsPos(parent["children"][i], x + spcx);
			}
		}
	}
	dfsPos(data, 0);
	return pos.sort((a, b) => a.index - b.index);
}
// console.log(calcPos(data));
const pos = ref(calcPos(data));

const rectangles = Array.from({ length: num }, () => {
	return {};
});
function returnPos(index) {
	let trianglePos = [
		{ x: pos.value[index].x + trileft, y: pos.value[index].y },
		{ x: pos.value[index].x + trileft, y: pos.value[index].y },
		{ x: pos.value[index].x + trileft, y: pos.value[index].y },
	];
	if (pos.value[index].childrenCount) {
		trianglePos = [
			{
				x: pos.value[index].x + (hei - l) / 2 + trileft,
				y: pos.value[index].y + (hei - l) / 2,
			},
			{
				x: pos.value[index].x + (hei - l) / 2 + l + trileft,
				y: pos.value[index].y + (hei - l) / 2,
			},
			{
				x: pos.value[index].x + (hei - l) / 2 + l / 2 + trileft,
				y: pos.value[index].y + (hei - l) / 2 + (l * Math.sqrt(3)) / 2,
			},
		];
	}
	return {
		x: pos.value[index].x,
		y: pos.value[index].y,
		fill: colors[pos.value[index].layer],
		triangle: `${trianglePos[0].x}, ${trianglePos[0].y} ${trianglePos[1].x}, ${trianglePos[1].y} ${trianglePos[2].x}, ${trianglePos[2].y}`,
		name: pos.value[index].name,
		showed: pos.value[index].showed,
		rotate: pos.value[index].toggled ? 0 : -90,
		textY: pos.value[index].showed
			? pos.value[index].y + hei / 2
			: pos.value[index].y + hei / 2,
		parentY: pos.value[props.series[index].data[2]].y,
		childrenCount: pos.value[index].childrenCount,
	};
}

// const tooltipPosition = computed(() => {
// 	return {
// 		left: `${mousePosition.value.x - 10}px`,
// 		top: `${mousePosition.value.y - 55}px`,
// 	};
// });
// const targetBox = ref(null);
// const mousePosition = ref({ x: null, y: null });
// function toggleActive(i) {
// 	// console.log('toggleActive called, ', i);
// 	targetBox.value = i;
// }
// function toggleActiveToNull() {
// 	// console.log('toggleActiveToNull called, ');
// 	targetBox.value = null;
// }
// function updateMouseLocation(e) {
// 	mousePosition.value.x = e.pageX;
// 	mousePosition.value.y = e.pageY;
// }

function toggleTriangle(clickedIndex) {
	if (clickedIndex === -1) return;

	// console.log("clicked", clickedIndex);
	let newData = showedData.value;
	// console.log(clickedIndex, pos.value, newData)

	function dfs(parent, toggledNodeFound) {
		// console.log(parent.index, clickedIndex, parent.toggled)
		if (toggledNodeFound) {
			if (parent["children"] && parent["children"].length > 0) {
				for (let i = 0; i < parent["children"].length; i++) {
					parent.children[i].showed = parent.toggled;
					parent.children[i].toggled = false;
					dfs(
						parent["children"][i],
						true,
						parent["children"][i].index
					);
				}
			}
		} else if (parent.index === clickedIndex) {
			if (parent.toggled) {
				parent.toggled = false;
				if (parent["children"] && parent["children"].length > 0) {
					for (let i = 0; i < parent["children"].length; i++) {
						parent.children[i].showed = false;
						parent.children[i].toggled = false;
						dfs(
							parent["children"][i],
							true,
							parent["children"][i].index
						);
					}
				}
			} else {
				parent.toggled = true;
				if (parent["children"] && parent["children"].length > 0) {
					for (let i = 0; i < parent["children"].length; i++) {
						parent.children[i].showed = true;
						parent.children[i].toggled = false;
						dfs(
							parent["children"][i],
							true,
							parent["children"][i].index
						);
					}
				}
			}
		} else {
			if (parent["children"] && parent["children"].length > 0) {
				for (let i = 0; i < parent["children"].length; i++) {
					dfs(
						parent["children"][i],
						false,
						parent["children"][i].index
					);
				}
			}
		}
		return parent;
	}

	newData = dfs(newData, false);
	// console.log(newData);
	showedData.value = newData;
	pos.value = calcPos(newData);
}
</script>

<template>
	<!-- conditionally render the chart -->
	<div v-if="activeChart === 'TreeChart'" class="treechart">
		<!-- The layout of the chart Vue component -->
		<!-- Utilize the @click event listener to enable map filtering by data selection -->
		<svg class="svg-container">
			<g
				:class="{ 'rectangles-g': true }"
				v-for="(rect, index) in rectangles"
				:key="num - index - 1"
				:x="returnPos(num - index - 1).x"
				:y="returnPos(num - index - 1).y"
				:height="hei"
			>
				<line
					:class="{
						[`initial-animation-rect-${num - index - 1}`]: true,
						'rectangles-rectangle': true,
					}"
					:x1="returnPos(num - index - 1).x - spcx / 2"
					:x2="returnPos(num - index - 1).x"
					:y1="returnPos(num - index - 1).y + hei / 2"
					:y2="returnPos(num - index - 1).y + hei / 2"
					:opacity="returnPos(num - index - 1).showed ? 1 : 0"
					stroke="#888787"
					stroke-width="2"
				/>
				<line
					:class="{
						[`initial-animation-rect-${num - index - 1}`]: true,
						'rectangles-rectangle': true,
					}"
					:x1="returnPos(num - index - 1).x - spcx / 2"
					:x2="returnPos(num - index - 1).x - spcx / 2"
					:y1="returnPos(num - index - 1).parentY + hei / 2"
					:y2="returnPos(num - index - 1).y + hei / 2"
					:opacity="returnPos(num - index - 1).showed ? 1 : 0"
					stroke="#888787"
					stroke-width="2"
				/>
				<rect
					:class="{
						[`initial-animation-rect-${num - index - 1}`]: true,
						'rectangles-rectangle': true,
					}"
					:x="returnPos(num - index - 1).x"
					:y="returnPos(num - index - 1).y"
					:width="253 - returnPos(num - index - 1).x"
					:height="hei"
					:rx="hei / 2"
					:ry="hei / 2"
					:fill="
						returnPos(num - index - 1).showed
							? returnPos(num - index - 1).fill
							: `rgba(255, 255, 255, 0)`
					"
					:opacity="returnPos(num - index - 1).showed ? 1 : 0"
					stroke="none"
				/>
				<text
					:class="{
						[`initial-animation-rect-${num - index - 1}`]: true,
						'rectangles-text': true,
					}"
					:x="
						returnPos(num - index - 1).childrenCount
							? returnPos(num - index - 1).x + hei
							: returnPos(num - index - 1).x + hei / 2
					"
					:y="returnPos(num - index - 1).textY"
					:height="hei"
					stroke="none"
					text-anchor="left"
					alignment-baseline="middle"
					:fill="
						returnPos(num - index - 1).showed
							? `#ffffff`
							: `rgba(255, 255, 255, 0)`
					"
					:opacity="returnPos(num - index - 1).showed ? 1 : 0"
					font-size="12.5"
				>
					{{ returnPos(num - index - 1).name }}
				</text>
				<polygon
					:class="{
						'rectangles-triangle': true,
						[`initial-animation-rect-${num - index - 1}`]: true,
					}"
					:points="returnPos(num - index - 1).triangle"
					:fill="
						returnPos(num - index - 1).showed
							? `rgba(255, 255, 255, 0.65)`
							: `rgba(255, 255, 255, 0)`
					"
					:transform="`rotate(${returnPos(num - index - 1).rotate})`"
					:style="{
						transformOrigin: `${
							returnPos(num - index - 1).x +
							hei / 2 +
							trileft * 0.8
						}px ${
							returnPos(num - index - 1).y + hei / 2 + trileft / 4
						}px`,
					}"
				/>
				<rect
					:x="returnPos(num - index - 1).x"
					:y="returnPos(num - index - 1).y"
					:width="hei * 1.5"
					:height="hei"
					:fill="`rgba(255, 255, 255, 0)`"
					stroke="none"
					:cursor="
						returnPos(num - index - 1).childrenCount
							? 'pointer'
							: 'default'
					"
					@click="toggleTriangle(num - index - 1)"
				/>
			</g>
		</svg>
		<Teleport to="body">
			<!-- The class "chart-tooltip" could be edited in /assets/styles/chartStyles.css -->
			<!-- <div v-if="targetBox !== null" class="circulardendrogram-chart-info chart-tooltip" :style="tooltipPosition">
				<h6>{{ props.series[targetBox].name }}</h6>
				<span>{{ props.series[targetBox].data[3] }} {{ props.chart_config.unit }}</span>
			</div> -->
		</Teleport>
	</div>
</template>

<style scoped lang="scss">
.treechart {
	/* styles for the chart Vue component */
	display: flex;
	justify-content: center;
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
	overflow: scroll;
}
.svg-container {
	padding: 20px;
	min-height: 1500px;
	overflow: scroll;
}
// .rectangles {
// 	&-triangle {
// 		transition: transform 0.3s, y 0.3s ease, points 0.3s ease;
// 	}
// 	&-rectangle {
// 		transition: all 0.3s ease;
// 	}
// 	&-text {
// 		transition: all 0.3s ease;
// 	}
// }

.rectangles {
	&-triangle {
		transition: transform 0.3s;
	}
}

@for $i from 0 through 100 {
	.initial-animation-#{$i} {
		@keyframes ease-in-#{$i} {
			0% {
				opacity: 0;
			}
			100% {
				opacity: 1;
			}
		}
		animation-name: ease-in-#{$i};
		animation-duration: 0.3s;
		animation-delay: 0.1s * $i;
		animation-timing-function: cubic-bezier(0.445, 0.05, 0.55, 0.95);
		animation-fill-mode: forwards;
		opacity: 0;
	}
	.initial-animation-line-#{$i} {
		@keyframes ease-in-line-#{$i} {
			0% {
				opacity: 0;
			}
			100% {
				opacity: 1;
			}
		}
		animation-name: ease-in-line-#{$i};
		animation-duration: 0.3s;
		animation-delay: 0.1s * $i + 0.06s;
		animation-timing-function: cubic-bezier(0.445, 0.05, 0.55, 0.95);
		animation-fill-mode: forwards;
		opacity: 0;
	}
}
/* Animation styles aren't required but recommended */
</style>
