<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import { useAuthStore } from '../../store/authStore';

import DialogContainer from './DialogContainer.vue';
import CustomCheckBox from '../utilities/CustomCheckBox.vue';

const dialogStore = useDialogStore();
const authStore = useAuthStore();

// Stores whether the user doesn't want to see this dialog again
const dontShowAgain = ref(false);

function handleSubmit() {
	if (dontShowAgain.value) {
		localStorage.setItem('initialWarning', 'shown');
	}
	handleClose();
}
function handleClose() {
	dontShowAgain.value = false;
	dialogStore.hideAllDialogs();
}
</script>

<template>
	<DialogContainer dialog="initialWarning" @on-close="handleClose">
		<div class="initialwarning">
			<h2 v-if="authStore.isMobileDevice">臺北城市儀表板行動版注意事項</h2>
			<h2 v-else>臺北城市儀表板開源版注意事項</h2>
			<div class="initialwarning-message" v-if="authStore.isMobileDevice">
				<p>臺北城市儀表板主要為給平板與電腦使用的平台，手機版僅為概覽使用，因此許多功能在行動版無法使用，效能亦仍在優化中。</p>
				<br />
				<p>This is the demo version of Taipei City Dashboard 2.0. All data displayed are static and are not
					regularly updated.</p>
				<br />
				<p>如希望完整體驗本產品，建議改成使用平板或電腦檢視。</p>
			</div>
			<div class="initialwarning-message" v-else>
				<p>本產品為臺北市政府城市聯合儀表板的開源版本，目的為 1. 分享府內重要決策工具與成果 2. 促進府內與民間開發者的交流互動 3. 推廣臺北開放資料應用。</p>
				<br />
				<p>本產品所呈現的資料集均以臺北開放資料為基礎，經由臺北大數據中心清理建構，但由於資安與個資考量，本產品為純前端展示，並未串接資料API，資料的有效性因此將受到影響，新增儀表板、設定儀表板、新增組件、刪除組件等功能亦只有暫存，煩請留意及見諒。
				</p>
				<br />
				<p>This is the demo version of Taipei City Dashboard 2.0. All data displayed are static and are not
					regularly updated.</p>
			</div>
			<div class="initialwarning-dontshow">
				<input type="checkbox" id="dontshow" :value="true" v-model="dontShowAgain" class="custom-check-input" />
				<CustomCheckBox for="dontshow">下次不再顯示此視窗</CustomCheckBox>
			</div>
			<div class="initialwarning-control">
				<button class="initialwarning-control-confirm" @click="handleSubmit">確定了解</button>
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
		margin: 1rem 0;
	}

	&-dontshow {
		margin: 1rem 0 0.5rem;

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