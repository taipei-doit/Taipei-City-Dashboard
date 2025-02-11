<!-- Developed by Taipei Urban Intelligence Center 2023-2024 -->

<script setup>
import { ref } from "vue";
import http from "../../router/axios";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";
import { useContentStore } from "../../store/contentStore";
import DialogContainer from "./DialogContainer.vue";

const dialogStore = useDialogStore();
const authStore = useAuthStore();
const contentStore = useContentStore();

const allInputs = ref({
	type: "組件基本資訊有誤",
	description: "",
	title: "",
});
const issueTypes = [
	"組件基本資訊有誤",
	"組件資料有誤或未更新",
	"系統問題",
	"其他建議",
];

async function handleSubmit() {
	const submitObject = {
		title: allInputs.value.title,
		description: allInputs.value.description,
		user_name: authStore.user.name,
		user_id: `${authStore.user.user_id}`,
		context: `類型：${allInputs.value.type} // 來源：${dialogStore.issue.id} - ${dialogStore.issue.index} - ${dialogStore.issue.name}`,
		status: "待處理",
	};
	await http.post(`/issue/`, submitObject);
	dialogStore.showNotification("success", "回報問題成功，感謝您的建議");
	contentStore.loading = false;
	handleClose();
}
function handleClose() {
	allInputs.value = {
		type: "組件基本資訊有誤",
		description: "",
		title: "",
	};
	dialogStore.dialogs.reportIssue = false;
}
</script>

<template>
  <DialogContainer
    dialog="reportIssue"
    @on-close="handleClose"
  >
    <div class="reportissue">
      <h2>回報問題</h2>
      <h3>問題標題* ({{ allInputs.title.length }}/20)</h3>
      <input
        v-model="allInputs.title"
        class="reportissue-input"
        type="text"
        :minLength="1"
        :maxLength="20"
        required
      >
      <h3>問題種類*</h3>
      <div
        v-for="item in issueTypes"
        :key="item"
      >
        <input
          :id="item"
          v-model="allInputs.type"
          class="reportissue-radio"
          type="radio"
          :value="item"
        >
        <label :for="item">
          <div />
          {{ item }}
        </label>
      </div>
      <h3>問題簡述* ({{ allInputs.description.length }}/200)</h3>
      <textarea
        v-model="allInputs.description"
        :minLength="1"
        :maxLength="200"
        required
      />
      <div class="reportissue-control">
        <button
          class="reportissue-control-cancel"
          @click="handleClose"
        >
          取消
        </button>
        <button
          v-if="allInputs.description && allInputs.title"
          class="reportissue-control-confirm"
          @click="handleSubmit"
        >
          回報問題
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.reportissue {
	width: 300px;
	display: flex;
	flex-direction: column;

	h3 {
		margin: 0.5rem 0;
		font-size: var(--font-s);
		font-weight: 400;
	}

	&-radio {
		display: none;

		&:checked + label {
			color: white;

			div {
				background-color: var(--color-highlight);
			}
		}

		&:hover + label {
			color: var(--color-highlight);

			div {
				border-color: var(--color-highlight);
			}
		}
	}

	label {
		position: relative;
		display: flex;
		align-items: center;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		transition: color 0.2s;
		cursor: pointer;

		div {
			width: calc(var(--font-s) / 2);
			height: calc(var(--font-s) / 2);
			margin-right: 4px;
			padding: calc(var(--font-s) / 4);
			border-radius: 50%;
			border: 1px solid var(--color-border);
			transition: background-color 0.2s, border-color 0.2s;
		}
	}

	&-control {
		display: flex;
		justify-content: flex-end;
		margin-top: var(--font-ms);

		&-cancel {
			margin: 0 2px;
			padding: 4px 6px;
			border-radius: 5px;
			transition: color 0.2s;

			&:hover {
				color: var(--color-highlight);
			}
		}

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
