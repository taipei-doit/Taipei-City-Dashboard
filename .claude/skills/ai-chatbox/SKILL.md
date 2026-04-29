---
name: ai-chatbox
description: >
  在 Taipei-City-Dashboard 的任意頁面為指定組件加入 AI 對話功能：hover 卡片出現 AI 按鈕，點擊後彈出對話框，自動以該組件的即時 DB 資料為 context 產生 AI 摘要，並支援使用者追問連續對話。

  觸發情境：使用者說「加 AI 摘要」「加 AI 對話」「讓組件可以追問 AI」「加一個 chatbox」「加 AI 按鈕」「幫我加 AI 功能到這個儀表板」「這個 component 可以給 AI 分析嗎」；或背景是某個 View 頁面已有 DashboardComponent，使用者想讓使用者可以針對組件資料詢問 AI。
  即使使用者沒明講 BE+FE 完整流程，只要目標是「用 AI 分析某個 dashboard component 的即時資料」，就觸發這個 skill。
---

# ai-chatbox

為 Taipei-City-Dashboard 的任意儀表板組件加入 AI 對話功能，完整走完 BE + FE 兩端實作。

## 為什麼需要這個 skill

這個功能橫跨 BE（Go/Gin + AI service）和 FE（Vue 3 + Axios），有幾個容易踩坑的地方：

- BE 的 `aiService.ChatWithTWCC` 接受的是 `[]llms.MessageContent`，不是裸字串
- `TWCC_*` env 必須明確列在 `docker-compose.yaml` 的 `environment` 區段，container 才能讀到
- FE modal 若用 `<Teleport to="body">` + `v-if/v-else` 相鄰，會因為 `v-else` 沒有緊鄰 `v-if` 而 crash；modal 要放在 `v-else` 區塊**之後**
- modal 定位改成 popover 時，需要從 `$event.currentTarget.getBoundingClientRect()` 取得按鈕位置，再以 `position: fixed` + computed style 定位
- `docker restart` 不會重新讀取 docker-compose 的 env 變更，需用 `docker compose up -d --no-build --no-deps <service>`

---

## 事前準備：確認輸入

開始前確認：

1. **目標 View 檔案路徑**（如 `src/views/MrtAccessibilityV2View.vue`）
2. **要加 AI 的組件清單**：每個組件的 `component_id`（對應 `/api/v1/mrt/a11y/...` 的路徑）和顯示名稱
3. **每個組件的 DB 查詢函數**：對應 `app/models/` 裡已有的 model 函數（如 `models.GetMrtAlertCount()`）及其回傳型別
4. **BE controller 檔案路徑**（如 `app/controllers/mrtA11y.go`）

如有缺漏，先問使用者補齊。

---

## Step 1：BE — 新增 AI Summary Controller

**修改**：`app/controllers/<domain>.go`

### 1a. 在 controller 檔案尾端加入

```go
// AiSummaryInput 接收 FE 傳來的組件 ID
type <Domain>AiSummaryInput struct {
    ComponentID string `json:"component_id" binding:"required"`
}

// Get<Domain>AiSummary handles POST /api/v1/<domain>/ai-summary
func Get<Domain>AiSummary(c *gin.Context) {
    var input <Domain>AiSummaryInput
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
        return
    }

    systemPrompt, err := build<Domain>ComponentPrompt(input.ComponentID)
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
        return
    }

    aiReq := aiService.AIChatRequest{
        SessionID: "<domain>-" + input.ComponentID + "-" + util.GenerateRandomString(6),
        UserID:    "system",
        IPAddress: c.ClientIP(),
        Messages: []llms.MessageContent{
            {
                Role:  llms.ChatMessageTypeSystem,
                Parts: []llms.ContentPart{llms.TextContent{Text: systemPrompt}},
            },
            {
                Role:  llms.ChatMessageTypeHuman,
                Parts: []llms.ContentPart{llms.TextContent{Text: "請根據以上即時數據，用繁體中文寫出 2–3 句精簡摘要，說明目前的狀況與最需注意的問題。請直接輸出摘要，不要加任何前言或標題。"}},
            },
        },
    }

    log, err := aiService.ChatWithTWCC(c.Request.Context(), aiReq,
        llms.WithMaxTokens(300),
        llms.WithTemperature(0.3),
    )
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "status":        "success",
        "summary":       log.Answer,
        "system_prompt": systemPrompt,
    })
}
```

