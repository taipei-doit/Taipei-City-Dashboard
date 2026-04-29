<!-- Component Name: MrtAiChatModal -->
<script setup>
import { ref, nextTick, watch, computed } from "vue";
import axios from "axios";
import { useAuthStore } from "../store/authStore";

const props = defineProps({
	show: { type: Boolean, default: false },
	componentId: { type: String, required: true },
	componentName: { type: String, default: "AI 助理" },
	anchor: { type: Object, default: () => ({ top: 0, left: 0 }) },
});
const emit = defineEmits(["close"]);

const authStore = useAuthStore();

const messages = ref([]);
const isLoading = ref(false);
const error = ref("");
const inputText = ref("");
const systemPrompt = ref("");
const messageListRef = ref(null);
let idCounter = 0;

function authHeaders() {
	return { Authorization: `Bearer ${authStore.token || ""}` };
}

const MODAL_WIDTH = 380;

const MODAL_HEIGHT = 420;

const popoverStyle = computed(() => {
	const { top, left } = props.anchor;
	const vh = window.innerHeight;
	// 優先放在按鈕左側；若超出螢幕左緣則放右側
	let x = left - MODAL_WIDTH - 8;
	if (x < 8) x = left + 40;
	// 從按鈕往上展開，確保 modal 底部不超出螢幕
	let y = top - MODAL_HEIGHT;
	if (y < 8) y = 8;
	return { top: `${y}px`, left: `${x}px` };
});

async function scrollToBottom() {
	await nextTick();
	if (messageListRef.value) {
		messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
	}
}

watch(
	[() => props.show, () => props.componentId],
	async ([show], [, oldComponentId]) => {
		if (!show) return;
		if (props.componentId !== oldComponentId) {
			messages.value = [];
			systemPrompt.value = "";
			error.value = "";
			inputText.value = "";
		}
		if (messages.value.length > 0) return;
		await fetchInitialSummary();
	}
);

async function fetchInitialSummary() {
	isLoading.value = true;
	error.value = "";
	try {
		const res = await axios.post("/api/v1/mrt/a11y/ai-summary", {
			component_id: props.componentId,
		}, { headers: authHeaders() });
		systemPrompt.value = res.data.system_prompt ?? "";
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.summary ?? "（無摘要內容）",
		});
		await scrollToBottom();
	} catch {
		error.value = "AI 摘要服務暫時無法使用，請稍後再試。";
	} finally {
		isLoading.value = false;
	}
}

async function handleSend() {
	const text = inputText.value.trim();
	if (!text || isLoading.value) return;

	inputText.value = "";
	error.value = "";
	messages.value.push({ id: ++idCounter, role: "user", content: text });
	await scrollToBottom();

	isLoading.value = true;
	try {
		const apiMessages = [
			...(systemPrompt.value
				? [{ role: "system", content: systemPrompt.value }]
				: []),
			...messages.value.map((m) => ({ role: m.role, content: m.content })),
		];
		const res = await axios.post("/api/v1/ai/chat/twai", {
			messages: apiMessages,
			temperature: 0.5,
			max_tokens: 500,
			top_p: 0.95,
		}, { headers: authHeaders() });
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.data?.content ?? "（無回應）",
		});
	} catch {
		error.value = "發生錯誤，請稍後再試。";
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

</script>

<template>
	<Teleport to="body">
		<Transition name="mrt-ai-modal">
			<div
				v-if="show"
				class="mrt-ai-modal"
				role="dialog"
				aria-modal="true"
				:style="popoverStyle"
			>
				<div class="mrt-ai-modal__header">
					<span class="material-icons mrt-ai-modal__icon">smart_toy</span>
					<span class="mrt-ai-modal__title">AI 助理｜{{ componentName }}</span>
					<button
						class="mrt-ai-modal__close"
						aria-label="關閉"
						@click="$emit('close')"
					>
						<span class="material-icons">close</span>
					</button>
				</div>

				<div
					ref="messageListRef"
					class="mrt-ai-modal__messages"
				>
					<div
						v-for="msg in messages"
						:key="msg.id"
						:class="['mrt-ai-bubble', `mrt-ai-bubble--${msg.role}`]"
					>
						{{ msg.content }}
					</div>

					<div
						v-if="isLoading"
						class="mrt-ai-bubble mrt-ai-bubble--assistant"
					>
						<div class="mrt-ai-dots">
							<span /><span /><span />
						</div>
					</div>
				</div>

				<div
					v-if="error"
					class="mrt-ai-modal__error"
				>
					{{ error }}
				</div>

				<div class="mrt-ai-modal__input-row">
					<textarea
						v-model="inputText"
						class="mrt-ai-modal__input"
						placeholder="繼續詢問…"
						rows="1"
						:disabled="isLoading"
						@keydown="handleInputKeydown"
					/>
					<button
						class="mrt-ai-modal__send"
						:disabled="isLoading || !inputText.trim()"
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
.mrt-ai-modal {
	position: fixed;
	display: flex;
	flex-direction: column;
	width: 380px;
	height: 420px;
	z-index: 1000;
	max-width: calc(100vw - 2 * var(--font-m));
	max-height: calc(100vh - 2 * var(--font-m));
	border-radius: 8px;
	background: var(--color-component-background);
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
	overflow: hidden;

	&__header {
		display: flex;
		flex-shrink: 0;
		align-items: center;
		gap: var(--font-s);
		padding: var(--font-m);
		border-bottom: 1px solid var(--color-border);
	}

	&__icon {
		font-size: 20px;
		color: var(--color-highlight);
	}

	&__title {
		flex: 1;
		font-size: var(--font-m);
		font-weight: 600;
		color: var(--color-normal-text);
	}

	&__close {
		display: flex;
		align-items: center;
		padding: 2px;
		border: none;
		border-radius: 4px;
		background: none;
		color: var(--color-complement-text);
		cursor: pointer;

		&:hover {
			color: var(--color-normal-text);
			background: rgba(255, 255, 255, 0.08);
		}
	}

	&__messages {
		display: flex;
		flex: 1;
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

	&__error {
		flex-shrink: 0;
		padding: var(--font-s) var(--font-m);
		color: #f87171;
		font-size: var(--font-s);
	}

	&__input-row {
		display: flex;
		flex-shrink: 0;
		align-items: flex-end;
		gap: var(--font-s);
		padding: var(--font-s) var(--font-m);
		border-top: 1px solid var(--color-border);
	}

	&__input {
		flex: 1;
		width: auto;
		min-width: 0;
		max-width: none;
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

	&__send {
		display: flex;
		flex-shrink: 0;
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
}

.mrt-ai-bubble {
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

.mrt-ai-dots {
	display: flex;
	align-items: center;
	height: 20px;
	gap: 5px;

	span {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--color-complement-text);
		animation: mrt-ai-bounce 1.2s infinite;

		&:nth-child(2) {
			animation-delay: 0.2s;
		}

		&:nth-child(3) {
			animation-delay: 0.4s;
		}
	}
}

@keyframes mrt-ai-bounce {
	0%,
	80%,
	100% {
		transform: scale(0.6);
		opacity: 0.4;
	}

	40% {
		transform: scale(1);
		opacity: 1;
	}
}

.mrt-ai-modal-enter-active,
.mrt-ai-modal-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.mrt-ai-modal-enter-from,
.mrt-ai-modal-leave-to {
	opacity: 0;
	transform: translateY(8px);
}
</style>
