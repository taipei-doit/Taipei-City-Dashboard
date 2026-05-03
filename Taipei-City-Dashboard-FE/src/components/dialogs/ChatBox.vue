<script setup>
import { ref, watch, nextTick, computed } from "vue";
import { storeToRefs } from "pinia";
import SendIcon from "../icons/SendIcon.vue";
import BotLogo from "../icons/BotLogo.vue";
import UserLogo from "../icons/UserLogo.vue";
import DashboardComponent from "../../dashboardComponent/DashboardComponent.vue";

import { useChatStore } from "../../store/chatStore";
import { useContentStore } from "../../store/contentStore";
import { useAuthStore } from "../../store/authStore";
import http from "../../router/axios";

const props = defineProps({
	expanded: { type: Boolean, default: false },
});
const emit = defineEmits(["toggle-expand", "start-compare"]);

const chatStore = useChatStore();
const contentStore = useContentStore();
const authStore = useAuthStore();
const { addChatData, addQueryData, saveChatLog } = chatStore;
const { createDashboard } = contentStore;
const { chatData } = storeToRefs(chatStore);
const { editDashboard } = storeToRefs(contentStore);
const { user } = storeToRefs(authStore);

const userMessage = ref("");
const chatAreaRef = ref(null);
const isStickyOpen = ref(false);
const dashboardCreationLoading = ref(false);

// 多選比較
const selectedComponents = ref([]);
const compareLoading = ref(false);
const compareViewLoading = ref(false);

const dashboardQuickQuestions = {
	"長照關懷": ["扶養比及老化指數", "高齡就業人口之年增結構", "長照指標"],
	"務實交通": ["YouBike使用情況", "電動巴士比例", "自行車道路統計資料"],
	"圖資資訊": ["自行車道路網圖資"],
	"食安健康": ["食因性疾病通報", "腹瀉送醫統計", "醫療量能床位通知"],
};

const quickQuestions = computed(() => {
	const name = contentStore.currentDashboard?.name;
	return dashboardQuickQuestions[name] || [];
});

function isSelected(item) {
	return selectedComponents.value.some(
		(c) => c.index === item.index && c.city === item.city,
	);
}

function toggleComponent(item) {
	const idx = selectedComponents.value.findIndex(
		(c) => c.index === item.index && c.city === item.city,
	);
	if (idx >= 0) {
		selectedComponents.value.splice(idx, 1);
	} else {
		selectedComponents.value.push(item);
	}
}

function clearSelection() {
	selectedComponents.value = [];
}