### 1b. 實作 `build<Domain>ComponentPrompt`

針對每個 component_id，查對應的 model 函數，組成 system prompt：

```go
func build<Domain>ComponentPrompt(componentID string) (string, error) {
    switch componentID {
    case "<component-id-1>":
        data, err := models.Get<ModelFunc1>()
        if err != nil { return "", err }
        // 從 data 提取關鍵數字組成人讀字串
        return fmt.Sprintf(`你是 XXX 分析助理。以下是目前的即時資料：

【即時資料】
<資料摘要>

請用繁體中文回答，回答要簡潔清楚。`, /* 填入資料 */), nil

    // ... 其他 component_id

    default:
        return "", fmt.Errorf("unknown component_id: %s", componentID)
    }
}
```

**注意 model 回傳型別**（查 `app/models/componentData.go`）：
- `TwoDimensionalDataOutput.Data[i].Data` 是 `float64`，轉 int 用 `int(data[0].Data[0].Data)`
- `ThreeDimensionalDataOutput.Data[i]` 是 `int`，`series.Name` 是字串
- 自訂 struct 的欄位要查對應 model 檔確認欄位名

### 1c. 確認 import 區段

```go
import (
    "fmt"
    "net/http"

    "TaipeiCityDashboardBE/app/models"
    aiService "TaipeiCityDashboardBE/app/services/ai"
    "TaipeiCityDashboardBE/app/util"

    "github.com/gin-gonic/gin"
    "github.com/tmc/langchaingo/llms"
)
```

---

## Step 2：BE — 新增路由

**修改**：`app/routes/router.go`

在對應的 route group 函數裡加一行：

```go
routes.POST("/ai-summary", controllers.Get<Domain>AiSummary)
```

---

## Step 3：BE — 確認 docker-compose env

**重要**：`TWCC_*` env 必須在 `docker/docker-compose.yaml` 的 `dashboard-be` service `environment` 區段明確列出，否則 container 內拿到空字串。

```yaml
environment:
  # ... 其他 env
  TWCC_API_URL: ${TWCC_API_URL}
  TWCC_API_KEY: ${TWCC_API_KEY}
  TWCC_MODEL: ${TWCC_MODEL}
  TWCC_TIMEOUT: ${TWCC_TIMEOUT}
  TWCC_MAX_RETRY: ${TWCC_MAX_RETRY}
  TWCC_MAX_CONCURRENT: ${TWCC_MAX_CONCURRENT}
```

確認 `docker/.env` 也有對應的值。修改後要用 `docker compose up -d --no-build --no-deps dashboard-be`（不是 `docker restart`）讓 env 生效。

---

## Step 4：BE — 重啟並驗證

```bash
# 重啟 container（volume mount 專案，go run main.go 會自動重新編譯）
docker restart dashboard-be

# 等待重新編譯完成（約 30 秒）後確認路由已掛載
docker logs dashboard-be --tail 30 | grep ai-summary
```

> **注意**：若有修改 docker-compose.yaml 的 env（Step 3），要改用 `docker compose up -d --no-build --no-deps dashboard-be`（不是 `docker restart`）才能讓新的 env 生效。

---

## Step 5：FE — 建立 `<Domain>AiChatModal.vue`

**新增**：`src/components/<Domain>AiChatModal.vue`

完整組件結構：

