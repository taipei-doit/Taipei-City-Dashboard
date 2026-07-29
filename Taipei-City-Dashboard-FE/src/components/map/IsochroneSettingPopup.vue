<template>
	<div class="mapcontainer-isochrone">
		<div class="mapcontainer-isochrone-header">
			<h3>等時圈設定</h3>
			<button class="close-btn" @click="$emit('close')">✕</button>
		</div>

		<div class="mapcontainer-isochrone-content">
			<!-- 目前等時圈資訊 -->
			<div v-if="currentParams" class="section current-params">
				<div class="title">目前等時圈設定</div>
				<div class="params-grid">
					<span class="param-label">座標</span>
					<span class="param-value">
						經度：{{ currentParams.lng.toFixed(4) }}， 緯度：{{
							currentParams.lat.toFixed(4)
						}}
					</span>
					<span class="param-label">時間</span>
					<span class="param-value">
						{{
							formatDepartureTime(
								currentParams.arrival_time ||
									currentParams.departure_time,
							)
						}}</span
					>
					<span class="param-label">類型</span>
					<span class="param-value">
						{{ TIME_TYPE_LABEL[currentParams.time_type] }}、
						{{ currentParams.service_profile }}
					</span>
					<span class="param-label">交通</span>
					<span class="param-value">{{
						formatModes(currentParams.modes)
					}}</span>
					<!-- <span class="param-label">區間</span>
					<span class="param-value">
						等時圈以 15 / 30 / 45 / 60
						分鐘分層，由內向外逐層擴展（每 15 分鐘一圈）
					</span> -->
				</div>
			</div>

			<!-- 說明區塊 -->
			<div class="section description">
				<div class="title">等時圈相關說明</div>
				<div class="desc-box">
					<h3>等時圈功能說明</h3>
					<p>
						等時圈以 15 / 30 / 45 / 60
						分鐘為分層，從指定位置由內向外擴展，呈現不同時間限制下的可達範圍。此功能結合實際交通路網與步行轉乘，用於分析在特定時間內可到達的區域與交通站點。
					</p>

					<h3>交通站點與圖例說明</h3>
					<p>
						系統會標示可達範圍內的交通站點，並以對應交通類型 icon
						進行分類呈現，各類型與 icon 對應如下：
					</p>
					<div class="legend-list">
						<div class="legend-item">
							<img
								src="../../../public/images/map/train.png"
								alt="公車icon"
							/>鐵路
						</div>
						<div class="legend-item">
							<img
								src="../../../public/images/map/metro.png"
								alt="公車icon"
							/>捷運
						</div>
						<div class="legend-item">
							<img
								src="../../../public/images/map/bus.png"
								alt="公車icon"
							/>公車 / 跳蛙公車
						</div>
					</div>

					<h3>使用方式與模式說明</h3>
					<p>
						使用者可透過定位按鈕帶入目前位置，並設定時間、時間類型（出發或抵達）、服務日型與交通模式後建立等時圈。建立後可於上方檢視條件，並可清除或重新設定參數以更新結果。出發模式以使用者位置為起點計算可達範圍；抵達模式則反推各時間區間建議出發位置。
					</p>
				</div>
			</div>

			<!-- 位置 -->
			<div class="section">
				<div class="title">位置</div>
				<div class="row location-row">
					<input
						v-model="lng"
						type="text"
						placeholder="經度 ( 如 121.5637758 )"
					/>
					<input
						v-model="lat"
						type="text"
						placeholder="緯度 ( 如 25.0374971 )"
					/>
					<button class="icon-wrapper" @click="handleCurrentLocation">
						<LocationIcon />
					</button>
				</div>
			</div>

			<!-- 時間 -->
			<div class="section">
				<div class="title">時間</div>
				<div class="row time-select-row">
					<div class="select-wrapper">
						<select v-model="ampm">
							<option value="AM">上午</option>
							<option value="PM">下午</option>
						</select>
					</div>
					<div class="select-wrapper">
						<select v-model="hour12">
							<option
								v-for="h in 12"
								:key="h"
								:value="String(h).padStart(2, '0')"
							>
								{{ String(h).padStart(2, "0") }}
							</option>
						</select>
					</div>
					<span class="time-separator">:</span>
					<!-- ▼ 分鐘改為 input -->
					<input
						v-model="minute"
						type="number"
						min="0"
						max="59"
						placeholder="分"
						class="minute-input"
						@blur="padMinute"
					/>
				</div>
			</div>

			<!-- 時間類型 -->
			<div class="section">
				<div class="title">時間類型</div>
				<div class="btn-row">
					<button
						v-for="t in TIME_TYPES"
						:key="t"
						:class="{ active: timeType === t }"
						@click="timeType = t"
					>
						{{ t }}
					</button>
				</div>
			</div>

			<!-- 服務日型 -->
			<div class="section">
				<div class="title">服務日型</div>
				<div class="btn-row">
					<button
						v-for="s in SERVICE_TYPES"
						:key="s"
						:class="{ active: serviceType === s }"
						@click="serviceType = s"
					>
						{{ s }}
					</button>
				</div>
			</div>

			<!-- 交通模式 -->
			<div class="section">
				<div class="title">交通模式</div>
				<div class="btn-row">
					<button
						v-for="m in TRANSPORT_LABELS"
						:key="m"
						:class="{ active: transport.includes(m) }"
						@click="toggleTransport(m)"
					>
						{{ m }}
					</button>
				</div>
			</div>

			<!-- 操作 -->
			<div class="section action">
				<div class="action-row">
					<button class="primary" @click="createIsochrone">
						建立等時圈
					</button>
					<button class="danger" @click="removeIsochrone">
						清除
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useMapStore } from "../../store/mapStore.js";
import { useDialogStore } from "../../store/dialogStore.js";
import LocationIcon from "../icons/LocationIcon.vue";

