<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, computed } from "vue";

import MetroCarDensity from "./MetroCarDensity.vue";
import { lineInfo } from "../utilities/taipeiMetroLines";

const props = defineProps(["chart_config", "activeChart", "series"]);

// const emits = defineEmits([
// 	"filterByParam",
// 	"filterByLayer",
// 	"clearByParamFilter",
// 	"clearByLayerFilter",
// 	"fly"
// ]);

const color = ref(props.chart_config.color[0]);
const line = computed(() => {
	if (props.series[0].data[0].x.includes("BR")) {
		return "BR";
	} else if (props.series[0].data[0].x.includes("R")) {
		return "R";
	} else if (props.series[0].data[0].x.includes("BL")) {
		return "BL";
	} else if (props.series[0].data[0].x.includes("G")) {
		return "G";
	} else if (props.series[0].data[0].x.includes("O")) {
		return "O";
	}
	return "R";
});

const parsedSeries = computed(() => {

	const parsedData = [
		{ name: line.value, data: [] },
		{ name: line.value, data: [] },
	];

	let toBeParsed = JSON.parse(JSON.stringify(props.series[0].data));

	toBeParsed.forEach((element) => {
		element.y = element.y.toString();

		if (element.x.includes("A")) {
			element.x = element.x.replace("A", "");
			parsedData[0].data.push(element);
		} else if (element.x.includes("D")) {
			element.x = element.x.replace("D", "");
			parsedData[1].data.push(element);
		}
	});

	return parsedData;
});
</script>

<template>
  <div
    v-if="activeChart === 'MetroChart'"
    class="metrochart"
  >
    <div
      v-for="(item, index) in lineInfo[line]"
      :key="`${line}-${index}`"
      :class="`initial-animation-${index + 1}`"
    >
      <!-- Shows station name / station label / density level of each train car -->
      <div
        v-if="item.id !== '0'"
        class="metrochart-block"
      >
        <h5>
          {{
            item.name.length < 6
              ? item.name
              : `${item.name.slice(0, 4)}...`
          }}
        </h5>
        <!-- Will show a different style if the station is a terminal station -->
        <div
          class="metrochart-block-tag"
          :style="{
            borderColor: color,
            backgroundColor:
              index === lineInfo[line].length - 1 ||
              index === 0 ||
              item.id === 'O21'
                ? color
                : 'white',
          }"
        >
          <p
            :style="{
              color:
                index === lineInfo[line].length - 1 ||
                index === 0 ||
                item.id === 'O21'
                  ? 'white'
                  : 'black',
            }"
          >
            {{ line }}
          </p>
          <p
            :style="{
              color:
                index === lineInfo[line].length - 1 ||
                index === 0 ||
                item.id === 'O21'
                  ? 'white'
                  : 'black',
            }"
          >
            {{ item.id.slice(-2) }}
          </p>
        </div>
        <MetroCarDensity
          :weight="
            parsedSeries[0].data.find(
              (element) => element.x === item.id
            )
          "
          direction="asc"
        />
        <MetroCarDensity
          :weight="
            parsedSeries[1].data.find(
              (element) => element.x === item.id
            )
          "
          direction="desc"
        />
      </div>
      <!-- Just shows the line connecting stations -->
      <div
        v-if="item.id !== '0' && item.id !== 'O21'"
        class="metrochart-block"
      >
        <div />
        <div
          class="metrochart-block-line"
          :style="{
            backgroundColor:
              index === lineInfo[line].length - 1
                ? 'transparent'
                : color,
          }"
        />
      </div>
      <div
        v-if="item.id === '0'"
        class="metrochart-block"
      >
        <div class="metrochart-block-break">
          <div />
          <p>{{ item.name }}</p>
          <div />
        </div>
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
		margin: 0 0.4rem 0 0;
		font-size: 0.7rem;
		font-weight: 400;
		pointer-events: none;
		user-select: none;
		color: var(--color-normal-text);
	}

	p {
		color: black;
		font-size: 0.6rem;
		line-height: 0.6rem;
		pointer-events: none;
		user-select: none;
		margin: 0;
	}

	&-block {
		display: grid;
		grid-template-columns: 3.9rem 20px 1fr 1fr;

		&-tag {
			min-width: var(--font-ms);
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
			height: var(--font-ms);
			margin: 0px 6px;
		}

		&-break {
			height: 2rem;
			grid-column: 1 / -1;
			display: flex;
			align-items: center;
			justify-content: center;
			column-gap: var(--font-ms);
			margin: 0.5rem 0;

			p {
				display: flex;
				align-items: center;
				height: var(--font-ms);
				color: var(--color-complement-text);
				font-size: var(--font-ms);
				overflow: visible;
			}
			div {
				flex: 1;
				border-bottom: dashed 1px
					var(--color-complement-text);
			}
		}
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