```vue
<!-- Component Name: <Domain>AiChatModal -->
<script setup>
import { ref, nextTick, watch, computed } from "vue";
import axios from "axios";

const props = defineProps({
    show: { type: Boolean, default: false },
    componentId: { type: String, required: true },
    componentName: { type: String, default: "AI 助理" },
    anchor: { type: Object, default: () => ({ top: 0, left: 0 }) },
});
const emit = defineEmits(["close"]);

const messages = ref([]);
const isLoading = ref(false);
const error = ref("");
const inputText = ref("");
const systemPrompt = ref("");
const messageListRef = ref(null);
let idCounter = 0;

const MODAL_WIDTH = 380;
const MODAL_HEIGHT = 420;

// 計算 popover 位置：優先放按鈕左側，空間不足則右側
const popoverStyle = computed(() => {
    const { top, left } = props.anchor;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let x = left - MODAL_WIDTH - 8;
    if (x < 8) x = left + 40;
    let y = top;
    if (y + MODAL_HEIGHT > vh - 8) y = vh - MODAL_HEIGHT - 8;
    return { top: `${y}px`, left: `${x}px` };
});

async function scrollToBottom() {
    await nextTick();
    if (messageListRef.value) {
        messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
    }
}

// 同一組件只取一次初始摘要，切換組件時 messages 已重置，watch 會重新觸發
watch(() => props.show, async (val) => {
    if (!val) return;
    if (messages.value.length > 0) return;
    await fetchInitialSummary();
});

async function fetchInitialSummary() {
    isLoading.value = true;
    error.value = "";
    try {
        const res = await axios.post("/api/v1/<domain>/ai-summary", {
            component_id: props.componentId,
        });
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
            ...(systemPrompt.value ? [{ role: "system", content: systemPrompt.value }] : []),
            ...messages.value.map((m) => ({ role: m.role, content: m.content })),
        ];
        const res = await axios.post("/api/v1/ai/chat/twai", {
            messages: apiMessages,
            temperature: 0.5,
            max_tokens: 500,
            top_p: 0.95,
        });
        messages.value.push({
            id: ++idCounter,
            role: "assistant",
            content: res.data.content ?? "（無回應）",
        });
    } catch {
        error.value = "發生錯誤，請稍後再試。";
    } finally {
        isLoading.value = false;
        await scrollToBottom();
    }
}

function handleKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
}
</script>

<template>
    <Teleport to="body">
        <Transition name="domain-ai-modal">
            <div
                v-if="show"
                class="domain-ai-modal"
                role="dialog"
                aria-modal="true"
                :style="popoverStyle"
            >
                <div class="domain-ai-modal__header">
                    <span class="material-icons domain-ai-modal__icon">smart_toy</span>
                    <span class="domain-ai-modal__title">AI 助理｜{{ componentName }}</span>
                    <button class="domain-ai-modal__close" aria-label="關閉" @click="$emit('close')">
                        <span class="material-icons">close</span>
                    </button>
                </div>

                <div ref="messageListRef" class="domain-ai-modal__messages">
                    <div
                        v-for="msg in messages"
                        :key="msg.id"
                        :class="['domain-ai-bubble', `domain-ai-bubble--${msg.role}`]"
                    >{{ msg.content }}</div>

                    <div v-if="isLoading" class="domain-ai-bubble domain-ai-bubble--assistant">
                        <div class="domain-ai-dots">
                            <span /><span /><span />
                        </div>
                    </div>
                </div>

                <div v-if="error" class="domain-ai-modal__error">{{ error }}</div>

                <div class="domain-ai-modal__input-row">
                    <textarea
                        v-model="inputText"
                        class="domain-ai-modal__input"
                        placeholder="繼續詢問… (Enter 送出，Shift+Enter 換行)"
                        rows="1"
                        :disabled="isLoading"
                        @keydown="handleKeydown"
                    />
                    <button
                        class="domain-ai-modal__send"
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
// 把 domain-ai- 前綴替換成專案命名（避免多個 chatbox 衝突）
.domain-ai-modal {
    position: fixed;
    display: flex;
    flex-direction: column;
    width: 380px;
    max-width: calc(100vw - 2 * var(--font-m));
    max-height: 60vh;
    border-radius: 8px;
    background: var(--color-component-background);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    z-index: 1000;

    &__header {
        display: flex;
        flex-shrink: 0;
        align-items: center;
        gap: var(--font-s);
        padding: var(--font-m);
        border-bottom: 1px solid var(--color-border);
    }

    &__icon { font-size: 20px; color: var(--color-highlight); }

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
        &:hover { color: var(--color-normal-text); background: rgba(255,255,255,0.08); }
    }

    &__messages {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: var(--font-s);
        padding: var(--font-m);
        overflow-y: auto;
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
        padding: var(--font-s);
        border: 1px solid var(--color-border);
        border-radius: 6px;
        background: var(--color-background);
        color: var(--color-normal-text);
        font-size: var(--font-s);
        line-height: 1.5;
        resize: none;
        &:focus { outline: none; border-color: var(--color-highlight); }
        &:disabled { opacity: 0.5; }
    }

    &__send {
        display: flex;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border: none;
        border-radius: 6px;
        background: var(--color-highlight);
        color: #fff;
        cursor: pointer;
        transition: background 0.15s ease;
        &:hover:not(:disabled) { background: #4a8ce8; }
        &:disabled { opacity: 0.5; cursor: not-allowed; }
        .material-icons { font-size: 18px; }
    }
}

.domain-ai-bubble {
    max-width: 85%;
    padding: var(--font-s) var(--font-m);
    border-radius: 12px;
    font-size: var(--font-s);
    line-height: 1.6;
    white-space: pre-wrap;

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

.domain-ai-dots {
    display: flex;
    align-items: center;
    height: 20px;
    gap: 5px;
    span {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--color-complement-text);
        animation: domain-ai-bounce 1.2s infinite;
        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
    }
}

@keyframes domain-ai-bounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40%            { transform: scale(1);   opacity: 1;   }
}

.domain-ai-modal-enter-active,
.domain-ai-modal-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}
.domain-ai-modal-enter-from,
.domain-ai-modal-leave-to {
    opacity: 0;
    transform: translateY(8px);
}
</style>
```

