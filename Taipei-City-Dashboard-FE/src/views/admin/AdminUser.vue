<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { onMounted, ref, computed } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useContentStore } from "../../store/contentStore";
import { useDialogStore } from "../../store/dialogStore";
import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import AdminEditUser from "../../components/dialogs/admin/AdminEditUser.vue";

const adminStore = useAdminStore();
const contentStore = useContentStore();
const dialogStore = useDialogStore();

const searchParams = ref({
	searchbyid: "",
	searchbyname: "",
	sort: "",
	order: "",
	pagesize: 10,
	pagenum: 1,
});

const pages = computed(() => {
	// return an array of pages based on results no stored in admin store
	if (adminStore.users) {
		const pages = Math.ceil(
			adminStore.userResults / searchParams.value.pagesize
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
	adminStore.getUsers(searchParams.value);
}

function handleNewQuery() {
	searchParams.value.pagenum = 1;
	adminStore.getUsers(searchParams.value);
}

function handleNewPage(page) {
	searchParams.value.pagenum = page;
	adminStore.getUsers(searchParams.value);
}

function handleOpenSettings(user) {
	adminStore.currentUser = JSON.parse(JSON.stringify(user));
	dialogStore.showDialog("adminEditUser");
}

onMounted(() => {
	adminStore.getUsers(searchParams.value);
});
</script>

<template>
  <div class="adminuser">
    <!-- 1. Search bar to search users by name or index -->
    <div class="adminuser-search">
      <div>
        <input
          v-model="searchParams.searchbyname"
          type="text"
          placeholder="以用戶名稱搜尋"
        >
        <span
          v-if="searchParams.searchbyname !== ''"
          @click="searchParams.searchbyname = ''"
        >cancel</span>
      </div>
      <div>
        <input
          v-model="searchParams.searchbyid"
          type="text"
          placeholder="以用戶ID搜尋"
        >
        <span
          v-if="searchParams.searchbyid !== ''"
          @click="searchParams.searchbyid = ''"
        >cancel</span>
      </div>
      <button @click="handleNewQuery">
        搜尋
      </button>
    </div>
    <!-- 2. The main table displaying all public users -->
    <table class="adminuser-table">
      <thead>
        <tr class="adminuser-table-header">
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
          <TableHeader min-width="150px">
            名稱
          </TableHeader>
          <TableHeader min-width="150px">
            帳號
          </TableHeader>
          <TableHeader
            min-width="100px"
            :sort="true"
            :mode="
              searchParams.sort === 'is_admin'
                ? searchParams.order
                : ''
            "
            @sort="handleSort('is_admin')"
          >
            身份
          </TableHeader>
          <TableHeader
            min-width="120px"
            :sort="true"
            :mode="
              searchParams.sort === 'is_whitelist'
                ? searchParams.order
                : ''
            "
            @sort="handleSort('is_whitelist')"
          >
            API白名單
          </TableHeader>
          <TableHeader
            min-width="120px"
            :sort="true"
            :mode="
              searchParams.sort === 'is_blacked'
                ? searchParams.order
                : ''
            "
            @sort="handleSort('is_blacked')"
          >
            API黑名單
          </TableHeader><TableHeader
            :sort="true"
            :mode="
              searchParams.sort === 'login_at'
                ? searchParams.order
                : ''
            "
            min-width="200px"
            @sort="handleSort('login_at')"
          >
            上次登入
          </TableHeader>
          <TableHeader
            min-width="120px"
            :sort="true"
            :mode="
              searchParams.sort === 'is_active'
                ? searchParams.order
                : ''
            "
            @sort="handleSort('is_active')"
          >
            啟用狀態
          </TableHeader>
          <TableHeader min-width="200px">
            停用時間
          </TableHeader>
        </tr>
      </thead>
      <!-- 2-1. users are present -->
      <tbody v-if="adminStore.users.length !== 0">
        <tr
          v-for="user in adminStore.users"
          :key="`user-${user.id}`"
        >
          <td class="adminuser-table-settings">
            <button @click="handleOpenSettings(user)">
              <span>settings</span>
            </button>
          </td>
          <td>{{ user.user_id }}</td>
          <td>{{ user.name }}</td>
          <td>{{ user.account ? user.account : user.TpAccount }}</td>
          <td>{{ user.is_admin ? "管理員" : "一般用戶" }}</td>
          <td>
            <span>{{
              user.is_whitelist ? "check_circle" : "cancel"
            }}</span>
          </td>
          <td>
            <span>{{
              user.is_blacked ? "check_circle" : "cancel"
            }}</span>
          </td>
          <td>{{ parseTime(user.login_at) }}</td>
          <td>
            <span>{{
              user.is_active ? "check_circle" : "cancel"
            }}</span>
          </td>
          <td>
            {{
              user.expired_at && !user.is_active
                ? parseTime(user.expired_at)
                : "未被停用"
            }}
          </td>
        </tr>
      </tbody>
      <!-- 2-2. users are still loading -->
      <div
        v-else-if="contentStore.loading"
        class="adminuser-nocontent"
      >
        <div class="adminuser-nocontent-content">
          <div />
        </div>
      </div>
      <!-- 2-3. An Error occurred -->
      <div
        v-else-if="contentStore.error"
        class="adminuser-nocontent"
      >
        <div class="adminuser-nocontent-content">
          <span>sentiment_very_dissatisfied</span>
          <h2>發生錯誤，無法載入用戶列表</h2>
        </div>
      </div>
      <!-- 2-4. users are loaded but there are none -->
      <div
        v-else
        class="adminuser-nocontent"
      >
        <div class="adminuser-nocontent-content">
          <span>search_off</span>
          <h2>查無符合篩選條件的用戶</h2>
        </div>
      </div>
    </table>
    <!-- 3. Records per page and pagination control -->
    <div class="adminuser-control">
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
      <div class="adminuser-control-page">
        <button
          v-for="page in pages"
          :key="`user-page-${page}`"
          :class="{ active: page === searchParams.pagenum }"
          @click="handleNewPage(page)"
        >
          {{ page }}
        </button>
      </div>
    </div>
    <AdminEditUser :search-params="searchParams" />
  </div>
</template>

<style scoped lang="scss">
.adminuser {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-search {
		display: flex;
		column-gap: 0.5rem;
		margin-bottom: var(--font-ms);

		div {
			position: relative;

			span {
				position: absolute;
				right: 0;
				top: 0.3rem;
				margin-right: 4px;
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				font-size: var(--font-m);
				transition: color 0.2s;
				cursor: pointer;

				&:hover {
					color: var(--color-highlight);
				}
			}
		}

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			margin-right: 0.4rem;
			padding: 0px 4px;
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
