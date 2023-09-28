<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { ref } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import DialogContainer from './DialogContainer.vue';

const dialogStore = useDialogStore();

const allInputs = ref({
	type: "組件基本資訊有誤",
	description: "",
	name: "",
});
const issueTypes = ["組件基本資訊有誤", "組件資料有誤或未更新", "系統問題", "其他建議"];

function handleSubmit() {
	const currentDate = new Date().toJSON().slice(0, 10).replaceAll("-", "");
	const secondaryLabel = allInputs.value.type === "其他建議" ? "enhancement" : "bug";
	const issueTitle = `[from-demo] ${currentDate} ${allInputs.value.type} - ${dialogStore.issue.id} | ${dialogStore.issue.name}`;
	const issueBody = allInputs.value.description.replaceAll('\n', '%0D%0A') + '%0D%0A%0D%0A' + 'Issue Opener: ' + allInputs.value.name;
	window.open(`https://github.com/tpe-doit/Taipei-City-Dashboard-FE/issues/new?assignees=igorho2000&labels=from-demo,${secondaryLabel}&title=${issueTitle}&body=${issueBody}`);
	handleClose();
}
function handleClose() {
	allInputs.value = {
		type: "組件基本資訊有誤",
		description: "",
		name: "",
	};
	dialogStore.dialogs.reportIssue = false;
}
</script>

<template>
	<DialogContainer dialog="reportIssue" @on-close="handleClose">
		<div class="reportissue">
			<h2>回報問題</h2>
			<h3>問題種類*</h3>
			<div v-for="item in issueTypes" :key="item">
				<input class="reportissue-radio" type="radio" v-model="allInputs.type" :value="item" :id="item" />
				<label :for="item">
					<div></div>
					{{ item }}
				</label>
			</div>
			<h3>問題簡述*</h3>
			<textarea v-model="allInputs.description"></textarea>
			<h3>姓名*</h3>
			<input class="reportissue-input" type="text" v-model="allInputs.name" />
			<div class="reportissue-control">
				<button class="reportissue-control-cancel" @click="handleClose">取消</button>
				<button v-if="allInputs.description && allInputs.name" class="reportissue-control-confirm"
					@click="handleSubmit">開立 GitHub
					Issue</button>
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

		&:checked+label {
			color: white;

			div {
				background-color: var(--color-highlight);
			}
		}

		&:hover+label {
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

	textarea {
		height: 125px;
		padding: 4px 6px;
		border: solid 1px var(--color-border);
		border-radius: 5px;
		background-color: transparent;
		font-size: var(--font-m);
		resize: none;

		&:focus {
			outline: none;
			border: solid 1px var(--color-highlight);
		}
	}

	&-input {
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