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

const { currentUser } = storeToRefs(adminStore);

function parseTime(time) {
	time = new Date(time);
	time.setHours(time.getHours() + 8);
	time = time.toISOString();
	return time.slice(0, 19).replace("T", " ");
}

function handleConfirm() {
	adminStore.updateUser(props.searchParams);
	handleClose();
}

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    :dialog="`adminEditUser`"
    @on-close="handleClose"
  >
    <div class="adminedituser">
      <div class="adminedituser-header">
        <h2>設定用戶</h2>
        <button @click="handleConfirm">
          確定更改
        </button>
      </div>
      <div class="adminedituser-settings">
        <div class="adminedituser-settings-items">
          <div class="two-block">
            <label>用戶名稱</label>
            <label>用戶 ID</label>
          </div>
          <div class="two-block">
            <input
              v-model="currentUser.name"
              type="text"
              required
            >
            <input
              v-model="currentUser.user_id"
              type="text"
              disabled
            >
          </div>
          <label>用戶帳號</label>
          <input
            type="text"
            :value="
              currentUser.account
                ? currentUser.account
                : currentUser.TpAccount
            "
            disabled
          >
          <label>用戶身份</label>
          <div class="toggle">
            <p>一般用戶</p>
            <label class="toggleswitch">
              <input
                v-model="currentUser.is_admin"
                type="checkbox"
                :disabled="shouldDisable"
                @change="handleToggle"
              >
              <span class="toggleswitch-slider" />
            </label>
            <p>管理員</p>
          </div>
          <div class="two-block">
            <label>API白名單</label><label>API黑名單</label>
          </div>
          <div class="two-block">
            <label class="toggleswitch">
              <input
                v-model="currentUser.is_whitelist"
                type="checkbox"
                :disabled="shouldDisable"
                @change="handleToggle"
              >
              <span class="toggleswitch-slider" />
            </label>
            <label class="toggleswitch">
              <input
                v-model="currentUser.is_blacked"
                type="checkbox"
                :disabled="shouldDisable"
                @change="handleToggle"
              >
              <span class="toggleswitch-slider" />
            </label>
          </div>
          <label>啟用狀態</label>
          <div class="toggle">
            <p>停用</p>
            <label class="toggleswitch">
              <input
                v-model="currentUser.is_active"
                type="checkbox"
                :disabled="shouldDisable"
                @change="handleToggle"
              >
              <span class="toggleswitch-slider" />
            </label>
            <p>啟用</p>
          </div>

          <label> 最近登入時間 </label>
          <input
            :value="parseTime(currentUser.login_at)"
            disabled
          >
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.adminedituser {
	width: 350px;
	height: 400px;

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
		.toggle {
			display: flex;
			flex-direction: row;
			align-items: center;
			column-gap: 6px;

			p {
				margin-top: 4px;
			}
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