async function analyzeComponents() {
	if (selectedComponents.value.length === 0 || compareLoading.value) return;
	compareLoading.value = true;

	const names = selectedComponents.value
		.map((c) => `「${c.name}」（${c.city === "taipei" ? "臺北市" : "雙北市"}）`)
		.join("、");

	const prompt = `請查詢並比對以下 ${selectedComponents.value.length} 個儀表板組件的資料：${names}。找出各組件的趨勢、彼此的關聯性或值得注意的差異，提供整合性分析，限150字。`;

	addChatData({
		role: "user",
		content: `🔬 AI 比對：${selectedComponents.value.map((c) => c.name).join(" × ")}`,
	});

	addChatData({ role: "bot", content: "🔍 正在查詢組件資料並進行比對分析…" });

	try {
		const baseUrl = import.meta.env.VITE_API_URL || "";
		const res = await fetch(`${baseUrl}/ai/chat/twai`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${authStore.token}`,
			},
			body: JSON.stringify({
				stream: true,
				messages: [{ role: "user", content: prompt }],
			}),
		});

		if (!res.ok) throw new Error(res.status);

		const reader = res.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";
		let result = "";
		const lastMsg = chatData.value[chatData.value.length - 1];
		lastMsg.content = "";

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split("\n");
			buffer = lines.pop();
			for (const line of lines) {
				if (!line.startsWith("data:")) continue;
				try {
					const json = JSON.parse(line.slice(5).trim());
					if (json.generated_text) {
						const text = json.generated_text
							.replace(/<tool[^>]*>[\s\S]*?<\/function>/g, "")
							.replace(/<[^>]+>/g, "");
						result += text;
						lastMsg.content = result;
					}
				} catch { /* skip */ }
			}
		}

		if (!result) lastMsg.content = "無法取得分析結果，請稍後再試。";
	} catch {
		const lastMsg = chatData.value[chatData.value.length - 1];
		lastMsg.content = "AI 分析服務暫時無法使用，請稍後再試。";
	} finally {
		compareLoading.value = false;
	}
}

async function fetchAndViewComponents() {
	if (selectedComponents.value.length === 0 || compareViewLoading.value) return;
	compareViewLoading.value = true;
	emit("start-compare"); // 切換到寬版比較模式

	const names = selectedComponents.value.map((c) => c.name).join(" × ");
	addChatData({ role: "bot", content: `正在載入「${names}」組件資料…`, compareComponents: null });

	try {
		const loaded = [];
		for (const sel of selectedComponents.value) {
			const r1 = await http.get("/component/", {
				params: { filtermode: "eq", filterby: "index", filtervalue: sel.index, city: sel.city },
			});
			const configs = r1.data?.data;
			if (!configs || configs.length === 0) continue;
			const config = configs[0];

			const r2 = await http.get(`/component/${config.id}/chart`, {
				params: { city: config.city },
			});
			config.chart_data = r2.data?.data ?? null;
			if (r2.data?.categories) {
				config.chart_config.categories = r2.data.categories;
			}
			loaded.push(config);
		}

		const lastMsg = chatData.value[chatData.value.length - 1];
		if (loaded.length > 0) {
			lastMsg.content = `已載入 ${loaded.length} 個組件，可對照查看：`;
			lastMsg.compareComponents = loaded;
		} else {
			lastMsg.content = "無法取得組件資料，請稍後再試。";
		}
	} catch {
		const lastMsg = chatData.value[chatData.value.length - 1];
		lastMsg.content = "載入組件資料失敗，請稍後再試。";
	} finally {
		compareViewLoading.value = false;
	}
}

const qaBtnHandler = async (text, relations) => {
	if (text === "建立儀表板") {
		if (dashboardCreationLoading.value === true) return;
		dashboardCreationLoading.value = true;
		const response = await http.get(`/dashboard/`);
		if (response.data?.data?.personal?.length > 20) {
			addChatData({
				role: "bot",
				content: "您的個人儀表板已超出限制 20 個，請先移除既有儀表板後，重新執行本功能！",
			});
			dashboardCreationLoading.value = false;
			return;
		}
		const components = Array.from(new Set(relations.map((r) => r.id))).map(
			(id) => ({ id }),
		);
		if (user.value.user_id) {
			editDashboard.value = {
				index: "",
				name: "推薦儀表板",
				icon: "star",
				components: components,
			};
			await createDashboard();
			saveChatLog("建立儀表板", "使用者成功建立儀表板!");
		} else {
			addChatData({ role: "bot", content: "請先登入會員以使用此功能喔！" });
		}
		dashboardCreationLoading.value = false;
	}
};

const sendBtnHandler = (text) => {
	if (!text.trim()) return;
	addQueryData({ role: "user", content: text });
	userMessage.value = "";
};

const toggleSticky = () => {
	isStickyOpen.value = !isStickyOpen.value;
};

watch(
	() => chatData.value.length,
	async () => {
		await nextTick();
		const chat = chatAreaRef.value;
		if (!chat) return;
		chat.scrollTop = chat.scrollHeight - chat.clientHeight;
	},
	{ deep: true },
);
</script>

<template>
  <div class="chat-widget">
    <!-- 標題 -->
    <div class="header">
      <h3>臺北城市儀表板小幫手</h3>
      <button
        class="expand-btn"
        :title="expanded ? '縮小視窗' : '放大視窗'"
        @click="emit('toggle-expand')"
      >
        <span class="material-icons">{{ expanded ? 'close_fullscreen' : 'open_in_full' }}</span>
      </button>
    </div>

    <!-- 聊天區 -->
    <div
      ref="chatAreaRef"
      class="chat-area scrollbar-custom"
    >
      <!-- 置頂訊息 -->
      <div class="chat-message sticky-message">
        <div
          class="sticky-header"
          @click="toggleSticky"
        >
          <span>置頂公告：小幫手使用須知</span>
          <button class="toggle-btn">
            {{ isStickyOpen ? "-" : "+" }}
          </button>
        </div>
        <div
          v-show="isStickyOpen"
          class="sticky-body"
        >
          <span>輸入您想查詢的主題，小幫手會推薦相關組件。勾選多個組件可請 AI 進行跨組件比對分析。</span>
        </div>
      </div>

      <!-- 主題快速問題 -->
      <div
        v-if="quickQuestions.length"
        class="quick-questions"
      >
        <p class="quick-questions-label">
          <span class="material-icons">tips_and_updates</span>
          {{ contentStore.currentDashboard?.name }} 相關查詢
        </p>
        <div class="quick-questions-chips">
          <button
            v-for="q in quickQuestions"
            :key="q"
            class="quick-chip"
            @click="sendBtnHandler(q)"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <!-- 對話訊息 -->
      <div
        v-for="chat in chatData"
        :key="chat.id"
        class="message"
      >
        <!-- 機器人訊息 -->
        <div
          v-if="chat.role === 'bot'"
          class="bot"
        >
          <div class="avatar">
            <BotLogo />
          </div>
          <div class="content">
            <div
              v-if="chat.content"
              class="message--bubble"
            >
              <p>{{ chat.content }}</p>
            </div>

            <!-- 組件卡片（取代舊 table） -->
            <div
              v-if="chat.relations && chat.relations.length"
              class="component-cards"
            >
              <div
                v-for="(item, index) in chat.relations"
                :key="index"
                class="component-card"
                :class="{ selected: isSelected(item) }"
                @click="toggleComponent(item)"
              >
                <div class="card-top">
                  <span class="card-check">
                    <span class="material-icons">
                      {{ isSelected(item) ? 'check_box' : 'check_box_outline_blank' }}
                    </span>
                  </span>
                  <span class="card-name">{{ item.name }}</span>
                  <span class="card-city">
                    {{ item.city === 'taipei' ? '臺北' : '雙北' }}
                  </span>
                </div>
                <div class="card-score">
                  <div
                    class="score-bar"
                    :style="{ width: `${Math.round(item.score * 100)}%` }"
                  />
                  <span>{{ Math.round(item.score * 100) }}% 相關</span>
                </div>
              </div>
            </div>

            <!-- 並排組件查看 -->
            <div
              v-if="chat.compareComponents && chat.compareComponents.length"
              class="compare-view"
            >
              <div
                v-for="comp in chat.compareComponents"
                :key="`compare-${comp.index}-${comp.city}`"
                class="compare-item"
              >
                <DashboardComponent
                  :config="comp"
                  mode="half"
                  :footer="false"
                  :info-btn="false"
                  :ai-summary-btn="false"
                  :favorite-btn="false"
                  :delete-btn="false"
                  :select-btn="false"
                  :active-city="comp.city"
                  :city-tag="comp.city === 'taipei' ? [{ name: '臺北', value: 'taipei' }] : [{ name: '雙北', value: 'metrotaipei' }]"
                />
              </div>
            </div>

            <!-- 建立儀表板按鈕 -->
            <div
              v-if="chat.button"
              v-horizontal-wheel
              class="message--button scrollbar-x-hide"
            >
              <button
                v-for="btn in chat.button"
                :key="btn.id"
                @click="qaBtnHandler(btn.text, chat.relations)"
              >
                {{ btn.text }}
              </button>
            </div>
          </div>
        </div>

        <!-- 使用者訊息 -->
        <div
          v-else
          class="user"
        >
          <div class="avatar">
            <UserLogo />
          </div>
          <div
            v-if="chat.content"
            class="content"
          >
            <div class="message--bubble">
              <p>{{ chat.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 比較列（有勾選時顯示） -->
    <div
      v-if="selectedComponents.length > 0"
      class="compare-bar"
    >
      <div class="compare-chips">
        <span
          v-for="c in selectedComponents"
          :key="`${c.index}|${c.city}`"
          class="compare-chip"
        >
          {{ c.name }}
          <button @click.stop="toggleComponent(c)">×</button>
        </span>
      </div>
      <div class="compare-actions">
        <button
          class="compare-btn-view"
          :disabled="compareViewLoading"
          @click="fetchAndViewComponents"
        >
          <span class="material-icons">dashboard</span>
          {{ compareViewLoading ? '載入中…' : '並排查看' }}
        </button>
        <button
          class="compare-btn-analyze"
          :disabled="compareLoading"
          @click="analyzeComponents"
        >
          <span class="material-icons">auto_awesome</span>
          {{ compareLoading ? '分析中…' : 'AI 比對' }}
        </button>
        <button
          class="compare-btn-clear"
          @click="clearSelection"
        >
          清除
        </button>
      </div>
    </div>

    <!-- 輸入區 -->
    <div class="input-area">
      <input
        v-model="userMessage"
        type="text"
        placeholder="輸入您想查詢的主題..."
        @keyup.enter="sendBtnHandler(userMessage)"
      >
      <button @click="sendBtnHandler(userMessage)">
        <SendIcon />
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
$bg-dark: #090909;
$panel-bg: #494b4e;
$card-bg: #1e2124;
$border-color: #888787;
$input-bg: #d9d9d9;
$white: #ffffff;
$highlight: #3b82f6;
$scroll-thumb-hover: #ababab;
$radius-10: 10px;
$radius-15: 15px;
$radius-20: 20px;

.scrollbar-x-hide {
	scrollbar-width: none;
	&::-webkit-scrollbar { display: none; }
}

.scrollbar-custom {
	&::-webkit-scrollbar { width: 2px; background: transparent; }
	&::-webkit-scrollbar-thumb { background: $white; border-radius: 8px; }
	&::-webkit-scrollbar-thumb:hover { background: $scroll-thumb-hover; }
}

.chat-widget {
	width: 100%;
	height: 100%;
	border-radius: $radius-20;
	overflow: hidden;
	background: $bg-dark;
	border: 1px solid $border-color;
	display: flex;
	flex-direction: column;

	.header {
		padding: 0.75rem 1rem;
		background: $panel-bg;
		border-bottom: 3px solid $border-color;
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		h3 { font-size: 18px; font-weight: 700; color: $white; margin: 0; }

		.expand-btn {
			background: none;
			border: none;
			cursor: pointer;
			padding: 2px 4px;
			display: flex;
			align-items: center;
			opacity: 0.6;
			transition: opacity 0.15s;
			&:hover { opacity: 1; }
			span {
				font-family: "Material Icons";
				color: $white;
				font-size: 18px;
			}
		}
	}

	.chat-area {
		flex: 1;
		margin: 0.25rem;
		padding: 0.75rem;
		overflow-y: auto;
		background: $bg-dark;
		min-height: 0;

		// 置頂訊息
		.sticky-message {
			padding: 4px 10px;
			margin: 0px 8px;
			border-radius: 8px;
			background-color: $bg-dark;
			border: 1px solid $white;
			position: sticky;
			top: 0;
			z-index: 10;

			.sticky-header {
				display: flex;
				font-weight: bold;
				justify-content: space-between;
				align-items: center;
				cursor: pointer;
				padding: 8px 12px;
			}
			.sticky-body { padding: 8px 12px; font-weight: 400; font-size: 14px; }
			.toggle-btn {
				background: none; border: none; font-size: 14px;
				cursor: pointer; color: $white;
			}
		}

		// 快速問題
		.quick-questions {
			padding: 8px 8px 4px;
			border-bottom: 1px solid #333;
			margin-bottom: 8px;

			.quick-questions-label {
				display: flex; align-items: center; gap: 4px;
				font-size: 11px; color: #888; margin-bottom: 6px;
				span { font-family: "Material Icons"; font-size: 13px; color: $highlight; }
			}
			.quick-questions-chips { display: flex; flex-wrap: wrap; gap: 6px; }
			.quick-chip {
				background: #1e2124; border: 1px solid $highlight;
				color: #a0c4ff; font-size: 12px; padding: 4px 10px;
				border-radius: 20px; cursor: pointer; white-space: nowrap;
				transition: background 0.15s;
				&:hover { background: #2a3a52; }
			}
		}

		.message {
			padding: 8px;

			.bot, .user {
				display: flex;
				gap: 0.5rem;
				align-items: flex-start;

				&.user { flex-direction: row-reverse; }

				.avatar {
					width: 40px; height: 40px;
					display: flex; align-items: center; justify-content: center;
					flex-shrink: 0;
					svg { width: 100%; height: auto; }
				}

				.content {
					display: flex;
					flex-direction: column;
					gap: 0.5rem;
					min-width: 0;
					flex: 1;

					.message--bubble {
						border: 1px solid $white;
						border-radius: $radius-10;
						background: #282a2c;
						p {
							color: $white; white-space: pre-line; margin: 0;
							padding: 8px 16px; font-size: 15px;
						}
					}

					// 組件卡片
					.component-cards {
						display: flex;
						flex-direction: column;
						gap: 6px;
						width: 100%;

						.component-card {
							background: $card-bg;
							border: 1px solid #333;
							border-radius: 8px;
							padding: 8px 12px;
							cursor: pointer;
							transition: border-color 0.15s, background 0.15s;

							&:hover { border-color: $highlight; background: #1a2030; }
							&.selected { border-color: $highlight; background: #1a2535; }

							.card-top {
								display: flex;
								align-items: center;
								gap: 8px;
								margin-bottom: 6px;

								.card-check {
									span {
										font-family: "Material Icons";
										font-size: 18px;
										color: $highlight;
										line-height: 1;
									}
								}
								.card-name {
									flex: 1; font-size: 14px; font-weight: 600;
									color: $white;
								}
								.card-city {
									font-size: 11px; padding: 2px 6px;
									background: #2a3a52; color: #a0c4ff;
									border-radius: 10px; white-space: nowrap;
								}
							}

							.card-score {
								display: flex; align-items: center; gap: 8px;
								.score-bar {
									height: 3px; background: $highlight;
									border-radius: 2px; transition: width 0.3s;
									max-width: 100%;
								}
								span { font-size: 11px; color: #888; white-space: nowrap; }
							}
						}
					}

					// 並排組件查看
					.compare-view {
						display: grid;
						grid-template-columns: 1fr 1fr;
						gap: 8px;
						width: 100%;

						.compare-item {
							min-width: 0; // 防止 grid item 撐破欄位
							border-radius: 5px;
							overflow: hidden;

							// 讓 DashboardComponent 填滿格子寬度
							:deep(.dashboardcomponent) {
								width: 100% !important;
								max-width: 100% !important;
							}
						}
					}

					.message--button {
						display: flex; gap: 0.5rem; overflow-x: auto;
						button {
							flex-shrink: 0; background: $panel-bg; color: $white;
							font-size: 14px; padding: 0.5rem 1rem;
							border-radius: $radius-15; border: none; cursor: pointer;
							white-space: nowrap;
							&:hover { filter: brightness(0.5); }
						}
					}
				}
			}
		}
	}

	// 比較列
	.compare-bar {
		flex-shrink: 0;
		background: #111;
		border-top: 1px solid #333;
		padding: 8px 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;

		.compare-chips {
			display: flex;
			flex-wrap: wrap;
			gap: 6px;

			.compare-chip {
				display: flex;
				align-items: center;
				gap: 4px;
				background: #1a2535;
				border: 1px solid $highlight;
				color: #a0c4ff;
				font-size: 12px;
				padding: 3px 8px;
				border-radius: 12px;

				button {
					background: none; border: none; color: #888;
					cursor: pointer; font-size: 14px; line-height: 1;
					padding: 0;
					&:hover { color: $white; }
				}
			}
		}

		.compare-actions {
			display: flex;
			gap: 8px;

			.compare-btn-view {
				flex: 1;
				display: flex; align-items: center; justify-content: center; gap: 4px;
				background: #1a6640; color: $white;
				border: none; border-radius: 8px;
				padding: 8px 12px; font-size: 13px; font-weight: 600;
				cursor: pointer;
				transition: filter 0.15s;

				span { font-family: "Material Icons"; font-size: 16px; }
				&:hover:not(:disabled) { filter: brightness(1.2); }
				&:disabled { opacity: 0.6; cursor: not-allowed; }
			}

			.compare-btn-analyze {
				flex: 1;
				display: flex; align-items: center; justify-content: center; gap: 4px;
				background: $highlight; color: $white;
				border: none; border-radius: 8px;
				padding: 8px 12px; font-size: 13px; font-weight: 600;
				cursor: pointer;
				transition: filter 0.15s;

				span { font-family: "Material Icons"; font-size: 16px; }
				&:hover:not(:disabled) { filter: brightness(1.2); }
				&:disabled { opacity: 0.6; cursor: not-allowed; }
			}

			.compare-btn-clear {
				background: #333; color: #aaa;
				border: none; border-radius: 8px;
				padding: 8px 12px; font-size: 13px;
				cursor: pointer;
				&:hover { background: #444; color: $white; }
			}
		}
	}

	.input-area {
		flex-shrink: 0;
		display: flex; align-items: center; justify-content: center;
		gap: 0.5rem; padding: 1rem 1.125rem;
		background: $panel-bg;

		input[type="text"] {
			background: $white; height: 35px; width: 100%;
			border-radius: 20px; padding: 0 1rem;
			border: none; outline: none; color: black;
		}
		button {
			height: 35px; display: flex; align-items: center; justify-content: center;
			background: transparent; border: none; cursor: pointer;
			&:hover { filter: brightness(0.5); }
		}
	}
}
</style>
