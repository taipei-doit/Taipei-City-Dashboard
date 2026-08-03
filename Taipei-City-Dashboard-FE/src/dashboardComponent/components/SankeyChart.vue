<script setup>
import { computed, ref } from "vue";
import { hexToRGB } from "../../assets/utilityFunctions/colorConvert";
import SankeyCanvas from "./SankeyCanvas.vue";
// import { useDialogStore } from "../../store/dialogStore.js";

// ── 流量篩選(legend range slider)state ──────────────────────────────────
const filterMin = ref(null); // null = 尚未使用者手動設定,採用完整範圍
const filterMax = ref(null);
let activeThumb = null; // 'min' | 'max'
let activeTrackEl = null;

const LEGEND_TRACK_W = 140;
const LEGEND_THUMB_R = 3; // 對應長方形寬度(6px)的一半

function thumbLeftPx(pct) {
	return LEGEND_THUMB_R + pct * (LEGEND_TRACK_W - LEGEND_THUMB_R * 2);
}

function formatValue(v) {
	if (v == null || Number.isNaN(v)) return "-";
	const abs = Math.abs(v);
	if (abs >= 1_000_000)
		return (v / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
	if (abs >= 1_000) return (v / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
	return String(Math.round(v));
}

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	// "map_filter",
	// "map_filter_on",
]);

// const dialogStore = useDialogStore();

// ── parsed series data ──────────────────────────────────────────────────────────────
const parsed_series = {
	categories: props.chart_config?.categories,
	data: props.series,
};

// ── Constants ──────────────────────────────────────────────────────────────
const NODE_W = 16;
const GAP = 4;
const isMobile =
	typeof window !== "undefined" &&
	window.matchMedia?.("(max-width: 770px)").matches;
const PAD_TOP = isMobile ? 28 : 36;
const PAD_BOT = isMobile ? 0 : 6;
const PAD_L = 250;
const PAD_R = 250;
const BASE_SVG_H = isMobile ? 360 : 500;
const TOP_N = 25;
const NC = darken(props.chart_config.color?.[0], 25) ?? "#6b8fa3";
const MIN_LABEL_GAP = isMobile ? 22 : 16;
const MIN_NODE_H = 3;

const COLOR_LOW = hexToRGB(props.chart_config.color?.[0] ?? "#3a6ea5");
const COLOR_HIGH = hexToRGB(props.chart_config.color?.[1] ?? "#e05c5c");
const colorLowCss = `rgb(${+COLOR_LOW.r},${+COLOR_LOW.g},${+COLOR_LOW.b})`;
const colorHighCss = `rgb(${+COLOR_HIGH.r},${+COLOR_HIGH.g},${+COLOR_HIGH.b})`;

// ── State ──────────────────────────────────────────────────────────────────
const wrapperRef = ref(null);
const hoveredTip = ref(null);
const tipX = ref(0);
const tipY = ref(0);
const tipOnLeft = ref(false);
const isExpanded = ref(false);

