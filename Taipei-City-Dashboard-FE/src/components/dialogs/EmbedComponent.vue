<!-- eslint-disable indent -->
<!-- eslint-disable no-mixed-spaces-and-tabs -->
<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { computed } from "vue";
import { useDialogStore } from "../../store/dialogStore";

import DialogContainer from "./DialogContainer.vue";

const dialogStore = useDialogStore();

const embedTemplate = computed(() => {
	return `<iframe
	id="Taipei-City-Dashboard-Component-${dialogStore.moreInfoContent.id}"
	title="${dialogStore.moreInfoContent.name}"
	src="https://citydashboard.taipei/embed/${dialogStore.moreInfoContent.id}"
	width="450"
	height="400"
	style="border-radius: 5px"
	frameborder="0"
	allow="fullscreen"
	loading="lazy"
></iframe>
	`;
});

function handleCopy() {
	navigator.clipboard.writeText(embedTemplate.value);
	dialogStore.showNotification("success", "複製內嵌碼成功");
}
function handleClose() {
	dialogStore.dialogs.embedComponent = false;
}
</script>

<template>
  <DialogContainer
    dialog="embedComponent"
    @on-close="handleClose"
  >
    <div class="embedcomponent">
      <h2>內嵌組件</h2>
      <div class="embedcomponent-input">
        <h3>複製以下內嵌碼至您的網頁即可內嵌本組件</h3>
        <textarea
          type="text"
          disabled
          :value="embedTemplate"
        />
      </div>
      <div class="embedcomponent-control">
        <button
          class="embedcomponent-control-confirm"
          @click="handleCopy"
        >
          複製內嵌碼
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.embedcomponent {
	width: 300px;

	h3 {
		margin-bottom: 0.5rem;
		font-size: var(--font-s);
		font-weight: 400;
		color: var(--color-complement-text);
	}

	&-input {
		display: flex;
		flex-direction: column;
		margin: 0.5rem 0;

		textarea {
			font-size: var(--font-s);
			height: 160px;
			resize: none;
		}
	}

	&-control {
		display: flex;
		justify-content: flex-end;

		&-confirm {
			margin: 0 2px;
			padding: 4px 10px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}
}
</style>
