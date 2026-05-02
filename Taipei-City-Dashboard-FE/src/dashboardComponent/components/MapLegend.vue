<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import bus from "../assets/map/bus.png";
import metro from "../assets/map/metro.png";
import triangle_green from "../assets/map/triangle_green.png";
import triangle_white from "../assets/map/triangle_white.png";
import bike_green from "../assets/map/bike_green.png";
import bike_orange from "../assets/map/bike_orange.png";
import bike_red from "../assets/map/bike_red.png";
import cross_bold from "../assets/map/cross_bold.png";
import cross_normal from "../assets/map/cross_normal.png";
import cctv from "../assets/map/cctv.png";
import live from "../assets/map/live.png";

const eco_cup = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='10' fill='%234CAF50'/%3E%3C/svg%3E";

const props = defineProps([
	"chart_config",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);
const emits = defineEmits([
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"toggleLayer",
	"fly"
]);

function returnIcon(name) {
	switch (name) {
	case "bus":
		return bus;
	case "metro":
		return metro;
	case "triangle_green":
		return triangle_green;
	case "triangle_white":
		return triangle_white;
	case "bike_green":
		return bike_green;
	case "bike_orange":
		return bike_orange;
	case "bike_red":
		return bike_red;
	case "cross_bold":
		return cross_bold;
	case "cross_normal":
		return cross_normal;
	case "cctv":
		return cctv;
	case "live":
		return live;
	case "eco_cup":
		return eco_cup;
	default:
		return "";
	}
}

const selectedIndex = ref(null);
const selectedIndices = ref(new Set());

function handleDataSelection(index) {
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}
	if (props.map_filter.mode === "byLayerToggle") {
		const {name} = props.series[index];
		if (selectedIndices.value.has(index)) {
			selectedIndices.value.delete(index);
			emits("toggleLayer", props.map_config, name, true);
		} else {
			selectedIndices.value.add(index);
			emits("toggleLayer", props.map_config, name, false);
		}
		return;
	}
	if (index !== selectedIndex.value) {
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				props.series[index].name,
				null
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits("filterByLayer", props.map_config, props.series[index].name);
		}
		selectedIndex.value = index;
	} else {
		if (props.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
}
</script>

<template>
  <div class="maplegend">
    <div class="maplegend-legend">
      <button
        v-for="(item, index) in series"
        :key="item.name"
        :class="{
          'maplegend-legend-item': true,
          'maplegend-filter': map_filter_on && map_filter,
          'maplegend-selected':
            map_filter_on && (map_filter?.mode === 'byLayerToggle' ? !selectedIndices.has(index) : selectedIndex === index),
        }"
        @click="handleDataSelection(index)"
      >
        <!-- Show different icons for different map types -->
        <div
          v-if="item.type !== 'symbol'"
          :style="{
            backgroundColor: `${chart_config.color[index]}`,
            height: item.type === 'line' ? '0.4rem' : '1rem',
            borderRadius: item.type === 'circle' ? '50%' : '2px',
          }"
        />
        <img
          v-else
          :src="returnIcon(item.icon)"
        >
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
* {
	margin: 0;
	padding: 0;
	font-family: "微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans",
		"Helvetica";
	overflow: hidden;
}

button {
	border: none;
	background-color: transparent;
}
.maplegend {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-top: -var(--font-ms);
	overflow: visible;

	&-legend {
		width: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		column-gap: 0.5rem;
		row-gap: 0.5rem;
		overflow: visible;

		&-item {
			display: flex;
			align-items: center;
			padding: 5px 10px 5px 5px;
			border: 1px solid transparent;
			border-radius: 5px;
			transition: box-shadow 0.2s;
			cursor: auto;

			div:first-child,
			img {
				width: var(--font-ms);
				margin-right: 0.75rem;
			}

			h5 {
				color: var(--color-complement-text);
				font-size: 0.75rem;
				text-align: left;
			}

			h6 {
				color: var(--color-normal-text);
				font-size: var(--font-ms);
				font-weight: 400;
				text-align: left;
			}
		}
	}

	&-filter {
		border: 1px solid var(--color-border);
		cursor: pointer;

		&:hover {
			box-shadow: 0px 0px 5px black;
		}
	}

	&-selected {
		box-shadow: 0px 0px 5px black;
	}
}
</style>
