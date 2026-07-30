<script setup>
import { ref, watch } from "vue";
import http from "../../router/axios";
import { hexToSpan } from "../../assets/utilityFunctions/colorConvert";

const props = defineProps({
	index: { type: String, required: true },
	name: { type: String, required: true },
	city: { type: String, required: true },
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
				params: { index, city, type: "map" },
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
        <p class="ai-warning">
          提醒：本洞察內容係依據儀表板呈現之數值，由 AI
          自動分析產生，可能存在解讀誤差，僅供參考。
        </p>
        <div class="row">
          <span class="meta-label">▪ 城市</span>
          <span class="description">{{
            city === "taipei" ? "臺北" : "雙北"
          }}</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 分析項目</span>
          <span class="description">{{ name }}</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 分析類別</span>
          <span class="description">地圖</span>
        </div>
        <div class="row">
          <span class="meta-label">▪ 使用 AI 模型</span>
          <span class="description"> : Llama3.3-FFM-70B-32K</span>
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
            <template v-else>{{
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
          關閉
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
	position: fixed;
	inset: 0;
	z-index: 20;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.7);
	padding: 16px;
}

.modal {
	width: 100%;
	max-width: 420px;
	max-height: min(78dvh, 680px);
	display: flex;
	flex-direction: column;
	background: #2a2c2f;
	border: 1px solid #494b4e;
	border-radius: 5px;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
	overflow: hidden;
}

.modal-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16px 18px 14px;
	border-bottom: 1px solid #494b4e;
	flex-shrink: 0;
}

.modal-title {
	display: flex;
	align-items: center;
	gap: 8px;
}

.title-text {
	font-size: 1rem;
	font-weight: 500;
	color: #ffffff;
}

.close-btn {
	border: none;
	background: transparent;
	color: #888787;
	font-size: 0.85rem;
	cursor: pointer;
}

.modal-content {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding: 16px 18px;
	overflow-y: auto;
	flex: 1;
	min-height: 0;
}

.modal-content > * {
	flex-shrink: 0;
}

.row {
	display: flex;
	align-items: baseline;
	gap: 12px;
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
	margin: 4px 0;
}

.section-label {
	font-size: 0.85rem;
	font-weight: 600;
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

.result {
	padding-bottom: 4px;
}

.modal-footer {
	display: flex;
	justify-content: flex-end;
	padding: 12px 18px 18px;
	border-top: 1px solid #494b4e;
	flex-shrink: 0;
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

.dots {
	display: inline-flex;
	height: 20px;
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

@media (max-width: 520px) {
	.overlay {
		padding: 0 16px;
	}

	.modal-header {
		padding: 14px 16px;
	}

	.modal-content {
		padding: 14px 16px;
	}

	.modal-footer {
		padding: 10px 16px 16px;
	}
}
</style>