// ── Constants ──────────────────────────────────────────────────────────────────

const TRANSPORT_MAP = { 公車: "bus", 捷運: "rail", 鐵路: "train" };
const MODE_LABEL = { bus: "公車", rail: "捷運", train: "鐵路" };
const TIME_TYPE_LABEL = {
	departure: "出發",
	arrival: "抵達",
};
const TRANSPORT_LABELS = Object.keys(TRANSPORT_MAP);
const TIME_TYPES = ["出發", "抵達"];
const SERVICE_TYPES = ["平日", "假日"];
const CUTOFFS = [900, 1800, 2700, 3600];

// ── Store ──────────────────────────────────────────────────────────────────────

const emit = defineEmits(["close"]);
const mapStore = useMapStore();
const dialogStore = useDialogStore();

// ── 取得目前時間作為預設值 ─────────────────────────────────────────────────────

function getNowTimeParts() {
	const now = new Date();
	const h24 = now.getHours();
	const min = now.getMinutes();
	const period = h24 < 12 ? "AM" : "PM";
	const h12 = h24 % 12 || 12;
	return {
		ampm: period,
		hour12: String(h12).padStart(2, "0"),
		minute: String(min).padStart(2, "0"),
	};
}

const { ampm: initAmpm, hour12: initHour, minute: initMin } = getNowTimeParts();

// ── Form state ─────────────────────────────────────────────────────────────────

const lng = ref("");
const lat = ref("");
const ampm = ref(initAmpm);
const hour12 = ref(initHour);
const minute = ref(initMin);
const timeType = ref("出發");
const serviceType = ref("平日");
const transport = ref(["公車"]);
const isDeparture = computed(() => timeType.value === "出發");

const currentParams = computed(() => mapStore.isochroneParams);

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatModes(modes) {
	return modes.map((m) => MODE_LABEL[m] ?? m).join("、");
}

