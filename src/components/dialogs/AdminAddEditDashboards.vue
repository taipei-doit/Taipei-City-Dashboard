<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref, computed } from "vue";
import axios from "axios";

import { useDialogStore } from "../../store/dialogStore";
import { useAdminStore } from "../../store/adminStore";
import { storeToRefs } from "pinia";

import DialogContainer from "./DialogContainer.vue";
import ComponentDragTags from "../utilities/forms/ComponentDragTags.vue";

import { allIcons } from "../../assets/configs/AllIcons";
import AdminAddComponent from "./AdminAddComponent.vue";

const { VITE_API_URL } = import.meta.env;

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["mode"]);

const { currentDashboard } = storeToRefs(adminStore);
const indexStatus = ref("");
const iconSearch = ref("");

const availableIcons = computed(() => {
	let filteredIcons = [...allIcons];
	if (iconSearch.value !== "") {
		filteredIcons = filteredIcons.filter((icon) =>
			icon.includes(iconSearch.value)
		);
	} else {
		const selected = filteredIcons.findIndex(
			(icon) => icon === currentDashboard.value.icon
		);
		if (selected >= 36) {
			filteredIcons.splice(selected, 1);
			filteredIcons.unshift(currentDashboard.value.icon);
		}
	}
	filteredIcons = filteredIcons.slice(0, 36);
	return filteredIcons;
});

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

function handleConfirm() {
	if (props.mode === "add") {
		adminStore.addDashboard(currentDashboard.value);
	} else if (props.mode === "edit") {
		adminStore.editDashboard(currentDashboard.value);
	}
	handleClose();
}

function handleClose() {
	indexStatus.value = "";
	iconSearch.value = "";
	adminStore.currentDashboard = null;
	dialogStore.hideAllDialogs();
}
</script>

<template>
	<DialogContainer :dialog="`adminaddeditdashboards`" @onClose="handleClose">
		<div class="adminaddeditdashboards">
			<div class="adminaddeditdashboards-header">
				<h2>{{ mode === "edit" ? "編輯" : "新增" }}公開儀表板</h2>
				<button @click="handleConfirm">
					確認{{ mode === "edit" ? "更改" : "新增" }}
				</button>
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
							:minlength="1"
							:maxlength="30"
							required
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
						required
					/>
					<label>圖示*</label>
					<input placeholder="尋找圖示(英文)" v-model="iconSearch" />
					<div class="adminaddeditdashboards-settings-icon">
						<div v-for="item in availableIcons" :key="item">
							<input
								type="radio"
								v-model="currentDashboard.icon"
								:id="item"
								:value="item"
							/>
							<label :for="item">{{ item }}</label>
						</div>
					</div>
				</div>
				<div class="adminaddeditdashboards-settings">
					<label
						>{{
							mode === "edit" ? "編輯" : "新增"
						}}儀表板組件</label
					>
					<div class="adminaddeditdashboards-settings-components">
						<ComponentDragTags
							:tags="currentDashboard.components"
							@deletetag="
								(index) => {
									currentDashboard.components.splice(
										index,
										1
									);
								}
							"
							@updatetagorder="
								(updatedTags) => {
									currentDashboard.components = updatedTags;
								}
							"
						/>
						<button
							@click="dialogStore.showDialog('adminaddcomponent')"
						>
							+
						</button>
					</div>
				</div>
			</div>
		</div>
		<AdminAddComponent />
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
		overflow-y: scroll;

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

		&-icon {
			display: grid;
			grid-template-columns: 26px 26px 26px 26px 26px 26px 26px 26px 26px;
			column-gap: 4px;
			row-gap: 4px;
			margin: 0.5rem 0;

			input {
				display: none;
				transition: border 0.2s;

				&:checked + label {
					border: solid 1px var(--color-highlight);
				}
			}

			label {
				width: 1.5rem;
				height: 1.5rem;
				display: flex;
				align-items: center;
				justify-content: center;
				margin: 0;
				border: solid 1px transparent;
				border-radius: 5px;
				font-size: 1.2rem;
				font-family: var(--font-icon);
				cursor: pointer;

				&:hover {
					border: solid 1px var(--color-border);
				}
			}
		}

		&-components {
			display: grid;
			grid-template-columns: 85px 85px 85px;
			column-gap: 6px;
			row-gap: 6px;
			overflow-y: scroll;

			button:last-child {
				height: 48px;
				display: flex;
				align-items: center;
				justify-content: center;
				border: dashed 2px var(--color-border);
				border-radius: 5px;
				color: var(--color-complement-text);
				font-size: 1.5rem;
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
