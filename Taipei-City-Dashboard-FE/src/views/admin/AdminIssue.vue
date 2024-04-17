<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { onMounted, ref, computed } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";

import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminEditIssue from "../../components/dialogs/admin/AdminEditIssue.vue";
import CustomCheckBox from "../../components/utilities/forms/CustomCheckBox.vue";

const adminStore = useAdminStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();

const statuses = ["待處理", "處理中", "已處理", "不處理"];

const searchParams = ref({
	filterbystatus: [],
	sort: "created_at",
	order: "desc",
	pagesize: 10,
	pagenum: 1,
});

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
	dialogStore.showDialog("adminEditIssue");
}

onMounted(() => {
	adminStore.getIssues(searchParams.value);
});
</script>

<template>
  <div class="adminissue">
    <!-- 1. Checkboxes to filter through different issue types -->
    <div class="adminissue-filter">
      <div
        v-for="status in statuses"
        :key="status"
      >
        <input
          :id="status"
          v-model="searchParams.filterbystatus"
          type="checkbox"
          class="custom-check-input"
          :value="status"
          @change="handleNewQuery"
        >
        <CustomCheckBox :for="status">
          {{ status }}
        </CustomCheckBox>
      </div>
    </div>
    <!-- 2. The main table displaying various issues -->
    <table class="adminissue-table">
      <thead>
        <tr class="adminissue-table-header">
          <TableHeader min-width="60px" />
          <TableHeader
            :sort="true"
            :mode="
              searchParams.sort === 'id' ? searchParams.order : ''
            "
            min-width="40px"
            @sort="handleSort('id')"
          >
            ID
          </TableHeader>
          <TableHeader min-width="300px">
            標題
          </TableHeader>
          <TableHeader min-width="350px">
            系統標籤
          </TableHeader>
          <TableHeader min-width="110px">
            狀態
          </TableHeader>
          <TableHeader
            :sort="true"
            :mode="
              searchParams.sort === 'created_at'
                ? searchParams.order
                : ''
            "
            min-width="200px"
            @sort="handleSort('created_at')"
          >
            開立時間
          </TableHeader>
          <TableHeader min-width="110px">
            上次編輯人
          </TableHeader>
          <TableHeader
            :sort="true"
            :mode="
              searchParams.sort === 'updated_at'
                ? searchParams.order
                : ''
            "
            min-width="200px"
            @sort="handleSort('updated_at')"
          >
            上次編輯
          </TableHeader>
        </tr>
      </thead>
      <!-- 2-1. Issues are present -->
      <tbody v-if="adminStore.issues.length !== 0">
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
      <!-- 2-2. Issues are still loading -->
      <div
        v-else-if="contentStore.loading"
        class="adminissue-nocontent"
      >
        <div class="adminissue-nocontent-content">
          <div />
        </div>
      </div>
      <!-- 2-3. An Error occurred -->
      <div
        v-else-if="contentStore.error"
        class="adminissue-nocontent"
      >
        <div class="adminissue-nocontent-content">
          <span>sentiment_very_dissatisfied</span>
          <h2>發生錯誤，無法載入問題列表</h2>
        </div>
      </div>
      <!-- 2-4. Issues are loaded but there are none -->
      <div
        v-else
        class="adminissue-nocontent"
      >
        <div class="adminissue-nocontent-content">
          <span>search_off</span>
          <h2>查無符合篩選條件的問題</h2>
        </div>
      </div>
    </table>
    <!-- 3. Records per page and pagination control -->
    <div
      v-if="adminStore.issues.length !== 0"
      class="adminissue-control"
    >
      <label for="pagesize">每頁顯示</label>
      <select
        v-model="searchParams.pagesize"
        @change="handleNewQuery"
      >
        <option value="10">
          10
        </option>
        <option value="20">
          20
        </option>
        <option value="30">
          30
        </option>
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
    <AdminEditIssue :search-params="searchParams" />
  </div>
</template>

<style scoped lang="scss">
.adminissue {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-filter {
		display: flex;
		column-gap: var(--font-ms);
		margin-bottom: var(--font-ms);

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

	&-control {
		display: flex;
		align-items: center;
		margin-top: 0.5rem;
		height: 2rem;

		label {
			margin-right: 0.5rem;
			font-size: var(--font-m);
		}
		select {
			width: 100px;
		}
		option {
			background-color: var(--color-background);
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
