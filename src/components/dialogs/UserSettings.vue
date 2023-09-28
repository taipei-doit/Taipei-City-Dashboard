<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<script setup>
import { useDialogStore } from '../../store/dialogStore';
import { useAuthStore } from '../../store/authStore';

import DialogContainer from './DialogContainer.vue';

const dialogStore = useDialogStore();
const authStore = useAuthStore();

const accountTypes = ['Email用戶', '台北通', '台北on'];

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
	<DialogContainer @onClose="handleClose" :dialog="`userSettings`">
		<h2>用戶設定</h2>
		<table class="usersettings">
			<tr>
				<th>名稱</th>
				<td colspan="3">{{ authStore.user.name }}</td>
			</tr>
			<tr>
				<th>類型</th>
				<td>{{ accountTypes[authStore.user.type] }}</td>
				<th>用戶代碼</th>
				<td>{{ authStore.user.id }}</td>
			</tr>
			<tr>
				<th>權限</th>
				<td>{{ authStore.user.status === 1 ? '管理員' : '一般用戶' }}</td>
				<th>帳戶狀態</th>
				<td>{{ authStore.user.status > 0 ? '啟用' : '停用' }}</td>
			</tr>
		</table>
	</DialogContainer>
</template>

<style scoped lang="scss">
.usersettings {
	width: 500px;
	margin: 1rem 0 0.5rem;
	border-spacing: 0;
	border: solid 1px var(--color-border);
	border-radius: 5px;

	td,
	th {
		height: 2rem;
		border: solid 1px var(--color-border);
		color: var(--color-complement-text);
	}

	th {
		width: 20%
	}

	td {
		width: 30%;
		padding-left: 0.5rem
	}
}
</style>