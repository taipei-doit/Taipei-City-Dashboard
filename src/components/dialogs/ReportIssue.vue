<!-- Developed by Taipei Urban Intelligence Center 2024 -->

<script setup>
import { ref } from "vue";
import axios from "axios";
import { useDialogStore } from "../../store/dialogStore";
import { useAuthStore } from "../../store/authStore";

import DialogContainer from "./DialogContainer.vue";
const { VITE_API_URL } = import.meta.env;

const dialogStore = useDialogStore();
const authStore = useAuthStore();

const allInputs = ref({
	type: "組件基本資訊有誤",
	description: "",
	title: "",
});
const issueTypes = [
	"組件基本資訊有誤",
	"組件資料有誤或未更新",
	"系統問題",
	"其他建議",
];

async function handleSubmit() {
	const submitObject = {
		title: allInputs.value.title,
		description: allInputs.value.description,
		user_name: authStore.user.name,
		user_id: `${authStore.user.id}`,
		context: `類型：${allInputs.value.type} // 來源：${dialogStore.issue.id} - ${dialogStore.issue.index} - ${dialogStore.issue.name}`,
		status: "待處理",
	};
	try {
		await axios.post(`${VITE_API_URL}/issue/`, submitObject);
		handleClose();
		dialogStore.showNotification("success", "回報問題成功，感謝您的建議");
	} catch {
		dialogStore.showNotification("fail", "回報問題失敗，請再試一次");
	}
}
function handleClose() {
	allInputs.value = {
		type: "組件基本資訊有誤",
		description: "",
		title: "",
	};
	dialogStore.dialogs.reportIssue = false;
}
</script>

<template>
	<DialogContainer dialog="reportIssue" @on-close="handleClose">
		<div class="reportissue">
			<h2>回報問題</h2>
			<h3>問題標題* ({{ allInputs.title.length }}/25)</h3>
			<input
				class="reportissue-input"
				type="text"
				v-model="allInputs.title"
				:min="1"
				:max="25"
				required
			/>
			<h3>問題種類*</h3>
			<div v-for="item in issueTypes" :key="item">
				<input
					class="reportissue-radio"
					type="radio"
					v-model="allInputs.type"
					:value="item"
					:id="item"
				/>
				<label :for="item">
					<div></div>
					{{ item }}
				</label>
			</div>
			<h3>問題簡述* ({{ allInputs.description.length }}/200)</h3>
			<textarea
				v-model="allInputs.description"
				:min="1"
				:max="200"
				required
			></textarea>
			<div class="reportissue-control">
				<button class="reportissue-control-cancel" @click="handleClose">
					取消
				</button>
				<button
					v-if="allInputs.description && allInputs.title"
					class="reportissue-control-confirm"
					@click="handleSubmit"
				>
					回報問題
				</button>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.reportissue {
	width: 300px;
	display: flex;
	flex-direction: column;

	h3 {
		margin: 0.5rem 0;
		font-size: var(--font-s);
		font-weight: 400;
	}

	&-radio {
		display: none;

		&:checked + label {
			color: white;

			div {
				background-color: var(--color-highlight);
			}
		}

		&:hover + label {
			color: var(--color-highlight);

			div {
				border-color: var(--color-highlight);
			}
		}
	}

	label {
		position: relative;
		display: flex;
		align-items: center;
		font-size: var(--font-s);
		color: var(--color-complement-text);
		transition: color 0.2s;
		cursor: pointer;

		div {
			width: calc(var(--font-s) / 2);
			height: calc(var(--font-s) / 2);
			margin-right: 4px;
			padding: calc(var(--font-s) / 4);
			border-radius: 50%;
			border: 1px solid var(--color-border);
			transition: background-color 0.2s, border-color 0.2s;
		}
	}

	&-control {
		display: flex;
		justify-content: flex-end;
		margin-top: 1rem;

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
	}
}
</style>
