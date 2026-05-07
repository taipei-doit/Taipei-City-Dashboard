<script setup>
import { ref } from "vue";
import AiChatModal from "../AiChatModal.vue";
import EcoDietStoryModal from "../EcoDietStoryModal.vue";
import EcoDietNearbyChatModal from "../EcoDietNearbyChatModal.vue";
import EcoDietWalkRoute from "../EcoDietWalkRoute.vue";

const props = defineProps({
	isMapView: { type: Boolean, default: false },
});

const showAiModal = ref(false);
const showStoryModal = ref(false);
const showNearbyChat = ref(false);

const aiComponentId = ref("");
const aiComponentName = ref("");
const aiAnchor = ref({ top: 0, left: 0 });

const walkRouteRef = ref(null);

function openAiModal(event, componentId, componentName) {
	if (aiComponentId.value !== componentId) {
		aiComponentId.value = componentId;
		aiComponentName.value = componentName;
	}
	const rect = event.currentTarget.getBoundingClientRect();
	aiAnchor.value = { top: rect.top, left: rect.left };
	showAiModal.value = true;
}

function openStoryModal() {
	showStoryModal.value = true;
}

function openNearbyChat() {
	showNearbyChat.value = true;
}

async function handleApplyActions(actions) {
	if (!Array.isArray(actions)) return;
	for (const a of actions) {
		if (a.type === "draw_route" && a.to && walkRouteRef.value) {
			await walkRouteRef.value.simulateClickRouteToFacility(a.to);
		}
	}
}

defineExpose({ openAiModal, openStoryModal, openNearbyChat });
</script>

<template>
  <AiChatModal
    :show="showAiModal"
    :component-id="aiComponentId"
    :component-name="aiComponentName"
    :anchor="aiAnchor"
    summary-endpoint="/api/v1/eco_diet/ai-summary"
    @close="showAiModal = false"
  />
  <EcoDietStoryModal
    :show="showStoryModal"
    @close="showStoryModal = false"
  />
  <template v-if="isMapView">
    <EcoDietNearbyChatModal
      :show="showNearbyChat"
      @close="showNearbyChat = false"
      @apply-actions="handleApplyActions"
    />
    <EcoDietWalkRoute ref="walkRouteRef" />
    <!-- 附近綠色飲食 AI 助理 FAB -->
    <button
      class="ecodiet-nearby-fab"
      title="附近綠色飲食 AI 助理"
      aria-label="附近綠色飲食 AI 助理"
      @click="showNearbyChat = true"
    >
      <span class="material-icons">eco</span>
    </button>
  </template>
</template>

<style scoped lang="scss">
.ecodiet-nearby-fab {
	width: 52px;
	height: 52px;
	display: flex;
	align-items: center;
	justify-content: center;
	position: fixed;
	right: 32px;
	bottom: 116px;
	border: none;
	border-radius: 50%;
	background: #5fcf80;
	color: #fff;
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
	cursor: pointer;
	transition: transform 0.15s ease, background 0.15s ease;
	z-index: 11;

	.material-icons {
		font-size: 26px;
	}

	&:hover {
		background: #4cb86c;
		transform: scale(1.05);
	}
}
</style>
