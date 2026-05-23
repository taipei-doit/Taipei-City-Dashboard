<!-- Developed by Bombs King, Taipei Codefest 2026 -->
 
<script setup>
import { computed, nextTick, ref, watch } from "vue";
import "material-icons/iconfont/material-icons.css";
import MapPickButton from "../../components/map/MapPickButton.vue";
import { useMapStore } from "../../store/mapStore";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
	"buffer_filter_options",
	"buffer_filter_value",
	/** 租屋熱區：與距離選單並排，顯示「地圖選點」按鈕 */
	"map_pick_show",
	"map_pick_armed",
	/** 租屋熱區：四分位列可點選以切換地圖熱力圖 */
	"rent_heatmap_row_mode",
	/** 目前選中的熱力：main（黃）| whole | suite | shared */
	"heatmap_chart_focus",
]);

const emit = defineEmits([
	"update:bufferFilter",
	"toggleMapPick",
	"rentHeatmapFocus",
	"filterByParam",
	"clearByParamFilter",
]);

const mapStore = useMapStore();

const items = computed(() => (Array.isArray(props.series) ? props.series : []));
const selectedCity = ref("");
const selectedDistrict = ref("");

const normalizedItems = computed(() =>
	items.value
		.map((it, index) => {
			const isNoData =
				Boolean(it.is_no_data) || it.no_data_reason != null;

			const q1 = it.q1 == null ? null : Number(it.q1);
			const median = it.median == null ? null : Number(it.median);
			const q3 = it.q3 == null ? null : Number(it.q3);

			// For "real" data rows, ensure quartile values are valid.
			if (!isNoData) {
				if (!Number.isFinite(q1) || !Number.isFinite(median) || !Number.isFinite(q3)) {
					return null;
				}
			}

			const min =
				it.min == null
					? (q1 ?? null)
					: Number(it.min);
			const max =
				it.max == null
					? (q3 ?? null)
					: Number(it.max);

			const sortKey = Number.isFinite(Number(it.sort_key))
				? Number(it.sort_key)
				: index;
			return {
				name: String(it.name ?? ""),
				icon: it.icon ? String(it.icon) : "stacked_line_chart",
				cityName: String(it.city_name ?? ""),
				districtName: String(it.district_name ?? ""),
				sortKey,
				isNoData,
				noDataReason: it.no_data_reason ?? null,
				min,
				q1,
				median,
				q3,
				max,
			};
		})
		.filter(Boolean),
);

const cityOptions = computed(() => {
	const values = [
		...new Set(
			normalizedItems.value.map((it) => it.cityName).filter(Boolean),
		),
	];
	return values.sort((a, b) => a.localeCompare(b, "zh-Hant"));
});

/** 雙北資料：縣市下拉排序仍照筆劃，但開啟組件時預設優先臺北市 */
const PREFERRED_DEFAULT_CITIES = ["臺北市", "台北市"];

function defaultCityFromOptions(cities) {
	if (!cities.length) return "";
	for (const name of PREFERRED_DEFAULT_CITIES) {
		if (cities.includes(name)) return name;
	}
	return cities[0];
}

const districtOptions = computed(() => {
	const source = normalizedItems.value.filter((it) => {
		if (!selectedCity.value) return true;
		return it.cityName === selectedCity.value;
	});
	const values = [
		...new Set(source.map((it) => it.districtName).filter(Boolean)),
	];
	return values.sort((a, b) => {
		if (a === "全市" && b !== "全市") return -1;
		if (b === "全市" && a !== "全市") return 1;
		return a.localeCompare(b, "zh-Hant");
	});
});

const filteredItems = computed(() => {
	let result = [...normalizedItems.value];
	if (selectedCity.value) {
		result = result.filter((it) => it.cityName === selectedCity.value);
	}
	if (selectedDistrict.value) {
		result = result.filter(
			(it) => it.districtName === selectedDistrict.value,
		);
	}
	// Generic ordering:
	// - Prefer API-provided sort_key (if exists)
	// - Otherwise preserve incoming order (map index)
	return result.sort((a, b) => a.sortKey - b.sortKey);
});

const displayItems = computed(() =>
	filteredItems.value.filter((it) => !it.isNoData),
);

