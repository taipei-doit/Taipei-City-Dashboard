<template>
  <div class="ai-report">
    <div class="ai-report__input-row">
      <input
        v-model="locationQuery"
        class="ai-report__input"
        type="text"
        placeholder="輸入路口名稱，例如：信義路/基隆路"
        :disabled="loading"
        @keyup.enter="generateReport"
      />
      <button
        class="ai-report__btn"
        :disabled="loading || !locationQuery.trim()"
        @click="generateReport"
      >
        <span v-if="loading" class="material-icons ai-report__spin">autorenew</span>
        <span v-else class="material-icons">psychology</span>
        {{ loading ? "分析中..." : "AI 分析" }}
      </button>
    </div>

    <div v-if="!report && !loading" class="ai-report__placeholder">
      <span class="material-icons">directions_walk</span>
      <p>輸入路口名稱，AI 將自動查詢事故統計並生成安全改善建議報告</p>
    </div>

    <div v-if="loading" class="ai-report__loading">
      <span class="material-icons ai-report__spin">autorenew</span>
      <p>正在分析路口安全資料，請稍候...</p>
    </div>

    <div v-else-if="error" class="ai-report__error">
      <span class="material-icons">error_outline</span>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="report" class="ai-report__result">
      <div class="ai-report__result-header">
        <span class="material-icons">summarize</span>
        路口安全評估報告
        <button class="ai-report__clear" @click="clearReport">
          <span class="material-icons">refresh</span>
        </button>
      </div>
      <div class="ai-report__content">{{ report }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import http from "../../router/axios";

const locationQuery = ref("");
const loading = ref(false);
const report = ref("");
const error = ref("");

const SYSTEM_PROMPT = `你是一位台灣行人安全政策分析師，專門分析路口事故資料並提供具體改善建議。
請使用 get_pedestrian_hotspot 工具查詢指定路口的事故統計資料，然後依據以下格式生成路口安全報告：
1. 路口概況（事故件數、傷亡人數）
2. 主要風險因素（肇因、高峰時段、號誌狀況）
3. 具體改善建議（2-3 項可行措施，如行人保護時相、縮短右轉等待、加強執法時段等）
請使用繁體中文，語氣專業簡潔。`;

async function generateReport() {
  if (!locationQuery.value.trim() || loading.value) return;

  loading.value = true;
  report.value = "";
  error.value = "";

  try {
    const res = await http.post("/ai/chat/twai", {
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        {
          role: "user",
          content: `請查詢並分析「${locationQuery.value.trim()}」的行人事故狀況，提供改善建議。`,
        },
      ],
      tools: [
        {
          type: "function",
          function: {
            name: "get_pedestrian_hotspot",
            description:
              "查詢雙北行人事故熱點路口的統計資料，包含事故件數、主要肇因、高峰時段、號誌狀況等",
            parameters: {
              type: "object",
              properties: {
                location: {
                  type: "string",
                  description: '路口名稱關鍵字，例如「信義路/基隆路」',
                },
                city: {
                  type: "string",
                  enum: ["taipei", "ntpc"],
                  description: "城市：taipei=臺北市，ntpc=新北市",
                },
              },
              required: ["location"],
            },
          },
        },
      ],
      max_new_tokens: 800,
      temperature: 0.3,
    });

    report.value = res.data?.data?.content || "無法取得分析結果";
  } catch (err) {
    error.value =
      err.response?.status === 401
        ? "請先登入才能使用 AI 分析功能"
        : err.response?.data?.message || "分析失敗，請稍後再試";
  } finally {
    loading.value = false;
  }
}

function clearReport() {
  report.value = "";
  error.value = "";
  locationQuery.value = "";
}
</script>

<style scoped>
.ai-report {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
  height: 100%;
  overflow: hidden;
}

.ai-report__input-row {
  display: flex;
  gap: 8px;
}

.ai-report__input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #444);
  background: var(--color-surface, #1e1e1e);
  color: var(--color-text, #fff);
  font-size: 0.875rem;
  outline: none;
}

.ai-report__input:focus {
  border-color: var(--color-highlight, #5eb3f0);
}

.ai-report__btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: 4px;
  border: none;
  background: var(--color-highlight, #5eb3f0);
  color: #fff;
  font-size: 0.875rem;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.2s;
}

.ai-report__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-report__spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.ai-report__placeholder,
.ai-report__loading,
.ai-report__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  color: var(--color-complement-text, #aaa);
  text-align: center;
  font-size: 0.875rem;
}

.ai-report__placeholder .material-icons {
  font-size: 2rem;
  opacity: 0.4;
}

.ai-report__error {
  color: #e57373;
}

.ai-report__result {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.ai-report__result-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--color-complement-text, #aaa);
  border-bottom: 1px solid var(--color-border, #444);
  padding-bottom: 6px;
}

.ai-report__clear {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-complement-text, #aaa);
  display: flex;
  align-items: center;
}

.ai-report__content {
  flex: 1;
  overflow-y: auto;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text, #fff);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
