/* eslint-disable no-mixed-spaces-and-tabs */
/* eslint-disable indent */
import axios from "axios";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
import { useAuthStore } from "./authStore";
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";
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
		// Edit Issue
		issues: [],
		issueResults: 0,
		currentIssue: null,
	}),
	getters: {},
	actions: {
		// Get all dashboard configs
		async getDashboards() {
			const dialogStore = useDialogStore();

			try {
				const response = await axios.get(`${VITE_API_URL}/dashboard/`);
				this.dashboards = response.data.data;
			} catch (err) {
				console.error(err);
				dialogStore.showDialog("fail", "無法取得儀表板");
			}
		},
		async getCurrentDashboardComponents() {
			const dialogStore = useDialogStore();

			try {
				const response = await axios.get(
					`${VITE_API_URL}/dashboard/${this.currentDashboard.index}`
				);
				this.currentDashboard.components = response.data.data;
			} catch (err) {
				console.error(err);
				dialogStore.showDialog("fail", "無法取得儀表板組件");
			}
		},
		async addDashboard() {
			const dialogStore = useDialogStore();

			this.currentDashboard.components =
				this.currentDashboard.components.map((el) => el.id);

			const dashboard = JSON.parse(JSON.stringify(this.currentDashboard));

			try {
				await axios.post(`${VITE_API_URL}/dashboard/`, dashboard);
				this.getDashboards();
				dialogStore.showNotification("success", "儀表板新增成功");
			} catch (err) {
				console.error(err);
				dialogStore.showNotification("fail", "儀表板新增失敗");
			}
		},
		async editDashboard() {
			const dialogStore = useDialogStore();

			this.currentDashboard.components =
				this.currentDashboard.components.map((el) => el.id);

			const dashboard = JSON.parse(JSON.stringify(this.currentDashboard));

			try {
				await axios.patch(
					`${VITE_API_URL}/dashboard/${dashboard.index}`,
					dashboard
				);
				this.getDashboards();
				dialogStore.showNotification("success", "儀表板更新成功");
			} catch (err) {
				console.error(err);
				dialogStore.showNotification("fail", "儀表板更新失敗");
			}
		},
		async deleteDashboard() {
			const dialogStore = useDialogStore();

			const dashboardIndex = this.currentDashboard.index;

			try {
				await axios.delete(
					`${VITE_API_URL}/dashboard/${dashboardIndex}`
				);
				this.getDashboards();
				dialogStore.showNotification("success", "儀表板刪除成功");
			} catch (err) {
				console.error(err);
				dialogStore.showNotification("fail", "儀表板刪除失敗");
			}
		},
		// Get all component configs
		async getPublicComponents(params) {
			const dialogStore = useDialogStore();

			try {
				const response = await axios.get(`${VITE_API_URL}/component/`, {
					params,
				});
				this.components = response.data.data;
				this.componentResults = response.data.results;
			} catch (err) {
				console.error(err);
				dialogStore.showDialog("fail", "無法取得組件");
			}
		},
		// Get component chart / history data and append to component config
		async getComponentData(component) {
			this.currentComponent = JSON.parse(JSON.stringify(component));
			axios
				.get(`${VITE_API_URL}/component/${component.id}/chart`, {
					headers: !["static", "current", "demo"].includes(
						component.time_from
					)
						? getComponentDataTimeframe(
								component.time_from,
								component.time_to,
								true
						  )
						: {},
				})
				.then((response) => {
					this.currentComponent.chart_data = response.data.data;
				});

			if (component.history_config && component.history_config.range) {
				for (let i in component.history_config.range) {
					await axios
						.get(
							`${VITE_API_URL}/component/${component.id}/history`,
							{
								headers: getComponentDataTimeframe(
									component.history_config.range[i],
									"now",
									true
								),
							}
						)
						.then((rs) => {
							if (i === "0") {
								this.currentComponent.history_data = [];
							}
							this.currentComponent.history_data.push(
								rs.data.data
							);
						})
						.catch((e) => {
							console.error(e);
						});
				}
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
		async getIssues(params) {
			const dialogStore = useDialogStore();
			const apiParams = JSON.parse(JSON.stringify(params));

			apiParams.filterbystatus = apiParams.filterbystatus.join(",");

			try {
				const response = await axios.get(`${VITE_API_URL}/issue/`, {
					params: apiParams,
				});
				this.issues = response.data.data;
				this.issueResults = response.data.results;
			} catch (err) {
				console.error(err);
				dialogStore.showDialog("fail", "無法取得用戶問題");
			}
		},
		async updateIssue(params) {
			const dialogStore = useDialogStore();
			const authStore = useAuthStore();

			try {
				await axios.patch(
					`${VITE_API_URL}/issue/${this.currentIssue.id}`,
					{
						status: this.currentIssue.status,
						decision_desc: this.currentIssue.decision_desc,
						updated_by: authStore.user.name,
					}
				);
				dialogStore.showNotification("success", "問題更新成功");
				this.getIssues(params);
			} catch (err) {
				console.error(err);
				dialogStore.showNotification("fail", "問題更新失敗");
			}

			this.currentIssue = null;
		},
	},
});