// ── Helpers ────────────────────────────────────────────────────────────────
function darken(hex, percent = 20) {
	const c = hex ?? "#6b8fa3";

	const num = parseInt(c.slice(1), 16);
	let r = (num >> 16) & 255;
	let g = (num >> 8) & 255;
	let b = num & 255;

	r = Math.floor(r * (1 - percent / 100));
	g = Math.floor(g * (1 - percent / 100));
	b = Math.floor(b * (1 - percent / 100));

	return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function flowColor(t) {
	const r = Math.round(+COLOR_LOW.r + (+COLOR_HIGH.r - +COLOR_LOW.r) * t);
	const g = Math.round(+COLOR_LOW.g + (+COLOR_HIGH.g - +COLOR_LOW.g) * t);
	const b = Math.round(+COLOR_LOW.b + (+COLOR_HIGH.b - +COLOR_LOW.b) * t);
	return `rgb(${r},${g},${b})`;
}

function allocateLinkHeights(entries, totalHeight, minThickness = 1) {
	if (!entries.length || totalHeight <= 0) return new Map();

	const minSafeThickness =
		entries.length * minThickness <= totalHeight
			? minThickness
			: totalHeight / entries.length;

	const allocations = new Map();
	const remaining = entries.map((entry) => ({ ...entry }));
	let remainingHeight = totalHeight;

	while (remaining.length) {
		const remainingValue = remaining.reduce(
			(sum, entry) => sum + entry.value,
			0,
		);
		if (remainingValue <= 0 || remainingHeight <= 0) {
			for (const entry of remaining) {
				allocations.set(entry.key, 0);
			}
			break;
		}

		const forced = remaining.filter(
			(entry) =>
				(entry.value / remainingValue) * remainingHeight <
				minSafeThickness,
		);

		if (!forced.length) {
			for (const entry of remaining) {
				allocations.set(
					entry.key,
					(entry.value / remainingValue) * remainingHeight,
				);
			}
			break;
		}

		for (const entry of forced) {
			allocations.set(entry.key, minSafeThickness);
			remainingHeight -= minSafeThickness;
		}

		const forcedKeys = new Set(forced.map((entry) => entry.key));
		for (let i = remaining.length - 1; i >= 0; i--) {
			if (forcedKeys.has(remaining[i].key)) {
				remaining.splice(i, 1);
			}
		}
	}

	return allocations;
}

function positionNodes(topList, xPos, availH) {
	if (!topList.length) return [];
	const total = topList.reduce((s, [, v]) => s + v, 0);
	const fillH = availH - GAP * (topList.length - 1);
	let y = PAD_TOP;
	return topList.map(([name, flow]) => {
		const h = Math.max(MIN_NODE_H, (flow / total) * fillH);
		const node = { name, flow, x: xPos, y, h };
		y += h + GAP;
		return node;
	});
}

function onPathMouseMove({ event, tip }) {
	hoveredTip.value = tip;
	tipX.value = event.clientX;
	tipY.value = event.clientY;
	const rect = wrapperRef.value?.getBoundingClientRect();
	tipOnLeft.value = rect ? event.clientX > rect.left + rect.width / 2 : false;
}

function onPathMouseLeave() {
	hoveredTip.value = null;
}

function handleExpand() {
	// if (window.innerWidth < 770) {
	// 	dialogStore.showNotification("fail","放大檢視僅限電腦版！");
	// 	return;
	// }
	isExpanded.value = true;
}

// ── Layout ─────────────────────────────────────────────────────────────────
const layout = computed(() => {
	const raw = parsed_series;

	const layerLabels = raw.categories ?? [];
	const links = (raw.data ?? []).filter(
		(l) =>
			l.source_layer != null &&
			l.target_layer != null &&
			l.source_layer !== l.target_layer,
	);

	const n =
		layerLabels.length ||
		links.reduce((m, l) => Math.max(m, l.source_layer, l.target_layer), 0) +
			1;

	if (n < 2)
		return {
			svgW: 800,
			xPositions: [],
			nodesPerLayer: [],
			layerLabels,
			paths: [],
			n,
			padTop: PAD_TOP,
		};

	const svgW = Math.max(800, PAD_L + PAD_R + n * 180);
	const usableW = svgW - PAD_L - PAD_R - NODE_W;
	const xPositions = Array.from({ length: n }, (_, i) =>
		Math.round(PAD_L + (n === 1 ? 0 : (i / (n - 1)) * usableW)),
	);

	const nodeFlow = Array.from({ length: n }, () => new Map());
	for (const l of links) {
		nodeFlow[l.source_layer].set(
			l.source,
			(nodeFlow[l.source_layer].get(l.source) || 0) + l.value,
		);
		nodeFlow[l.target_layer].set(
			l.target,
			(nodeFlow[l.target_layer].get(l.target) || 0) + l.value,
		);
	}

	// 逐層選取 TOP N:
	// 第一層依整體流量排序;之後每一層只從「與前一層已選節點相連」的項目中,
	// 依相連流量取 TOP N,確保每一層都是承接自前面已選中的節點。
	const setPerLayer = Array.from({ length: n }, () => new Set());
	const topPerLayer = [];

	for (let i = 0; i < n; i++) {
		let candidates;

		if (i === 0) {
			candidates = [...nodeFlow[0].entries()].sort((a, b) => b[1] - a[1]);
		} else {
			const flowFromSelected = new Map();
			for (const l of links) {
				if (l.target_layer !== i) continue;
				if (!setPerLayer[l.source_layer].has(l.source)) continue;
				flowFromSelected.set(
					l.target,
					(flowFromSelected.get(l.target) || 0) + l.value,
				);
			}
			candidates = [...flowFromSelected.entries()].sort(
				(a, b) => b[1] - a[1],
			);
		}

		const top = candidates.slice(0, TOP_N);
		topPerLayer.push(top);
		setPerLayer[i] = new Set(top.map(([name]) => name));
	}

	const maxNodeCount = topPerLayer.reduce(
		(max, layer) => Math.max(max, layer.length),
		0,
	);
	const minAvailH =
		maxNodeCount > 0
			? maxNodeCount * MIN_NODE_H +
				Math.max(0, maxNodeCount - 1) * MIN_LABEL_GAP
			: 0;
	const svgH = Math.max(BASE_SVG_H, PAD_TOP + PAD_BOT + minAvailH);
	const availH = svgH - PAD_TOP - PAD_BOT;

	const nodesPerLayer = topPerLayer.map((top, i) =>
		positionNodes(top, xPositions[i], availH),
	);
	const mapPerLayer = nodesPerLayer.map(
		(nodes) => new Map(nodes.map((nd) => [nd.name, nd])),
	);

	const aggMap = new Map();
	for (const l of links) {
		const sl = l.source_layer,
			tl = l.target_layer;
		if (!setPerLayer[sl].has(l.source) || !setPerLayer[tl].has(l.target))
			continue;
		const key = `${sl}|${l.source}||${tl}|${l.target}`;
		const e = aggMap.get(key) ?? {
			source: l.source,
			source_layer: sl,
			target: l.target,
			target_layer: tl,
			value: 0,
		};
		e.value += l.value;
		aggMap.set(key, e);
	}
	const aggLinks = [...aggMap.values()].sort((a, b) => b.value - a.value);

	// ── 統計每個 node 的流入 / 流出總量,掛在 node 物件上供 hover 顯示 ──
	const inFlowMap = new Map();
	const outFlowMap = new Map();
	for (const l of aggLinks) {
		const outKey = `${l.source_layer}|${l.source}`;
		outFlowMap.set(outKey, (outFlowMap.get(outKey) || 0) + l.value);

		const inKey = `${l.target_layer}|${l.target}`;
		inFlowMap.set(inKey, (inFlowMap.get(inKey) || 0) + l.value);
	}

	for (let layerIndex = 0; layerIndex < nodesPerLayer.length; layerIndex++) {
		for (const node of nodesPerLayer[layerIndex]) {
			const key = `${layerIndex}|${node.name}`;
			const inFlow = Math.round(inFlowMap.get(key) || 0);
			const outFlow = Math.round(outFlowMap.get(key) || 0);

			node.inFlow = inFlow;
			node.outFlow = outFlow;

			const bits = [];
			if (outFlow > 0) bits.push(`流出 ${outFlow.toLocaleString()} 次`);
			if (inFlow > 0) bits.push(`流入 ${inFlow.toLocaleString()} 次`);
			node.tip = `${node.name}｜${bits.join("，")}`;
		}
	}

	const allValues = aggLinks.map((l) => l.value);
	const minV = allValues.length ? Math.min(...allValues) : 0;
	const maxV = allValues.length ? Math.max(...allValues) : 1;
	const normalize = (v) => (maxV === minV ? 0.5 : (v - minV) / (maxV - minV));

	const sourceHeightMap = new Map();
	const targetHeightMap = new Map();
	for (let layerIndex = 0; layerIndex < nodesPerLayer.length; layerIndex++) {
		for (const node of nodesPerLayer[layerIndex]) {
			const sourceEntries = aggLinks
				.filter(
					(link) =>
						link.source_layer === layerIndex &&
						link.source === node.name,
				)
				.map((link) => ({
					key: `${link.source_layer}|${link.source}||${link.target_layer}|${link.target}`,
					value: link.value,
				}));
			const targetEntries = aggLinks
				.filter(
					(link) =>
						link.target_layer === layerIndex &&
						link.target === node.name,
				)
				.map((link) => ({
					key: `${link.source_layer}|${link.source}||${link.target_layer}|${link.target}`,
					value: link.value,
				}));

			for (const [key, height] of allocateLinkHeights(
				sourceEntries,
				node.h,
			)) {
				sourceHeightMap.set(key, height);
			}
			for (const [key, height] of allocateLinkHeights(
				targetEntries,
				node.h,
			)) {
				targetHeightMap.set(key, height);
			}
		}
	}

	const usedRight = nodesPerLayer.map(
		(nodes) => new Map(nodes.map((nd) => [nd.name, 0])),
	);
	const usedLeft = nodesPerLayer.map(
		(nodes) => new Map(nodes.map((nd) => [nd.name, 0])),
	);

	const paths = [];
	for (const l of aggLinks) {
		const src = mapPerLayer[l.source_layer].get(l.source);
		const tgt = mapPerLayer[l.target_layer].get(l.target);
		if (!src || !tgt) continue;

		const linkKey = `${l.source_layer}|${l.source}||${l.target_layer}|${l.target}`;
		const lh = Math.min(
			sourceHeightMap.get(linkKey) ?? 0,
			targetHeightMap.get(linkKey) ?? 0,
		);
		if (lh <= 0) continue;

		const sOff = usedRight[l.source_layer].get(l.source);
		const tOff = usedLeft[l.target_layer].get(l.target);
		const x1 = src.x + NODE_W,
			y1 = src.y + sOff;
		const x2 = tgt.x,
			y2 = tgt.y + tOff;
		const mx = (x1 + x2) / 2;

		paths.push({
			d: [
				`M ${x1} ${y1}`,
				`C ${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`,
				`L ${x2} ${y2 + lh}`,
				`C ${mx} ${y2 + lh} ${mx} ${y1 + lh} ${x1} ${y1 + lh}`,
				"Z",
			].join(" "),
			fill: flowColor(normalize(l.value)),
			opacity: 0.35 + normalize(l.value) * 0.35,
			value: l.value,
			tip:
				l.target_layer - l.source_layer > 1
					? `${l.source} → ${l.target}（跨 ${l.target_layer - l.source_layer} 層）：${Math.round(l.value).toLocaleString()} 次`
					: `${l.source} → ${l.target}：${Math.round(l.value).toLocaleString()} 次`,
		});

		usedRight[l.source_layer].set(l.source, sOff + lh);
		usedLeft[l.target_layer].set(l.target, tOff + lh);
	}

	return {
		svgW,
		svgH,
		xPositions,
		nodesPerLayer,
		layerLabels,
		paths,
		n,
		padTop: PAD_TOP,
		valueRange: { min: minV, max: maxV },
	};
});

// ── Legend 數值範圍 & 篩選 ────────────────────────────────────────────────
const valueMin = computed(() => layout.value.valueRange?.min ?? 0);
const valueMax = computed(() => layout.value.valueRange?.max ?? 1);

const effectiveMin = computed(() => filterMin.value ?? valueMin.value);
const effectiveMax = computed(() => filterMax.value ?? valueMax.value);

const isFiltered = computed(() => {
	const eps = Math.max(1e-9, (valueMax.value - valueMin.value) * 1e-6);
	return (
		effectiveMin.value > valueMin.value + eps ||
		effectiveMax.value < valueMax.value - eps
	);
});

function pctFromValue(v) {
	const span = valueMax.value - valueMin.value;
	if (span <= 0) return 0;
	return Math.min(1, Math.max(0, (v - valueMin.value) / span));
}

function valueFromPct(pct) {
	return valueMin.value + pct * (valueMax.value - valueMin.value);
}

// 套用篩選:落在區間外的連結淡出(hidden = true),node/版面本身不重排
const filteredLayout = computed(() => {
	const eps = Math.max(1e-9, (valueMax.value - valueMin.value) * 1e-6);
	return {
		...layout.value,
		paths: (layout.value.paths ?? []).map((p) => ({
			...p,
			hidden:
				p.value < effectiveMin.value - eps ||
				p.value > effectiveMax.value + eps,
		})),
	};
});

function pctFromEvent(event, trackEl) {
	const rect = trackEl.getBoundingClientRect();
	const clientX = event.touches ? event.touches[0].clientX : event.clientX;
	const usable = rect.width - LEGEND_THUMB_R * 2;
	if (usable <= 0) return 0;
	return Math.min(
		1,
		Math.max(0, (clientX - rect.left - LEGEND_THUMB_R) / usable),
	);
}

function startDrag(thumb, event) {
	activeThumb = thumb;
	activeTrackEl = event.currentTarget.closest(".legend-track");
	window.addEventListener("mousemove", onDrag);
	window.addEventListener("mouseup", endDrag);
	window.addEventListener("touchmove", onDrag, { passive: false });
	window.addEventListener("touchend", endDrag);
	event.preventDefault();
}

function onDrag(event) {
	if (!activeThumb || !activeTrackEl) return;
	if (event.cancelable) event.preventDefault();

	const v = valueFromPct(pctFromEvent(event, activeTrackEl));

	if (activeThumb === "min") {
		filterMin.value = Math.min(v, effectiveMax.value);
	} else {
		filterMax.value = Math.max(v, effectiveMin.value);
	}
}

function endDrag() {
	activeThumb = null;
	activeTrackEl = null;
	window.removeEventListener("mousemove", onDrag);
	window.removeEventListener("mouseup", endDrag);
	window.removeEventListener("touchmove", onDrag);
	window.removeEventListener("touchend", endDrag);
}

function resetFilter() {
	if (!isFiltered.value) return;
	filterMin.value = null;
	filterMax.value = null;
}
</script>

<template>
	<div
		v-if="activeChart === 'SankeyChart'"
		ref="wrapperRef"
		class="sankey-wrapper"
	>
		<!-- Tooltip -->
		<div
			v-if="hoveredTip"
			class="sankey-tooltip"
			:style="
				tipOnLeft
					? {
							left: tipX - 14 + 'px',
							top: tipY - 10 + 'px',
							transform: 'translateX(-100%)',
						}
					: { left: tipX + 14 + 'px', top: tipY - 10 + 'px' }
			"
		>
			{{ hoveredTip }}
		</div>

		<!-- 放大按鈕 -->
		<button class="expand-btn" title="放大檢視" @click="handleExpand">
			<span>⛶</span>
		</button>

		<!-- 一般檢視 -->
		<SankeyCanvas
			:layout="filteredLayout"
			:svg-h="layout.svgH || BASE_SVG_H"
			:node-w="NODE_W"
			:nc="NC"
			class="sankey-svg"
			@path-mousemove="onPathMouseMove"
			@path-mouseleave="onPathMouseLeave"
			@node-mousemove="onPathMouseMove"
			@node-mouseleave="onPathMouseLeave"
		/>

		<!-- Legend -->
		<div class="sankey-legend">
			<span class="legend-value">{{ formatValue(effectiveMin) }} 次</span>
			<div class="legend-track">
				<div
					class="legend-gradient"
					:style="`background: linear-gradient(to right, ${colorLowCss}, ${colorHighCss})`"
				/>
				<div
					class="legend-mask legend-mask--left"
					:style="{
						width: thumbLeftPx(pctFromValue(effectiveMin)) + 'px',
					}"
				/>
				<div
					class="legend-mask legend-mask--right"
					:style="{
						width:
							LEGEND_TRACK_W -
							thumbLeftPx(pctFromValue(effectiveMax)) +
							'px',
					}"
				/>
				<div
					class="legend-thumb"
					:style="{
						left: thumbLeftPx(pctFromValue(effectiveMin)) + 'px',
					}"
					@mousedown="startDrag('min', $event)"
					@touchstart="startDrag('min', $event)"
				/>
				<div
					class="legend-thumb"
					:style="{
						left: thumbLeftPx(pctFromValue(effectiveMax)) + 'px',
					}"
					@mousedown="startDrag('max', $event)"
					@touchstart="startDrag('max', $event)"
				/>
			</div>
			<span class="legend-value">{{ formatValue(effectiveMax) }} 次</span>
			<button
				class="legend-reset-btn"
				:class="{ 'legend-reset-btn--disabled': !isFiltered }"
				:disabled="!isFiltered"
				title="清除篩選"
				@click="resetFilter"
			>
				重置
			</button>
		</div>

		<!-- Fullscreen overlay -->
		<Teleport to="body">
			<div
				v-if="isExpanded"
				class="sankey-overlay"
				@click.self="isExpanded = false"
			>
				<div class="sankey-modal">
					<button class="modal-close-btn" @click="isExpanded = false">
						✕
					</button>

					<!-- Tooltip（共用同一份 ref） -->
					<div
						v-if="hoveredTip"
						class="sankey-tooltip"
						:style="
							tipOnLeft
								? {
										left: tipX - 14 + 'px',
										top: tipY - 10 + 'px',
										transform: 'translateX(-100%)',
									}
								: {
										left: tipX + 14 + 'px',
										top: tipY - 10 + 'px',
									}
						"
					>
						{{ hoveredTip }}
					</div>

					<!-- 放大檢視 -->
					<div class="sankey-scroll sankey-scroll-full">
						<SankeyCanvas
							:layout="filteredLayout"
							:svg-h="layout.svgH || BASE_SVG_H"
							:node-w="NODE_W"
							:nc="NC"
							class="sankey-svg-full"
							@path-mousemove="onPathMouseMove"
							@path-mouseleave="onPathMouseLeave"
							@node-mousemove="onPathMouseMove"
							@node-mouseleave="onPathMouseLeave"
						/>
					</div>

					<!-- Legend -->
					<div class="sankey-legend">
						<span class="legend-value">{{
							formatValue(effectiveMin)
						}} 次</span>
						<div class="legend-track">
							<div
								class="legend-gradient"
								:style="`background: linear-gradient(to right, ${colorLowCss}, ${colorHighCss})`"
							/>
							<div
								class="legend-mask legend-mask--left"
								:style="{
									width:
										thumbLeftPx(
											pctFromValue(effectiveMin),
										) + 'px',
								}"
							/>
							<div
								class="legend-mask legend-mask--right"
								:style="{
									width:
										LEGEND_TRACK_W -
										thumbLeftPx(
											pctFromValue(effectiveMax),
										) +
										'px',
								}"
							/>
							<div
								class="legend-thumb"
								:style="{
									left:
										thumbLeftPx(
											pctFromValue(effectiveMin),
										) + 'px',
								}"
								@mousedown="startDrag('min', $event)"
								@touchstart="startDrag('min', $event)"
							/>
							<div
								class="legend-thumb"
								:style="{
									left:
										thumbLeftPx(
											pctFromValue(effectiveMax),
										) + 'px',
								}"
								@mousedown="startDrag('max', $event)"
								@touchstart="startDrag('max', $event)"
							/>
						</div>
						<span class="legend-value">{{
							formatValue(effectiveMax)
						}} 次</span>
						<button
							class="legend-reset-btn"
							:class="{
								'legend-reset-btn--disabled': !isFiltered,
							}"
							:disabled="!isFiltered"
							title="清除篩選"
							@click="resetFilter"
						>
							重置
						</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>

