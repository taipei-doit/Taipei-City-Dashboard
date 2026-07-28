<script setup>
import { ref, watch } from "vue";
import http from "../../router/axios";
import { hexToSpan } from "../../assets/utilityFunctions/colorConvert";

const props = defineProps({
	index: { type: String },
	name: { type: String },
	city: { type: String },
	analysisTime: { type: String },
	description: {
		type: String,
	},
});
defineEmits(["close"]);

const response = ref(null);
const isLoading = ref(false);

const formatTime = (time) => {
	if (!time) return "";

	return time
		.replace("T", " ")
		.replace(/\.\d+Z?$/, "")
		.replace(/Z$/, "");
};

watch(
	() => [props.index, props.city],
	async ([index, city]) => {
		isLoading.value = true;
		try {
			const res = await http.get("/component/ai-summary", {
				params: { index, city, type: "chart" },
			});
			response.value = res;
		} finally {
			isLoading.value = false;
		}
	},
	{ immediate: true },
);
</script>

<template>
  <div
    class="overlay"
    @click.self="$emit('close')"
  >
    <div class="modal">
      <div class="modal-header">
        <div class="modal-title">
          <span class="title-icon">✦</span>
          <span class="title-text">AI 洞察</span>
        </div>
        <button
          class="close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="modal-content">
		<p class="ai-warning">提醒：本洞察內容係依據儀表板呈現之數值，由 AI 自動分析產生，可能存在解讀誤差，僅供參考。</p>
        <div class="row">
          <span class="meta-label">▪ 城市</span>
          <span class="description">
            : {{ city === "taipei" ? "臺北" : "雙北" }}</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 分析項目</span>
          <span class="description"> : {{ name }}</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 分析類別</span>
          <span class="description"> : 圖表</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 資料分析時間</span>
          <span class="description">
            <span
              v-if="isLoading"
              class="dots"
            >
              <span /><span /><span />
            </span>
            <template v-else>
              :
              {{
                formatTime(response?.data?.data?.updated_at)
              }}</template>
          </span>
        </div>

        <div class="divider" />

        <p class="section-label">
          ▪ 資料洞察成果
        </p>
        <p class="description result">
          <span
            v-if="isLoading"
            class="dots"
          >
            <span /><span /><span />
          </span>
          <template v-else>
            <span
              v-html="hexToSpan(response?.data?.data?.result)"
            />
          </template>
        </p>
      </div>

      <div class="modal-footer">
        <button
          class="btn-secondary"
          @click="$emit('close')"
        >
          ← 返回
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.65);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
	padding: 16px;
}

.modal {
	width: 100%;
	max-width: 480px;
	background: #2a2c2f;
	border: 1px solid #494b4e;
	border-radius: 5px;
	overflow: hidden;
}

.modal-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16px 20px;
	border-bottom: 1px solid #494b4e;
}

.modal-title {
	display: flex;
	align-items: center;
	gap: 8px;
}

.title-icon {
	font-size: 1.2rem;
	color: #c8cacc;
}

.title-text {
	font-size: 1rem;
	font-weight: 500;
	color: #ffffff;
}

.close-btn {
	background: transparent;
	border: none;
	cursor: pointer;
	color: #888787;
	display: flex;
	justify-content: center;
	align-items: center;
	font-size: 1rem;
	line-height: 1;
	padding: 0;
	width: 32px;
	height: 32px;
	border-radius: 999px;
	transition: background 0.15s;
}

.close-btn:hover {
	background: #3d3f42;
}

.modal-content {
	display: flex;
	flex-direction: column;
	gap: 6px;
	padding: 16px 20px;
}

.meta-label {
	flex-shrink: 0;
	font-size: 0.85rem;
	font-weight: 500;
	color: #ffffff;
	white-space: nowrap;
}

.divider {
	border-top: 1px solid #494b4e;
	margin: 6px 0;
}

.section-label {
	font-size: 0.85rem;
	font-weight: 500;
	color: #ffffff;
	margin: 0;
}

.ai-warning {
	display: flex;
	width: fit-content;
	align-items: center;
	gap: 6px;
	font-size: 0.78rem;
	color: #ffffff;
	background: rgba(160, 164, 168, 0.08);
	border: 1px solid #ffffff;
	border-radius: 4px;
	padding: 6px 10px;
	margin: 0 0 4px;
	line-height: 1.4;
}

.description {
	font-size: 0.9rem;
	color: #888787;
	line-height: 1.6;
	margin: 0;
}

.modal-footer {
	padding: 12px 20px 16px;
	display: flex;
	justify-content: flex-end;
	border-top: 1px solid #494b4e;
}

.btn-secondary {
	background: transparent;
	border: 1px solid #494b4e;
	border-radius: 6px;
	padding: 6px 18px;
	font-size: 0.95rem;
	color: #888787;
	cursor: pointer;
	transition: background 0.15s;
}

.btn-secondary:hover {
	background: #3d3f42;
}

@media (max-width: 520px) {
	.overlay {
		padding: 0 1rem;
	}

	.modal-header {
		padding: 14px 16px;
	}

	.modal-content {
		gap: 4px;
		padding: 14px 16px;
	}

	.modal-footer {
		padding: 10px 16px 24px;
	}

	.meta-label {
		font-size: 0.85rem;
	}

	.description {
		font-size: 0.9rem;
	}
}

.dots {
	display: inline-flex;
	gap: 5px;
	align-items: center;
}

.dots span {
	width: 6px;
	height: 6px;
	border-radius: 50%;
	background: #888787;
	animation: bounce 1.2s infinite ease-in-out;
}

.dots span:nth-child(2) {
	animation-delay: 0.2s;
}
.dots span:nth-child(3) {
	animation-delay: 0.4s;
}

@keyframes bounce {
	0%,
	80%,
	100% {
		transform: translateY(0);
		opacity: 0.4;
	}
	40% {
		transform: translateY(-5px);
		opacity: 1;
	}
}

:deep(.color-preview) {
	display: inline-block;
	width: 12px;
	height: 12px;
	border-radius: 3px;
	margin: 0 4px;
	vertical-align: middle;
}
</style>
