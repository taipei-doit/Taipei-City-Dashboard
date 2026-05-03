import { createApp } from "vue";
import "./assets/styles/globalStyles.css";
import "./assets/styles/toggleswitch.css";
import "highlight.js/styles/foundation.css";
import "city-dashboard-component/style.css";
import App from "./App.vue";

import router from "./router";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import { en } from "./assets/lang/en";
import { ch } from "./assets/lang/ch";

const app = createApp(App);

app.use(router);
const pinia = createPinia();
app.use(pinia);
const i18n = createI18n({
	locale: "ch",
	allowComposition: true,
	messages: {
		en: en,
		ch: ch,
	},
});
app.use(i18n);

app.mount("#app");