<style scoped lang="scss">
.sankey-wrapper {
	position: relative;
	width: 100%;
	height: 90%;
	display: flex;
	gap: 4px;
	flex-direction: column;
	justify-content: center;
	background: transparent;
}

.expand-btn {
	position: absolute;
	top: 4px;
	right: 4px;
	z-index: 5;
	background: #282a2c;
	border: 1px solid #555;
	border-radius: 4px;
	color: var(--color-text-secondary, #aaa);
	width: 26px;
	height: 26px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 14px;
	line-height: 1;
	padding: 0;
	transition:
		border-color 0.15s,
		color 0.15s;

	&:hover {
		border-color: #aaa;
		color: #fff;
	}
}

.sankey-svg {
	width: 100%;
	height: auto;
	display: block;
}

.sankey-scroll {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	overflow-x: hidden;
}

.sankey-tooltip {
	position: fixed;
	background: #282a2c;
	box-shadow: 0px 0px 5px black;
	color: #fff;
	padding: 3px 12px;
	border: 1px solid #666;
	border-radius: 4px;
	font-size: 0.875rem;
	pointer-events: none;
	white-space: nowrap;
	z-index: 9999;
}

.sankey-legend {
	display: flex;
	align-items: center;
	gap: 8px;
	justify-content: center;
	font-size: 0.72rem;
	color: var(--color-text-secondary, #aaa);
	flex-shrink: 0;
	margin: 12px;
}

.legend-value {
	font-size: 14px;
	white-space: nowrap;
	min-width: 32px;
	text-align: center;
	font-variant-numeric: tabular-nums;
}

.legend-track {
	position: relative;
	width: 140px;
	height: 15px;
	touch-action: none;
	user-select: none;
	-webkit-user-select: none;
	-webkit-touch-callout: none; // 防止 iOS 長按跳出選單/預覽
}

.legend-gradient {
	position: absolute;
	left: 0;
	right: 0;
	top: 2px;
	height: 10px;
	border-radius: 3px;
}

.legend-mask {
	position: absolute;
	top: 2px;
	height: 10px;
	background: rgba(0, 0, 0, 0.6);
	pointer-events: none;

	&--left {
		left: 0;
		border-radius: 3px 0 0 3px;
	}

	&--right {
		right: 0;
		border-radius: 0 3px 3px 0;
	}
}

.legend-thumb {
	position: absolute;
	top: 50%;
	width: 6px; // = LEGEND_THUMB_R * 2
	height: 18px;
	background: #fff;
	border: 2px solid #282a2c;
	border-radius: 2px;
	transform: translate(-50%, -50%);
	cursor: grab;
	box-shadow: 0 0 3px rgba(0, 0, 0, 0.5);
	user-select: none;
	-webkit-user-select: none;
	-webkit-touch-callout: none;

	&:active {
		cursor: grabbing;
	}
}

.legend-reset-btn {
	background: transparent;
	border: 1px solid #555;
	border-radius: 4px;
	color: var(--color-text-secondary, #aaa);
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 12px;
	line-height: 1;
	padding: 4px 8px;
	white-space: nowrap;
	transition:
		border-color 0.15s,
		color 0.15s,
		opacity 0.15s;

	&:hover {
		border-color: #aaa;
		color: #fff;
	}

	&--disabled {
		opacity: 0.4;
		cursor: default;
		pointer-events: none;
	}
}

@media (max-width: 770px) {
	.legend-value {
		font-size: 3.4vw;
	}

	.legend-track {
		width: 30vw;
	}
}

// ── Fullscreen overlay ─────────────────────────────────────────────────────
.sankey-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.75);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
}

.sankey-modal {
	position: relative;
	background: #1a1c1e;
	border: 1px solid #444;
	border-radius: 8px;
	width: 75vw;
	aspect-ratio: 4 / 3;
	max-height: 75vh;
	display: flex;
	flex-direction: column;
	padding: 6vh 16px;
	box-sizing: border-box;
}

.modal-close-btn {
	position: absolute;
	top: 10px;
	right: 12px;
	background: transparent;
	border: 1px solid #555;
	border-radius: 4px;
	color: #aaa;
	width: 28px;
	height: 28px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 14px;
	z-index: 1;
	transition:
		border-color 0.15s,
		color 0.15s;

	&:hover {
		border-color: #aaa;
		color: #fff;
	}
}

.sankey-svg-full {
	width: 100%;
	height: auto;
	display: block;
}

.sankey-scroll-full {
	flex: 1;
}

@media (max-width: 770px) {
	.legend-label {
		font-size: 3vw;
	}

	.sankey-modal {
		width: 90vw;
		height: 60vh;
	}
}
</style>
