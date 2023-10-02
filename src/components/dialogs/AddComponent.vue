<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- This component only serves a functional purpose if a backend is connected -->
<!-- For static applications, this component could be removed or modified to be a dashboard component overviewer -->

<script setup>
import { computed, ref } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import { useContentStore } from '../../store/contentStore';

import DialogContainer from './DialogContainer.vue';
import ComponentTag from '../utilities/ComponentTag.vue';
import CustomCheckBox from '../utilities/CustomCheckBox.vue';

const { BASE_URL } = import.meta.env;

const dialogStore = useDialogStore();
const contentStore = useContentStore();

// The following six states store the filters / parameters inputted by the user
const searchName = ref('');
const searchIndex = ref('');
const searchId = ref('');
const filterSource = ref([]);
const filterType = ref([]);
const filterFrequency = ref([]);
const filterControl = ref([]);
// This state stores the components currently selected
const componentsSelected = ref([]);
// The options for each filter (source, type, frequency, control)
const filterOptions = {
	source: ['1999', '陳情系統', '交通局', '警察局', '都發局', '消防局', '社會局', '工務局', '衛生局', '地政局', '捷運局'],
	// type: ['交通', '產業', '土地', '安全'],
	// frequency: ['無定期更新', '每半年', '每個月', '每兩週', '每一週', '每一天', '每一小時'],
	control: ['篩選地圖', '空間資料', "歷史資料"]
};

// Filters out components already in the dashboard / maplayer components
const availableComponents = computed(() => {
	const allComponentIds = Object.keys(contentStore.components);
	const taken = contentStore.currentDashboard.content.map((item) => item.id);
	const maplayer = contentStore.mapLayers.map((item) => item.id);
	const available = allComponentIds.filter(item => !taken.includes(+item) && !maplayer.includes(+item));
	const output = [];
	available.forEach(element => {
		output.push(contentStore.components[element]);
	});
	return output;
});
// Applies the filters selected by the user to "availableComponents"
const outputList = computed(() => {
	let output = [...availableComponents.value];

	if (searchName.value) {
		output = output.filter((item) => item.name.toLowerCase().includes(searchName.value.toLowerCase()));
	}
	if (searchIndex.value) {
		output = output.filter((item) => item.index.toString().includes(searchIndex.value));
	}
	if (searchId.value) {
		output = output.filter((item) => item.id.toString().includes(searchId.value));
	}
	if (filterSource.value.length > 0) {
		output = output.filter((item) => filterSource.value.findIndex((el) => item.source.includes(el)) > -1);
	}
	if (filterControl.value.includes('篩選地圖')) {
		output = output.filter((item) => item.chart_config.map_filter);
	}
	if (filterControl.value.includes('空間資料')) {
		output = output.filter((item) => item.map_config !== null);
	}
	if (filterControl.value.includes('歷史資料')) {
		output = output.filter((item) => item.history_data);
	}

	return output;
});

// Parses time data into display format
function dataTime(time_from, time_to) {
	if (!time_from) {
		return '固定資料';
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
		year: "年"
	};
	if (!update_freq) {
		return '不定期更新';
	}
	return `每${update_freq}${unitRef[update_freq_unit]}更新`;
}

function handleSubmit() {
	// addComponents is currently a dummy function to demonstrate what adding components may look like
	// Connect a backend to actually implement the function or remove altogether
	contentStore.addComponents(componentsSelected.value);
	handleClose();
}
function handleClose() {
	searchName.value = '';
	searchIndex.value = '';
	componentsSelected.value = [];
	clearFilters();
	dialogStore.hideAllDialogs();
}
function clearFilters() {
	filterSource.value = [];
	filterControl.value = [];
	filterType.value = [];
	filterFrequency.value = [];
}
</script>

