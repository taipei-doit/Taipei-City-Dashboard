<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
]);

const wrapRef = ref(null);
const chartWidth = ref(420);
const chartHeight = ref(260);
let resizeObserver = null;
const hoverTip = ref({
	show: false,
	x: 0,
	y: 0,
	text: "",
	placeLeft: false,
	placeAbove: true,
});
const hoveredNode = ref("");

function normalizeRows(raw) {
	if (Array.isArray(raw)) return raw;
	if (!raw || typeof raw !== "object") return [];
	const wrapped =
		raw.data || raw.rows || raw.items || raw.series || raw.result || null;
	return Array.isArray(wrapped) ? wrapped : [];
}

function parseLinks(raw) {
	const rows = Array.isArray(raw?.edges) ? raw.edges : normalizeRows(raw);
	return rows
		.map((it) => ({
			source: String(
				it.source ?? it.from ?? it.x_axis ?? it.x ?? "",
			).trim(),
			target: String(it.target ?? it.to ?? it.y_axis ?? "").trim(),
			value: Number(it.value ?? it.data ?? it.y ?? 0),
			color: it.color ? String(it.color) : null,
		}))
		.filter(
			(it) =>
				it.source &&
				it.target &&
				Number.isFinite(it.value) &&
				it.value > 0,
		);
}

function getPalette() {
	const c = props.chart_config?.color;
	if (Array.isArray(c) && c.length > 0) return c;
	return ["#4EA3FF", "#F5A623", "#7C4DFF", "#56B96D", "#E170A6", "#AF4137"];
}

function getSunburstBranchColors() {
	const cfg = props.chart_config?.color;
	if (
		Array.isArray(cfg) &&
		cfg.length >= 2 &&
		cfg.every((x) => typeof x === "string" && x.trim())
	) {
		return [cfg[0], cfg[1]];
	}
	return ["#4EA3FF", "#F5A623"];
}

