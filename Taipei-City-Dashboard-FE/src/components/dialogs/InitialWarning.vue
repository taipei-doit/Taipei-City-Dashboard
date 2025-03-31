<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";

import DialogContainer from "./DialogContainer.vue";
import CustomCheckBox from "../utilities/forms/CustomCheckBox.vue";

const dialogStore = useDialogStore();
const authStore = useAuthStore();

// Stores whether the user doesn't want to see this dialog again
const dontShowAgain = ref(false);

function handleSubmit() {
	if (dontShowAgain.value) {
		localStorage.setItem("initialWarning", "shown");
	}
	handleClose();
}
function handleClose() {
	dontShowAgain.value = false;
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    dialog="initialWarning"
    @on-close="handleClose"
  >
    <div class="initialwarning">
      <h2 v-if="authStore.isMobileDevice">
        臺北城市儀表板行動版注意事項
      </h2>
      <h2 v-else>
        臺北城市儀表板使用說明
      </h2>
      <div
        v-if="authStore.isMobileDevice"
        class="initialwarning-message"
      >
        <p>
          臺北城市儀表板主要為給平板與電腦使用的平台，手機版僅為概覽使用，因此許多功能在行動版無法使用。
        </p>
        <br>
        <p>
          手機版不支援的功能包含：登入、地圖檢視、組件瀏覽平台、回報問題等。
        </p>
        <br>
        <p>如希望完整體驗本產品，建議改成使用平板或電腦檢視。</p>
      </div>
      <div
        v-else
        class="initialwarning-message"
      >
        <p>
          歡迎使用臺北城市儀表板，本產品的目的為 1.
          分享府內重要決策工具與成果 2. 促進府內與民間開發者的交流互動
          3. 推廣臺北開放資料應用。
        </p>
        <br>
        <p>
          本產品所呈現的資料集均以臺北開放資料為基礎，經由臺北大數據中心清理建構，並在本平台展示供民眾使用下載。
        </p>
        <br>
        <p>
          如果希望新增並儲存自己的儀表板，請點擊右上方的「登入」按鈕，並使用台北通APP註冊/登入本平台。
        </p>
      </div>
      <div class="initialwarning-dontshow">
        <input
          id="dontshow"
          v-model="dontShowAgain"
          type="checkbox"
          :value="true"
          class="custom-check-input"
        >
        <CustomCheckBox for="dontshow">
          下次不再顯示此視窗
        </CustomCheckBox>
      </div>
      <div class="initialwarning-control">
        <button
          class="initialwarning-control-confirm"
          @click="handleSubmit"
        >
          確定了解
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.initialwarning {
	width: 300px;

	&-message {
		display: flex;
		flex-direction: column;
		margin: var(--font-ms) 0;
	}

	&-dontshow {
		margin: var(--font-ms) 0 0.5rem;

		input {
			display: none;
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
