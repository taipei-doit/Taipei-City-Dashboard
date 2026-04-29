---
name: chart
description: >
  當使用者要新增、修改、除錯圖表元件，或涉及 chart_config、chart_data、ApexCharts、DashboardComponent、dashboardComponent/ 資料夾時觸發此技能。
  觸發情境：「新增圖表」「修改圖表樣式」「新圖表類型」「客製化 ApexCharts」「chart_config 怎麼設」「DashboardComponent 怎麼用」「為儀表板加一個折線圖」等。
  不要使用：使用者只問地圖圖層、彈跳視窗、頁面路由等純非圖表問題。
---

# 客製化圖表

## Step 0：觀摩既有圖表（**強制**，開工前必做）

**任何新圖表元件動手前，必須先讀至少一個既有圖表 Vue 元件**，確認視覺風格、prop 命名、ApexCharts 選項結構一致。

建議讀：`Taipei-City-Dashboard-FE/src/dashboardComponent/components/ColumnChart.vue`

讀完後，在對話中向使用者回報：
- 打算重用哪個元件的結構
- 哪些 `chartOptions` 設定沿用
- 明確偏離點（如果有）

## Step 0.5：盤點 `utilities/` 與 `dialogs/`（**強制**）

掃 `Taipei-City-Dashboard-FE/src/components/utilities/` 與 `src/components/dialogs/`，列出可重用元件，**不得自己生成已存在的元件**。

## 顯示圖表

如此先前文章中簡介的，每當頁面加載時，會呼叫 API 獲取組件的統計資料。一旦獲取到資料，將在圖表配置中加入"chart_data"參數，並填入資料，最後儲存在 contentStore 中，以便在整個應用程式中均能使用。

### 組件容器(Container)

負責渲染圖表的 Vue 元件分別是ComponentContainer和ComponentMapContainer，分別用於儀表板頁面和地圖頁面。這兩個 Vue 元件均位於/src/components/components。

如果一個組件包含多個圖表類型，將在組件容器頂部顯示以圖表名稱為標題的灰色按鈕，用戶可以點擊這些按鈕以切換圖表類型。此效果是透過在渲染它的 Vue 元件中儲存當前顯示的圖表名稱，並有條件地渲染圖表Vue元件達成的。

### 圖表 Vue 元件的結構

所有圖表 Vue 元件都接受四個屬性(props)：“activeChart”、“chart_config”、“series” 和 “map_config”。activeChart 屬性通知圖表 Vue 元件是否應該被渲染；chart_config 屬性包含指定圖表如何渲染的相關設定；series 屬性包含統計資料；"map_config" 使圖表能控制附加在同一組件的地圖；map_filter 儲存額外的地圖篩選設定.

以下是一個以 Apexcharts 為基底的圖表 Vue 元件的架構。

```vue
<script setup>
import { computed, ref } from 'vue'
import { useMapStore } from '../../store/mapStore';

// 註冊四個屬性(props)
const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config', 'map_filter'])
const mapStore = useMapStore()

// 選擇性包含
// 部分圖表包含編譯函式以確保圖表間的相容性，使同一份資料能選染多種圖表
const parseSeries = computed(() => {
    // Parse props.series to compatible format
    ...
    return output
})

// Apexcharts 設定
const chartOptions = ref({
    chart: {
        ...
    },
    colors: props.chart_config.color,
    labels: props.chart_config.categories ? props.chart_config.categories : [],
    ...
})

// 選擇性包含
// 如圖表希望支援地圖篩選則應包含
const selectedIndex = ref(null)

function handleDataSelection(e, chartContext, config) {
    // 完整函式內容請參照程式庫
    ...
}
</script>

<template>
 <!-- conditionally render the chart -->
 <div v-if="activeChart === 'GuageChart'">
  <!-- type: apexcharts 的圖表種類。可能與本專案的命名有些不同。 -->
  <!-- options: 填入 chartOptions 物件 -->
  <!-- series: 填入 series 或 parsed series -->
  <!-- dataPointSelection: 如有地圖篩選功能應包含 -->
  <apexchart
   width="80%"
   height="300px"
   type="radialBar"
   :options="chartOptions"
   :series="parseSeries.series"
   @dataPointSelection="handleDataSelection"
  >
  </apexchart>
 </div>
</template>
```

以下是不使用第三方套件，客製化開發的圖表的Vue元件架構。

```vue
<script setup>
import { computed, ref } from 'vue'
import { useMapStore } from '../../store/mapStore';

// 註冊四個屬性(props)
const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config'])
const mapStore = useMapStore()

// 選擇性包含
// 如圖表希望支援地圖篩選則應包含
const selectedIndex = ref(null)

function handleDataSelection(index) {
    // 完整函式內容請參照程式庫
    ...
}
</script>

<template>
 <!-- conditionally render the chart -->
 <div v-if="activeChart === 'MetroChart'" class="metrochart">
  <!-- 此圖表 Vue 元件的架構 -->
  <!-- 使用 @click 來導入地圖篩選功能 -->
 </div>
</template>

<style scoped lang="scss">
.metrochart {
 /* 圖表 Vue 元件的樣式 */
}

/* 建議亦為客製化圖表新增一些出場動畫 */
</style>
```

# 建立新的圖表類型

首先，決定圖表名稱，然後建立一個遵循圖表 Vue 元件結構的 Vue 元件。如果使用 Apexcharts 來渲染該圖表，亦須填寫相關的圖表選項(chartOptions)。

接下來，註冊該圖表，將其添加到 `/src/assets/configs/apexcharts/chartTypes.js` 文件的列表中。然後在 `/src/main.js` 中將該圖表 Vue 元件註冊為全域 Vue 元件。

最後，在任何組件配置中添加該圖表名稱以渲染它。

## 完成後檢查

- [ ] 已讀既有圖表元件（Step 0）確認視覺一致
- [ ] Vue 元件放在 `src/dashboardComponent/components/`
- [ ] 已在 `chartTypes.js` 註冊新圖表名稱
- [ ] 已在 `main.js` 全域註冊 Vue 元件
- [ ] props 包含 `chart_config`、`activeChart`、`series`、`map_config`
- [ ] 無 hardcoded 顏色（用 `var(--color-*)` 或 `chart_config.color`）
- [ ] `npm run lint` 無錯誤
