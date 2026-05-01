<!-- Component Name: NearbyA11yChatModal -->
<script setup>
import { ref, nextTick, watch } from "vue";
import axios from "axios";
import { useAuthStore } from "../store/authStore";

const props = defineProps({
	show: { type: Boolean, default: false },
	radius: { type: Number, default: 500 },
});
const emit = defineEmits(["close"]);

const authStore = useAuthStore();

const messages = ref([]);
const isLoading = ref(false);
const isLocating = ref(false);
const error = ref("");
const inputText = ref("");
const coords = ref(null);
const messageListRef = ref(null);
let idCounter = 0;

function authHeaders() {
	return { Authorization: `Bearer ${authStore.token || ""}` };
}

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
			content: "已取得您的定位，請問附近的捷運無障礙設施狀況？例如「附近有沒有故障的電梯？」",
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
		const res = await axios.post(
			"/api/v1/mrt/a11y/nearby-chat",
			{
				lat: coords.value.lat,
				lng: coords.value.lng,
				radius: props.radius,
				messages: apiMessages,
			},
			{ headers: authHeaders() },
		);
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.answer ?? "（無回應）",
		});
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
		<Transition name="nearby-a11y-chat">
			<div
				v-if="show"
				class="nearbya11ychat"
				role="dialog"
				aria-modal="true"
			>
				<div class="nearbya11ychat-header">
					<span class="material-icons nearbya11ychat-icon">location_on</span>
					<span class="nearbya11ychat-title">附近捷運無障礙設施 AI 助理</span>
					<button
						class="nearbya11ychat-close"
						aria-label="關閉"
						@click="handleClose"
					>
						<span class="material-icons">close</span>
					</button>
				</div>

				<div class="nearbya11ychat-meta">
					<template v-if="isLocating">
						<span class="material-icons nearbya11ychat-meta-icon">my_location</span>
						定位中…
					</template>
					<template v-else-if="coords">
						<span class="material-icons nearbya11ychat-meta-icon">place</span>
						目前位置：{{ coords.lat.toFixed(5) }}, {{ coords.lng.toFixed(5) }}（半徑 {{ radius }} m）
					</template>
					<template v-else>
						<span class="material-icons nearbya11ychat-meta-icon">location_off</span>
						尚未取得定位
					</template>
				</div>

				<div
					ref="messageListRef"
					class="nearbya11ychat-messages"
				>
					<div
						v-for="msg in messages"
						:key="msg.id"
						:class="['nearbya11ychat-bubble', `nearbya11ychat-bubble--${msg.role}`]"
					>
						{{ msg.content }}
					</div>
					<div
						v-if="isLoading"
						class="nearbya11ychat-bubble nearbya11ychat-bubble--assistant"
					>
						<div class="nearbya11ychat-dots">
							<span /><span /><span />
						</div>
					</div>
				</div>

				<div
					v-if="error"
					class="nearbya11ychat-error"
				>
					<span>{{ error }}</span>
					<button
						v-if="!coords"
						class="nearbya11ychat-error-retry"
						type="button"
						:disabled="isLocating"
						@click="tryLocate"
					>
						<span class="material-icons">refresh</span>
						重試定位
					</button>
				</div>

				<div class="nearbya11ychat-input-row">
					<textarea
						v-model="inputText"
						class="nearbya11ychat-input"
						placeholder="例如：附近哪些電梯故障？"
						rows="1"
						:disabled="isLoading || isLocating || !coords"
						@keydown="handleInputKeydown"
					/>
					<button
						class="nearbya11ychat-send"
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
.nearbya11ychat {
	width: 380px;
	height: 480px;
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
		color: var(--color-highlight);
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
		background: var(--color-highlight);
		color: #fff;
		cursor: pointer;
		transition: background 0.15s ease;

		.material-icons {
			font-size: 18px;
		}

		&:hover:not(:disabled) {
			background: #4a8ce8;
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
			background: var(--color-highlight);
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
			animation: nearbya11ychat-bounce 1.2s infinite;

			&:nth-child(2) {
				animation-delay: 0.2s;
			}

			&:nth-child(3) {
				animation-delay: 0.4s;
			}
		}
	}
}

@keyframes nearbya11ychat-bounce {
	0%, 80%, 100% {
		transform: scale(0.6);
		opacity: 0.4;
	}

	40% {
		transform: scale(1);
		opacity: 1;
	}
}

.nearby-a11y-chat-enter-active,
.nearby-a11y-chat-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.nearby-a11y-chat-enter-from,
.nearby-a11y-chat-leave-to {
	opacity: 0;
	transform: translateY(8px);
}
</style>
