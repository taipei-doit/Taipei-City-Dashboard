<script setup>
import { ref, watch, onMounted } from "vue";
import http from "../../router/axios";

const props = defineProps({
	index: { type: String },
	name: { type: String },
	city: { type: String },
	analysisTime: { type: String, default: "2026-06-04 12:00:00" },
	description: {
		type: String,
		default: "這裡是 AI 洞察的內容，可以根據實際需求進行調整。",
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
				params: { index, city, type: "map" },
			});
			response.value = res;
		} finally {
			isLoading.value = false;
		}
	},
	{ immediate: true }
);

const panelRef = ref(null);
const pos = ref({ x: 0, y: 0 });
const dragging = ref(false);
const dragOffset = ref({ x: 0, y: 0 });

onMounted(() => {
	const panelW = 480;
	const panelH = panelRef.value?.offsetHeight ?? 320;
	pos.value = {
		x: (window.innerWidth - panelW) / 2,
		y: (window.innerHeight - panelH) / 2,
	};
});

const onMouseDown = (e) => {
	dragging.value = true;
	dragOffset.value = {
		x: e.clientX - pos.value.x,
		y: e.clientY - pos.value.y,
	};
	window.addEventListener("mousemove", onMouseMove);
	window.addEventListener("mouseup", onMouseUp);
};

const onMouseMove = (e) => {
	if (!dragging.value) return;
	pos.value = {
		x: e.clientX - dragOffset.value.x,
		y: e.clientY - dragOffset.value.y,
	};
};

const onMouseUp = () => {
	dragging.value = false;
	window.removeEventListener("mousemove", onMouseMove);
	window.removeEventListener("mouseup", onMouseUp);
};
</script>

<template>
  <div
    ref="panelRef"
    class="floating-panel"
    :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
  >
    <div
      class="modal-header"
      @mousedown="onMouseDown"
    >
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
      <div class="row">
        <span class="meta-label">▪ 城市</span>
        <span class="description">{{ city === "taipei" ? "臺北" : "雙北" }}</span>
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
        <span class="meta-label">▪ 資料分析時間</span>
        <span class="description">
          <span
            v-if="isLoading"
            class="dots"
          >
            <span /><span /><span />
          </span>
          <template v-else>{{ formatTime(response?.data?.data?.updated_at) }}</template>
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
          {{ response?.data?.data?.result }}
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
</template>

<style scoped>
.floating-panel {
	position: fixed;
	width: 100%;
	max-width: 480px;
	background: #2a2c2f;
	border: 1px solid #494b4e;
	border-radius: 5px;
	overflow: hidden;
	z-index: 1000;
	box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
	user-select: none;
}

.modal-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16px 20px;
	border-bottom: 1px solid #494b4e;
	cursor: grab;
}

.modal-header:active {
	cursor: grabbing;
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
	font-size: 1rem;
	line-height: 1;
	padding: 2px 6px;
	border-radius: 4px;
	transition: background 0.15s;
}

.close-btn:hover {
	background: #3d3f42;
}

.modal-content {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding: 16px 20px;
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
	font-weight: 500;
	color: #ffffff;
	margin: 0;
}

.description {
	font-size: 0.9rem;
	color: #888787;
	line-height: 1.6;
	margin: 0;
}

.result {
	line-height: 1.8;
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

.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
	0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
	40%           { transform: translateY(-5px); opacity: 1; }
}
</style>