<template>
	<DialogContainer :dialog="`addComponent`" @onClose="handleClose">
		<div class="addcomponent">
			<div class="addcomponent-header">
				<h2>新增組件</h2>
				<div class="addcomponent-header-search">
					<div>
						<div>
							<input type="text" placeholder="以名稱搜尋" v-model="searchName" />
							<span v-if="searchName" @click="() => { searchName = '' }">cancel</span>
						</div>
						<div>
							<input type="text" placeholder="以Index搜尋" v-model="searchIndex" />
							<span v-if="searchIndex" @click="() => { searchIndex = '' }">cancel</span>
						</div>
						<div>
							<input type="text" placeholder="以Id搜尋" v-model="searchId" />
							<span v-if="searchId" @click="() => { searchId = '' }">cancel</span>
						</div>
					</div>
					<div>
						<button @click="handleClose">取消</button>
						<button v-if="componentsSelected.length > 0"
							@click="handleSubmit"><span>add_chart</span>確認新增</button>
					</div>
				</div>
			</div>
			<div class="addcomponent-filter">
				<button @click="clearFilters">清除篩選條件</button>
				<div>
					<h3>依資料來源篩選</h3>
					<div v-for="item in filterOptions.source" :key="item">
						<input type="checkbox" :id="item" :value="item" v-model="filterSource" class="custom-check-input" />
						<CustomCheckBox :for="item">{{ item }}</CustomCheckBox>
					</div>
					<!-- <h3>依類別標籤篩選</h3>
                    <div v-for="item in filterOptions.type" :key="item">
                        <input type="checkbox" :id="item" :value="item" v-model="filterType" class="custom-check-input" />
                        <CustomCheckBox :for="item">{{ item }}</CustomCheckBox>
                    </div>
                    <h3>依更新頻率篩選</h3>
                    <div v-for="item in filterOptions.frequency" :key="item">
                        <input type="checkbox" :id="item" :value="item" v-model="filterFrequency"
                            class="custom-check-input" />
                        <CustomCheckBox :for="item">{{ item }}</CustomCheckBox>
                    </div> -->
					<h3>依功能種類篩選</h3>
					<div>
						<div v-for="item in filterOptions.control" :key="item">
							<input type="checkbox" :id="item" :value="item" v-model="filterControl"
								class="custom-check-input" />
							<CustomCheckBox :for="item">{{ item }}</CustomCheckBox>
						</div>
					</div>
				</div>
			</div>
			<div>
				<p :style="{ margin: '0 0 0.5rem 1rem' }">計 {{ outputList.length }} 個組件符合篩選條件 | 共選取 {{
					componentsSelected.length }} 個</p>
				<div class="addcomponent-list">
					<div v-for="item in outputList" :key="item.id">
						<input type="checkbox" :id="item.name" :value="item.id" v-model="componentsSelected" />
						<label :for="item.name" class="addcomponent-list-item">
							<div>
								<img :src="`${BASE_URL}/images/thumbnails/${item.chart_config.types[0]}.svg`" />
							</div>
							<div>
								<div>
									<h2>{{ item.name }}
										<ComponentTag icon=""
											:text="`${updateFreq(item.update_freq, item.update_freq_unit)}`" mode="small" />
									</h2>
									<h3>{{ `${item.source} | ${dataTime(item.time_from, item.time_to)}` }}</h3>
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
									<ComponentTag v-if="item.chart_config.map_filter && item.map_config" icon="tune"
										text="篩選地圖" />
									<ComponentTag v-if="item.map_config" icon="map" text="空間資料" />
									<ComponentTag v-if="item.history_data" icon="insights" text="歷史資料" />
								</div>
							</div>
						</label>
					</div>
				</div>
			</div>
		</div>
	</DialogContainer>
</template>

<style scoped lang="scss">
.addcomponent {
	width: 800px;
	height: 600px;
	display: grid;
	grid-template-columns: 180px 1fr;
	grid-template-areas:
		"header header"
		"filter list";
	grid-template-rows: 5.5rem 1fr;
	padding: 10px;

	&-header {
		grid-area: header;

		h2 {
			font-size: var(--font-m);
		}

		&-search {
			display: flex;
			justify-content: space-between;
			margin-top: 1rem;

			>div {
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

	&-filter {
		grid-area: filter;
		border-right: solid 1px var(--color-border);
		padding-right: 1rem;
		overflow-y: scroll;

		span {
			font-family: var(--font-icon);
			font-size: calc(var(--font-m) * var(--font-to-icon));
		}

		button {
			color: var(--color-highlight);
		}

		h3 {
			margin: 0.5rem 0;
			color: var(--color-complement-text);
			font-size: var(--font-m);
			font-weight: 400;
		}

		label {
			margin-left: 0.5rem;
			color: var(--color-complement-text);
			font-size: var(--font-m);
			transition: color 0.2s;
		}

		input {
			display: none;

			&:checked+label {
				color: white
			}

			&:hover+label {
				color: var(--color-highlight)
			}
		}
	}

	&-list {
		max-height: calc(100% - 1rem);
		grid-area: list;
		padding-left: 1rem;
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
			transition: border-color 0.2s,
				border-width 0.2s;
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

			>div:first-child {
				max-width: 150px;
				max-height: 150px;
				display: flex;
				align-items: center;
				justify-content: center;
				border-radius: 5px;
				background-color: var(--color-complement-text);
				pointer-events: none;
			}

			>div:nth-child(2) {
				>div:nth-child(2) {
					margin: 0.75rem 0;
				}

				>div:nth-child(3) {
					display: flex;
					margin-top: 0.5rem;
				}

				>div:nth-child(4) {
					display: flex;
					margin-top: 4px;
				}
			}
		}

		input {
			display: none;
		}

		input:checked+&-item {
			border-color: var(--color-highlight);
		}
	}
}
</style>