const hasData = computed(() => displayItems.value.length > 0);

const noDataReason = computed(() => {
	const found =
		filteredItems.value.find((it) => it.isNoData && it.noDataReason) ||
		null;
	return found?.noDataReason || "";
});

const shouldScroll = computed(() => displayItems.value.length > 4);

const showAreaSelectors = computed(() =>
	normalizedItems.value.some((it) => it.cityName || it.districtName),
);

const bufferFilterOptionsList = computed(() =>
	Array.isArray(props.buffer_filter_options) ? props.buffer_filter_options : [],
);

const showBufferSelector = computed(
	() => bufferFilterOptionsList.value.length > 0,
);

const showMapPickControl = computed(() => Boolean(props.map_pick_show));

const showFilterRow = computed(
	() =>
		showAreaSelectors.value ||
		showBufferSelector.value ||
		showMapPickControl.value,
);

const selectedBufferModel = computed({
	get() {
		const opts = bufferFilterOptionsList.value;
		const v = props.buffer_filter_value;
		if (v != null && opts.some((o) => o.value === v)) {
			return v;
		}
		return opts[0]?.value ?? "";
	},
	set(next) {
		emit("update:bufferFilter", next);
	},
});

const bufferFilterTransitionKey = computed(() =>
	[
		selectedCity.value || "all",
		selectedDistrict.value || "all",
		selectedBufferModel.value || "buf",
	].join("-"),
);

watch(
	normalizedItems,
	() => {
		if (showAreaSelectors.value) {
			if (
				!selectedCity.value ||
				!cityOptions.value.includes(selectedCity.value)
			) {
				selectedCity.value = defaultCityFromOptions(cityOptions.value);
			}
			if (
				!selectedDistrict.value ||
				!districtOptions.value.includes(selectedDistrict.value)
			) {
				selectedDistrict.value = districtOptions.value[0] ?? "";
			}
		} else {
			selectedCity.value = "";
			selectedDistrict.value = "";
		}
	},
	{ immediate: true },
);

watch(selectedCity, () => {
	if (!districtOptions.value.includes(selectedDistrict.value)) {
		selectedDistrict.value = districtOptions.value[0] ?? "";
	}
});

function pushRentMapFilter() {
	if (!props.map_filter_on || !props.map_config?.length) return;
	const mf = props.map_filter;
	if (!mf || mf.mode !== "byParam" || !mf.byParam) return;

	const bp = mf.byParam;
	const city = selectedCity.value;
	const dist = selectedDistrict.value;

	if (!city) {
		emit("clearByParamFilter", props.map_config);
		return;
	}

	// 行政區選「全市」：圖表仍顯示該縣市彙總，地圖取消篩選以恢復雙北（或單一市）全區著色（不變更目前縮放與中心）
	if (dist === "全市" || dist === "") {
		emit("clearByParamFilter", props.map_config);
		return;
	}

	if (bp.xParam && bp.yParam) {
		emit("filterByParam", mf, props.map_config, dist, city);
	} else if (bp.xParam) {
		emit("filterByParam", mf, props.map_config, dist, null);
	}
}

watch(
	[selectedCity, selectedDistrict],
	() => {
		pushRentMapFilter();
	},
	{ immediate: true },
);

watch(
	() => mapStore.quartileDistrictFromMap?.seq,
	(seq) => {
		if (seq == null || !showAreaSelectors.value) return;
		const m = mapStore.quartileDistrictFromMap;
		if (!m?.tName) return;

		const matchCity =
			cityOptions.value.find((c) => c === m.pName) ??
			cityOptions.value.find(
				(c) =>
					m.pName &&
					(m.pName.includes(c) || c.includes(m.pName)),
			);
		if (!matchCity) return;

		// 與圖資 TNAME 對齊的行政區名（不依賴 districtOptions 時序）
		const districtNames = [
			...new Set(
				normalizedItems.value
					.filter((it) => it.cityName === matchCity)
					.map((it) => it.districtName)
					.filter((d) => d && d !== "全市"),
			),
		];
		const matchDist =
			districtNames.find((d) => d === m.tName) ??
			districtNames.find(
				(d) =>
					m.tName &&
					(m.tName.includes(d) || d.includes(m.tName)),
			);
		if (!matchDist) return;

		// 地圖上再點同一行政區：組件改為該縣市「全市」、地圖由 pushRentMapFilter 清篩選並還原視角
		if (
			selectedCity.value === matchCity &&
			selectedDistrict.value === matchDist
		) {
			selectedDistrict.value = "全市";
			return;
		}

		selectedCity.value = matchCity;
		nextTick(() => {
			if (matchDist) selectedDistrict.value = matchDist;
		});
	},
);

