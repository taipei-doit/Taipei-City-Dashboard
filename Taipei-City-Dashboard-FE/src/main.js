/* Developed By Taipei Urban Intelligence Center 2023-2024 */

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Systems & Auth: Ann Shih (Systems Engineer)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)

/* Department of Information Technology, Taipei City Government */

// Import the Essentials
import { createApp } from "vue";
import "./assets/styles/globalStyles.css";
import "./assets/styles/chartStyles.css";
import "./assets/styles/toggleswitch.css";
import "city-dashboard-component/style.css";
import App from "./App.vue";

// Import Core Packages: Vue-Router, Pinia, Apexcharts
import router from "./router";
import { createPinia } from "pinia";
import VueApexCharts from "vue3-apexcharts";
import debounce from "lodash/debounce";

const app = createApp(App);

// Add Core Packages: Vue-Router, Pinia, Apexcharts
app.use(router);
const pinia = createPinia();
pinia.use(({ options, store }) => {
	if (options.debounce) {
		return Object.keys(options.debounce).reduce(
			(debouncedActions, action) => {
				debouncedActions[action] = debounce(
					store[action],
					options.debounce[action]
				);
				return debouncedActions;
			},
			{}
		);
	}
});

app.use(pinia);
app.use(VueApexCharts);

app.mount("#app");
