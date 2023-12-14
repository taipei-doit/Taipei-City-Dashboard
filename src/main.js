/* Developed By Taipei Urban Intelligence Center 2023 */

// Lead Developer:  Igor Ho (FE Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Systems: Ann Shih (Systems Engineer)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)

/* Department of Information Technology, Taipei City Government */

// Import the Essentials
import { createApp } from "vue";
import "./assets/styles/globalStyles.css";
import "./assets/styles/chartStyles.css";
import "./assets/styles/toggleswitch.css";
import App from "./App.vue";

// Import Core Packages: Vue-Router, Pinia, Apexcharts
import router from "./router";
import { createPinia } from "pinia";
import VueApexCharts from "vue3-apexcharts";

// Import Global Components
import DistrictChart from "./components/charts/DistrictChart.vue";
import DonutChart from "./components/charts/DonutChart.vue";
import BarChart from "./components/charts/BarChart.vue";
import TreemapChart from "./components/charts/TreemapChart.vue";
import ColumnChart from "./components/charts/ColumnChart.vue";
import BarPercentChart from "./components/charts/BarPercentChart.vue";
import GuageChart from "./components/charts/GuageChart.vue";
import RadarChart from "./components/charts/RadarChart.vue";
import TimelineSeparateChart from "./components/charts/TimelineSeparateChart.vue";
import TimelineStackedChart from "./components/charts/TimelineStackedChart.vue";
import MapLegend from "./components/charts/MapLegend.vue";
import MetroChart from "./components/charts/MetroChart.vue";
import HeatmapChart from "./components/charts/HeatmapChart.vue";
import PolarAreaChart from "./components/charts/PolarAreaChart.vue";
import ColumnLineChart from "./components/charts/ColumnLineChart.vue";
import BarChartWithGoal from "./components/charts/BarChartWithGoal.vue";
import IconPercentChart from "./components/charts/IconPercentChart.vue";

const app = createApp(App);

// Add Core Packages: Vue-Router, Pinia, Apexcharts
app.use(router);
const pinia = createPinia();
app.use(pinia);
app.use(VueApexCharts);

app.component("DistrictChart", DistrictChart);
app.component("DonutChart", DonutChart);
app.component("BarChart", BarChart);
app.component("TreemapChart", TreemapChart);
app.component("ColumnChart", ColumnChart);
app.component("BarPercentChart", BarPercentChart);
app.component("GuageChart", GuageChart);
app.component("RadarChart", RadarChart);
app.component("TimelineSeparateChart", TimelineSeparateChart);
app.component("TimelineStackedChart", TimelineStackedChart);
app.component("MapLegend", MapLegend);
app.component("MetroChart", MetroChart);
app.component("HeatmapChart", HeatmapChart);
app.component("PolarAreaChart", PolarAreaChart);
app.component("ColumnLineChart", ColumnLineChart);
app.component("BarChartWithGoal", BarChartWithGoal);
app.component("IconPercentChart", IconPercentChart);

app.mount("#app");
