<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";

import DialogContainer from "./DialogContainer.vue";

const dialogStore = useDialogStore();
const authStore = useAuthStore();

const { editUser } = storeToRefs(authStore);

function handleClose() {
	dialogStore.hideAllDialogs();
	authStore.editUser = authStore.user;
}

function parseTime(time) {
	time = new Date(time);
	time.setHours(time.getHours() + 8);
	time = time.toISOString();
	return time.slice(0, 19).replace("T", " ");
}

async function handleSubmit() {
	if (editUser.value.name === authStore.user.name || !editUser.value.name) {
		dialogStore.showNotification("info", "用戶名稱不變");
		dialogStore.hideAllDialogs();
		return;
	}
	await authStore.updateUserInfo();
	dialogStore.showNotification("success", "用戶資訊已更新");
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    :dialog="`userSettings`"
    @on-close="handleClose"
  >
    <div class="usersettings">
      <h2>用戶設定</h2>
      <label> 用戶名稱 </label>
      <input
        v-model="editUser.name"
        :minlength="1"
        :maxlength="10"
        required
      >
      <label> 用戶帳號 </label>
      <input
        :value="
          editUser.account ? editUser.account : editUser.TpAccount
        "
        :minlength="1"
        disabled
      >
      <label> 用戶類型 </label>
      <input
        :value="editUser.is_admin ? '管理員' : '一般用戶'"
        disabled="true"
        required
      >
      <label> 最近登入時間 </label>
      <input
        :value="parseTime(editUser.login_at)"
        disabled
      >
      <div class="usersettings-control">
        <button
          v-if="editUser.name"
          class="usersettings-control-confirm"
          @click="handleSubmit"
        >
          更改用戶資訊
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.usersettings {
	width: 300px;
	display: flex;
	flex-direction: column;

	label {
		margin: 8px 0 4px;
		font-size: var(--font-s);
		color: var(--color-complement-text);
	}

	&-control {
		height: 27px;
		display: flex;
		justify-content: flex-end;
		margin-top: var(--font-ms);

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
