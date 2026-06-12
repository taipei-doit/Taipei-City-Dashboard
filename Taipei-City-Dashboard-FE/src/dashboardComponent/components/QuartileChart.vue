<script setup>
import { computed, ref } from "vue";

const props = defineProps([
	"chart_config",
	"activeChart",
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
	"fly",
]);

const selectedIndex = ref(null);

const parseSeries = computed(() => {
	// categories 順序：優先從 chart_config 拿，否則 hardcode
	const categories = props.chart_config?.categories ?? [
		"q1",
		"median",
		"q3",
		"min",
		"max",
	];

	const idx = (key) => categories.indexOf(key);

	return props.series.map((it) => {
		const d = it.data ?? [];
		return {
			name: it.name ?? "",
			q1: d[idx("q1")] ?? 0,
			median: d[idx("median")] ?? 0,
			q3: d[idx("q3")] ?? 0,
			// min: d[idx("min")] ?? d[idx("q1")] ?? 0,
			// max: d[idx("max")] ?? d[idx("q3")] ?? 0,
		};
	});
});

const shouldScroll = computed(() => parseSeries.value.length > 4);

/** color */
function colorForIndex(i) {
	const colors = props.chart_config?.color;
	return Array.isArray(colors) && colors.length
		? colors[i % colors.length]
		: "var(--color-highlight)";
}

/** number format */
function formatNumber(v) {
	if (!Number.isFinite(v)) return "-";
	return new Intl.NumberFormat("zh-TW").format(Math.round(v));
}

/** quartile bar position */
function rangeStyle(i) {
	return {
		left: "16.6667%",
		width: "66.6667%",
		backgroundColor: colorForIndex(i),
	};
}

function medianStyle() {
	return { left: "50%" };
}

function whiskerStyle(type) {
	return { left: type === "min" ? "0%" : "100%" };
}

const handleDataSelection = (name) => {
	// Dean 待測試 20260527
	if (!props.map_filter || !props.map_filter_on) {
		return;
	}

	if (name !== selectedIndex.value) {
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				name,
				null,
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits("filterByLayer", props.map_config, name);
		}
		selectedIndex.value = name;
	} else {
		if (props.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
};
</script>

<template>
	<div v-if="activeChart === 'QuartileChart'" class="QuartileChart">
		<div
			:class="[
				'QuartileChart__list',
				{
					'QuartileChart__list--scroll': shouldScroll,
				},
			]"
		>
			<div
				v-for="(it, i) in parseSeries"
				:key="`${it.name}-${i}`"
				class="QuartileChart__row"
			>
				<!-- LEFT -->
				<div class="QuartileChart__left">
					<div class="QuartileChart__meta">
						<div
							class="QuartileChart__title"
							:class="{
								'QuartileChart__title--active':
									selectedIndex === it.name,
							}"
							@click="handleDataSelection(it.name)"
						>
							{{ it.name }}
						</div>
					</div>
				</div>

				<!-- RIGHT -->
				<div class="QuartileChart__right">
					<div class="QuartileChart__labels">
						<div class="QuartileChart__label">
							<div class="QuartileChart__labelKey">Q1</div>
							<div class="QuartileChart__labelVal">
								{{ formatNumber(it.q1) }}
							</div>
						</div>

						<div class="QuartileChart__label">
							<div class="QuartileChart__labelKey">Q2</div>
							<div class="QuartileChart__labelVal">
								{{ formatNumber(it.median) }}
							</div>
						</div>

						<div class="QuartileChart__label">
							<div class="QuartileChart__labelKey">Q3</div>
							<div class="QuartileChart__labelVal">
								{{ formatNumber(it.q3) }}
							</div>
						</div>
					</div>

					<!-- TRACK -->
					<div class="QuartileChart__track">
						<div
							class="QuartileChart__trackLine"
							:style="{
								backgroundColor: colorForIndex(i),
								opacity: 0.25,
							}"
						/>

						<div
							class="QuartileChart__whisker QuartileChart__whisker--min"
							:style="whiskerStyle('min')"
						/>

						<div
							class="QuartileChart__whisker QuartileChart__whisker--max"
							:style="whiskerStyle('max')"
						/>

						<div
							class="QuartileChart__range"
							:style="rangeStyle(i)"
						/>

						<div
							class="QuartileChart__median"
							:style="medianStyle()"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.QuartileChart {
	width: 100%;
	height: 100%;
	overflow: hidden;

	&__list {
		height: 100%;
		overflow: hidden;
	}

	&__list--scroll {
		overflow-y: auto;
	}

	&__row {
		display: grid;
		grid-template-columns: 120px 1fr;
		align-items: center;
		padding: 8px 4px;
		border-bottom: 1px solid var(--color-border);
	}

	&__left {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	&__title {
		font-weight: 600;
		cursor: pointer;
	}

	&__title--active {
		color: var(--color-highlight);
	}

	&__labels {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		font-size: 12px;
		margin-bottom: 4px;
	}

	&__label {
		text-align: center;
	}

	&__labelVal {
		font-weight: 600;
	}

	&__track {
		position: relative;
		height: 14px;
	}

	&__trackLine {
		position: absolute;
		top: 50%;
		left: 0;
		right: 0;
		height: 3px;
		transform: translateY(-50%);
		border-radius: 999px;
	}

	&__range {
		position: absolute;
		top: 50%;
		height: 5px;
		transform: translateY(-50%);
		border-radius: 999px;
	}

	&__median {
		position: absolute;
		top: 50%;
		width: 10px;
		height: 10px;
		transform: translate(-50%, -50%);
		border-radius: 50%;
		background: #fff;
		border: 2px solid rgba(0, 0, 0, 0.3);
	}

	&__whisker {
		position: absolute;
		top: 50%;
		width: 2px;
		height: 10px;
		transform: translate(-50%, -50%);
		background: rgba(0, 0, 0, 0.3);
	}
}
</style>
