<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { defineProps } from "vue";
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["searchParams"]);

const { currentIssue } = storeToRefs(adminStore);

function handleConfirm() {
	adminStore.updateIssue(props.searchParams);
	handleClose();
}

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    :dialog="`adminEditIssue`"
    @on-close="handleClose"
  >
    <div class="admineditissue">
      <div class="admineditissue-header">
        <h2>用戶問題處理</h2>
        <button @click="handleConfirm">
          確定更改
        </button>
      </div>
      <div class="admineditissue-settings">
        <div class="admineditissue-settings-items">
          <div class="two-block">
            <label>回報用戶名稱</label>
            <label>回報用戶 ID</label>
          </div>
          <div class="two-block">
            <input
              v-model="currentIssue.user_name"
              type="text"
              disabled
            >
            <input
              v-model="currentIssue.user_id"
              type="text"
              disabled
            >
          </div>
          <label>問題標題</label>
          <input
            v-model="currentIssue.title"
            type="text"
            disabled
          >
          <label>問題簡述</label>
          <textarea
            v-model="currentIssue.description"
            disabled
          />
          <label>系統註記</label>
          <textarea
            v-model="currentIssue.context"
            disabled
          />
          <label>更改處理狀態</label>
          <select v-model="currentIssue.status">
            <option value="待處理">
              待處理
            </option>
            <option value="處理中">
              處理中
            </option>
            <option value="已處理">
              已處理
            </option>
            <option value="不處理">
              不處理
            </option>
          </select>
          <label>完成問題處理說明 (已處理/不處理時填寫)</label>
          <textarea
            v-model="currentIssue.decision_desc"
            :disabled="
              currentIssue.status !== '已處理' &&
                currentIssue.status !== '不處理'
            "
            :required="
              currentIssue.status === '已處理' ||
                currentIssue.status === '不處理'
            "
          />
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admineditissue {
	width: 500px;
	height: 500px;

	@media (max-width: 520px) {
		display: none;
	}
	@media (max-height: 520px) {
		display: none;
	}

	&-header {
		display: flex;
		justify-content: space-between;
		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-ms);
		}
	}

	&-settings {
		height: calc(100% - 55px);
		padding: 0 0.5rem 0.5rem 0.5rem;
		margin-top: var(--font-ms);
		border-radius: 5px;
		border: solid 1px var(--color-border);
		overflow-y: scroll;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		.two-block {
			display: grid;
			grid-template-columns: 1fr 1fr;
			column-gap: 0.5rem;
		}

		&-items {
			display: flex;
			flex-direction: column;

			hr {
				margin: var(--font-ms) 0 0.5rem;
				border: none;
				border-bottom: dashed 1px var(--color-complement-text);
			}
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			border-radius: 4px;
			background-color: rgba(136, 135, 135, 0.5);
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}
}
</style>