function colorForIndex(i) {
	const colors = props.chart_config?.color;
	return Array.isArray(colors) && colors.length > 0
		? colors[i % colors.length]
		: "var(--color-highlight)";
}

function formatNumber(v) {
	if (!Number.isFinite(v)) return "-";
	// Match design: display as integer to avoid ugly decimals.
	const rounded = Math.round(v);
	return new Intl.NumberFormat("zh-TW").format(rounded);
}

function rangeStyle(_it, i) {
	// Align segment with the center of Q1/Q3 label columns (1/6 -> 5/6)
	return {
		left: "16.6667%",
		width: "66.6667%",
		backgroundColor: colorForIndex(i),
	};
}

function medianStyle() {
	return { left: "50%" };
}

function rentHeatmapFocusFromRow(it, rowIndex) {
	const name = String(it?.name || "");
	if (name.includes("全部")) return "main";
	if (name.includes("整戶")) return "whole";
	if (name.includes("獨立套房")) return "suite";
	if (name.includes("分租") || name.includes("雅房")) return "shared";
	const sk = Number(it.sortKey);
	if (sk === 1) return "main";
	if (sk === 2) return "whole";
	if (sk === 3) return "suite";
	if (sk === 4) return "shared";
	if (rowIndex === 0) return "main";
	if (rowIndex === 1) return "whole";
	if (rowIndex === 2) return "suite";
	if (rowIndex === 3) return "shared";
	return "main";
}

function onRentHeatmapRowClick(it, rowIndex) {
	if (!props.rent_heatmap_row_mode) return;
	emit("rentHeatmapFocus", rentHeatmapFocusFromRow(it, rowIndex));
}

function rentHeatmapRowActive(it, rowIndex) {
	if (!props.rent_heatmap_row_mode) return false;
	const f =
		props.heatmap_chart_focus != null
			? String(props.heatmap_chart_focus)
			: "main";
	return f === rentHeatmapFocusFromRow(it, rowIndex);
}

function whiskerStyle(type) {
	// color is applied via inline styles below
	return { left: type === "min" ? "0%" : "100%" };
}
</script>