function formatDepartureTime(iso) {
	const [hStr, mStr] = iso.split("T")[1].split(":");
	const h = parseInt(hStr) % 24;
	const m = mStr.replace(/\D/g, "").slice(0, 2);

	if (h === 0) return `上午 12:${m}`;
	if (h < 12) return `上午 ${h}:${m}`;
	if (h === 12) return `下午 12:${m}`;
	return `下午 ${h - 12}:${m}`;
}

function convertTo24h(hour, period) {
	let h = Number(hour);
	if (period === "AM" && h === 12) h = 0;
	if (period === "PM" && h !== 12) h += 12;
	return String(h).padStart(2, "0");
}

function buildDepartureTime(hour24, min) {
	const now = new Date();
	const yyyy = now.getFullYear();
	const mm = String(now.getMonth() + 1).padStart(2, "0");
	const dd = String(now.getDate()).padStart(2, "0");
	return `${yyyy}-${mm}-${dd}T${hour24}:${min}:00.000+08:00`;
}

// ── 分鐘 blur 補零 & 範圍修正 ──────────────────────────────────────────────────

function padMinute() {
	const v = parseInt(minute.value);
	if (isNaN(v) || v < 0) {
		minute.value = "00";
		return;
	}
	if (v > 59) {
		minute.value = "59";
		return;
	}
	minute.value = String(v).padStart(2, "0");
}

// ── Validation ─────────────────────────────────────────────────────────────────

function validateForm() {
	if (!lng.value || isNaN(parseFloat(lng.value))) {
		dialogStore.showNotification("fail", "請填寫有效的經度 !");
		return false;
	}
	if (!lat.value || isNaN(parseFloat(lat.value))) {
		dialogStore.showNotification("fail", "請填寫有效的緯度 !");
		return false;
	}
	const m = parseInt(minute.value);
	if (isNaN(m) || m < 0 || m > 59) {
		dialogStore.showNotification("fail", "請填寫有效的分鐘（0–59）!");
		return false;
	}
	if (transport.value.length === 0) {
		dialogStore.showNotification("fail", "請至少選擇一種交通模式 !");
		return false;
	}
	return true;
}

// ── Handlers ───────────────────────────────────────────────────────────────────

function handleCurrentLocation() {
	mapStore.setCurrentLocation();
	const { longitude, latitude } = mapStore.userLocation;
	if (longitude && latitude) {
		lng.value = longitude;
		lat.value = latitude;
	} else {
		dialogStore.showNotification(
			"fail",
			"使用者位置取得失敗，請留意是否開啟瀏覽器位置權限 !",
		);
	}
}

function toggleTransport(mode) {
	transport.value = transport.value.includes(mode)
		? transport.value.filter((t) => t !== mode)
		: [...transport.value, mode];
}

async function createIsochrone() {
	if (!validateForm()) return;

	const hour24 = convertTo24h(hour12.value, ampm.value);
	const departureTime = buildDepartureTime(hour24, minute.value);

	const payload = {
		lat: parseFloat(lat.value),
		lng: parseFloat(lng.value),
		time_type: isDeparture.value ? "departure" : "arrival",
		departure_time: isDeparture.value ? departureTime : null,
		arrival_time: !isDeparture.value ? departureTime : null,
		service_profile: serviceType.value,
		cutoffs: CUTOFFS,
		modes: transport.value.map((m) => TRANSPORT_MAP[m]),
	};

	const res = await mapStore.setIsochroneLayer(payload);

	if (res === "無相關等時圈分析成果") {
		dialogStore.showNotification("fail", "無相關等時圈分析成果 !");
		return;
	} else if (res == "等時圈分析失敗") {
		dialogStore.showNotification("fail", "等時圈分析失敗，請稍後再試 !");
		return;
	}

	emit("close");
}

function removeIsochrone() {
	mapStore.clearIsochroneLayer();
}
</script>