> **命名提醒**：把所有 `domain-ai-` 前綴換成你的 domain（如 `mrt-ai-`），避免多個 chatbox 的 CSS 衝突。

---

## Step 6：FE — 修改 View 加入 AI 按鈕

**修改**：`src/views/<Domain>View.vue`

### 6a. 加 import 與 state

```js
import <Domain>AiChatModal from "../components/<Domain>AiChatModal.vue";

// AI modal state（放在其他 ref 宣告之後）
const activeAiComponentId = ref("");
const activeAiComponentName = ref("");
const showAiModal = ref(false);
const aiModalAnchor = ref({ top: 0, left: 0 });

function openAiModal(event, componentId, componentName) {
    if (activeAiComponentId.value !== componentId) {
        activeAiComponentId.value = componentId;
        activeAiComponentName.value = componentName;
        // 切換組件時清空對話歷史（讓 watch 重新觸發 fetchInitialSummary）
        // 注意：清空邏輯在 modal 組件的 watch 裡，這裡只需重設 id
    }
    const rect = event.currentTarget.getBoundingClientRect();
    aiModalAnchor.value = { top: rect.top, left: rect.left };
    showAiModal.value = true;
}
```

### 6b. 包 wrapper + 加按鈕

把每個 `<DashboardComponent>` 包一層 `<div class="ai-card-wrapper">`：

```vue
<div class="ai-card-wrapper">
    <DashboardComponent :config="c1Component" mode="default" :info-btn="false" />
    <button
        class="ai-chat-btn"
        title="AI 分析"
        @click="openAiModal($event, c1Component.id, 'C1｜組件名稱')"
    >
        <span class="material-icons">smart_toy</span>
    </button>
</div>
```

