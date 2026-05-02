<!-- Component Name: EcoDietNearbyChatModal -->
<script setup>
import { ref, nextTick, watch } from "vue";
import http from "../router/axios";

const props = defineProps({
	show: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "apply-actions"]);

const FACILITY_OPTIONS = [
	{ value: "restaurant", label: "環保餐廳", color: "#5fcf80" },
	{ value: "green_store", label: "綠色商店", color: "#5a9cf8" },
	{ value: "food_bank", label: "實物銀行", color: "#a37cf6" },
];

const messages = ref([]);
const isLoading = ref(false);
const isLocating = ref(false);
const error = ref("");
const inputText = ref("");
const coords = ref(null);
const messageListRef = ref(null);
const radiusValue = ref(800);
const selectedTypes = ref([]); // [] = 全部
let idCounter = 0;

async function scrollToBottom() {
	await nextTick();
	if (messageListRef.value) {
		messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
	}
}

function resetState() {
	messages.value = [];
	error.value = "";
	inputText.value = "";
	coords.value = null;
	radiusValue.value = 800;
	selectedTypes.value = [];
}

function locateUser() {
	return new Promise((resolve, reject) => {
		if (!navigator.geolocation) {
			reject(new Error("此瀏覽器不支援定位功能"));
			return;
		}
		navigator.geolocation.getCurrentPosition(
			(pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
			(err) => reject(err),
			{ enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 },
		);
	});
}

function describeGeoError(e) {
	if (e?.code === 1) return "未授權使用定位，請於瀏覽器網址列旁的鎖頭圖示允許位置存取後重試。";
	if (e?.code === 2) return "目前無法取得位置。請確認 macOS『系統設定 → 隱私權與安全性 → 定位服務』已開啟，且瀏覽器有獲准存取定位。";
	if (e?.code === 3) return "定位逾時。請檢查網路或關閉 VPN 後重試。";
	return e?.message || "無法取得定位，請稍後再試。";
}

async function tryLocate() {
	if (isLocating.value) return;
	isLocating.value = true;
	error.value = "";
	try {
		coords.value = await locateUser();
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: "已取得您的定位，可詢問附近的環保餐廳、綠色商店或實物銀行。",
		});
		await scrollToBottom();
	} catch (e) {
		error.value = describeGeoError(e);
	} finally {
		isLocating.value = false;
	}
}

watch(
	() => props.show,
	async (show) => {
		if (!show) return;
		if (coords.value) return;
		await tryLocate();
	},
);

function toggleType(value) {
	const idx = selectedTypes.value.indexOf(value);
	if (idx === -1) {
		selectedTypes.value = [...selectedTypes.value, value];
	} else {
		selectedTypes.value = selectedTypes.value.filter((v) => v !== value);
	}
}

function selectAllTypes() {
	selectedTypes.value = [];
}

function isTypeSelected(value) {
	return selectedTypes.value.includes(value);
}

async function handleSend() {
	const text = inputText.value.trim();
	if (!text || isLoading.value || isLocating.value) return;
	if (!coords.value) {
		error.value = "尚未取得定位，無法查詢。";
		return;
	}

	inputText.value = "";
	error.value = "";
	messages.value.push({ id: ++idCounter, role: "user", content: text });
	await scrollToBottom();

	isLoading.value = true;
	try {
		const apiMessages = messages.value
			.filter((m) => m.role === "user" || m.role === "assistant")
			.map((m) => ({ role: m.role, content: m.content }));
		const res = await http.post(
			"/api/v1/eco_diet/nearby-chat",
			{
				lat: coords.value.lat,
				lng: coords.value.lng,
				radius: radiusValue.value,
				facility_types: selectedTypes.value,
				messages: apiMessages,
			},
			{ baseURL: "" },
		);
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.answer ?? "（無回應）",
		});
		if (Array.isArray(res.data.actions) && res.data.actions.length) {
			emit("apply-actions", res.data.actions);
		}
	} catch {
		error.value = "AI 服務暫時無法使用，請稍後再試。";
	} finally {
		isLoading.value = false;
		await scrollToBottom();
	}
}

function handleInputKeydown(event) {
	if (event.key !== "Enter") return;
	if (!event.metaKey && !event.ctrlKey) return;
	event.preventDefault();
	handleSend();
}

function handleClose() {
	resetState();
	emit("close");
}
</script>

