// Cleaned

/* authStore */
/*
The authStore stores authentication and user information.
Since this template doesn't implement user authentication, only dummy user info is stored.
If you wish to implement authentication, you can reference the logic below (based on the authentication system of Taipei City Dashboard)
or design a new system from scratch that tailors to your needs. 
*/

import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";

export const useAuthStore = defineStore("auth", {
	state: () => ({
		// This is a shortened version of the user object Taipei City Dashboard's backend will return once authenticated
		user: {
			email: "tuic-admin@gov.taipei",
			gid: 1,
			id: 1,
			name: "儀表板測試者🤩",
			status: 1,
			type: 0,
		},
		tokens: {},
		errorMessage: "",
		isMobileDevice: false,
	}),
	getters: {},
	actions: {
		// Call this function to log in
		handleLogin() {},

		// Call this function to log out (Currently just shows a 'cannot log out' notification)
		handleLogout() {
			const dialogStore = useDialogStore();
			dialogStore.showNotification(
				"fail",
				"尚未新增用戶管理功能，無法登出"
			);
		},

		// If your authentication system supports refresh tokens, call this function to refresh existing tokens
		executeRefreshTokens() {},

		// Call this function to store tokens in the store as well as in localstorage/cookies/etc.
		setTokens() {},

		// Call this function to store user info in the store
		setUser() {},

		// Call this function to clear the entire store
		executeClearStore() {},
		checkIfMobile() {
			if (navigator.maxTouchPoints > 2) {
				this.isMobileDevice = true;
			}
			if (window.matchMedia("(pointer:fine)").matches) {
				this.isMobileDevice = false;
			}
		},
	},
});
