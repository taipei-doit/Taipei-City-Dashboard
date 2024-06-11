<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { ref, defineProps } from "vue";
import { storeToRefs } from "pinia";
import { DashboardComponent } from "city-dashboard-component";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";
import InputTags from "../../utilities/forms/InputTags.vue";
import SelectButtons from "../../utilities/forms/SelectButtons.vue";
import HistoryChart from "../../charts/HistoryChart.vue";

import { chartsPerDataType } from "../../../assets/configs/apexcharts/chartTypes";
import { timeTerms } from "../../../assets/configs/AllTimes";
import { mapTypes } from "../../../assets/configs/mapbox/mapConfig";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["searchParams"]);

const { currentComponent } = storeToRefs(adminStore);
const currentSettings = ref("all");
const tempInputStorage = ref({
	link: "",
	contributor: "",
	chartColor: "#000000",
	historyColor: "#000000",
});

function handleConfirm() {
	adminStore.updateComponent(props.searchParams);
	handleClose();
}

function handleClose() {
	currentSettings.value = "all";
	dialogStore.hideAllDialogs();
	adminStore.currentComponent = null;
}
</script>

<template>
  <DialogContainer
    :dialog="`adminComponentSettings`"
    @on-close="handleClose"
  >
    <div class="admincomponentsettings">
      <div class="admincomponentsettings-header">
        <h2>組件設定</h2>
        <button @click="handleConfirm">
          確定更改
        </button>
      </div>
      <div class="admincomponentsettings-tabs">
        <button
          :class="{ active: currentSettings === 'all' }"
          @click="currentSettings = 'all'"
        >
          整體
        </button>
        <button
          :class="{ active: currentSettings === 'chart' }"
          @click="currentSettings = 'chart'"
        >
          圖表
        </button>
        <button
          v-if="currentComponent.history_config !== null"
          :class="{ active: currentSettings === 'history' }"
          @click="currentSettings = 'history'"
        >
          歷史軸
        </button>
        <button
          v-if="currentComponent.map_config[0] !== null"
          :class="{ active: currentSettings === 'map' }"
          @click="currentSettings = 'map'"
        >
          地圖
        </button>
      </div>
      <div class="admincomponentsettings-content">
        <div class="admincomponentsettings-settings">
          <div
            v-if="currentSettings === 'all'"
            class="admincomponentsettings-settings-items"
          >
            <label>組件名稱* ({{
              currentComponent.name.length
            }}/10)</label>
            <input
              v-model="currentComponent.name"
              type="text"
              :minlength="1"
              :maxlength="15"
              required
            >
            <div class="two-block">
              <label>組件 ID</label>
              <label>組件 Index</label>
            </div>
            <div class="two-block">
              <input
                type="text"
                :value="currentComponent.id"
                disabled
              >
              <input
                type="text"
                :value="currentComponent.index"
                disabled
              >
            </div>
            <label>資料來源*</label>
            <input
              v-model="currentComponent.source"
              type="text"
              :minlength="1"
              :maxlength="12"
              required
            >
            <label>更新頻率* (0 = 不定期更新)</label>
            <div class="two-block">
              <input
                v-model="currentComponent.update_freq"
                type="number"
                :min="0"
                :max="31"
                required
              >
              <select v-model="currentComponent.update_freq_unit">
                <option value="minute" />
                <option value="hour">
                  時
                </option>
                <option value="day">
                  天
                </option>
                <option value="week">
                  週
                </option>
                <option value="month">
                  月
                </option>
                <option value="year">
                  年
                </option>
              </select>
            </div>
            <label>資料區間</label>
            <!-- eslint-disable no-mixed-spaces-and-tabs -->
            <div class="three-block">
              <select
                v-model="currentComponent.time_from"
                @change="
                  () => {
                    if (
                      [
                        'current',
                        'static',
                        'demo',
                        'maintain',
                      ].includes(
                        currentComponent.time_from
                      )
                    ) {
                      currentComponent.time_to = '';
                    } else {
                      currentComponent.time_to = 'now';
                    }
                  }
                "
              >
                <option
                  v-for="time in [
                    'current',
                    'static',
                    'demo',
                    'maintain',
                    'day_start',
                    'week_start',
                    'month_start',
                    'quarter_start',
                    'year_start',
                    'day_ago',
                    'week_ago',
                    'month_ago',
                    'quarter_ago',
                    'halfyear_ago',
                    'year_ago',
                  ]"
                  :key="time"
                  :value="time"
                >
                  {{ timeTerms[time] }}
                </option>
              </select>
              <div
                :style="{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }"
              >
                至
              </div>
              <input
                :value="
                  currentComponent.time_to === 'now'
                    ? '現在'
                    : 'N/A'
                "
                :disabled="true"
              >
            </div>
            <label required>組件簡述* ({{
              currentComponent.short_desc.length
            }}/50)</label>
            <textarea
              v-model="currentComponent.short_desc"
              :minlength="1"
              :maxlength="50"
              required
            />
            <label>組件詳述* ({{
              currentComponent.long_desc.length
            }}/100)</label>
            <textarea
              v-model="currentComponent.long_desc"
              :minlength="1"
              :maxlength="100"
              required
            />
            <label>範例情境* ({{
              currentComponent.use_case.length
            }}/100)</label>
            <textarea
              v-model="currentComponent.use_case"
              :minlength="1"
              :maxlength="100"
              required
            />
            <label>資料連結</label>
            <InputTags
              :tags="currentComponent.links"
              @deletetag="
                (index) => {
                  currentComponent.links.splice(index, 1);
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.links = updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.link"
              type="text"
              :minlength="1"
              @keypress.enter="
                () => {
                  if (tempInputStorage.link.length > 0) {
                    currentComponent.links.push(
                      tempInputStorage.link
                    );
                    tempInputStorage.link = '';
                  }
                }
              "
            >
            <label>貢獻者</label>
            <InputTags
              :tags="currentComponent.contributors"
              @deletetag="
                (index) => {
                  currentComponent.contributors.splice(
                    index,
                    1
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.contributors = updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.contributor"
              type="text"
              @keypress.enter="
                () => {
                  if (
                    tempInputStorage.contributor.length > 0
                  ) {
                    currentComponent.contributors.push(
                      tempInputStorage.contributor
                    );
                    tempInputStorage.contributor = '';
                  }
                }
              "
            >
          </div>
          <div
            v-else-if="currentSettings === 'chart'"
            class="admincomponentsettings-settings-items"
          >
            <label>圖表資料型態</label>
            <select
              :value="currentComponent.query_type"
              disabled
            >
              <option value="two_d">
                二維資料
              </option>
              <option value="three_d">
                三維資料
              </option>
              <option value="time">
                時間序列資料
              </option>
              <option value="percent">
                百分比資料
              </option>
              <option value="map_legend">
                圖例資料
              </option>
            </select>
            <label>資料單位*</label>
            <input
              v-model="currentComponent.chart_config.unit"
              type="text"
              :minlength="1"
              :maxlength="6"
              required
            >
            <label>圖表類型*（限3種，依點擊順序排列）</label>
            <SelectButtons
              :tags="
                chartsPerDataType[currentComponent.query_type]
              "
              :selected="currentComponent.chart_config.types"
              :limit="3"
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.chart_config.types =
                    updatedTags;
                }
              "
            />
            <label>圖表顏色</label>
            <InputTags
              :tags="currentComponent.chart_config.color"
              :color-data="true"
              @deletetag="
                (index) => {
                  currentComponent.chart_config.color.splice(
                    index,
                    1
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.chart_config.color =
                    updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.chartColor"
              type="color"
              class="admincomponentsettings-settings-inputcolor"
              @focusout="
                () => {
                  if (
                    tempInputStorage.chartColor.length === 7
                  ) {
                    currentComponent.chart_config.color.push(
                      tempInputStorage.chartColor
                    );
                    tempInputStorage.chartColor = '#000000';
                  }
                }
              "
            >
            <div v-if="currentComponent.map_config[0] !== null">
              <label>地圖篩選</label>
              <textarea v-model="currentComponent.map_filter" />
            </div>
          </div>
          <div
            v-else-if="currentSettings === 'history'"
            class="admincomponentsettings-settings-items"
          >
            <label>歷史軸時間區間
              (依點擊順序排列，資料無法預覽)</label>
            <SelectButtons
              :tags="[
                'month_ago',
                'quarter_ago',
                'halfyear_ago',
                'year_ago',
                'twoyear_ago',
                'fiveyear_ago',
                'tenyear_ago',
              ]"
              :selected="currentComponent.history_config.range"
              :limit="5"
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.history_config.range =
                    updatedTags;
                }
              "
            />
            <label>歷史軸顏色 (若無提供沿用圖表顏色)</label>
            <InputTags
              :tags="currentComponent.history_config.color"
              :color-data="true"
              @deletetag="
                (index) => {
                  currentComponent.history_config.color.splice(
                    index,
                    1
                  );
                }
              "
              @updatetagorder="
                (updatedTags) => {
                  currentComponent.history_config.color =
                    updatedTags;
                }
              "
            />
            <input
              v-model="tempInputStorage.historyColor"
              type="color"
              class="admincomponentsettings-settings-inputcolor"
              @focusout="
                () => {
                  if (
                    tempInputStorage.historyColor.length ===
                    7
                  ) {
                    currentComponent.history_config.color.push(
                      tempInputStorage.historyColor
                    );
                    tempInputStorage.historyColor =
                      '#000000';
                  }
                }
              "
            >
          </div>
          <div v-else-if="currentSettings === 'map'">
            <div
              v-for="(
                map_config, index
              ) in currentComponent.map_config"
              :key="map_config.index"
              class="admincomponentsettings-settings-items"
            >
              <hr v-if="index > 0">
              <label>地圖{{ index + 1 }} ID / Index</label>
              <div class="two-block">
                <input
                  :value="
                    currentComponent.map_config[index].id
                  "
                  disabled
                >
                <input
                  v-model="
                    currentComponent.map_config[index].index
                  "
                  :maxlength="30"
                  :minlength="1"
                  required
                >
              </div>

              <label>地圖{{ index + 1 }} 名稱* ({{
                currentComponent.map_config[index].title
                  .length
              }}/10)</label>
              <input
                v-model="
                  currentComponent.map_config[index].title
                "
                type="text"
                :minlength="1"
                :maxlength="10"
                required
              >
              <label>地圖{{ index + 1 }} 類型*</label>
              <select
                v-model="
                  currentComponent.map_config[index].type
                "
              >
                <option
                  v-for="(value, key) in mapTypes"
                  :key="key"
                  :value="key"
                >
                  {{ value }}
                </option>
              </select>
              <label>地圖{{
                index + 1
              }}
                預設變形（大小/圖示）</label>
              <div class="two-block">
                <select
                  v-model="
                    currentComponent.map_config[index].size
                  "
                >
                  <option :value="''">
                    無
                  </option>
                  <option value="small">
                    small (點圖)
                  </option>
                  <option value="big">
                    big (點圖)
                  </option>
                  <option value="wide">
                    wide (線圖)
                  </option>
                </select>
                <select
                  v-model="
                    currentComponent.map_config[index].icon
                  "
                >
                  <option :value="''">
                    無
                  </option>
                  <option value="heatmap">
                    heatmap (點圖)
                  </option>
                  <option value="dash">
                    dash (線圖)
                  </option>
                  <option value="metro">
                    metro (符號圖)
                  </option>
                  <option value="metro-density">
                    metro-density (符號圖)
                  </option>
                  <option value="triangle_green">
                    triangle_green (符號圖)
                  </option>
                  <option value="triangle_white">
                    triangle_white (符號圖)
                  </option>
                  <option value="youbike">
                    youbike (符號圖)
                  </option>
                  <option value="bus">
                    bus (符號圖)
                  </option>
                  <option value="cctv">
                    cctv (符號圖)
                  </option>
                </select>
              </div>
              <label>地圖{{ index + 1 }} Paint屬性</label>
              <textarea
                v-model="
                  currentComponent.map_config[index].paint
                "
              />
              <label>地圖{{ index + 1 }} Popup標籤</label>
              <textarea
                v-model="
                  currentComponent.map_config[index].property
                "
              />
            </div>
          </div>
        </div>
        <div class="admincomponentsettings-preview">
          <DashboardComponent
            v-if="
              currentSettings === 'all' ||
                currentSettings === 'chart'
            "
            :key="`${currentComponent.index}-${currentComponent.chart_config.color}-${currentComponent.chart_config.types}`"
            :config="JSON.parse(JSON.stringify(currentComponent))"
            mode="large"
          />
          <div
            v-else-if="currentSettings === 'history'"
            :style="{ width: '300px' }"
          >
            <HistoryChart
              :key="`${currentComponent.index}-${currentComponent.history_config.color}`"
              :chart_config="currentComponent.chart_config"
              :series="currentComponent.history_data"
              :history_config="
                JSON.parse(
                  JSON.stringify(
                    currentComponent.history_config
                  )
                )
              "
            />
          </div>
          <div
            v-else-if="currentSettings === 'map'"
            index="componentsettings"
          >
            預覽功能 Coming Soon
          </div>
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admincomponentsettings {
	width: 750px;
	height: 500px;

	@media (max-width: 770px) {
		display: none;
	}
	@media (max-height: 520px) {
		display: none;
	}

	&-header {
		display: flex;
		justify-content: space-between;

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-ms);
		}
	}

	&-content {
		height: calc(100% - 70px);
		display: grid;
		grid-template-columns: 1fr 350px;
	}

	&-tabs {
		height: 30px;
		display: flex;
		align-items: center;
		margin-top: var(--font-s);

		button {
			width: 70px;
			height: 30px;
			border-radius: 5px 5px 0px 0px;
			background-color: var(--color-border);
			font-size: var(--font-m);
			color: var(--color-text);
			cursor: pointer;
			transition: background-color 0.2s;

			&:hover {
				background-color: var(--color-complement-text);
			}
		}
		.active {
			background-color: var(--color-complement-text);
		}
	}

	&-settings {
		padding: 0 0.5rem 0.5rem 0.5rem;
		margin-right: var(--font-ms);
		border-radius: 0px 5px 5px 5px;
		border: solid 1px var(--color-border);
		overflow-y: scroll;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		.two-block {
			display: grid;
			grid-template-columns: 1fr 1fr;
			column-gap: 0.5rem;
		}
		.three-block {
			display: grid;
			grid-template-columns: 1fr 2rem 1fr;
			column-gap: 0.5rem;
		}

		&-items {
			display: flex;
			flex-direction: column;

			hr {
				margin: var(--font-ms) 0 0.5rem;
				border: none;
				border-bottom: dashed 1px var(--color-complement-text);
			}
		}

		&-inputcolor {
			width: 140px;
			height: 40px;
			appearance: none;
			display: flex;
			justify-content: center;
			align-items: center;
			padding: 0;
			outline: none;
			cursor: pointer;

			&::-webkit-color-swatch {
				border: none;
				border-radius: 5px;
			}
			&::-moz-color-swatch {
				border: none;
			}
			&:before {
				content: "選擇顏色";
				position: absolute;
				display: block;
				border-radius: 5px;
				font-size: var(--font-ms);
				color: var(--color-complement-text);
			}
			&:focus:before {
				content: "點擊空白處確認";
				text-shadow: 0px 0px 1px black;
			}
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			background-color: rgba(136, 135, 135, 0.5);
			border-radius: 4px;
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}

	&-preview {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		border-radius: 5px;
		border: solid 1px var(--color-border);
	}
}
</style>
