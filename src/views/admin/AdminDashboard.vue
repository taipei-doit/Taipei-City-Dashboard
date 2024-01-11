<script setup>
import { onMounted, ref } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useDialogStore } from "../../store/dialogStore";

import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminAddEditDashboards from "../../components/dialogs/AdminAddEditDashboards.vue";
import AdminDeleteDashboard from "../../components/dialogs/AdminDeleteDashboard.vue";

const adminStore = useAdminStore();
const dialogStore = useDialogStore();

const dialogMode = ref("edit");

function parseTime(time) {
	return time.slice(0, 19).replace("T", " ");
}

function handleOpenSettings(dashboard) {
	adminStore.currentDashboard = JSON.parse(JSON.stringify(dashboard));
	adminStore.getCurrentDashboardComponents();
	dialogMode.value = "edit";
	dialogStore.showDialog("adminaddeditdashboards");
}

function handleAddDashboard() {
	adminStore.currentDashboard = {
		index: "",
		name: "",
		components: [],
		icon: "star",
	};
	dialogMode.value = "add";
	dialogStore.showDialog("adminaddeditdashboards");
}

function handleDeleteDashboard(dashboard) {
	adminStore.currentDashboard = JSON.parse(JSON.stringify(dashboard));
	dialogStore.showDialog("admindeletedashboard");
}

onMounted(() => {
	adminStore.getDashboards();
});
</script>

<template>
	<div class="admindashboard">
		<div class="admindashboard-control">
			<button @click="handleAddDashboard">新增公開儀表板</button>
		</div>
		<table class="admindashboard-table">
			<thead>
				<tr class="admindashboard-table-header">
					<TableHeader minWidth="80px"></TableHeader>
					<TableHeader @sort="handleSort('id')" minWidth="150px"
						>Index</TableHeader
					>
					<TableHeader minWidth="180px">名稱</TableHeader>
					<TableHeader minWidth="480px">組件</TableHeader>
					<TableHeader minWidth="40px">圖示</TableHeader>
					<TableHeader minWidth="200px">上次編輯</TableHeader>
				</tr>
			</thead>
			<tbody v-if="adminStore.dashboards">
				<tr
					v-for="dashboard in adminStore.dashboards"
					:key="dashboard.index"
				>
					<td class="admindashboard-table-settings">
						<button @click="handleOpenSettings(dashboard)">
							<span>settings</span>
						</button>
						<button @click="handleDeleteDashboard(dashboard)">
							<span>delete</span>
						</button>
					</td>
					<td>{{ dashboard.index }}</td>
					<td>{{ dashboard.name }}</td>
					<td>{{ dashboard.components }}</td>
					<td>
						<span>{{ dashboard.icon }}</span>
					</td>
					<td>{{ parseTime(dashboard.updated_at) }}</td>
				</tr>
			</tbody>
			<div v-else class="admindashboard-nocontent">
				<div class="admindashboard-nocontent-content">
					<div></div>
				</div>
			</div>
		</table>
	</div>
	<AdminAddEditDashboards :mode="dialogMode" />
	<AdminDeleteDashboard />
</template>

<style scoped lang="scss">
.admindashboard {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-control {
		display: flex;
		column-gap: 0.5rem;
		margin-bottom: 1rem;

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			margin-right: 0.4rem;
			padding: 0px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-m);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
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
}
</style>
