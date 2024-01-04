import axios from "axios";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
const { VITE_API_URL } = import.meta.env;

export const useAdminStore = defineStore("admin", {
	state: () => ({
		// Edit Component
		components: [],
		componentResults: 0,
		currentComponent: null,
	}),
	getters: {},
	actions: {
		// Get all component configs
		getPublicComponents(params) {
			const dialogStore = useDialogStore();

			axios
				.get(`${VITE_API_URL}/component/`, {
					params,
				})
				.then((response) => {
					this.components = response.data.data;
					this.componentResults = response.data.results;
				})
				.catch((err) => {
					console.error(err);
					dialogStore.showDialog("fail", "無法取得組件");
				});
		},
		// Get component chart / history data and append to component config
		getComponentData(component) {
			this.currentComponent = JSON.parse(JSON.stringify(component));

			axios
				.get(`${VITE_API_URL}/component/${component.id}/chart`)
				.then((response) => {
					this.currentComponent.chart_data = response.data.data;
				});

			if (component.history_config) {
				axios
					.get(`${VITE_API_URL}/component/${component.id}/history`)
					.then((response) => {
						this.currentComponent.history_data = response.data.data;
					});
			}

			if (!this.currentComponent.links) this.currentComponent.links = [];
			if (!this.currentComponent.chart_config?.color)
				this.currentComponent.chart_config.color = [];
		},
	},
});