<template>
	<div v-if="activeChart === 'QuartileChart'" class="QuartileChart">
		<div
			v-if="showFilterRow"
			class="QuartileChart__filters"
			:class="{
				'QuartileChart__filters--bufferOnly':
					showBufferSelector && !showAreaSelectors,
				'QuartileChart__filters--bufferAndPick':
					showBufferSelector &&
					showMapPickControl &&
					!showAreaSelectors,
			}"
		>
			<select v-if="showAreaSelectors" v-model="selectedCity">
				<option v-for="city in cityOptions" :key="city" :value="city">
					{{ city }}
				</option>
			</select>
			<select v-if="showAreaSelectors" v-model="selectedDistrict">
				<option
					v-for="district in districtOptions"
					:key="district"
					:value="district"
				>
					{{ district }}
				</option>
			</select>
			<select
				v-if="showBufferSelector"
				v-model="selectedBufferModel"
				class="QuartileChart__selectBuffer"
			>
				<option
					v-for="opt in bufferFilterOptionsList"
					:key="opt.value"
					:value="opt.value"
				>
					{{ opt.label }}
				</option>
			</select>
			<MapPickButton
				v-if="showMapPickControl"
				title="先按此鈕，再於地圖上點選查詢中心"
				aria-label="於地圖上點選租屋熱區查詢中心"
				:armed="map_pick_armed"
				@toggle="emit('toggleMapPick')"
			/>
		</div>

		<Transition name="quartile-fade" mode="out-in">
			<div
				:key="bufferFilterTransitionKey"
				:class="[
					'QuartileChart__list',
					{
						'QuartileChart__list--scroll': shouldScroll,
						'QuartileChart__list--fit4': !shouldScroll,
					},
				]"
			>
				<div v-if="hasData">
					<div
						v-for="(it, i) in displayItems"
						:key="`${it.name}-${i}`"
						class="QuartileChart__row"
						:class="{
							'QuartileChart__row--selectable': rent_heatmap_row_mode,
							'QuartileChart__row--active': rentHeatmapRowActive(it, i),
						}"
						role="button"
						:tabindex="rent_heatmap_row_mode ? 0 : undefined"
						@click="onRentHeatmapRowClick(it, i)"
						@keydown.enter.prevent="onRentHeatmapRowClick(it, i)"
						@keydown.space.prevent="onRentHeatmapRowClick(it, i)"
					>
						<div class="QuartileChart__left">
							<div
								class="QuartileChart__icon"
								:style="{ backgroundColor: colorForIndex(i) }"
							>
								<span>{{ it.icon }}</span>
							</div>
							<div class="QuartileChart__meta">
								<div class="QuartileChart__title">
									{{ it.name }}
								</div>
								<div class="QuartileChart__unit">
									{{
										props.chart_config?.unit
											? `單位：${props.chart_config.unit}`
											: ""
									}}
								</div>
							</div>
						</div>

						<div class="QuartileChart__right">
							<div class="QuartileChart__labels">
								<div class="QuartileChart__label">
									<div class="QuartileChart__labelKey">Q1</div>
									<div
										class="QuartileChart__labelVal"
										:style="{ color: colorForIndex(i) }"
									>
										{{ formatNumber(it.q1) }}
									</div>
								</div>
								<div class="QuartileChart__label">
									<div class="QuartileChart__labelKey">
										中位數
									</div>
									<div
										class="QuartileChart__labelVal QuartileChart__labelVal--median"
										:style="{ color: colorForIndex(i) }"
									>
										{{ formatNumber(it.median) }}
									</div>
								</div>
								<div class="QuartileChart__label">
									<div class="QuartileChart__labelKey">Q3</div>
									<div
										class="QuartileChart__labelVal"
										:style="{ color: colorForIndex(i) }"
									>
										{{ formatNumber(it.q3) }}
									</div>
								</div>
							</div>

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
									:style="{
										...whiskerStyle('min', i),
										backgroundColor: colorForIndex(i),
										opacity: 0.42,
									}"
								/>
								<div
									class="QuartileChart__whisker QuartileChart__whisker--max"
									:style="{
										...whiskerStyle('max', i),
										backgroundColor: colorForIndex(i),
										opacity: 0.42,
									}"
								/>
								<div
									class="QuartileChart__range"
									:style="rangeStyle(it, i)"
								/>
								<div
									class="QuartileChart__median"
									:style="medianStyle(it)"
								/>
							</div>
						</div>
					</div>
				</div>
				<div v-else class="QuartileChart__noData">
					{{ noDataReason }}
				</div>
			</div>
		</Transition>
	</div>
</template>