<style scoped lang="scss">
// ── Typography ─────────────────────────────────────────────────────────────────
$fs-title: 1rem;
$fs-section: 0.8rem;
$fs-body: 0.875rem;
$fs-action: 0.95rem;

$fw-normal: 400;
$fw-medium: 500;
$fw-bold: 600;

// ── Colors ─────────────────────────────────────────────────────────────────────
$bg-dark: #2b2c2e;
$bg-darker: #1e1e1e;
$bg-header: #3a3b3d;
$border: #555;
$border-in: #444;
$accent: #4ba3e3;
$accent-dk: #2f7fd1;
$text: #eee;
$text-muted: #aaa;

// ── Root ───────────────────────────────────────────────────────────────────────
.mapcontainer-isochrone {
	position: absolute;
	right: 48px;
	top: 10px;
	z-index: 10;
	width: 100%;
	max-width: 350px;
	font-size: $fs-body;
	color: $text;
	background: $bg-dark;
	border-radius: 8px;
	border: 1px solid $border;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	@media (max-width: 400px) {
		left: 50%;
		top: 50%;
		right: auto;
		transform: translate(-50%, -50%);
		z-index: 20;
	}
}

// ── Header ─────────────────────────────────────────────────────────────────────
.mapcontainer-isochrone-header {
	background: $bg-header;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 8px 14px;
	border-bottom: 1px solid $border;

	h3 {
		margin: 0;
		font-size: $fs-title;
		font-weight: $fw-bold;
	}
}

.close-btn {
	background: transparent;
	border: none;
	display: flex;
	justify-content: center;
	align-items: center;
	border-radius: 999px;
	flex: none;
	padding: 1rem 0.7rem;
	font-size: $fs-body;
	color: $text-muted;
	cursor: pointer;

	&:hover {
		color: $text;
	}
}

// ── Content ────────────────────────────────────────────────────────────────────
.mapcontainer-isochrone-content {
	padding: 14px;
	max-height: 54vh;
	overflow-y: auto;
}

// ── Section ────────────────────────────────────────────────────────────────────
.section {
	margin-bottom: 10px;

	.title {
		font-size: $fs-section;
		font-weight: $fw-bold;
		color: $accent;
		margin-bottom: 8px;
		letter-spacing: 0.04em;
	}
}

// ── Layout rows ────────────────────────────────────────────────────────────────
.row {
	display: flex;
	gap: 10px;
	align-items: center;
}

.location-row {
	@extend .row;
}
.time-select-row {
	display: flex;
	flex: 1;
	align-items: center;
	gap: 6px;
}

.time-separator {
	color: $text-muted;
	font-size: $fs-body;
	flex-shrink: 0;
}

// ── Icon button ────────────────────────────────────────────────────────────────
.icon-wrapper {
	width: 32px;
	height: 32px;
	flex: 0 0 32px;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 999px;
	background: none;
	border: unset;
	cursor: pointer;

	&:hover {
		color: $accent;
	}

	:deep(svg) {
		width: 18px;
		height: 18px;
	}
}

// ── Select wrapper ─────────────────────────────────────────────────────────────
.select-wrapper {
	position: relative;
	flex: 1;
	min-width: 0;

	&::after {
		content: "▾";
		position: absolute;
		right: 10px;
		top: 50%;
		transform: translateY(-50%);
		color: $text-muted;
		font-size: 0.7rem;
		pointer-events: none;
	}
}

// ── Inputs & Selects ───────────────────────────────────────────────────────────
input,
select {
	width: 100%;
	height: 30px;
	border: 1px solid $border-in;
	border-radius: 4px;
	background: $bg-darker;
	color: $text;
	font-size: $fs-body;
	box-sizing: border-box;
	appearance: none;
	-webkit-appearance: none;

	&::placeholder {
		color: $text-muted;
	}
}

