// Developed by Taipei Urban Intelligence Center 2023-2024

/* themeStore — 淺色／深色介面，偏好存於 localStorage */

import { defineStore } from "pinia";

const STORAGE_KEY = "tcd-theme";

export const useThemeStore = defineStore("theme", {
	state: () => ({
		theme: "dark",
	}),
	getters: {
		isLight: (s) => s.theme === "light",
	},
	actions: {
		init() {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved === "light" || saved === "dark") {
				this.theme = saved;
			}
			this.apply();
		},
		setTheme(theme) {
			if (theme !== "light" && theme !== "dark") return;
			this.theme = theme;
			localStorage.setItem(STORAGE_KEY, theme);
			this.apply();
		},
		toggle() {
			this.setTheme(this.theme === "dark" ? "light" : "dark");
		},
		apply() {
			document.documentElement.setAttribute("data-theme", this.theme);
		},
	},
});
