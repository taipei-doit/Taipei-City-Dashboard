import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
	state: () => ({
		mode: localStorage.getItem("mode") || "light",
		lang: localStorage.getItem("lang") || "ch",
		docs: null,
		sidebar: false,
		isMobileDevice: false,
	}),
	getters: {},
	actions: {
		toggleMode() {
			this.mode = this.mode === "dark" ? "light" : "dark";
			localStorage.setItem("mode", this.mode);
		},
		toggleLang(lang) {
			this.lang = lang;
			document.title =
				this.lang === "en"
					? "Docs | Taipei City Dashboard"
					: "文件｜城市聯合儀表板";
		},
		toggleSidebar(mode) {
			this.sidebar = mode;
		},
		checkIfMobile() {
			if (navigator.maxTouchPoints > 2) {
				this.isMobileDevice = true;
			}
		},
	},
});
