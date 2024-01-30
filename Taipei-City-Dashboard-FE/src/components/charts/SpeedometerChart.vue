<!-- Developed by Mosquito, Taipei Codefest 2023 -->
<!-- Refactored and Maintained by Taipei Urban Intelligence Center -->

<!-- STILL UNDER DEVELOPMENT. NOT READY. DO NOT USE. -->

<script setup>
import { ref } from "vue";
const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
]);
/****************** Parameters definition *******************/
/*												  			*/
/*  R: radius of the speedometer	(outer circle)  		*/
/*  Rx: center x of the speedometer in svg coordinate		*/
/*  Ry: center y of the speedometer in svg coordinate		*/
/*  Llength: width of the speedometer arc					*/
/*												  			*/
/************************************************************/
const R = 180;
const Rx = 275;
const Ry = 240;
const Llength = 15;
let targetvalue = ref(0);
/*  set the target value to the toggled element  */
function toggleActive(e) {
	targetvalue.value = e.target.dataset.name;
}
function toggleActiveToNull() {
	// targetvalue.value = 0;
}
/******************* Calculate Gradient Combination ******************/
/*  Returns the array for <linearGradient> to render speedometer arc */
function calGradComp() {
	const { percent, grad_color } = props.chart_config;
	const res = [];
	res.push([grad_color[0], "0%"]);
	for (let i = 0; i < percent.length - 1; i++) {
		res.push([
			grad_color[i],
			// Uses average percent of endpoints as the color
			(
				(parseFloat(percent[i]) + parseFloat(percent[i + 1])) /
				2
			).toString() + "%",
		]);
	}
	return res;
}
/*  Calculate the Angle for given percentage  */
function calAngle(percentvalue) {
	return percentvalue * 1.8;
}
/*  Calculate the point(in svg coordinates) for given angle and radius
	with respect to the center of the speedometer  */
