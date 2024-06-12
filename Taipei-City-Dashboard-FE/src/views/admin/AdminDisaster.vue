<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<script setup>
import { onMounted, ref, computed } from "vue";
import { useAdminStore } from "../../store/adminStore";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";
import http from "../../router/axios";

import TableHeader from "../../components/utilities/forms/TableHeader.vue";
import CustomCheckBox from "../../components/utilities/forms/CustomCheckBox.vue";

const adminStore = useAdminStore();
const dialogStore = useDialogStore();
const contentStore = useContentStore();

const statuses = ["待處理", "通過", "不通過"];
const statusName = {
	待處理: "pending",
	通過: "accepted",
	不通過: "rejected",
};
const searchParams = ref({
	filterbystatus: [],
	sort: "time",
	order: "desc",
	pagesize: 10,
	pagenum: 1,
});

const pages = computed(() => {
	// return an array of pages based on results no stored in admin store
	if (adminStore.disasters) {
		const pages = Math.ceil(
			adminStore.disasterResults / searchParams.value.pagesize
		);
		return Array.from({ length: pages }, (_, i) => i + 1);
	}
	return [];
});

function parseTime(time) {
	// return time.slice(0, 19).replace("T", " ");
	return new Date(time).toLocaleString("zh-TW", { hour12: false });
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
	adminStore.getDisasters(searchParams.value);
}

function handleNewQuery() {
	searchParams.value.pagenum = 1;
	adminStore.getDisasters(searchParams.value);
}

function handleNewPage(page) {
	searchParams.value.pagenum = page;
	adminStore.getDisasters(searchParams.value);
}

function handleDelete(id) {
	adminStore.deleteDisaster(id, searchParams.value);
	handleNewQuery();
}

async function handleReview(id, result) {
	if (result === 1) {
		await http.patch("/incident/" + id, {
			status: "accepted",
		});
		// const uploadGeoJson = {
		// 	type: "Feature",
		// 	geometry: {
		// 		type: "Point",
		// 		coordinates: [target.longitude, target.latitude],
		// 	},
		// 	properties: {
		// 		類型: target.inctype,
		// 		描述: target.description,
		// 		距離: target.distance.toString() + "公里",
		// 		時間: parseTime(target.reportTime),
		// 	},
		// };
		// data.methods.uploadData(uploadGeoJson);

		dialogStore.showNotification("success", `ID:${id} 事件已接受`);
		// contentStore.sendMessage(target);
	} else if (result === 0) {
		await http.patch("/incident/" + id, {
			status: "rejected",
		});
		dialogStore.showNotification("fail", `ID:${id} 事件已拒絕`);
	} else {
		await http.patch("/incident/" + id, {
			status: "pending",
		});
		dialogStore.showNotification("info", `ID:${id} 事件已更新狀態`);
	}
	handleNewQuery();
}

onMounted(() => {
	adminStore.getDisasters(searchParams.value);
});
</script>

<template>
  <div class="admindisaster">
    <!-- 1. Checkboxes to filter through different issue types -->
    <h2>本功能尚測試中，未對一般用戶開放</h2>
    <div class="admindisaster-filter">
      <div
        v-for="status in statuses"
        :key="status"
      >
        <input
          :id="status"
          v-model="searchParams.filterbystatus"
          type="checkbox"
          class="custom-check-input"
          :value="statusName[status]"
          @change="handleNewQuery"
        >
        <CustomCheckBox :for="status">
          {{ status }}
        </CustomCheckBox>
      </div>
    </div>
    <!-- 2. The main table displaying various issues -->
    <table class="admindisaster-table">
      <thead>
        <tr class="admindisaster-table-header">
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
            種類
          </TableHeader>
          <TableHeader min-width="250px">
            描述
          </TableHeader>
          <TableHeader min-width="320px">
            地點
          </TableHeader>
          <TableHeader min-width="180px">
            時間
          </TableHeader>
          <TableHeader min-width="200px">
            審核
          </TableHeader>
        </tr>
      </thead>
      <!-- 2-1. Disasters are present -->
      <tbody v-if="adminStore.disasters.length !== 0">
        <tr
          v-for="disaster in adminStore.disasters"
          :key="`disaster-${disaster.id}`"
        >
          <td>
            <span
              v-if="disaster.status === 'accepted'"
              class="material-symbols-rounded"
              style="color: yellowgreen"
            >
              verified
            </span>
            <span
              v-else-if="disaster.status === 'rejected'"
              class="material-symbols-rounded"
              style="color: lightcoral"
            >
              cancel
            </span>
          </td>
          <td>{{ disaster.ID }}</td>
          <td>{{ disaster.inctype }}</td>
          <td class="admindisaster-table-description">
            {{ disaster.description }}
          </td>
          <td>{{ disaster.place }}</td>
          <td>{{ parseTime(disaster.reportTime) }}</td>
          <td class="admindisaster-table-review">
            <div
              v-if="disaster.status !== 'pending'"
              class="btn"
            >
              <button
                v-if="
                  disaster.status === 'accepted' ||
                    disaster.status === 'rejected'
                "
                @click="handleDelete(disaster.ID)"
              >
                <span>delete</span>
              </button>
              <button
                v-else
                @click="handleReview(disaster.ID, -1)"
              >
                <span>refresh</span>
              </button>
            </div>
            <div
              v-else
              class="btn"
            >
              <button
                class="reviewBtn"
                @click="handleReview(disaster.ID, 1)"
              >
                通過
              </button>
              <button
                class="reviewBtn"
                @click="handleReview(disaster.ID, 0)"
              >
                拒絕
              </button>
            </div>
          </td>
        </tr>
      </tbody>
      <!-- 2-2. Disaster are still loading -->
      <div
        v-else-if="contentStore.loading"
        class="admindisaster-nocontent"
      >
        <div class="admindisaster-nocontent-content">
          <h2>載入中...</h2>
        </div>
      </div>
      <!-- 2-3. An Error occurred -->
      <div
        v-else-if="contentStore.error"
        class="admindisaster-nocontent"
      >
        <div class="admindisaster-nocontent-content">
          <span>sentiment_very_dissatisfied</span>
          <h2>發生錯誤，無法載入問題列表</h2>
        </div>
      </div>
      <!-- 2-4. Disasters are loaded but there are none -->
      <div
        v-else
        class="admindisaster-nocontent"
      >
        <div class="admindisaster-nocontent-content">
          <span>search_off</span>
          <h2>查無符合篩選條件的災害</h2>
        </div>
      </div>
    </table>
    <!-- 3. Records per page and pagination control -->
    <div
      v-if="adminStore.disasters.length !== 0"
      class="admindisaster-control"
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
      <div class="admindisaster-control-page">
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
  </div>
</template>

<style scoped lang="scss">
.admindisaster {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	margin-top: 20px;
	padding: 0 20px 20px;

	h2 {
		margin-bottom: 1rem;
	}

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

		&-description {
			word-wrap: break-word;
			overflow-wrap: break-word;
			white-space: normal;
			word-break: break-word;
			max-width: 450px;
		}

		&-review {
			display: flex;
			justify-content: center;
			align-items: center;
			// min-height: 120px;
			.btn {
				display: flex;
				flex-direction: row;
				justify-content: center;
				align-items: center;
				.reviewBtn {
					padding: 7px;
					margin: 5px;
					font-size: var(--font-ms);
					background-color: var(--color-highlight);
					border-radius: 10px;
					&:hover {
						opacity: 0.85;
					}
				}
			}
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