function hexToRgb(hex) {
	const s = String(hex || "").replace("#", "");
	if (s.length !== 6) return null;
	const n = Number.parseInt(s, 16);
	if (!Number.isFinite(n)) return null;
	return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

function parseAnyColorToRgb(input) {
	const s = String(input || "").trim();
	if (!s) return null;
	const hex = hexToRgb(s);
	if (hex) return hex;
	const m = s.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
	if (m) {
		const r = Number(m[1]);
		const g = Number(m[2]);
		const b = Number(m[3]);
		if ([r, g, b].every((n) => n >= 0 && n <= 255)) return { r, g, b };
	}
	return null;
}

function rgbToHsl(r, g, b) {
	const rn = r / 255;
	const gn = g / 255;
	const bn = b / 255;
	const max = Math.max(rn, gn, bn);
	const min = Math.min(rn, gn, bn);
	const l = (max + min) / 2;
	let h = 0;
	let s = 0;
	if (max !== min) {
		const d = max - min;
		s = l > 0.5 ? d / (2 - max - min) : d / (max - min);
		switch (max) {
			case rn:
				h = (gn - bn) / d + (gn < bn ? 6 : 0);
				break;
			case gn:
				h = (bn - rn) / d + 2;
				break;
			default:
				h = (rn - gn) / d + 4;
		}
		h /= 6;
	}
	return { h, s, l };
}

function hslToRgb(h, s, l) {
	let r;
	let g;
	let b;
	if (s === 0) {
		r = g = b = l;
	} else {
		const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
		const p = 2 * l - q;
		const hue2rgb = (t) => {
			let x = t;
			if (x < 0) x += 1;
			if (x > 1) x -= 1;
			if (x < 1 / 6) return p + (q - p) * 6 * x;
			if (x < 1 / 2) return q;
			if (x < 2 / 3) return p + (q - p) * (2 / 3 - x) * 6;
			return p;
		};
		r = hue2rgb(h + 1 / 3);
		g = hue2rgb(h);
		b = hue2rgb(h - 1 / 3);
	}
	return {
		r: Math.round(Math.min(255, Math.max(0, r * 255))),
		g: Math.round(Math.min(255, Math.max(0, g * 255))),
		b: Math.round(Math.min(255, Math.max(0, b * 255))),
	};
}

function branchRingFill(input, ring, branchFillDepth) {
	const rgb = parseAnyColorToRgb(input);
	if (!rgb) return input;
	const { h, s } = rgbToHsl(rgb.r, rgb.g, rgb.b);
	let u = 0;
	if (branchFillDepth <= 1) {
		u = 0;
	} else if (branchFillDepth === 2) {
		u = (ring - 1) / 2;
	} else {
		u = (ring - 1) / (branchFillDepth - 1);
	}
	const lDeep = 0.32;
	const lOut = 0.74;
	const l2 = lDeep + u * (lOut - lDeep);
	const satMul = 0.86;
	const s2 = Math.max(0.3, Math.min(0.86, s * (1 - u * 0.1) * satMul));
	const o = hslToRgb(h, s2, l2);
	return `rgb(${o.r}, ${o.g}, ${o.b})`;
}

function lighten(hex, ratio = 0.25) {
	const rgb = parseAnyColorToRgb(hex);
	if (!rgb) return hex;
	const r = Math.round(rgb.r + (255 - rgb.r) * ratio);
	const g = Math.round(rgb.g + (255 - rgb.g) * ratio);
	const b = Math.round(rgb.b + (255 - rgb.b) * ratio);
	return `rgb(${r}, ${g}, ${b})`;
}

function darken(hex, ratio = 0.18) {
	const rgb = parseAnyColorToRgb(hex);
	if (!rgb) return hex;
	const r = Math.round(rgb.r * (1 - ratio));
	const g = Math.round(rgb.g * (1 - ratio));
	const b = Math.round(rgb.b * (1 - ratio));
	return `rgb(${r}, ${g}, ${b})`;
}

function polarToCartesian(cx, cy, r, angleRad) {
	return {
		x: cx + r * Math.cos(angleRad),
		y: cy + r * Math.sin(angleRad),
	};
}

function arcPath(cx, cy, innerR, outerR, start, end) {
	const large = end - start > Math.PI ? 1 : 0;
	const p1 = polarToCartesian(cx, cy, outerR, start);
	const p2 = polarToCartesian(cx, cy, outerR, end);
	const p3 = polarToCartesian(cx, cy, innerR, end);
	const p4 = polarToCartesian(cx, cy, innerR, start);
	return [
		`M ${p1.x} ${p1.y}`,
		`A ${outerR} ${outerR} 0 ${large} 1 ${p2.x} ${p2.y}`,
		`L ${p3.x} ${p3.y}`,
		`A ${innerR} ${innerR} 0 ${large} 0 ${p4.x} ${p4.y}`,
		"Z",
	].join(" ");
}

function buildSunburstGraph(links) {
	const children = new Map();
	const indeg = new Map();
	const outsum = new Map();
	for (const l of links) {
		if (!children.has(l.source)) children.set(l.source, []);
		children.get(l.source).push({ name: l.target, value: l.value });
		indeg.set(l.target, (indeg.get(l.target) || 0) + 1);
		indeg.set(l.source, indeg.get(l.source) || 0);
		outsum.set(l.source, (outsum.get(l.source) || 0) + l.value);
	}
	return { children, indeg, outsum };
}

function maxTreeDepthFrom(nodeName, children, depth) {
	const kids = children.get(nodeName);
	if (!kids || !kids.length) return depth;
	return Math.max(
		...kids.map((k) => maxTreeDepthFrom(k.name, children, depth + 1)),
	);
}

const sunburstData = computed(() => {
	const links = parseLinks(props.series);
	const W = Math.max(180, chartWidth.value);
	const H = Math.max(140, chartHeight.value);
	if (!links.length) return { arcs: [], labels: [], width: W, height: H };

	const { children, indeg, outsum } = buildSunburstGraph(links);

	const roots = [...indeg.keys()].filter((k) => (indeg.get(k) || 0) === 0);
	const root = roots[0];
	if (!root) return { arcs: [], labels: [], width: W, height: H };

	const level1 = (children.get(root) || [])
		.slice()
		.sort((a, b) => b.value - a.value);
	const palette = getPalette();
	const [branchBlue, branchOrange] = getSunburstBranchColors();
	const branchColor = new Map();
	level1.forEach((n, i) => {
		if (i === 0) branchColor.set(n.name, branchBlue);
		else if (i === 1) branchColor.set(n.name, branchOrange);
		else branchColor.set(n.name, palette[i % palette.length]);
	});

	const maxRingDepth = Math.max(
		2,
		...level1.map((n) => maxTreeDepthFrom(n.name, children, 1)),
	);

	let maxLeafVal = 1;
	for (const [, outs] of children) {
		for (const { name, value } of outs) {
			const ch = children.get(name);
			if (!ch || !ch.length) maxLeafVal = Math.max(maxLeafVal, value);
		}
	}

	// 作為品項層比例的分母
	const ring2NodeSet = new Set();
	for (const l1 of level1) {
		for (const k of children.get(l1.name) || []) {
			ring2NodeSet.add(k.name);
		}
	}
	const ring2total = Math.max(
		1,
		[...ring2NodeSet].reduce((s, name) => {
			return s + (outsum.get(name) || 0);
		}, 0),
	);

	const cx = W / 2;
	const cy = H / 2;
	const pad = Number(props.chart_config?.sunburst_inset_pad);
	const inset = Number.isFinite(pad) && pad >= 0 ? pad : 14;
	const R_max = Math.max(52, Math.min(W, H) / 2 - inset);
	const rHoleRatio = 0.26;
	const polarSlack = 1.3;
	const rHole = R_max * rHoleRatio;
	const w = (R_max - rHole) / (maxRingDepth + polarSlack);
	const baseOuter = rHole + maxRingDepth * w;

	const arcs = [];
	const rawLabels = [];

	function pushLabel(a0, a1, innerR, outerR, text, ring) {
		const span = a1 - a0;
		const avgR = (innerR + outerR) / 2;
		const need = ring <= 1 ? 40 : ring === 2 ? 36 : 28;
		if (span * avgR < need) return;
		const am = (a0 + a1) / 2;
		const p = polarToCartesian(
			cx,
			cy,
			innerR + (outerR - innerR) * 0.52,
			am,
		);
		rawLabels.push({
			key: `t-${text}-${ring}-${a0}`,
			x: p.x,
			y: p.y,
			text,
			ring,
		});
	}

	function ringBaseOpacity(ring) {
		if (maxRingDepth <= 1) return 0.96;
		const t = (ring - 1) / Math.max(1e-6, maxRingDepth - 1);
		return 0.96 - t * 0.06;
	}

	function recurse(
		parentName,
		a0,
		a1,
		parentRing,
		branchHex,
		chain,
		branchFillDepth,
	) {
		const kids = (children.get(parentName) || [])
			.slice()
			.sort((a, b) => b.value - a.value);
		if (!kids.length) return;
		const pSum = kids.reduce((s, x) => s + x.value, 0);
		let cur = a0;
		for (const k of kids) {
			const span = ((a1 - a0) * k.value) / Math.max(1e-6, pSum);
			const aEnd = cur + span;
			const sub = children.get(k.name) || [];
			const childRing = parentRing + 1;
			const fill = branchRingFill(branchHex, childRing, branchFillDepth);
			const baseOpacity = ringBaseOpacity(childRing);

			if (sub.length) {
				const nodeTotal = outsum.get(k.name) || k.value;
				const pct = ((nodeTotal / ring2total) * 100).toFixed(1);
				const pathTip =
					[...chain, k.name].join(" → ") +
					`：${nodeTotal} ${props.chart_config.unit}（佔${pct}%）`;
				const innerR = rHole + (childRing - 1) * w;
				const outerR = rHole + childRing * w;
				arcs.push({
					key: `n-${k.name}-${childRing}-${cur}`,
					d: arcPath(cx, cy, innerR, outerR, cur, aEnd),
					fill,
					ring: childRing,
					baseOpacity,
					node: k.name,
					parent: parentName,
					title: `${k.name}：${nodeTotal} ${props.chart_config.unit}`,
					tooltip: pathTip,
				});
				pushLabel(cur, aEnd, innerR, outerR, k.name, childRing);
				recurse(
					k.name,
					cur,
					aEnd,
					childRing,
					branchHex,
					[...chain, k.name],
					branchFillDepth,
				);
			} else {
				const nodeTotal = outsum.get(k.name) || k.value;
				const pct = ((nodeTotal / ring2total) * 100).toFixed(1);
				const pathTip =
					[...chain, k.name].join(" → ") +
					`：${k.value} ${props.chart_config.unit}（佔${pct}%）`;
				const innerR = rHole + (childRing - 1) * w;
				const polar = w * (0.12 + 1.18 * (k.value / maxLeafVal));
				const outerR = baseOuter + polar;
				arcs.push({
					key: `leaf-${k.name}-${childRing}-${cur}`,
					d: arcPath(cx, cy, innerR, outerR, cur, aEnd),
					fill,
					ring: childRing,
					baseOpacity,
					node: k.name,
					parent: parentName,
					title: `${k.name}：${k.value} ${props.chart_config.unit}`,
					tooltip: pathTip,
				});
				pushLabel(cur, aEnd, innerR, outerR, k.name, childRing);
			}
			cur = aEnd;
		}
	}

	let a0 = -Math.PI / 2;

	const ring1Total = Math.max(
		1,
		level1.reduce((sum, item) => {
			return sum + (outsum.get(item.name) || item.value);
		}, 0),
	);

	for (const l1 of level1) {
		const nodeTotal = outsum.get(l1.name) || l1.value;
		// 第一環佔整圈比例，用 l1.value（這段弧的實際流量）/ total
		const pct = ((nodeTotal / ring1Total) * 100).toFixed(1);
		const span1 = (Math.PI * 2 * nodeTotal) / ring1Total;
		const a1 = a0 + span1;
		const c1 = branchColor.get(l1.name) || "#7C4DFF";
		const sub = children.get(l1.name) || [];
		const branchFillDepth = Math.max(
			1,
			maxTreeDepthFrom(l1.name, children, 1),
		);
		if (sub.length) {
			const innerR = rHole;
			const outerR = rHole + w;
			arcs.push({
				key: `l1-${l1.name}`,
				d: arcPath(cx, cy, innerR, outerR, a0, a1),
				fill: branchRingFill(c1, 1, branchFillDepth),
				ring: 1,
				baseOpacity: ringBaseOpacity(1),
				node: l1.name,
				parent: root,
				title: `${l1.name}：${nodeTotal} ${props.chart_config.unit}`,
				tooltip: `${l1.name}：${nodeTotal} ${props.chart_config.unit}（佔${pct}%）`,
			});
			pushLabel(a0, a1, innerR, outerR, l1.name, 1);
			recurse(l1.name, a0, a1, 1, c1, [l1.name], branchFillDepth);
		} else {
			const polar = w * (0.12 + 1.18 * (l1.value / maxLeafVal));
			const outerR = baseOuter + polar;
			arcs.push({
				key: `l1leaf-${l1.name}`,
				d: arcPath(cx, cy, rHole, outerR, a0, a1),
				fill: branchRingFill(c1, 1, branchFillDepth),
				ring: 1,
				baseOpacity: ringBaseOpacity(1),
				node: l1.name,
				parent: root,
				title: `${l1.name}：${l1.value} ${props.chart_config.unit}`,
				tooltip: `${l1.name}：${l1.value} ${props.chart_config.unit}（佔${pct}%）`,
			});
			pushLabel(a0, a1, rHole, outerR, l1.name, 1);
		}
		a0 = a1;
	}

	const labels = [];
	const boxPaddingX = 8;
	const boxH = 14;
	for (const it of rawLabels) {
		const boxW = Math.max(16, it.text.length * 13 * 0.62 + boxPaddingX);
		const box = {
			left: it.x - boxW / 2,
			right: it.x + boxW / 2,
			top: it.y - boxH / 2,
			bottom: it.y + boxH / 2,
		};
		const overlapped = labels.some((ex) => {
			const eb = ex._box;
			return !(
				box.right < eb.left ||
				box.left > eb.right ||
				box.bottom < eb.top ||
				box.top > eb.bottom
			);
		});
		if (!overlapped) labels.push({ ...it, _box: box });
	}

	const childrenByNode = {};
	const parentByNode = {};
	for (const [k, arr] of children.entries()) {
		childrenByNode[k] = arr.map((x) => x.name);
		for (const x of arr) parentByNode[x.name] = k;
	}

	return { arcs, labels, width: W, height: H, childrenByNode, parentByNode };
});

function updateSize() {
	const w = wrapRef.value?.clientWidth || 420;
	const h = wrapRef.value?.clientHeight || 260;
	chartWidth.value = w;
	chartHeight.value = h;
}

function onArcHoverMove(evt, arc) {
	if (!wrapRef.value || !arc) return;
	const text = arc.tooltip || arc.title || "";
	const pad = 8;
	const g = 4;
	const vw = window.innerWidth;
	const vh = window.innerHeight;
	const maxW = Math.min(400, vw - 2 * pad);
	const estW = Math.max(140, Math.min(maxW, text.length * 13 + 28));
	const lineCount = Math.max(1, Math.ceil((text.length * 13) / estW));
	const estH = Math.min(vh - 2 * pad, lineCount * 22 + 20);

	const roomAbove = evt.clientY - pad >= estH + g;
	const roomBelow = vh - pad - evt.clientY >= estH + g;
	const placeAbove = roomAbove || !roomBelow;

	const roomRight = vw - pad - evt.clientX >= estW + g;
	const roomLeft = evt.clientX - pad >= estW + g;
	let placeLeft = false;
	if (!roomRight && roomLeft) placeLeft = true;
	else if (roomRight && roomLeft) placeLeft = evt.clientX > vw * 0.5;
	else if (!roomRight && !roomLeft)
		placeLeft = evt.clientX + estW / 2 > vw * 0.5;

	hoverTip.value = {
		show: true,
		x: evt.clientX,
		y: evt.clientY,
		text,
		placeLeft,
		placeAbove,
	};
	hoveredNode.value = arc.node || "";
}

function onArcHoverLeave() {
	hoverTip.value.show = false;
	hoveredNode.value = "";
}

function highlightSet() {
	const root = hoveredNode.value;
	if (!root) return null;
	const set = new Set([root]);
	const childrenByNode = sunburstData.value.childrenByNode || {};
	const parentByNode = sunburstData.value.parentByNode || {};

	const q = [root];
	while (q.length) {
		const n = q.shift();
		const kids = childrenByNode[n] || [];
		for (const k of kids) {
			if (!set.has(k)) {
				set.add(k);
				q.push(k);
			}
		}
	}

	let p = parentByNode[root];
	while (p) {
		set.add(p);
		p = parentByNode[p];
	}
	return set;
}

function arcFill(arc) {
	const hs = highlightSet();
	if (!hs) return arc.fill;
	return hs.has(arc.node) ? lighten(arc.fill, 0.1) : darken(arc.fill, 0.16);
}

function arcOpacity(arc) {
	const hs = highlightSet();
	const base = arc.baseOpacity ?? 0.9;
	if (!hs) return base;
	return hs.has(arc.node)
		? Math.min(0.99, base + 0.06)
		: Math.max(0.26, base * 0.52);
}

onMounted(() => {
	updateSize();
	resizeObserver = new ResizeObserver(updateSize);
	if (wrapRef.value) resizeObserver.observe(wrapRef.value);
});

onBeforeUnmount(() => {
	if (resizeObserver) resizeObserver.disconnect();
});
</script>

<template>
	<div
		v-if="activeChart === 'SunburstChart'"
		ref="wrapRef"
		class="sunburstchart"
	>
		<div class="sunburstchart__svg-clip">
			<svg
				:viewBox="`0 0 ${sunburstData.width} ${sunburstData.height}`"
				width="100%"
				height="100%"
			>
				<g>
					<path
						v-for="a in sunburstData.arcs"
						:key="a.key"
						:d="a.d"
						class="sunburstchart__arc"
						:fill="arcFill(a)"
						:fill-opacity="arcOpacity(a)"
						role="img"
						:aria-label="a.title"
						@mouseenter="(evt) => onArcHoverMove(evt, a)"
						@mousemove="(evt) => onArcHoverMove(evt, a)"
						@mouseleave="onArcHoverLeave"
					/>
				</g>
				<g>
					<text
						v-for="t in sunburstData.labels"
						:key="t.key"
						:x="t.x"
						:y="t.y"
						class="sunburstchart__label"
						text-anchor="middle"
						dominant-baseline="middle"
					>
						{{ t.text }}
					</text>
				</g>
			</svg>
		</div>
		<div
			v-if="hoverTip.show"
			class="sunburstchart__hover"
			:class="{
				'sunburstchart__hover--tl':
					hoverTip.placeLeft && hoverTip.placeAbove,
				'sunburstchart__hover--tr':
					!hoverTip.placeLeft && hoverTip.placeAbove,
				'sunburstchart__hover--bl':
					hoverTip.placeLeft && !hoverTip.placeAbove,
				'sunburstchart__hover--br':
					!hoverTip.placeLeft && !hoverTip.placeAbove,
			}"
			:style="{ left: `${hoverTip.x}px`, top: `${hoverTip.y}px` }"
		>
			{{ hoverTip.text }}
		</div>
	</div>
