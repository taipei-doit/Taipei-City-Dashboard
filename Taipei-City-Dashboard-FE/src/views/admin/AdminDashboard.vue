<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { onMounted, ref } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminAddEditDashboards from "../../components/dialogs/admin/AdminAddEditDashboards.vue";
import AdminDeleteDashboard from "../../components/dialogs/admin/AdminDeleteDashboard.vue";

const adminStore = useAdminStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();

const dialogMode = ref("edit");

function parseTime(time) {
	return time.slice(0, 19).replace("T", " ");
}

function handleOpenSettings(dashboard) {
	adminStore.currentDashboard = JSON.parse(JSON.stringify(dashboard));
	adminStore.getCurrentDashboardComponents();
	dialogMode.value = "edit";
	dialogStore.showDialog("adminAddEditDashboards");
}

function handleAddDashboard() {
	adminStore.currentDashboard = {
		index: "",
		name: "",
		components: [],
		icon: "star",
	};
	dialogMode.value = "add";
	dialogStore.showDialog("adminAddEditDashboards");
}

function handleDeleteDashboard(dashboard) {
	adminStore.currentDashboard = JSON.parse(JSON.stringify(dashboard));
	dialogStore.showDialog("adminDeleteDashboard");
}

onMounted(() => {
	adminStore.getDashboards();
});
</script>

<template>
  <div class="admindashboard">
    <!-- 1. Button to open a dialog to add a new public dashboard -->
    <div class="admindashboard-control">
      <button @click="handleAddDashboard">
        新增公開儀表板
      </button>
    </div>
    <!-- 2. Table to show all public dashboards -->
    <table class="admindashboard-table">
      <thead>
        <tr class="admindashboard-table-header">
          <TableHeader min-width="80px" />
          <TableHeader
            min-width="150px"
            @sort="handleSort('id')"
          >
            Index
          </TableHeader>
          <TableHeader min-width="180px">
            名稱
          </TableHeader>
          <TableHeader min-width="480px">
            組件
          </TableHeader>
          <TableHeader min-width="40px">
            圖示
          </TableHeader>
          <TableHeader min-width="200px">
            上次編輯
          </TableHeader>
        </tr>
      </thead>
      <!-- 2-1. Dashboards are present -->
      <tbody v-if="adminStore.dashboards.length !== 0">
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
      <!-- 2-2. Dashboards are still loading -->
      <div
        v-else-if="contentStore.loading"
        class="admindashboard-nocontent"
      >
        <div class="admindashboard-nocontent-content">
          <div />
        </div>
      </div>
      <!-- 2-3. An Error occurred -->
      <div
        v-else-if="contentStore.error"
        class="admindashboard-nocontent"
      >
        <div class="admindashboard-nocontent-content">
          <span>sentiment_very_dissatisfied</span>
          <h2>發生錯誤，無法載入儀表板列表</h2>
        </div>
      </div>
      <!-- 2-4. Dashboards are loaded but there are none -->
      <div
        v-else
        class="admindashboard-nocontent"
      >
        <div class="admindashboard-nocontent-content">
          <span>search_off</span>
          <h2>查無公開儀表板</h2>
        </div>
      </div>
    </table>
  </div>
  <AdminAddEditDashboards :mode="dialogMode" />
  <AdminDeleteDashboard />
</template>

<style scoped lang="scss">
.admindashboard {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-control {
		display: flex;
		column-gap: 0.5rem;
		margin-bottom: var(--font-ms);

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			margin-right: 0.4rem;
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-ms);
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
			border-radius: 4px;
			background-color: rgba(136, 135, 135, 0.5);
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

			span {
				margin-bottom: var(--font-ms);
				font-family: var(--font-icon);
				font-size: 2rem;
			}

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
