<!-- Component Name: EcoDietStoryModal -->
<script setup>
import { ref, nextTick, watch } from "vue";
import axios from "axios";
import { useAuthStore } from "../store/authStore";

const props = defineProps({
	show: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const authStore = useAuthStore();

const SYSTEM_PROMPT = `你是「綠色飲食行為流程儀表板」的故事講述者，以溫暖、有人情味的方式介紹這個儀表板的故事與意義。

以下是這個儀表板的核心故事：

故事：一頓晚餐，改變一座城市

在台北市的某個下班夜晚，小安站在便利商店門口，盯著架上打折的便當發呆。
他其實沒有特別想吃什麼，只是單純覺得——每天吃、每天丟，好像有點浪費。

那天，他滑到一個剛上線的「綠色飲食儀表板」。

【了解】原來，選擇早就存在
他打開地圖，發現一件讓他有點驚訝的事：
原來他公司附近，居然有好幾家「環保餐廳」，而且整個新北市加起來，竟然有幾百個選擇。
地圖上的點，一個一個亮著。有些標示「惜食」、有些寫「在地食材」、有些甚至標「不主動提供一次性餐具」。
他第一次意識到：「不是沒有選擇，是我從來沒看見。」

【參與】一個小決定的開始
隔天中午，小安沒有再走去平常的連鎖店。
他打開儀表板的篩選器，勾選：惜食、公司附近、外帶友善。
然後選了一家他從來沒注意過的小店。老闆娘笑著說：「我們都會把賣不完的食材再利用，不浪費。」
那一餐其實沒有特別驚艷，但小安心裡有一種奇怪的滿足感。像是——他參與了什麼。

【看見成果】原來真的有差
幾週後，他又打開儀表板，這次不是看餐廳，而是看「成果」。
廚餘量的趨勢線、每年減少的浪費量、換算成碳排減少。
畫面上寫著一行話：「你的一次選擇，可能減少了 0.5 公斤的食物浪費」
他愣了一下。這些數字很小，小到幾乎感覺不到。
但當整個城市一起做的時候——線條真的在往下走。
那一刻他才真正理解：「原來改變不是一瞬間，是累積。」

【給予】當選擇變成連結
某天晚上，小安整理冰箱。裡面有一些還能吃，但他確定不會吃完的食物。
以前，他會直接丟掉。但這次，他打開儀表板的最後一個功能：「找到最近的實物銀行」
地圖跳出幾個點，他點了最近的一個。隔天，他把食物送過去。
門口的志工說：「這些會分給需要的人，謝謝你。」
小安離開時，心情有點複雜。那不是「做好事」的開心，比較像是——「我終於把一件原本會浪費的事，變成有意義的事。」

結尾
幾個月後，小安已經不太特別去想「要不要環保」。因為那已經變成習慣。
他只是：偶爾看一下附近有沒有新的餐廳、吃不完就想著能不能分享、看到數據時，知道自己是其中一部分。
而那個儀表板，對他來說，也不再只是工具，而是一個提醒：「你的一頓飯，其實正在改變這座城市。」

---
請以這個故事為核心，用溫暖、簡潔的中文回答使用者的問題。可以引導使用者探索儀表板的各個功能（環保餐廳地圖、廚餘趨勢、實物銀行等）。`;

const OPENING_USER_MSG = "請用簡短有溫度的方式，向我介紹這個儀表板的故事。";

const messages = ref([]);
const isLoading = ref(false);
const error = ref("");
const inputText = ref("");
const messageListRef = ref(null);
let idCounter = 0;

function authHeaders() {
	return { Authorization: `Bearer ${authStore.token || ""}` };
}

function isAuthError(err) {
	if (!authStore.token) return true;
	const status = err?.response?.status;
	return status === 401 || status === 403;
}

const LOGIN_REQUIRED_MESSAGE = "請先登入後再使用 AI 助理。";

async function scrollToBottom() {
	await nextTick();
	if (messageListRef.value) {
		messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
	}
}

watch(
	() => props.show,
	async (show) => {
		if (!show) return;
		if (messages.value.length > 0) return;
		await fetchOpening();
	}
);

async function fetchOpening() {
	isLoading.value = true;
	error.value = "";
	try {
		const res = await axios.post(
			"/api/v1/ai/chat/twai",
			{
				messages: [
					{ role: "system", content: SYSTEM_PROMPT },
					{ role: "user", content: OPENING_USER_MSG },
				],
				temperature: 0.7,
				max_tokens: 600,
				top_p: 0.95,
			},
			{ headers: authHeaders() }
		);
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.data?.content ?? "（無回應）",
		});
		await scrollToBottom();
	} catch (err) {
		error.value = isAuthError(err)
			? LOGIN_REQUIRED_MESSAGE
			: "AI 故事服務暫時無法使用，請稍後再試。";
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
			{ role: "system", content: SYSTEM_PROMPT },
			...messages.value.map((m) => ({ role: m.role, content: m.content })),
		];
		const res = await axios.post(
			"/api/v1/ai/chat/twai",
			{
				messages: apiMessages,
				temperature: 0.7,
				max_tokens: 600,
				top_p: 0.95,
			},
			{ headers: authHeaders() }
		);
		messages.value.push({
			id: ++idCounter,
			role: "assistant",
			content: res.data.data?.content ?? "（無回應）",
		});
	} catch (err) {
		error.value = isAuthError(err)
			? LOGIN_REQUIRED_MESSAGE
			: "發生錯誤，請稍後再試。";
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
	emit("close");
}
</script>