<style scoped lang="scss">
.QuartileChart {
	height: 100%;
	width: 100%;
	overflow: hidden;
	overflow-x: hidden;
	box-sizing: border-box;
	padding-bottom: 8px;

	&__list {
		height: 100%;
		min-height: 0;
		overflow: hidden;
		box-sizing: border-box;
		padding-bottom: 8px;
	}

	&__list--scroll {
		overflow-y: auto;
	}

	&__list--fit4 {
		overflow: hidden;
	}

	&__filters {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(85px, max-content));
		justify-content: start;
		gap: 6px;
		padding: 2px 2px 6px;

		select {
			height: auto;
			min-height: auto;
			font-size: var(--font-ms);
			line-height: 1.2;
			padding: 2px 6px;
			width: 85px;
			max-width: 44vw;
			justify-self: start;
		}

		&--bufferOnly select {
			min-width: 100px;
			width: auto;
		}

		&--bufferAndPick {
			display: flex;
			justify-content: space-between;
			align-items: center;
			width: 100%;
			box-sizing: border-box;
			gap: 8px;
		}
	}

	&__selectBuffer {
		min-width: 100px;
		width: auto !important;
		max-width: 50vw !important;
	}

	&__noData {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 12px;
		text-align: center;
		font-size: var(--font-ms);
		color: var(--color-complement-text);
	}

	&__row {
		display: grid;
		grid-template-columns: minmax(88px, 120px) minmax(0, 1fr);
		align-items: center;
		column-gap: 6px;
		padding: 6px 2px;
		border-bottom: 1px solid var(--color-border);

		&.QuartileChart__row--selectable {
			column-gap: 2px;
			grid-template-columns: minmax(72px, 100px) minmax(0, 1fr);
		}
	}

	&__row--selectable {
		cursor: pointer;
		border-radius: 8px;
		margin: 3px -2px;
		padding: 7px 6px 7px 4px;
		transform: scale(1);
		transform-origin: left center;
		opacity: 0.5;
		transition:
			transform 0.2s cubic-bezier(0.32, 0.72, 0, 1),
			opacity 0.2s ease;

		&.QuartileChart__row--active {
			position: relative;
			z-index: 1;
			opacity: 1;
			transform: translateX(-2px) scale(1.036);

			// Active row is slightly zoomed; shrink quartile track a bit
			// so min/max whiskers are less likely to be clipped.
			:deep(.QuartileChart__trackLine) {
				left: 2px;
				right: 10px;
			}
			:deep(.QuartileChart__range) {
				left: calc(16.6667% + 2px);
				width: calc(66.6667% - 12px);
			}
			:deep(.QuartileChart__whisker) {
				z-index: 6;
				height: 13px;
				opacity: 0.5;
			}
			:deep(.QuartileChart__whisker--max) {
				left: calc(100% - 8px) !important;
			}
			:deep(.QuartileChart__whisker--min) {
				left: 4px !important;
			}
		}

		&:hover:not(.QuartileChart__row--active) {
			opacity: 0.72;
		}

		&:focus-visible {
			outline: 2px solid var(--color-highlight);
			outline-offset: 1px;
		}
	}

	&__row:last-child {
		padding-bottom: 10px;
		border-bottom: none;
	}

	&__left {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
	}

	&__row--selectable &__left {
		gap: 4px;
	}

	&__icon {
		width: 30px;
		height: 30px;
		border-radius: 999px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;

		span {
			font-family: var(--font-icon);
			font-size: 1rem;
			color: rgba(255, 255, 255, 0.95);
			user-select: none;
		}
	}

	&__meta {
		min-width: 0;
	}

	&__title {
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--color-normal-text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	&__unit {
		font-size: 0.72rem;
		color: var(--color-complement-text);
		margin-top: 1px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	&__right {
		min-width: 0;
	}

	&__labels {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		align-items: end;
		margin-bottom: 2px;
	}

	&__label {
		min-width: 0;
		text-align: center;
	}

	&__labelKey {
		font-size: var(--font-s);
		color: var(--color-complement-text);
		line-height: 1;
	}

	&__labelVal {
		margin-top: 1px;
		font-size: var(--font-ms);
		font-weight: 700;
		line-height: 1.1;
		white-space: nowrap;
	}

	&__track {
		position: relative;
		height: 16px;
	}

	&__trackLine {
		position: absolute;
		left: 0;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		height: 3px;
		border-radius: 999px;
		background: transparent;
	}

	&__range {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		height: 5px;
		border-radius: 999px;
		z-index: 3;
	}

	&__median {
		position: absolute;
		top: 50%;
		transform: translate(-50%, -50%);
		width: 10px;
		height: 10px;
		border-radius: 999px;
		background: #fff;
		border: 2px solid rgba(0, 0, 0, 0.3);
		z-index: 4;
	}

	&__whisker {
		position: absolute;
		top: 50%;
		transform: translate(-50%, -50%);
		width: 2px;
		height: 11px;
		background: transparent;
		z-index: 2;
	}

	&__labelVal--median {
		font-size: 1.06rem;
	}
}

.quartile-fade-enter-active,
.quartile-fade-leave-active {
	transition:
		opacity 0.18s ease,
		transform 0.18s ease;
}

.quartile-fade-enter-from,
.quartile-fade-leave-to {
	opacity: 0;
	transform: translateY(4px);
}
</style>