<template>
	<Teleport to="body">
		<Transition name="ecodietnearbychat">
			<div
				v-if="show"
				class="ecodietnearbychat"
				role="dialog"
				aria-modal="true"
			>
				<div class="ecodietnearbychat-header">
					<span class="material-icons ecodietnearbychat-icon">eco</span>
					<span class="ecodietnearbychat-title">附近綠色飲食 AI 助理</span>
					<button
						class="ecodietnearbychat-close"
						aria-label="關閉"
						@click="handleClose"
					>
						<span class="material-icons">close</span>
					</button>
				</div>

				<div class="ecodietnearbychat-meta">
					<template v-if="isLocating">
						<span class="material-icons ecodietnearbychat-meta-icon">my_location</span>
						定位中…
					</template>
					<template v-else-if="coords">
						<span class="material-icons ecodietnearbychat-meta-icon">place</span>
						目前位置：{{ coords.lat.toFixed(5) }}, {{ coords.lng.toFixed(5) }}
					</template>
					<template v-else>
						<span class="material-icons ecodietnearbychat-meta-icon">location_off</span>
						尚未取得定位
					</template>
				</div>

				<div class="ecodietnearbychat-controls">
					<div class="ecodietnearbychat-controls-row">
						<label class="ecodietnearbychat-controls-label">查詢半徑</label>
						<input
							v-model.number="radiusValue"
							type="range"
							class="ecodietnearbychat-slider"
							min="300"
							max="1500"
							step="100"
						>
						<span class="ecodietnearbychat-controls-value">{{ radiusValue }} m</span>
					</div>
					<div class="ecodietnearbychat-controls-row">
						<label class="ecodietnearbychat-controls-label">設施類型</label>
						<div class="ecodietnearbychat-chips">
							<button
								type="button"
								class="ecodietnearbychat-chip"
								:class="{ 'ecodietnearbychat-chip--selected': selectedTypes.length === 0 }"
								@click="selectAllTypes"
							>
								全部
							</button>
							<button
								v-for="opt in FACILITY_OPTIONS"
								:key="opt.value"
								type="button"
								class="ecodietnearbychat-chip"
								:class="{ 'ecodietnearbychat-chip--selected': isTypeSelected(opt.value) }"
								:style="isTypeSelected(opt.value) ? { background: opt.color, borderColor: opt.color } : {}"
								@click="toggleType(opt.value)"
							>
								{{ opt.label }}
							</button>
						</div>
					</div>
					<p class="ecodietnearbychat-controls-tip">
						下一則訊息將以此為查詢條件
					</p>
				</div>

				<div
					ref="messageListRef"
					class="ecodietnearbychat-messages"
				>
					<div
						v-for="msg in messages"
						:key="msg.id"
						:class="['ecodietnearbychat-bubble', `ecodietnearbychat-bubble--${msg.role}`]"
					>
						{{ msg.content }}
					</div>
					<div
						v-if="isLoading"
						class="ecodietnearbychat-bubble ecodietnearbychat-bubble--assistant"
					>
						<div class="ecodietnearbychat-dots">
							<span /><span /><span />
						</div>
					</div>
				</div>

				<div
					v-if="error"
					class="ecodietnearbychat-error"
				>
					<span>{{ error }}</span>
					<button
						v-if="!coords"
						class="ecodietnearbychat-error-retry"
						type="button"
						:disabled="isLocating"
						@click="tryLocate"
					>
						<span class="material-icons">refresh</span>
						重試定位
					</button>
				</div>

				<div class="ecodietnearbychat-input-row">
					<textarea
						v-model="inputText"
						class="ecodietnearbychat-input"
						placeholder="例如：附近有什麼環保餐廳？"
						rows="1"
						:disabled="isLoading || isLocating || !coords"
						@keydown="handleInputKeydown"
					/>
					<button
						class="ecodietnearbychat-send"
						:disabled="isLoading || isLocating || !coords || !inputText.trim()"
						aria-label="送出"
						@click="handleSend"
					>
						<span class="material-icons">send</span>
					</button>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped lang="scss">
