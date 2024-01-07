import axios from "axios";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
const { VITE_API_URL } = import.meta.env;

export const useAdminStore = defineStore("admin", {
	state: () => ({
		// Edit Dashboard
		dashboards: [],
		currentDashboard: null,
		// Edit Component
		components: [],
		componentResults: 0,
		currentComponent: null,
	}),
	getters: {},
	actions: {
		// Get all dashboard configs
		getDashboards() {
			const dialogStore = useDialogStore();

			axios
				.get(`${VITE_API_URL}/dashboard/`)
				.then((response) => {
					this.dashboards = response.data.data;
				})
				.catch((err) => {
					console.error(err);
					dialogStore.showDialog("fail", "無法取得儀表板");
				});
		},
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
			if (!this.currentComponent.chart_config?.color) {
				this.currentComponent.chart_config.color = [];
			}

			if (this.currentComponent.history_config !== null) {
				if (!this.currentComponent.history_config?.color) {
					this.currentComponent.history_config.color = [];
				}
			}

			if (this.currentComponent.map_config[0] !== null) {
				this.currentComponent.map_config.forEach((map_config) => {
					map_config.paint = JSON.stringify(
						map_config.paint,
						undefined,
						2
					);
					map_config.property = JSON.stringify(
						map_config.property,
						undefined,
						2
					);
				});
			}
			if (this.currentComponent.map_filter !== null) {
				this.currentComponent.map_filter = JSON.stringify(
					this.currentComponent.map_filter,
					undefined,
					2
				);
			}
		},
		async updateComponent(params) {
			const dialogStore = useDialogStore();

			delete this.currentComponent.chart_data;
			delete this.currentComponent.history_data;

			const chart_config = JSON.parse(
				JSON.stringify(this.currentComponent.chart_config)
			);
			if (this.currentComponent.map_filter !== null) {
				this.currentComponent.map_filter = JSON.parse(
					this.currentComponent.map_filter
				);
			}

			if (this.currentComponent.map_config[0] !== null) {
				this.currentComponent.map_config.forEach((map_config) => {
					map_config.paint = JSON.parse(map_config.paint);
					map_config.property = JSON.parse(map_config.property);
				});
			}
			const map_config = JSON.parse(
				JSON.stringify(this.currentComponent.map_config)
			);

			delete this.currentComponent.chart_config;
			delete this.currentComponent.map_config;

			const componentId = this.currentComponent.id;
			const component_config = JSON.parse(
				JSON.stringify(this.currentComponent)
			);
			try {
				await axios.patch(
					`${VITE_API_URL}/component/${componentId}/chart`,
					chart_config
				);
				await axios.patch(
					`${VITE_API_URL}/component/${componentId}`,
					component_config
				);
				if (map_config[0] !== null) {
					for (let i = 0; i < map_config.length; i++) {
						await axios.patch(
							`${VITE_API_URL}/component/${map_config[i].index}/map`,
							map_config[i]
						);
					}
				}
				dialogStore.showNotification("success", "組件更新成功");
				this.getPublicComponents(params);
			} catch (err) {
				console.error(err);
				dialogStore.showNotification("fail", "組件更新失敗");
			}
		},
	},
});
