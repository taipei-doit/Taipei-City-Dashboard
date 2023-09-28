<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import { useContentStore } from '../../store/contentStore';

import DialogContainer from './DialogContainer.vue';
import CustomCheckBox from '../utilities/CustomCheckBox.vue';
import { validateStrInput } from '../../assets/utilityFunctions/validate';

const dialogStore = useDialogStore();
const contentStore = useContentStore();

// Stores the user inputted new name
const newName = ref('');
const errorMessage = ref(null);
// Stores whether the user confirmed to enable the delete dashboard function
const deleteConfirm = ref(false);

function handleSubmit() {
	if (validateStrInput(newName.value) !== true) {
		errorMessage.value = validateStrInput(newName.value);
		return;
	}
	// changeCurrentDashboardName is currently a dummy function to demonstrate what changing a dashboard's name would look like
	// Connect a backend to actually implement the function or remove altogether
	contentStore.changeCurrentDashboardName(newName.value);
	handleClose();
}
function handleClose() {
	newName.value = '';
	errorMessage.value = null;
	deleteConfirm.value = false;
	dialogStore.hideAllDialogs();
}
function handleDelete() {
	// deleteCurrentDashboard is currently a dummy function to demonstrate what deleting a dashboard
	// Connect a backend to actually implement the function or remove altogether
	contentStore.deleteCurrentDashboard();
	handleClose();
}
</script>

<template>
	<DialogContainer dialog="dashboardSettings" @on-close="handleClose">
		<div class="dashboardsettings">
			<h2>儀表板設定</h2>
			<div class="dashboardsettings-input">
				<p v-if="errorMessage">{{ errorMessage }}</p>
				<label for="name">
					更改名稱
				</label>
				<input name="name" v-model="newName" :placeholder="contentStore.currentDashboard.name" />
				<div>
					<input type="checkbox" id="delete" :value="true" v-model="deleteConfirm" class="custom-check-input" />
					<CustomCheckBox for="delete">啟動刪除儀表板功能</CustomCheckBox>
				</div>
			</div>
			<div class="dashboardsettings-control">
				<button class="dashboardsettings-control-cancel" @click="handleClose">取消</button>
				<button v-if="newName" class="dashboardsettings-control-confirm" @click="handleSubmit">確定更改</button>
				<button v-if="deleteConfirm" class="dashboardsettings-control-delete" @click="handleDelete">刪除儀表板</button>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.dashboardsettings {
	width: 300px;

	&-input {
		display: flex;
		flex-direction: column;
		margin: 1rem 0 1.5rem;

		label {
			margin-bottom: 0.5rem;
			font-size: var(--font-s);
		}

		p {
			color: rgb(216, 52, 52);
		}

		input {
			padding: 4px 6px;
			border: solid 1px var(--color-border);
			border-radius: 5px;
			background-color: transparent;
			font-size: var(--font-m);

			&:focus {
				outline: none;
				border: solid 1px var(--color-highlight);
			}
		}

		div {
			margin-top: 0.5rem;

			label {
				color: var(--color-complement-text);
				font-size: 0.9rem;
			}

			input {
				display: none;

				&:checked+label {
					color: white
				}

				&:hover+label {
					color: var(--color-highlight)
				}
			}
		}
	}

	&-control {
		display: flex;
		justify-content: flex-end;

		&-cancel {
			margin: 0 2px;
			padding: 4px 6px;
			border-radius: 5px;
			transition: color 0.2s;

			&:hover {
				color: var(--color-highlight);
			}
		}

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

		&-delete {
			margin: 0 2px;
			padding: 4px 10px;
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