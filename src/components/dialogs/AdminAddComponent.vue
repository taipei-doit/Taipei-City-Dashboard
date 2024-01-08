<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component only serves a functional purpose if a backend is connected -->
<!-- For static applications, this component could be removed or modified to be a dashboard component overviewer -->

<script setup>
import { computed, onMounted, ref } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useAdminStore } from "../../store/adminStore";

import DialogContainer from "./DialogContainer.vue";
import ComponentTag from "../utilities/ComponentTag.vue";
import axios from "axios";

const { BASE_URL, VITE_API_URL } = import.meta.env;

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

// The following six states store the filters / parameters inputted by the user
const searchName = ref("");
const searchIndex = ref("");

const allComponents = ref(null);
const componentsSelected = ref([]);

// Filters out components already in the dashboard / maplayer components
const availableComponents = computed(() => {
	const taken = adminStore.currentDashboard.components.map((item) => item.id);
	const available = allComponents.value.filter(
		(item) => !taken.includes(+item.id)
	);
	return available;
});

// Parses time data into display format
function dataTime(time_from, time_to) {
	if (!time_from) {
		return "固定資料";
	}
	if (!time_to) {
		return time_from.slice(0, 10);
	}
	return `${time_from.slice(0, 10)} ~ ${time_to.slice(0, 10)}`;
}
// Parses update frequency data into display format
function updateFreq(update_freq, update_freq_unit) {
	const unitRef = {
		minute: "分",
		hour: "時",
		day: "天",
		week: "週",
		month: "月",
		year: "年",
	};
	if (!update_freq) {
		return "不定期更新";
	}
	return `每${update_freq}${unitRef[update_freq_unit]}更新`;
}
function handleSearch() {
	axios
		.get(`${VITE_API_URL}/component/`, {
			params: {
				pagesize: 100,
				searchbyindex: searchIndex.value,
				searchbyname: searchName.value,
			},
		})
		.then((res) => {
			allComponents.value = res.data.data;
		});
}
function handleSubmit() {
	adminStore.currentDashboard.components =
		adminStore.currentDashboard.components.concat(componentsSelected.value);
	handleClose();
}
function handleClose() {
	searchName.value = "";
	searchIndex.value = "";
	componentsSelected.value = [];
	dialogStore.dialogs.adminaddcomponent = false;
}

onMounted(() => {
	handleSearch();
});
</script>

<template>
	<DialogContainer :dialog="`adminaddcomponent`" @onClose="handleClose">
		<div class="addcomponent">
			<div class="addcomponent-header">
				<h2>新增組件至儀表板</h2>
				<div class="addcomponent-header-search">
					<div>
						<div>
							<input
								type="text"
								placeholder="以名稱搜尋 (Enter)"
								v-model="searchName"
								@keypress.enter="handleSearch"
							/>
							<span
								v-if="searchName"
								@click="
									() => {
										searchName = '';
										handleSearch();
									}
								"
								>cancel</span
							>
						</div>
						<div>
							<input
								type="text"
								placeholder="以Index搜尋 (Enter)"
								v-model="searchIndex"
								@keypress.enter="handleSearch"
							/>
							<span
								v-if="searchIndex"
								@click="
									() => {
										searchIndex = '';
										handleSearch();
									}
								"
								>cancel</span
							>
						</div>
					</div>
					<div>
						<button @click="handleClose">取消</button>
						<button
							v-if="componentsSelected.length > 0"
							@click="handleSubmit"
						>
							<span>add_chart</span>確認新增
						</button>
					</div>
				</div>
			</div>
			<p :style="{ margin: '1rem 0 0.5rem' }">
				計 {{ availableComponents.length }} 個組件符合篩選條件 | 共選取
				{{ componentsSelected.length }} 個
			</p>

			<div class="addcomponent-list">
				<div v-for="item in availableComponents" :key="item.id">
					<input
						type="checkbox"
						:id="item.name"
						:value="{ id: item.id, name: item.name }"
						v-model="componentsSelected"
					/>
					<label :for="item.name" class="addcomponent-list-item">
						<div>
							<img
								:src="`${BASE_URL}/images/thumbnails/${item.chart_config.types[0]}.svg`"
							/>
						</div>
						<div>
							<div>
								<h2>
									{{ item.name }}
									<ComponentTag
										icon=""
										:text="`${updateFreq(
											item.update_freq,
											item.update_freq_unit
										)}`"
										mode="small"
									/>
								</h2>
								<h3>
									{{
										`${item.source} | ${dataTime(
											item.time_from,
											item.time_to
										)}`
									}}
								</h3>
							</div>
							<div>
								<p>{{ item.short_desc }}</p>
								<br />
								<p><b>組件ID：</b>{{ item.id }}</p>
								<p><b>組件Index：</b>{{ item.index }}</p>
							</div>
							<!-- <div>
                                    <ComponentTag v-for="element in item.tags" icon="" :text="element" mode="fill" />
                                </div> -->
							<div>
								<ComponentTag
									v-if="item.map_filter && item.map_config"
									icon="tune"
									text="篩選地圖"
								/>
								<ComponentTag
									v-if="item.map_config"
									icon="map"
									text="空間資料"
								/>
								<ComponentTag
									v-if="item.history_config"
									icon="insights"
									text="歷史資料"
								/>
							</div>
						</div>
					</label>
				</div>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.addcomponent {
	width: 600px;
	height: 600px;
	padding: 10px;

	&-header {
		h2 {
			font-size: var(--font-m);
		}

		&-search {
			display: flex;
			justify-content: space-between;
			margin-top: 1rem;

			> div {
				display: flex;
				justify-content: space-between;

				&:first-child {
					div {
						position: relative;
					}

					input {
						width: 150px;
						margin-right: 0.5rem;
					}

					span {
						position: absolute;
						right: 0.5rem;
						top: 0.4rem;
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

				&:last-child {
					span {
						margin-right: 4px;
						font-family: var(--font-icon);
						font-size: calc(var(--font-m) * var(--font-to-icon));
					}

					button {
						display: flex;
						align-items: center;
						justify-self: baseline;
						margin-right: 0.4rem;
						border-radius: 5px;
						font-size: var(--font-m);

						&:nth-child(2) {
							padding: 2px 4px;
							background-color: var(--color-highlight);
						}
					}
				}
			}
		}
	}

	&-list {
		max-height: calc(100% - 1rem);
		grid-area: list;
		overflow-y: scroll;

		&-item {
			width: calc(100% - 1.2rem);
			display: grid;
			grid-template-columns: 150px 1fr;
			column-gap: 1rem;
			margin: 0.5rem 0;
			padding: 0.5rem;
			border: solid 1px var(--color-border);
			border-radius: 5px;
			transition: border-color 0.2s, border-width 0.2s;
			cursor: pointer;

			h2 {
				display: flex;
				align-items: center;
				font-size: var(--font-m);
			}

			h3 {
				color: var(--color-complement-text);
				font-weight: 400;
			}

			> div:first-child {
				max-width: 150px;
				max-height: 150px;
				display: flex;
				align-items: center;
				justify-content: center;
				border-radius: 5px;
				background-color: var(--color-complement-text);
				pointer-events: none;
			}

			> div:nth-child(2) {
				> div:nth-child(2) {
					margin: 0.75rem 0;
				}

				> div:nth-child(3) {
					display: flex;
					margin-top: 0.5rem;
				}

				> div:nth-child(4) {
					display: flex;
					margin-top: 4px;
				}
			}
		}

		input {
			display: none;
		}

		input:checked + &-item {
			border-color: var(--color-highlight);
		}
	}
}
</style>