.ecodietnearbychat {
	width: 380px;
	height: 560px;
	display: flex;
	flex-direction: column;
	position: fixed;
	right: 24px;
	bottom: 96px;
	border-radius: 8px;
	background: var(--color-component-background);
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
	overflow: hidden;
	max-width: calc(100vw - 2 * var(--font-m));
	max-height: calc(100vh - 2 * var(--font-m));
	z-index: 1000;

	&-header {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: var(--font-s);
		padding: var(--font-m);
		border-bottom: 1px solid var(--color-border);
	}

	&-icon {
		color: #5fcf80;
		font-size: 20px;
	}

	&-title {
		flex: 1;
		color: var(--color-normal-text);
		font-size: var(--font-m);
		font-weight: 600;
	}

	&-close {
		display: flex;
		align-items: center;
		padding: 2px;
		border: none;
		border-radius: 4px;
		background: none;
		color: var(--color-complement-text);
		cursor: pointer;

		&:hover {
			background: rgba(255, 255, 255, 0.08);
			color: var(--color-normal-text);
		}
	}

	&-meta {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: 4px;
		padding: var(--font-s) var(--font-m);
		border-bottom: 1px solid var(--color-border);
		color: var(--color-complement-text);
		font-size: var(--font-s);

		&-icon {
			font-size: 14px;
		}
	}

	&-controls {
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: var(--font-s) var(--font-m);
		border-bottom: 1px solid var(--color-border);

		&-row {
			display: flex;
			align-items: center;
			gap: var(--font-s);
		}

		&-label {
			flex-shrink: 0;
			width: 56px;
			color: var(--color-complement-text);
			font-size: var(--font-s);
		}

		&-value {
			flex-shrink: 0;
			min-width: 48px;
			text-align: right;
			color: var(--color-normal-text);
			font-size: var(--font-s);
		}

		&-tip {
			margin: 0;
			color: var(--color-complement-text);
			font-size: 0.7rem;
			text-align: right;
			opacity: 0.7;
		}
	}

	&-slider {
		flex: 1;
		min-width: 0;
		accent-color: var(--color-highlight);
		cursor: pointer;
	}

	&-chips {
		flex: 1;
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}

	&-chip {
		padding: 3px 10px;
		border: 1px solid var(--color-border);
		border-radius: 999px;
		background: transparent;
		color: var(--color-complement-text);
		font-size: var(--font-s);
		cursor: pointer;
		transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;

		&:hover {
			color: var(--color-normal-text);
			border-color: var(--color-normal-text);
		}

		&--selected {
			border-color: var(--color-highlight);
			background: var(--color-highlight);
			color: #fff;

			&:hover {
				color: #fff;
				border-color: var(--color-highlight);
			}
		}
	}

	&-messages {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--font-m);
		padding: var(--font-m) var(--font-s) var(--font-m) var(--font-m);
		min-height: 0;
		overflow-x: hidden;
		overflow-y: scroll;
		scrollbar-gutter: stable;
		scrollbar-width: thin;
		scrollbar-color: var(--color-complement-text) transparent;

		&::-webkit-scrollbar {
			width: 4px;
		}

		&::-webkit-scrollbar-track {
			background: transparent;
		}

		&::-webkit-scrollbar-thumb {
			border-radius: 8px;
			background: var(--color-complement-text);
		}

		&::-webkit-scrollbar-thumb:hover {
			background: var(--color-normal-text);
		}
	}

	&-error {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: var(--font-s);
		padding: var(--font-s) var(--font-m);
		color: #f87171;
		font-size: var(--font-s);
		line-height: 1.5;

		span {
			flex: 1;
		}

		&-retry {
			flex-shrink: 0;
			display: inline-flex;
			align-items: center;
			gap: 4px;
			padding: 4px 10px;
			border: 1px solid var(--color-border);
			border-radius: 999px;
			background: transparent;
			color: var(--color-normal-text);
			font-size: var(--font-s);
			cursor: pointer;
			transition: background 0.15s ease;

			.material-icons {
				font-size: 14px;
			}

			&:hover:not(:disabled) {
				background: rgba(255, 255, 255, 0.08);
			}

			&:disabled {
				opacity: 0.5;
				cursor: not-allowed;
			}
		}
	}

	&-input-row {
		flex-shrink: 0;
		display: flex;
		align-items: flex-end;
		gap: var(--font-s);
		padding: var(--font-s) var(--font-m);
		border-top: 1px solid var(--color-border);
	}

	&-input {
		flex: 1;
		min-width: 0;
		padding: var(--font-s);
		border: 1px solid var(--color-border);
		border-radius: 6px;
		background: var(--color-background);
		color: var(--color-normal-text);
		font-size: var(--font-s);
		line-height: 1.5;
		resize: none;

		&:focus {
			outline: none;
			border-color: var(--color-highlight);
		}

		&:disabled {
			opacity: 0.5;
		}
	}

	&-send {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		padding: 0;
		border: none;
		border-radius: 50%;
		background: #5fcf80;
		color: #fff;
		cursor: pointer;
		transition: background 0.15s ease;

		.material-icons {
			font-size: 18px;
		}

		&:hover:not(:disabled) {
			background: #4cb86c;
		}

		&:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
	}

	&-bubble {
		flex-shrink: 0;
		max-width: 85%;
		padding: var(--font-s) var(--font-m);
		border-radius: 12px;
		font-size: var(--font-s);
		line-height: 1.6;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
		word-break: break-word;

		&--assistant {
			align-self: flex-start;
			border-bottom-left-radius: 4px;
			background: var(--color-background);
			color: var(--color-normal-text);
		}

		&--user {
			align-self: flex-end;
			border-bottom-right-radius: 4px;
			background: #5fcf80;
			color: #fff;
		}
	}

	&-dots {
		display: flex;
		align-items: center;
		gap: 5px;
		height: 20px;

		span {
			width: 7px;
			height: 7px;
			border-radius: 50%;
			background: var(--color-complement-text);
			animation: ecodietnearbychat-bounce 1.2s infinite;

			&:nth-child(2) {
				animation-delay: 0.2s;
			}

			&:nth-child(3) {
				animation-delay: 0.4s;
			}
		}
	}
}

@keyframes ecodietnearbychat-bounce {
	0%, 80%, 100% {
		transform: scale(0.6);
		opacity: 0.4;
	}

	40% {
		transform: scale(1);
		opacity: 1;
	}
}

.ecodietnearbychat-enter-active,
.ecodietnearbychat-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.ecodietnearbychat-enter-from,
.ecodietnearbychat-leave-to {
	opacity: 0;
	transform: translateY(8px);
}
</style>