<template>
  <Teleport to="body">
    <Transition name="story-modal">
      <div
        v-if="show"
        class="story-modal-overlay"
        @click.self="handleClose"
      >
        <div
          class="story-modal"
          role="dialog"
          aria-modal="true"
        >
          <div class="story-modal__header">
            <span class="material-icons story-modal__icon">auto_stories</span>
            <span class="story-modal__title">綠色飲食｜儀表板故事</span>
            <button
              class="story-modal__close"
              aria-label="關閉"
              @click="handleClose"
            >
              <span class="material-icons">close</span>
            </button>
          </div>

          <div
            ref="messageListRef"
            class="story-modal__messages"
          >
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['story-bubble', `story-bubble--${msg.role}`]"
            >
              {{ msg.content }}
            </div>

            <div
              v-if="isLoading"
              class="story-bubble story-bubble--assistant"
            >
              <div class="story-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>

          <div
            v-if="error"
            class="story-modal__error"
          >
            {{ error }}
          </div>

          <div class="story-modal__input-row">
            <textarea
              v-model="inputText"
              class="story-modal__input"
              placeholder="繼續追問故事…（Ctrl+Enter 送出）"
              rows="2"
              :disabled="isLoading"
              @keydown="handleInputKeydown"
            />
            <button
              class="story-modal__send"
              :disabled="isLoading || !inputText.trim()"
              aria-label="送出"
              @click="handleSend"
            >
              <span class="material-icons">send</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
.story-modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	z-index: 1100;
	display: flex;
	align-items: center;
	justify-content: center;
	width: 100vw;
	height: 100vh;
	background: rgba(0, 0, 0, 0.55);
}

.story-modal {
	display: flex;
	flex-direction: column;
	width: 640px;
	height: 75vh;
	max-width: calc(100vw - 2 * var(--font-m));
	max-height: calc(100vh - 2 * var(--font-m));
	border-radius: 12px;
	background: var(--color-component-background);
	box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
	overflow: hidden;

	&__header {
		display: flex;
		flex-shrink: 0;
		align-items: center;
		gap: var(--font-s);
		padding: var(--font-m) calc(var(--font-m) * 1.2);
		border-bottom: 1px solid var(--color-border);
		background: linear-gradient(
			135deg,
			rgba(90, 156, 248, 0.08) 0%,
			rgba(90, 248, 156, 0.06) 100%
		);
	}

	&__icon {
		font-size: 22px;
		color: #5af89c;
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
		transition: color 0.15s, background 0.15s;

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
		transition: border-color 0.15s;

		&:focus {
			outline: none;
			border-color: #5af89c;
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
		background: #5af89c;
		color: #090909;
		cursor: pointer;
		transition: background 0.15s ease;

		.material-icons {
			font-size: 18px;
		}

		&:hover:not(:disabled) {
			background: #3ed47e;
		}

		&:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
	}
}

.story-bubble {
	flex-shrink: 0;
	max-width: 85%;
	padding: var(--font-s) var(--font-m);
	border-radius: 12px;
	font-size: var(--font-s);
	line-height: 1.7;
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
		background: rgba(90, 248, 156, 0.18);
		color: var(--color-normal-text);
	}
}

.story-dots {
	display: flex;
	align-items: center;
	height: 20px;
	gap: 5px;

	span {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: #5af89c;
		animation: story-bounce 1.2s infinite;

		&:nth-child(2) {
			animation-delay: 0.2s;
		}

		&:nth-child(3) {
			animation-delay: 0.4s;
		}
	}
}

@keyframes story-bounce {
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

.story-modal-enter-active,
.story-modal-leave-active {
	transition: opacity 0.25s ease;

	.story-modal {
		transition: opacity 0.25s ease, transform 0.25s ease;
	}
}

.story-modal-enter-from,
.story-modal-leave-to {
	opacity: 0;

	.story-modal {
		opacity: 0;
		transform: scale(0.96) translateY(12px);
	}
}
</style>
