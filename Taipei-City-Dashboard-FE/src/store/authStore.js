// Developed by Taipei Urban Intelligence Center 2023-2024

/* authStore */
/*
The authStore stores authentication and user information.
*/

import { defineStore } from "pinia";
import http from "../router/axios";
import { useDialogStore } from "./dialogStore";
import { useContentStore } from "./contentStore";
import router from "../router/index";

export const useAuthStore = defineStore("auth", {
	state: () => ({
		// This is a shortened version of the user object Taipei City Dashboard's backend will return once authenticated
		user: {
			user_id: null,
			account: "",
			name: "",
			is_active: null,
			is_whitelist: null,
			is_blacked: null,
			login_at: null,
			isAdmin: false,
		},
		editUser: {},
		token: null,
		errorMessage: "",
		isMobileDevice: false,
		isNarrowDevice: false,
		currentPath: "",
	}),
	getters: {},
	actions: {
		/* Authentication Functions */
		// Initial Checks
		async initialChecks() {
			// Check if the user is using a mobile device
			this.checkIfMobile();

			// Check if the user is logged in
			if (localStorage.getItem("token")) {
				this.token = localStorage.getItem("token");
				this.user = JSON.parse(localStorage.getItem("user"));
				this.editUser = JSON.parse(localStorage.getItem("user"));
			}
		},
		// Email Login
		async loginByEmail(email, password) {
			const response = await http.post(
				"/auth/login",
				{},
				{
					auth: {
						username: email,
						password: password,
					},
				}
			);
			this.handleSuccessfullLogin(response);
		},
		async loginByTaipeiPass(code) {
			try {
				const response = await http.get("/auth/callback", {
					params: {
						code: code,
					},
				});
				router.replace("/dashboard");
				this.handleSuccessfullLogin(response);
			} catch {
				router.replace("/dashboard");
			}
		},
		handleSuccessfullLogin(response) {
			const dialogStore = useDialogStore();
			const contentStore = useContentStore();

			this.token = response.data.token;
			localStorage.setItem("token", this.token);
			this.user = {
				user_id: response.data.user.user_id,
				account: response.data.user.account,
				name: response.data.user.name,
				is_active: response.data.user.is_active.Bool,
				is_whitelist: response.data.user.is_whitelist.Bool,
				is_blacked: response.data.user.is_blacked.Bool,
				login_at: response.data.user.login_at,
				isAdmin: response.data.user.is_admin
			};
			this.editUser = this.user;
			localStorage.setItem("user", JSON.stringify(this.user));

			contentStore.publicDashboards = [];
			router.go();
			dialogStore.showNotification("success", "登入成功");
		},

		// Logout
		handleLogout() {
			const dialogStore = useDialogStore();
			const contentStore = useContentStore();

			localStorage.removeItem("token");
			localStorage.removeItem("user");
			this.user = {};
			this.editUser = {};
			this.token = null;

			contentStore.publicDashboards = [];
			router.go();
			dialogStore.showNotification("success", "登出成功");
		},

		// If your authentication system supports refresh tokens, call this function to refresh existing tokens
		executeRefreshTokens() {},

		/* Other Utility Functions */
		// 1. Check if the user is using a mobile device.
		// This is used to determine whether to show the mobile version of the dashboard.
		checkIfMobile() {
			if (navigator.maxTouchPoints > 2) {
				this.isMobileDevice = true;
			}
			if (window.matchMedia("(pointer:fine)").matches) {
				this.isMobileDevice = false;
			}
			if (window.screen.width < 750) {
				this.isNarrowDevice = true;
			}
		},
		// 2. Set the current path of the user
		setCurrentPath(path) {
			this.currentPath = path;
		},
	},
});