// ── 分鐘輸入框 ─────────────────────────────────────────────────────────────────
.minute-input {
	flex: 1;
	min-width: 0;
	text-align: center;
	padding: 0 6px;

	// 隱藏 number input 的上下箭頭
	&::-webkit-inner-spin-button,
	&::-webkit-outer-spin-button {
		appearance: none;
	}
	-moz-appearance: textfield;
}

// ── Toggle buttons ─────────────────────────────────────────────────────────────
.btn-row {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

button {
	flex: 1;
	height: 30px;
	border-radius: 6px;
	border: 1px solid $border;
	background: $bg-darker;
	color: $text-muted;
	font-size: $fs-body;
	font-weight: $fw-medium;
	cursor: pointer;
	transition:
		background 0.2s,
		color 0.2s,
		border-color 0.2s;

	&:hover {
		background: #444;
		color: $text;
	}
	&.active {
		border-color: $accent;
		color: $text;
	}
}

// ── Action section ─────────────────────────────────────────────────────────────
.section.action {
	margin-top: 20px;
	padding-top: 10px;
	border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.action-row {
	display: flex;
	gap: 8px;
}

button.primary {
	flex: 1;
	height: 46px;
	border: none;
	border-radius: 8px;
	font-size: $fs-action;
	font-weight: $fw-bold;
	color: white;
	background: linear-gradient(135deg, $accent, $accent-dk);
	box-shadow: 0 6px 14px rgba(75, 163, 227, 0.35);
	transition:
		transform 0.15s,
		filter 0.15s,
		box-shadow 0.15s;

	&:hover {
		filter: brightness(0.8);
	}
	&:active {
		transform: translateY(0);
		box-shadow: 0 3px 8px rgba(75, 163, 227, 0.25);
	}
}

button.danger {
	flex: 0 0 64px;
	height: 46px;
	border: none;
	border-radius: 8px;
	font-size: $fs-body;
	font-weight: $fw-bold;
	color: white;
	background: #e05c5c;
	cursor: pointer;
	transition: filter 0.15s;

	&:hover {
		filter: brightness(0.8);
	}
	&:active {
		filter: brightness(0.65);
	}
}

// ── Current params block ───────────────────────────────────────────────────────
.current-params {
	background: rgba(75, 163, 227, 0.08);
	border: 1px solid rgba(75, 163, 227, 0.25);
	border-radius: 6px;
	padding: 10px 12px;
}

.params-grid {
	display: grid;
	grid-template-columns: 3em 1fr;
	gap: 4px 8px;
	align-items: baseline;
}

.param-label {
	font-size: 0.75rem;
	color: $text-muted;
	white-space: nowrap;
}

.param-value {
	font-size: 0.8rem;
	color: $text;
	word-break: break-all;
}

.description {
	.desc-box {
		font-size: 0.78rem;
		line-height: 1.6;
		color: $text-muted;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		padding: 12px;
		border-radius: 6px;

		max-height: 180px; // 控制這個區塊最大高度,可依需求調整
		overflow-y: auto; // 超過高度就出現卷軸

		h3 {
			display: flex;
			align-items: center;
			margin: 0 0 6px;
			padding: 4px 8px;
			font-size: 0.82rem;
			font-weight: $fw-bold;
			color: $accent;
			background: rgba(75, 163, 227, 0.1);
			border-left: 3px solid $accent;
			border-radius: 0 4px 4px 0;

			&:not(:first-child) {
				margin-top: 14px;
			}
		}

		p {
			margin: 0;
		}
	}
}

.description .desc-box {
	&::-webkit-scrollbar {
		width: 3px;
	}
	&::-webkit-scrollbar-track {
		background: transparent;
	}
	&::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.15);
		border-radius: 3px;

		&:hover {
			background: rgba(255, 255, 255, 0.25);
		}
	}
}

.legend-list {
	display: flex;
	flex-direction: column;
	gap: 4px;
	margin-top: 4px;

	.legend-item {
		img {
			width: 16px;
			height: 16px;
		}
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 999px;
		flex: none;
	}
}
</style>
