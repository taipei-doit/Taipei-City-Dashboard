<script setup>
import { onMounted, ref } from "vue";
import { useAdminStore } from "../../store/adminStore";
import TableHeader from "../../components/utilities/TableHeader.vue";
import ComponentTag from "../../components/utilities/ComponentTag.vue";
import { chartTypes } from "../../assets/configs/apexcharts/chartTypes";
import { mapTypes } from "../../assets/configs/mapbox/mapConfig";

const adminStore = useAdminStore();

const searchParams = ref({
	searchbyindex: "",
	searchbyname: "",
	sort: "",
	order: "",
	pagesize: 10,
	pagenum: 1,
});

function updateFreq(update_freq, update_freq_unit) {
	const unitRef = {
		minute: "分",
		hour: "時",
		day: "天",
		week: "週",
		month: "月",
		year: "年",
	};
	if (update_freq == 0) {
		return "不定期更新";
	}
	return `每${update_freq}${unitRef[update_freq_unit]}更新`;
}

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
	adminStore.getPublicComponents(searchParams.value);
}

onMounted(() => {
	adminStore.getPublicComponents(searchParams.value);
});
</script>

<template>
	<div class="admineditcomponent">
		<div class="admineditcomponent-search">
			<div>
				<input
					type="text"
					v-model="searchParams.searchbyname"
					placeholder="以組件名稱搜尋"
				/>
				<span
					v-if="searchParams.searchbyname !== ''"
					@click="searchParams.searchbyname = ''"
					>cancel</span
				>
			</div>
			<div>
				<input
					type="text"
					v-model="searchParams.searchbyindex"
					placeholder="以組件Index搜尋"
				/>
				<span
					v-if="searchParams.searchbyindex !== ''"
					@click="searchParams.searchbyindex = ''"
					>cancel</span
				>
			</div>
			<button @click="adminStore.getPublicComponents(searchParams)">
				搜尋
			</button>
		</div>
		<table class="admineditcomponent-table">
			<thead>
				<tr class="admineditcomponent-table-header">
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
					<TableHeader
						@sort="handleSort('index')"
						:sort="true"
						:mode="
							searchParams.sort === 'index'
								? searchParams.order
								: ''
						"
						minWidth="200px"
						>Index</TableHeader
					>
					<TableHeader minWidth="200px">名稱</TableHeader>
					<TableHeader>狀態</TableHeader>
					<TableHeader
						@sort="handleSort('source')"
						:sort="true"
						:mode="
							searchParams.sort === 'source'
								? searchParams.order
								: ''
						"
						minWidth="150px"
						>資料來源</TableHeader
					>
					<TableHeader minWidth="165px">圖表類型</TableHeader>
					<TableHeader minWidth="165px">地圖類型</TableHeader>
					<TableHeader>歷史資料</TableHeader>
					<TableHeader>更新頻率</TableHeader>
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
			<tbody>
				<tr
					v-for="component in adminStore.components"
					:key="component.index"
				>
					<td class="admineditcomponent-table-settings">
						<button><span>settings</span></button>
					</td>
					<td>{{ component.id }}</td>
					<td>{{ component.index }}</td>
					<td>{{ component.name }}</td>
					<td>啟動</td>
					<td>{{ component.source }}</td>
					<td>
						<div class="admineditcomponent-table-charts">
							<ComponentTag
								v-for="(chart, index) in component.chart_config
									.types"
								:text="chartTypes[chart]"
								:key="`${component.index}-chart-${index}`"
								mode="fill"
							/>
						</div>
					</td>
					<td>
						<div
							class="admineditcomponent-table-maps"
							v-if="component.map_config[0] !== null"
						>
							<ComponentTag
								v-for="(map, index) in component.map_config"
								:text="mapTypes[map?.type]"
								:key="`${component.index}-map-${index}`"
								mode="fill"
							/>
						</div>
					</td>
					<td>
						<span>{{
							component.history_data !== null
								? "check_circle"
								: ""
						}}</span>
					</td>
					<td>
						<div class="admineditcomponent-table-update">
							<ComponentTag
								:text="
									updateFreq(
										component.update_freq,
										component.update_freq_unit
									)
								"
								mode="small"
							/>
						</div>
					</td>
					<td>{{ parseTime(component.updated_at) }}</td>
				</tr>
			</tbody>
		</table>
		<!-- html element to select a results per page -->
		<div class="admineditcomponent-select">
			<label for="pagesize">每頁顯示</label>
			<select
				v-model="searchParams.pagesize"
				@change="adminStore.getPublicComponents(searchParams)"
			>
				<option value="10">10</option>
				<option value="20">20</option>
				<option value="30">30</option>
			</select>
		</div>
	</div>
</template>

<style scoped lang="scss">
.admineditcomponent {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	margin-top: 20px;
	padding: 0 20px 20px;

	&-search {
		display: flex;
		column-gap: 0.5rem;
		margin-bottom: 1rem;

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
				cursor: pointer;
				transition: color 0.2s;

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
			padding: 2px 4px;
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

	&-select {
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
	}
}
</style>
