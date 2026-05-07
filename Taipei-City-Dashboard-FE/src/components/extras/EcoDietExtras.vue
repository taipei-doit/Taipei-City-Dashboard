<script setup>
import { ref } from "vue";
import AiChatModal from "../AiChatModal.vue";
import EcoDietStoryModal from "../EcoDietStoryModal.vue";
import EcoDietNearbyChatModal from "../EcoDietNearbyChatModal.vue";

defineProps({
	isMapView: { type: Boolean, default: false },
});

const emit = defineEmits(["apply-actions"]);

const showAiModal = ref(false);
const showStoryModal = ref(false);
const showNearbyChat = ref(false);

const aiComponentId = ref("");
const aiComponentName = ref("");
const aiAnchor = ref({ top: 0, left: 0 });

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
  <EcoDietNearbyChatModal
    v-if="isMapView"
    :show="showNearbyChat"
    @close="showNearbyChat = false"
    @apply-actions="(actions) => emit('apply-actions', actions)"
  />
</template>
