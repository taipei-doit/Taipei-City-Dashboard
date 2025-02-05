/* eslint-disable indent */
// Developed by Taipei Urban Intelligence Center 2023-2024

// This file centrally handles all axios requests made in the application.

import axios from "axios";
import { usePersonStore } from "../store/personStore.js";
import { useDialogStore } from "../store/dialogStore";
import { useContentStore } from "../store/contentStore";
import { DataManager } from "../assets/utilityFunctions/dataManager.js";

const http = axios.create({
	baseURL: import.meta.env.VITE_API_URL,
	headers: {
		"Content-Type": "application/json",
	},
});

// Request Handler
http.interceptors.request.use((request) => {
	const personStore = usePersonStore();
	const contentStore = useContentStore();

	contentStore.loading = true;
	contentStore.error = false;

	if (personStore.code) {
		request.headers.setAuthorization(`Bearer ${personStore.code}`);
	} else {
		request.headers.setAuthorization(`Bearer`);
	}
	return request;
});

// Response Handler
http.interceptors.response.use(
	(response) => {
		// handle loading directly in request since sometimes requests are stringed together
		const personStore = usePersonStore();
		const dataManager = new DataManager(response.data);

		if (dataManager.getData("data")) {
			personStore.code = dataManager.getData("data");
			localStorage.setItem("code", personStore.code);
		}
		return response;
	},
	(error) => {
		const dialogStore = useDialogStore();
		const personStore = usePersonStore();
		const contentStore = useContentStore();

		contentStore.error = true;
		contentStore.loading = false;

		switch (error.response.status) {
			case 401:
				if (personStore.code) {
					dialogStore.showNotification(
						"fail",
						"401，登入逾時，請重新登入"
					);
					personStore.handleLogout();
				} else {
					dialogStore.showNotification(
						"fail",
						"登入錯誤，請確認帳號密碼是否正確"
					);
				}
				break;
			case 403:
				if (personStore.code) {
					dialogStore.showNotification(
						"fail",
						"403，沒有權限執行此動作"
					);
				}
				break;
			case 429:
				dialogStore.showNotification(
					"fail",
					"429，請求過於頻繁，請稍後再試"
				);
				break;
			case 500:
				dialogStore.showNotification(
					"fail",
					"500，伺服器錯誤，動作無法完成"
				);
				break;
			default:
				dialogStore.showNotification(
					"fail",
					`${error.response.status}，${error.response.data.message}`
				);
				break;
		}
		return Promise.reject(error);
	}
);

export default http;
