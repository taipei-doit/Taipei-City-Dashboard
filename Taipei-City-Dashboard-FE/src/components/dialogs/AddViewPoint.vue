<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";

import DialogContainer from "./DialogContainer.vue";

const dialogStore = useDialogStore();
const mapStore = useMapStore();

const props = defineProps(["name"]);

const viewPoint = ref({
	name: "",
	coordinates: [],
	zoom: null,
	pitch: null,
	bearing: null,
});

function handleClose() {
	viewPoint.value = {
		name: "",
		coordinates: [],
		zoom: null,
		pitch: null,
		bearing: null,
	};
	dialogStore.hideAllDialogs();
}

function handleAddViewPoint() {
	if (props.name === "addPin") {
		mapStore.addMarker(viewPoint.value.name);
		dialogStore.showNotification("success", "新增地標成功");
	} else {
		mapStore.addViewPoint(viewPoint.value.name);
		dialogStore.showNotification("success", "新增視角成功");
	}

	handleClose();
}
</script>

<template>
  <DialogContainer
    :dialog="name"
    @on-close="handleClose"
  >
    <div class="addviewpoint">
      <div class="addviewpoint-title">
        <h2>
          {{ name === "addPin" ? "新增地標" : "新增視角" }}
        </h2>
        <button
          v-if="viewPoint.name.length > 0"
          @click="handleAddViewPoint"
        >
          確認
        </button>
      </div>
      <div class="addviewpoint-content">
        <label>{{ name === "addPin" ? "地標" : "視角" }}名稱 ({{
          viewPoint.name.length
        }}/10)</label>
        <input
          v-model="viewPoint.name"
          maxlength="10"
          type="text"
          name="view-point-name"
          :placeholder="`請輸入${
            name === 'addPin' ? '地標' : '視角'
          }名稱`"
          required
        >
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.addviewpoint {
	width: 300px;
	display: flex;
	flex-direction: column;
	justify-content: space-between;

	&-title {
		display: flex;
		justify-content: space-between;
		align-items: center;

		button {
			background-color: var(--color-highlight);
			padding: 2px 4px;
			font-size: var(--font-ms);
			border-radius: 5px;
			cursor: pointer;
		}
	}

	&-content {
		display: flex;
		flex-direction: column;
		margin-top: 1rem;

		label {
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		input {
			margin-top: 4px;
		}
	}
}
</style>
