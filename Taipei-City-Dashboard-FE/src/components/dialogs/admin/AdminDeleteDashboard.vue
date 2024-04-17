<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const { currentDashboard } = storeToRefs(adminStore);
const deleteConfirm = ref("");

function handleClose() {
	deleteConfirm.value = "";
	dialogStore.hideAllDialogs();
}
function handleDelete() {
	adminStore.deleteDashboard();
	handleClose();
}
</script>

<template>
  <DialogContainer
    dialog="adminDeleteDashboard"
    @on-close="handleClose"
  >
    <div class="admindeletedashboard">
      <h2>確定刪除儀表板嗎？</h2>
      <div class="admindeletedashboard-input">
        <label for="name">
          輸入「{{ currentDashboard.name }}」以刪除
        </label>
        <input
          v-model="deleteConfirm"
          name="name"
        >
      </div>
      <div class="admindeletedashboard-control">
        <button
          v-if="deleteConfirm === currentDashboard.name"
          class="admindeletedashboard-control-delete"
          @click="handleDelete"
        >
          刪除儀表板
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admindeletedashboard {
	width: 300px;

	&-input {
		display: flex;
		flex-direction: column;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}
	}

	&-control {
		height: var(--font-xl);
		display: flex;
		justify-content: flex-end;
		margin-top: 8px;

		&-delete {
			padding: 2px 4px;
			border-radius: 5px;
			background-color: rgb(192, 67, 67);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}
}
</style>