</template>

<style scoped lang="scss">
.sunburstchart {
	width: 100%;
	height: 100%;
	position: relative;
	overflow: visible;
}

.sunburstchart__svg-clip {
	width: 100%;
	height: 100%;
	overflow: hidden;
}

.sunburstchart__label {
	font-family:
		"微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans",
		"Helvetica", sans-serif;
	font-size: 14px;
	font-weight: 700;
	fill: #e6edf5;
	paint-order: stroke;
	stroke: rgba(23, 28, 36, 0.42);
	stroke-width: 1px;
	pointer-events: none;
}

.sunburstchart__arc {
	stroke: rgba(120, 120, 120, 0.65);
	stroke-width: 1;
	transition:
		fill 180ms ease,
		fill-opacity 180ms ease;
}

.sunburstchart__hover {
	--tip-gap: 4px;
	position: fixed;
	margin: 0;
	background: rgba(8, 11, 18, 0.92);
	color: #fff;
	font-family:
		"微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans",
		"Helvetica", sans-serif;
	font-size: 14px;
	font-weight: 700;
	padding: 8px 12px;
	border-radius: 6px;
	border: 1px solid rgba(255, 255, 255, 0.2);
	pointer-events: none;
	white-space: normal;
	word-break: break-word;
	line-height: 1.4;
	max-width: min(400px, calc(100vw - 20px));
	z-index: 10050;
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
	&--tr {
		transform: translate(var(--tip-gap), calc(-100% - var(--tip-gap)));
	}
	&--tl {
		transform: translate(
			calc(-100% - var(--tip-gap)),
			calc(-100% - var(--tip-gap))
		);
	}
	&--br {
		transform: translate(var(--tip-gap), var(--tip-gap));
	}
	&--bl {
		transform: translate(calc(-100% - var(--tip-gap)), var(--tip-gap));
	}
}
</style>