function calPt(angle, radius) {
	const rad = (angle * Math.PI) / 180;
	return { x: Rx - radius * Math.cos(rad), y: Ry - radius * Math.sin(rad) };
}
/*  Calculate the line endpt for given angle and length  */
function calLine(angle, length) {
	const rad = (angle * Math.PI) / 180;
	return { x: length * Math.cos(rad), y: length * Math.sin(rad) };
}
/********** Calculate Triangle(pointer) Path **********/
function calTri(value) {
	const getvalue = value.y ?? value;
	const { standards, percent } = props.chart_config;
	// calculate the percentage of the value (based on standards & percent ranges)
	let percentvalue = 0;
	// if the value exceeds min or max standards
	if (getvalue <= standards[0]) percentvalue = 0;
	else if (getvalue >= standards[standards.length - 1]) percentvalue = 100;
	else {
		let idx = 0;
		while (standards[idx] < getvalue) idx += 1;
		// calculate by proportion in the chosen range
		percentvalue =
			((getvalue - standards[idx - 1]) /
				(standards[idx] - standards[idx - 1])) *
				(percent[idx] - percent[idx - 1]) +
			percent[idx - 1];
	}
	let triAngle = calAngle(percentvalue);
	// this is the coord. of the top vertex of the triangle
	let triPt = calPt(triAngle, R - Llength);
	/***** Render logic *****/
	/* 1. left side edge    */
	/* 2. bottom edge		*/
	/* 3. close the area	*/
	/************************/
	let res = "";
	// the "half" of the top angle of the triangle(pointer)
	// in this case, top angle = 40 deg
	let topAngle = 20;
	// the side length (both sides) of the triangle
	// it is an isosceles triangle
	let sideLength = 30;
	// start pt
	res += "M " + triPt.x + " " + triPt.y + "\n";
	// left side edge
	res +=
		"l " +
		calLine(triAngle + topAngle, sideLength).x +
		" " +
		calLine(triAngle + topAngle, sideLength).y +
		"\n";
	// bottom edge (perpendicular to the radius line)
	// utilitizes simple trigonometric relations
	res +=
		"l " +
		calLine(
			triAngle - 90,
			2 * sideLength * Math.sin((topAngle * Math.PI) / 180)
		).x +
		" " +
		calLine(
			triAngle - 90,
			2 * sideLength * Math.sin((topAngle * Math.PI) / 180)
		).y +
		"\n";
	res += "z\n";
	return res;
}
/***** Calculate Speedometer Arc Path *****/
function CheckpathD(startpercent, endpercent) {
	let startAngle = calAngle(startpercent, props.chart_config);
	let endAngle = calAngle(endpercent, props.chart_config);
	// coord. of startPt (outer circle) with respect to the svg coord.
	let startPt = calPt(startAngle, R);
	let endPt = calPt(endAngle, R);
	// coord. of startPt (inner circle)
	let startbotPt = calPt(startAngle, R - Llength);
	// the line to close outer & inner circle at endPt
	let line = calLine(endAngle, Llength);
	/***************** Render logic *****************/
	/* 1. outer circle      						*/
	/* 2. the line to close outer & innter circle	*/
	/* 3. inner circle								*/
	/* 4. close the area							*/
	/************************************************/
	let res = "";
	res += "M " + startPt.x + " " + startPt.y + "\n";
	// outer circle
	res += "A " + R + " " + R + " 0 0 1 " + endPt.x + " " + endPt.y + "\n";
	// the line to close
	res += "l " + line.x + " " + line.y + "\n";
	// inner circle
	res +=
		"A " +
		(R - Llength) +
		" " +
		(R - Llength) +
		" 0 0 0 " +
		startbotPt.x +
		" " +
		startbotPt.y +
		"\n";
	// close
	res += "z\n";
	return res;
}
/* Handles the format of the blocks under speedometer */
function handleTable(list) {
	let res = [[], []];
	// 2 by N/2
	for (let i = 0; i <= (list.length - 1) / 2; i++) {
		res[0].push([2 * i, list[2 * i].x ?? list[2 * i]]);
		if (2 * i + 1 < list.length)
			res[1].push([2 * i + 1, list[2 * i + 1].x ?? list[2 * i + 1]]);
	}
	return res;
}
</script>
<template>
	<div v-if="activeChart === 'SpeedometerChart'" class="speedometer">
		<g>
			<svg
				viewBox="0 0 550 260"
				xmlns="http://www.w3.org/2000/svg"
				class="initial-animation-1"
			>
				<!-- Color Gradient -->
				<defs>
					<linearGradient
						:id="'grad1-' + chart_config.name"
						x1="0%"
						y1="0%"
						x2="100%"
						y2="0%"
					>
						<stop
							v-for="grad in calGradComp()"
							:key="grad"
							:offset="grad[1]"
							:style="{
								'stop-color': grad[0],
								'stop-opacity': 1,
							}"
						/>
					</linearGradient>
				</defs>
				<!-- Render Speedometer arc -->
				<path
					:fill="'url(#grad1-' + chart_config.name + ')'"
					:d="CheckpathD(0, 100)"
				/>
				<!-- Render pointer -->
				<path
					fill="#ddd"
					stroke="#ddd"
					:d="calTri(series[0].data[targetvalue])"
				/>
				<text
					:x="Rx"
					:y="Ry"
					dominant-baseline="start"
					text-anchor="middle"
					class="small"
				>
					<!-- Render the name of the dataset and the specific data title -->
					<tspan>
						{{
							chart_config.name +
							" (" +
							(series[0].data[targetvalue].x ??
								chart_config.categories[targetvalue]) +
							")"
						}}
					</tspan>
				</text>
				<!-- Render the value -->
				<text
					:x="Rx - 10"
					:y="Ry - 35"
					dominant-baseline="start"
					text-anchor="middle"
					class="heavy"
				>
					{{
						series[0].data[targetvalue].y ??
						series[0].data[targetvalue]
					}}
				</text>
				<!-- Render the unit of the data type -->
				<text
					:x="Rx + 90"
					:y="Ry - 30"
					dominant-baseline="start"
					text-anchor="middle"
					class="small"
				>
					<tspan>{{ chart_config.unit }}</tspan>
				</text>
			</svg>
			<div class="tablediv">
				<table>
					<tbody>
						<!-- Table size: 2 * ceil(N/2) -->
						<tr
							v-for="(subTable, i) in handleTable(
								series[0].data[0].x
									? series[0].data
									: chart_config.categories
							)"
							:key="i"
						>
							<td
								v-for="(submatter, i) in subTable"
								:key="i"
								:data-name="submatter[0].toString()"
								@mouseenter="toggleActive"
								@mouseleave="toggleActiveToNull"
								:class="'initial-animation-' + submatter[0]"
							>
								<!-- Value of the data title -->
								<div class="mattertable">
									{{ submatter[1] }}
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</g>
	</div>
</template>
<style scoped lang="scss">
.speedometer {
	user-select: none;
}
.small {
	font: 16px sans-serif;
	fill: #ddd;
}
.smallsub {
	font: 12px sans-serif;
	fill: #ddd;
}
.heavy {
	font: 60px sans-serif;
	fill: #ddd;
}
.tablediv {
	display: flex;
	justify-content: center;
}
table {
	/* border-collapse: collapse; */
	/* width: 90%; */
	border-spacing: 3px;
	width: 90%;
	table-layout: fixed;
}
th,
td {
	width: 30%;
	/* border: 2px solid #666; */
	padding: 6px;
	text-align: left;
	border-radius: 5px;
	font-size: 12px;
	background-color: #444444;
}
td:hover {
	background-color: #111111;
	cursor: default;
}
.mattertable {
	width: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
}
.mattervalue {
	display: flex;
	justify-content: space-around;
	align-items: end;
	font-size: 10px;
}
.mattername {
	font-size: 14px;
	font-family: sans-serif;
}
@keyframes ease-in {
	0% {
		opacity: 0;
	}

	100% {
		opacity: 1;
	}
}

@for $i from 1 through 20 {
	.initial-animation-#{$i} {
		animation-name: ease-in;
		animation-duration: 0.3s;
		animation-delay: 0.1s * ($i - 1);
		animation-timing-function: linear;
		animation-fill-mode: forwards;
		opacity: 0;
	}
}
</style>
