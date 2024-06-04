<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useMapStore } from "../../store/mapStore";
import DialogContainer from "./DialogContainer.vue";
const dialogStore = useDialogStore();
const mapStore = useMapStore();
const params = ref({
	name: "",
	longitude: null,
	latitude: null,
});
const viewPoint = ref({
	name: "",
	coordinates: [],
	zoom: null,
	pitch: null,
	bearing: null,
});

function handleClose() {
	dialogStore.hideAllDialogs();
	params.value.longitude = null;
	params.value.latitude = null;
}

const handleAddViewPoint = () => {
	if (!viewPoint.value.name) {
		dialogStore.showNotification("fail", "請輸入視角名稱");
		return;
	}
	const { lng, lat } = mapStore.map.getCenter();
	const zoom = mapStore.map.getZoom();
	const pitch = mapStore.map.getPitch();
	const bearing = mapStore.map.getBearing();
	viewPoint.value.zoom = zoom;
	viewPoint.value.pitch = pitch;
	viewPoint.value.bearing = bearing;
	viewPoint.value.coordinates = [lng, lat];
	const viewPointArray = [
		[lng, lat],
		zoom,
		pitch,
		bearing,
		viewPoint.value.name,
	];
	mapStore.addViewPoint(viewPointArray);
	dialogStore.hideAllDialogs();
	dialogStore.showNotification("success", "新增視角成功");
	viewPoint.value = {
		name: "",
		coordinates: [],
		zoom: null,
		pitch: null,
		bearing: null,
	};
};
</script>

<template>
  <DialogContainer
    dialog="addMarkToMap"
    @on-close="handleClose"
  >
    <div class="login add-mark-to-map">
      <div class="title-box">
        <h2 class="title">
          建立視角
        </h2>
        <button @click.prevent="handleAddViewPoint">
          確認
        </button>
      </div>

      <div class="content">
        <label for="view-point-name">視角名稱：</label>
        <input
          id="view-point-name"
          v-model="viewPoint.name"
          type="text"
          name="view-point-name"
          placeholder="請輸入視角名稱"
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
		margin-bottom: 4px;
		color: var(--color-complement-text);
		font-size: var(--font-s);
		align-self: flex-start;
	}

	input {
		margin-bottom: 8px;
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
	}
	.content {
		margin: 30px 0 30px;
	}
	h1 {
		text-align: center;
	}
	input {
		font-size: var(--font-s);
		margin-bottom: 4px;
		margin-top: 4px;
	}

	/* Chrome, Safari, Edge, Opera */
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	/* Firefox */
	input[type="number"] {
		-moz-appearance: textfield;
	}
}
</style>
