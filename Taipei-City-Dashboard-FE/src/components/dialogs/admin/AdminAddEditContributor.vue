<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { defineProps } from "vue";
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["searchParams", "mode"]);

const { currentContributor } = storeToRefs(adminStore);

function parseTime(time) {
	time = new Date(time);
	time.setHours(time.getHours() + 8);
	time = time.toISOString();
	return time.slice(0, 19).replace("T", " ");
}

function handleConfirm() {
	if (props.mode === "add") {
		adminStore.addContributor(props.searchParams);
	} else if (props.mode === "edit") {
		adminStore.updateContributor(props.searchParams);
	}
	handleClose();
}

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    :dialog="`adminAddEditContributor`"
    @on-close="handleClose"
  >
    <div
      class="adminaddeditcontributor"
      :style="{ height: props.mode === 'edit' ? '400px' : '340px' }"
    >
      <div class="adminaddeditcontributor-header">
        <h2>
          {{ props.mode === "edit" ? "設定貢獻者" : "新增貢獻者" }}
        </h2>
        <button @click="handleConfirm">
          {{ props.mode === "edit" ? "確定更改" : "確定新增" }}
        </button>
      </div>
      <div class="adminaddeditcontributor-settings">
        <div class="adminaddeditcontributor-settings-items">
          <div class="two-block">
            <label>貢獻者 ID</label>
            <label>貢獻者名稱</label>
          </div>
          <div class="two-block">
            <input
              v-model="currentContributor.user_id"
              type="text"
              required
            >
            <input
              v-model="currentContributor.user_name"
              type="text"
              required
            >
          </div>
          <div class="small-two-block">
            <label>貢獻者身份</label>
            <label>貢獻者清單</label>
          </div>
          <div class="small-two-block">
            <input
              v-model="currentContributor.identity"
              type="text"
            >
            <label class="toggleswitch">
              <input
                v-model="currentContributor.include"
                type="checkbox"
                @change="handleToggle"
              >
              <span class="toggleswitch-slider" />
            </label>
          </div>
          <label>貢獻者照片</label>
          <input
            v-model="currentContributor.image"
            type="text"
            required
          >
          <label>貢獻者簡介</label>
          <input
            v-model="currentContributor.description"
            type="text"
          >
          <label>貢獻者連結</label>
          <input
            v-model="currentContributor.link"
            type="text"
            required
          >

          <template v-if="props.mode === 'edit'">
            <label> 最後更新時間 </label>
            <input
              :value="parseTime(currentContributor.created_at)"
              disabled
            >
          </template>
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.adminaddeditcontributor {
	width: 350px;

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
		.small-two-block {
			display: grid;
			grid-template-columns: 1fr 4rem;
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
