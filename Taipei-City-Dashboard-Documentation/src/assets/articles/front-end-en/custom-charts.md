## Displaying Charts
As briefly illustrated in [this previous article](/front-end/rendering-strategy), whenever a page is loaded, APIs are called to get component chart data. Once received, the data will be appended to the chart configuration object under the key `"chart_data"` and stored in the `contentStore` so that it’s globally available throughout the application.

### Component Container
The Vue components responsible for rendering charts are `ComponentContainer` and `ComponentMapContainer` respectively for the dashboard view and map view. Both Vue components are located in `/src/components/components`.

If a component contains more than 1 chart type, gray buttons with chart names will appear at the top which will allow the user to switch between chart types. This effect is achieved by storing the currently active chart name in the Vue component rendering it and conditionally rendering the active chart Vue component.

>**w01**
>If you are unfamiliar with the current chart types available and their respective English and Mandarin names, please be sure to read through [this previous article](/front-end/supported-chart-types) before continuing.

>**w02**
>If you are unfamiliar with how Apexcharts works in Vue, please be sure to read through Apexchart's [documentation](https://apexcharts.com/docs/vue-charts/) on the topic before continuing.

### Anatomy of a Chart Vue Component
All chart Vue components accept four props: `“activeChart”`, `“chart_config”`, `“series”`, and `“map_config”`. `activeChart` informs the chart Vue component whether it should be rendered; `chart_config` contains aesthetic details that specify how the chart should be rendered; `series` contains chart data; `"map_config"` allows the chart to control maps attached to the same component; `map_filter` stores additional map filtering configurations.

The following is a breakdown of a typical chart Vue component that is based on apexcharts.
```html
&lt;script setup&gt;
import { computed, ref } from 'vue'
import { useMapStore } from '../../store/mapStore';

// register the four required props
const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config', 'map_filter'])
const mapStore = useMapStore()

// Optional.
// a few charts require this to achieve interoperability between chart types.
const parseSeries = computed(() =&gt; {
    // Parse props.series to compatible format
    ...
    return output
})

// Apexcharts options
const chartOptions = ref({
    chart: {
        ...
    },
    colors: props.chart_config.color,
    labels: props.chart_config.categories ? props.chart_config.categories : [],
    ...
})

// Optional
// Required for charts that support map filtering
const selectedIndex = ref(null)

function handleDataSelection(e, chartContext, config) {
    // Refer to the codebase for the complete function
    ...
}
&lt;/script&gt;

&lt;template&gt;
    &lt;!-- conditionally render the chart --&gt;
    &lt;div v-if=&quot;activeChart === 'GuageChart'&quot;&gt;
        &lt;!-- type: apexcharts chart type. May differ from chart name in this project --&gt;
        &lt;!-- options: pass in chartOptions --&gt;
        &lt;!-- series: pass in series or parsed series --&gt;
        &lt;!-- dataPointSelection: if map filtering is supported --&gt;
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

The following is a breakdown of a typical chart Vue component that is custom-built and doesn’t use third-party libraries.

```html
&lt;script setup&gt;
import { computed, ref } from 'vue'
import { useMapStore } from '../../store/mapStore';

// register the four required props
const props = defineProps(['chart_config', 'activeChart', 'series', 'map_config'])
const mapStore = useMapStore()

// Optional
// Required for charts that support map filtering
const selectedIndex = ref(null)

function handleDataSelection(index) {
    // Refer to the codebase for the complete function
    ...
}
&lt;/script&gt;

&lt;template&gt;
    &lt;!-- conditionally render the chart --&gt;
    &lt;div v-if=&quot;activeChart === 'MetroChart'&quot; class=&quot;metrochart&quot;&gt;
        &lt;!-- The layout of the chart Vue component --&gt;
        &lt;!-- Utilize the @click event listener to enable map filtering by data selection --&gt;
    &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped lang=&quot;scss&quot;&gt;
.metrochart {
    /* styles for the chart Vue component */
}

/* Animation styles aren't required but recommended */
&lt;/style&gt;
```

## Create a New Chart Type
First, decide on a chart name and create a Vue component following the anatomy of a chart Vue component. If the chart is rendered using Apexcharts, be sure to also fill in relevant chart option settings. 

Next, register the chart by adding it to the list in the file `chartTypes.js` in `/src/assets/configs/apexcharts`. And then register the chart Vue component as a global Vue component in `main.js` located in `/src`.

Finally, add the chart name to any component configuration to render it.
