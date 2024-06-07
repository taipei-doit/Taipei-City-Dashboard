<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";
import DialogContainer from "./DialogContainer.vue";
const dialogStore = useDialogStore();
const mapStore = useMapStore();
const params = ref({
	longitude: null,
	latitude: null,
});
const pinName = ref("");

function handleClose() {
	dialogStore.hideAllDialogs();
	params.value.longitude = null;
	params.value.latitude = null;
	pinName.value = "";
}

function handleAddPin() {
	if (!pinName.value) {
		dialogStore.showNotification("fail", "請輸入地標名稱");
		return;
	}
	mapStore.addMarker(pinName.value);
	dialogStore.hideAllDialogs();
	dialogStore.showNotification("success", "新增地標成功");
	pinName.value = "";
}
</script>

<template>
  <DialogContainer
    dialog="addPin"
    @on-close="handleClose"
  >
    <div class="login add-mark-to-map">
      <div class="title-box">
        <h1 class="title">
          建立地標
        </h1>
        <button
          v-if="pinName.trim().length"
          @click.prevent="handleAddPin"
        >
          確認
        </button>
      </div>
      <div class="content">
        <label for="view-point-name">地標名稱：</label>
        <input
          id="view-point-name"
          v-model="pinName"
          type="text"
          name="view-point-name"
          placeholder="請輸入地標名稱"
          maxlength="6"
          required
        >
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.login {
	width: 300px;

	p {
		text-align: center;
		color: var(--color-complement-text);
	}

	a {
		color: var(--color-highlight);
	}

	label {
		color: var(--color-complement-text);
		font-size: var(--font-s);
		align-self: flex-start;
	}

	input {
		width: calc(100% - 14px);
	}

	&-logo {
		display: flex;
		justify-content: center;

		h1 {
			font-weight: 500;
		}

		h2 {
			font-size: var(--font-s);
			font-weight: 400;
		}

		&-image {
			width: 22.94px;
			height: 45px;
			margin: 0 10px 0 0;

			img {
				height: 45px;
				filter: invert(1);
			}
		}
	}

	&-form {
		width: 100%;
		height: 200px;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}
}
.add-mark-to-map {
	display: flex;
	flex-direction: column;
	.title-box {
		display: flex;
		justify-content: space-between;
		align-items: center;
		button {
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 2px 4px;
			font-size: var(--font-ms);
			background-color: var(--color-highlight);
			border-radius: 5px;
		}
	}
	label {
		text-align: center;
		margin: 1rem 0 4px;
	}
}
</style>
