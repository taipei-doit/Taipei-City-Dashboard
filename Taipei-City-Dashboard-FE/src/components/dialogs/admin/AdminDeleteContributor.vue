<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";
const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["searchParams"]);

const { currentContributor } = storeToRefs(adminStore);
const deleteConfirm = ref("");

function handleDelete() {
	adminStore.deleteContributor(props.searchParams);
	handleClose();
}

function handleClose() {
	deleteConfirm.value = "";
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    dialog="adminDeleteContributor"
    @on-close="handleClose"
  >
    <div class="admindeletecontributor">
      <h2>確定刪除貢獻者嗎？</h2>
      <div class="admindeletecontributor-input">
        <label for="name">
          輸入「{{ currentContributor.user_name }}」刪除
        </label>
        <input
          v-model="deleteConfirm"
          name="user_name"
        >
      </div>
      <div class="admindeletecontributor-control">
        <button
          v-if="deleteConfirm === currentContributor.user_name"
          class="admindeletecontributor-control-delete"
          @click="handleDelete"
        >
          刪除貢獻者
        </button>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admindeletecontributor {
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
