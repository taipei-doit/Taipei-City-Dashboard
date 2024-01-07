<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from "vue";
import axios from "axios";

import { useDialogStore } from "../../store/dialogStore";
import { useAdminStore } from "../../store/adminStore";
import { storeToRefs } from "pinia";

import DialogContainer from "./DialogContainer.vue";
const { VITE_API_URL } = import.meta.env;
import {
	validateStrInput,
	validateEngInput,
} from "../../assets/utilityFunctions/validate";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["mode"]);

const { currentDashboard } = storeToRefs(adminStore);
const indexStatus = ref("");

async function verifyIndex() {
	const res = await axios.get(
		`${VITE_API_URL}/dashboard/check-index/${currentDashboard.value.index}`
	);
	if (res.data.available) {
		indexStatus.value = "check_circle";
	} else {
		indexStatus.value = "cancel";
	}
}

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
	<DialogContainer :dialog="`adminaddeditdashboards`" @onClose="handleClose">
		<div class="adminaddeditdashboards">
			<div class="adminaddeditdashboards-header">
				<h2>{{ mode === "edit" ? "編輯" : "新增" }}公開儀表板</h2>
				<button>確認{{ mode === "edit" ? "更改" : "新增" }}</button>
			</div>
			<div class="adminaddeditdashboards-content">
				<div class="adminaddeditdashboards-settings">
					<label>Index*</label>
					<input
						v-if="mode === 'edit'"
						:value="currentDashboard.index"
						disabled="true"
					/>
					<div
						v-else-if="mode === 'add'"
						class="adminaddeditdashboards-settings-index"
					>
						<input
							v-model="currentDashboard.index"
							@focusout="verifyIndex"
						/>
						<span
							:style="{
								color:
									indexStatus === 'cancel'
										? 'rgb(237, 90, 90)'
										: 'greenyellow',
							}"
							>{{ indexStatus }}</span
						>
					</div>
					<label>名稱* ({{ currentDashboard.name.length }}/10)</label>
					<input
						v-model="currentDashboard.name"
						:minlength="1"
						:maxlength="10"
					/>
					<label>圖示*</label>
				</div>
				<div class="adminaddeditdashboards-settings"></div>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.adminaddeditdashboards {
	width: 600px;
	height: 350px;

	@media (max-width: 600px) {
		display: none;
	}
	@media (max-height: 350px) {
		display: none;
	}

	&-header {
		display: flex;
		justify-content: space-between;
		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			border-radius: 5px;
			font-size: var(--font-m);
			padding: 0px 4px;
			background-color: var(--color-highlight);
		}
	}

	&-content {
		height: calc(100% - 45px);
		display: grid;
		grid-template-columns: 1fr 1fr;
		margin-top: 1rem;
		column-gap: 1rem;
	}

	&-settings {
		display: flex;
		flex-direction: column;
		padding: 0 0.5rem 0.5rem 0.5rem;
		border-radius: 5px;
		border: solid 1px var(--color-border);

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		&-index {
			width: 100%;
			position: relative;
			display: flex;
			align-items: center;

			input {
				width: 100%;
			}

			span {
				position: absolute;
				right: 4px;
				font-family: var(--font-icon);
			}
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}
}
</style>
