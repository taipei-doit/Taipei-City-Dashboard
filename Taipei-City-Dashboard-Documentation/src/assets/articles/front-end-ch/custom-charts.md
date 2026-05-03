## 顯示圖表
如[此先前文章](/front-end/rendering-strategy)中簡介的，每當頁面加載時，會呼叫 API 獲取組件的統計資料。一旦獲取到資料，將在圖表配置中加入`"chart_data"`參數，並填入資料，最後儲存在 `contentStore` 中，以便在整個應用程式中均能使用。

### 組件容器(Container)
負責渲染圖表的 Vue 元件分別是`ComponentContainer`和`ComponentMapContainer`，分別用於儀表板頁面和地圖頁面。這兩個 Vue 元件均位於`/src/components/components`。

如果一個組件包含多個圖表類型，將在組件容器頂部顯示以圖表名稱為標題的灰色按鈕，用戶可以點擊這些按鈕以切換圖表類型。此效果是透過在渲染它的 Vue 元件中儲存當前顯示的圖表名稱，並有條件地渲染圖表Vue元件達成的。

>**w01**
>如果您對目前支援的圖表類型及其對應的中英名稱不熟悉，請先閱讀[此先前文章](/front-end/supported-chart-types)。

>**w02**
>如果您對Apexcharts在Vue中的運作方式不熟悉，請先閱讀Apexchart的[相關文件](https://apexcharts.com/docs/vue-charts/)。

### 圖表 Vue 元件的結構
所有圖表 Vue 元件都接受四個屬性(props)：`“activeChart”`、`“chart_config”`、`“series”` 和 `“map_config”`。`activeChart` 屬性通知圖表 Vue 元件是否應該被渲染；`chart_config` 屬性包含指定圖表如何渲染的相關設定；`series` 屬性包含統計資料；`"map_config"` 使圖表能控制附加在同一組件的地圖；`map_filter` 儲存額外的地圖篩選設定.

以下是一個以 Apexcharts 為基底的圖表 Vue 元件的架構。

```html
&lt;script setup&gt;
import { computed, ref } from 'vue'
import { useMapStore } from '../../store/mapStore';

// 註冊四個屬性(props)
const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config', 'map_filter'])
const mapStore = useMapStore()

// 選擇性包含
// 部分圖表包含編譯函式以確保圖表間的相容性，使同一份資料能選染多種圖表
const parseSeries = computed(() =&gt; {
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
&lt;/script&gt;

&lt;template&gt;
    &lt;!-- conditionally render the chart --&gt;
    &lt;div v-if=&quot;activeChart === 'GuageChart'&quot;&gt;
        &lt;!-- type: apexcharts 的圖表種類。可能與本專案的命名有些不同。 --&gt;
        &lt;!-- options: 填入 chartOptions 物件 --&gt;
        &lt;!-- series: 填入 series 或 parsed series --&gt;
        &lt;!-- dataPointSelection: 如有地圖篩選功能應包含 --&gt;
        &lt;apexchart 
            width=&quot;80%&quot; 
            height=&quot;300px&quot; 
            type=&quot;radialBar&quot; 
            :options=&quot;chartOptions&quot; 
            :series=&quot;parseSeries.series&quot;
            @dataPointSelection=&quot;handleDataSelection&quot;&gt;
        &lt;/apexchart&gt;
    &lt;/div&gt;
&lt;/template&gt;
```

以下是不使用第三方套件，客製化開發的圖表的Vue元件架構。

```html
&lt;script setup&gt;
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
&lt;/script&gt;

&lt;template&gt;
    &lt;!-- conditionally render the chart --&gt;
    &lt;div v-if=&quot;activeChart === 'MetroChart'&quot; class=&quot;metrochart&quot;&gt;
        &lt;!-- 此圖表 Vue 元件的架構 --&gt;
        &lt;!-- 使用 @click 來導入地圖篩選功能 --&gt;
    &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped lang=&quot;scss&quot;&gt;
.metrochart {
    /* 圖表 Vue 元件的樣式 */
}

/* 建議亦為客製化圖表新增一些出場動畫 */
&lt;/style&gt;
```

## 建立新的圖表類型
首先，決定圖表名稱，然後建立一個遵循圖表 Vue 元件結構的 Vue 元件。如果使用 Apexcharts 來渲染該圖表，亦須填寫相關的圖表選項(`chartOptions`)。

接下來，註冊該圖表，將其添加到 `/src/assets/configs/apexcharts` 中的 `chartTypes.js` 文件的列表中。然後在 `/src` 目錄下的 `main.js` 中將該圖表 Vue 元件註冊為全域 Vue 元件。

最後，在任何組件配置中添加該圖表名稱以渲染它。