### 6c. 加 modal（放在最後一個 v-if/v-else 區塊**之後**）

```vue
<!-- ⚠️ modal 必須放在 v-if/v-else 對之後，不能插在中間 -->
<<Domain>AiChatModal
    :show="showAiModal"
    :component-id="activeAiComponentId"
    :component-name="activeAiComponentName"
    :anchor="aiModalAnchor"
    @close="showAiModal = false"
/>
```

### 6d. 加 SCSS

```scss
.ai-card-wrapper {
    position: relative;
    flex-shrink: 0;   // mapview flex 容器必要，防止卡片被壓縮
    height: 330px;    // grid 容器必要，固定 row 高度與 DashboardComponent 一致

    .ai-chat-btn {
        position: absolute;
        bottom: var(--font-s);
        right: var(--font-s);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border: none;
        border-radius: 50%;
        background: var(--color-highlight);
        color: #fff;
        cursor: pointer;
        opacity: 0;
        pointer-events: none;  // 隱形時不攔截 scroll 事件，否則 overflow-y: scroll 的容器無法滾動
        transition: opacity 0.15s ease, transform 0.15s ease;
        z-index: 10;

        .material-icons { font-size: 16px; }
        &:hover { transform: scale(1.1); }
    }

    &:hover .ai-chat-btn {
        opacity: 1;
        pointer-events: auto;
    }
}
```

---

## Step 7：驗證清單

### BE 驗證

```bash
# 測試單一 component
curl -X POST http://localhost:8088/api/v1/<domain>/ai-summary \
  -H "Content-Type: application/json" \
  -d '{"component_id": "<component-id>"}'
# 預期：{"status":"success","summary":"...","system_prompt":"..."}

# 測試未知 id → 應回 400
curl -X POST http://localhost:8088/api/v1/<domain>/ai-summary \
  -H "Content-Type: application/json" \
  -d '{"component_id": "unknown"}'
```

### FE 驗證

1. Hover 卡片 → 右下角出現 AI 按鈕（opacity 0 → 1）
2. 點擊 → popover 出現在按鈕旁邊，顯示 loading dots
3. 摘要顯示為 assistant 氣泡
4. 輸入追問 → Enter 送出 → AI 回覆
5. 切換不同卡片 → modal 重新取得對應資料（對話歷史不跨組件保留）
6. 同一卡片再次開啟 → 保留對話歷史

### 常見問題排查

| 症狀 | 原因 | 解法 |
|---|---|---|
| BE 回 500，log 顯示 `unsupported protocol scheme ""` | `TWCC_API_URL` 沒傳進 container | 確認 docker-compose.yaml 有列 `TWCC_*` env，用 `docker compose up -d --no-build --no-deps` 重建 |
| FE 報 `v-else has no adjacent v-if` | modal 插在 v-if/v-else 中間 | 把 `<Modal>` 移到整個 v-if/v-else 區塊之後 |
| popover 出現在右下角而非按鈕旁 | `anchor` prop 沒傳，或沒用 `$event` | 確認 `@click="openAiModal($event, ...)"` 有傳 event |
| 切換組件 modal 不更新 | `messages` 未清空，watch 條件 `messages.length > 0` 跳過 | 在 `openAiModal` 切換組件時加 `messages.value = []`（需 expose 或改為 emit 事件通知 modal 重置） |
| 卡片高度被壓縮 / row-gap 消失 | wrapper div 作為 grid item 但未設明確高度，grid stretch 行為不同於直接放 DashboardComponent | `.ai-card-wrapper { height: 330px }` |
| scroll container 無法滾動 | 隱形按鈕（`opacity: 0`）仍接收 pointer events，攔截滾輪事件 | `.ai-chat-btn { pointer-events: none }` + `&:hover .ai-chat-btn { pointer-events: auto }` |
