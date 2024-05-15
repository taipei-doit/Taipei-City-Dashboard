<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { onMounted, ref, computed } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useContentStore } from "../../store/contentStore";
import { useDialogStore } from "../../store/dialogStore";
import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminAddEditContributor from "../../components/dialogs/admin/AdminAddEditContributor.vue";
import AdminDeleteContributor from "../../components/dialogs/admin/AdminDeleteContributor.vue";

const adminStore = useAdminStore();
const contentStore = useContentStore();
const dialogStore = useDialogStore();

const dialogMode = ref("edit");
const searchParams = ref({
	pagesize: 10,
	pagenum: 1,
});

const pages = computed(() => {
	// return an array of pages based on results no stored in admin store
	if (adminStore.contributors) {
		const pages = Math.ceil(
			adminStore.contributorResults / searchParams.value.pagesize
		);
		return Array.from({ length: pages }, (_, i) => i + 1);
	}
	return [];
});

function parseTime(time) {
	time = new Date(time);
	time.setHours(time.getHours() + 8);
	time = time.toISOString();
	return time.slice(0, 19).replace("T", " ");
}

function handleNewQuery() {
	searchParams.value.pagenum = 1;
	adminStore.getContributors(searchParams.value);
}

function handleNewPage(page) {
	searchParams.value.pagenum = page;
	adminStore.getContributors(searchParams.value);
}

function handleDeleteContributor(contributor) {
	adminStore.currentContributor = JSON.parse(JSON.stringify(contributor));
	dialogStore.showDialog("adminDeleteContributor");
}

function handleAddContributor() {
	adminStore.currentContributor = {
		user_id: "",
		user_name: "",
		image: "",
		link: "",
	};
	dialogMode.value = "add";
	dialogStore.showDialog("adminAddEditContributor");
}

function handleOpenSettings(contributor) {
	adminStore.currentContributor = JSON.parse(JSON.stringify(contributor));
	dialogMode.value = "edit";
	dialogStore.showDialog("adminAddEditContributor");
}

onMounted(() => {
	adminStore.getContributors(searchParams.value);
});
</script>

<template>
  <div class="admincontributor">
    <!-- 1. Search bar to search contributors by name or index -->
    <div class="admincontributor-bar">
      <button @click="handleAddContributor">
        新增貢獻者
      </button>
    </div>
    <!-- 2. The main table displaying all contributors -->
    <table class="admincontributor-table">
      <thead>
        <tr class="admincontributor-table-header">
          <TableHeader min-width="60px" />
          <TableHeader min-width="60px">
            ID
          </TableHeader>
          <TableHeader min-width="150px">
            名稱
          </TableHeader>
          <TableHeader min-width="150px">
            圖片
          </TableHeader>
          <TableHeader min-width="200px">
            連結
          </TableHeader>
          <TableHeader min-width="200px">
            建立時間
          </TableHeader>
          <TableHeader min-width="200px">
            更新時間
          </TableHeader>
        </tr>
      </thead>
      <!-- 2-1. contributors are present -->
      <tbody v-if="adminStore.contributors.length !== 0">
        <tr
          v-for="contributor in adminStore.contributors"
          :key="`contributor-${contributor.id}`"
        >
          <td class="admincontributor-table-settings">
            <button @click="handleOpenSettings(contributor)">
              <span>settings</span>
            </button>
            <button @click="handleDeleteContributor(contributor)">
              <span>delete</span>
            </button>
          </td>
          <td>{{ contributor.user_id }}</td>
          <td>{{ contributor.user_name }}</td>
          <td>{{ contributor.image }}</td>
          <td>{{ contributor.link }}</td>
          <td>{{ parseTime(contributor.created_at) }}</td>
          <td>{{ parseTime(contributor.updated_at) }}</td>
        </tr>
      </tbody>
      <!-- 2-2. contributors are still loading -->
      <div
        v-else-if="contentStore.loading"
        class="admincontributor-nocontent"
      >
        <div class="admincontributor-nocontent-content">
          <div />
        </div>
      </div>
      <!-- 2-3. An Error occurred -->
      <div
        v-else-if="contentStore.error"
        class="admincontributor-nocontent"
      >
        <div class="admincontributor-nocontent-content">
          <span>sentiment_very_dissatisfied</span>
          <h2>發生錯誤，無法載入貢獻者列表</h2>
        </div>
      </div>
      <!-- 2-4. contributors are loaded but there are none -->
      <div
        v-else
        class="admincontributor-nocontent"
      >
        <div class="admincontributor-nocontent-content">
          <span>search_off</span>
          <h2>查無符合篩選條件的貢獻者</h2>
        </div>
      </div>
    </table>
    <!-- 3. Records per page and pagination control -->
    <div class="admincontributor-control">
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
      <div class="admincontributor-control-page">
        <button
          v-for="page in pages"
          :key="`contributor-page-${page}`"
          :class="{ active: page === searchParams.pagenum }"
          @click="handleNewPage(page)"
        >
          {{ page }}
        </button>
      </div>
    </div>
    <AdminAddEditContributor
      :mode="dialogMode"
      :search-params="searchParams"
    />
    <AdminDeleteContributor :search-params="searchParams" />
  </div>
</template>

<style scoped lang="scss">
.admincontributor {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-bar {
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
		height: 2rem;
		display: flex;
		align-items: center;
		margin-top: 0.5rem;

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
