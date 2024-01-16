<script setup>
import { onMounted, ref, computed } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useDialogStore } from "../../store/dialogStore";

import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminEditIssue from "../../components/dialogs/AdminEditIssue.vue";
import CustomCheckBox from "../../components/utilities/forms/CustomCheckBox.vue";

const adminStore = useAdminStore();
const dialogStore = useDialogStore();

const searchParams = ref({
	filterbystatus: ["待處理"],
	sort: "created_at",
	order: "desc",
	pagesize: 10,
	pagenum: 1,
});

const statuses = ["待處理", "處理中", "已處理", "不處理"];

const pages = computed(() => {
	// return an array of pages based on results no stored in admin store
	if (adminStore.issues) {
		const pages = Math.ceil(
			adminStore.issueResults / searchParams.value.pagesize
		);
		return Array.from({ length: pages }, (_, i) => i + 1);
	}
	return [];
});

function parseTime(time) {
	return time.slice(0, 19).replace("T", " ");
}

function handleSort(sort) {
	// asc => desc => "" => asc
	if (searchParams.value.sort === sort) {
		if (searchParams.value.order === "asc") {
			searchParams.value.order = "desc";
		} else {
			searchParams.value.order = "";
			searchParams.value.sort = "";
		}
	} else {
		searchParams.value.sort = sort;
		searchParams.value.order = "asc";
	}
	adminStore.getIssues(searchParams.value);
}

function handleNewQuery() {
	searchParams.value.pagenum = 1;
	adminStore.getIssues(searchParams.value);
}

function handleNewPage(page) {
	searchParams.value.pagenum = page;
	adminStore.getIssues(searchParams.value);
}

function handleOpenSettings(issue) {
	adminStore.currentIssue = JSON.parse(JSON.stringify(issue));
	dialogStore.showDialog("admineditissue");
}

onMounted(() => {
	adminStore.getIssues(searchParams.value);
});
</script>

<template>
	<div class="adminissue">
		<div class="adminissue-filter">
			<div v-for="status in statuses" :key="status">
				<input
					type="checkbox"
					v-model="searchParams.filterbystatus"
					class="custom-check-input"
					:id="status"
					:value="status"
					@change="handleNewQuery"
				/>
				<CustomCheckBox :for="status">{{ status }}</CustomCheckBox>
			</div>
		</div>
		<table class="adminissue-table">
			<thead>
				<tr class="adminissue-table-header">
					<TableHeader minWidth="60px"></TableHeader>
					<TableHeader
						@sort="handleSort('id')"
						:sort="true"
						:mode="
							searchParams.sort === 'id' ? searchParams.order : ''
						"
						minWidth="40px"
						>ID</TableHeader
					>
					<TableHeader minWidth="300px">標題</TableHeader>
					<TableHeader minWidth="350px">系統標籤</TableHeader>
					<TableHeader minWidth="110px">狀態</TableHeader>
					<TableHeader
						@sort="handleSort('created_at')"
						:sort="true"
						:mode="
							searchParams.sort === 'created_at'
								? searchParams.order
								: ''
						"
						minWidth="200px"
						>開立時間</TableHeader
					>
					<TableHeader minWidth="110px">上次編輯人</TableHeader>
					<TableHeader
						@sort="handleSort('updated_at')"
						:sort="true"
						:mode="
							searchParams.sort === 'updated_at'
								? searchParams.order
								: ''
						"
						minWidth="200px"
						>上次編輯</TableHeader
					>
				</tr>
			</thead>
			<tbody v-if="adminStore.issues">
				<tr
					v-for="issue in adminStore.issues"
					:key="`issue-${issue.id}`"
				>
					<td class="adminissue-table-settings">
						<button @click="handleOpenSettings(issue)">
							<span>edit_note</span>
						</button>
					</td>
					<td>{{ issue.id }}</td>
					<td>{{ issue.title }}</td>
					<td>{{ issue.context ? issue.context : "無" }}</td>
					<td>{{ issue.status }}</td>
					<td>{{ parseTime(issue.created_at) }}</td>
					<td>{{ issue.updated_by }}</td>
					<td>{{ parseTime(issue.updated_at) }}</td>
				</tr>
			</tbody>
			<div v-else class="adminissue-nocontent">
				<div class="adminissue-nocontent-content">
					<div></div>
				</div>
			</div>
		</table>
		<!-- html element to select a results per page -->
		<div class="adminissue-control" v-if="adminStore.issues.length !== 0">
			<label for="pagesize">每頁顯示</label>
			<select v-model="searchParams.pagesize" @change="handleNewQuery">
				<option value="10">10</option>
				<option value="20">20</option>
				<option value="30">30</option>
			</select>
			<div class="adminissue-control-page">
				<button
					v-for="page in pages"
					:key="`component-page-${page}`"
					:class="{ active: page === searchParams.pagenum }"
					@click="handleNewPage(page)"
				>
					{{ page }}
				</button>
			</div>
		</div>
		<AdminEditIssue :searchParams="searchParams" />
	</div>
</template>

<style scoped lang="scss">
.adminissue {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-filter {
		display: flex;
		column-gap: 1rem;
		margin-bottom: 1rem;

		input {
			display: none;

			& + label {
				color: var(--color-complement-text);
			}

			&:checked + label {
				color: white;
			}

			&:hover + label {
				color: var(--color-highlight);
			}
		}
	}

	&-table {
		max-width: calc(100% - 40px);
		max-height: calc(100% - 90px);

		&::-webkit-scrollbar {
			width: 8px;
			height: 8px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
		&::-webkit-scrollbar-corner {
			background-color: transparent;
		}

		span {
			font-family: var(--font-icon);
			font-size: var(--font-l);
			transition: color 0.2s;
			cursor: default;
		}
		button span:hover {
			color: var(--color-highlight);
			cursor: pointer;
		}

		&-settings {
			position: sticky;
			left: 0;
		}

		&-charts,
		&-maps {
			max-width: 165px;
			display: flex;
			flex-wrap: wrap;
			justify-content: center;
			row-gap: 4px;
		}

		&-update {
			display: flex;
			justify-content: center;
		}
	}

	&-nocontent {
		grid-template-columns: 1fr;

		&-content {
			width: 100%;
			height: calc(100vh - 250px);
			height: calc(100 * var(--vh) - 250px);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;

			div {
				width: 2rem;
				height: 2rem;
				border-radius: 50%;
				border: solid 4px var(--color-border);
				border-top: solid 4px var(--color-highlight);
				animation: spin 0.7s ease-in-out infinite;
			}
		}
	}

	&-control {
		display: flex;
		align-items: center;
		margin-top: 0.5rem;
		height: 2rem;

		label {
			font-size: var(--font-m);
			margin-right: 0.5rem;
		}
		select {
			width: 100px;
		}

		&-page {
			button {
				margin-left: 0.5rem;
				padding: 0.2rem 0.5rem;
				border-radius: 5px;
				background-color: var(--color-component-background);
				font-size: var(--font-m);
				transition: opacity 0.2s background-color 0.2s;

				&:hover {
					opacity: 0.7;
				}
			}
			.active {
				background-color: var(--color-complement-text);
			}
		}
	}
}
</style>
