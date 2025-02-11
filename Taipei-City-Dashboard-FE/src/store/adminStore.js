/* eslint-disable indent */

// Developed by Taipei Urban Intelligence Center 2023-2024

/* adminStore */
/*
The adminStore handles actions that are used in the admin pages.
*/
import http from "../router/axios";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
import { useContentStore } from "./contentStore";
import { useAuthStore } from "./authStore";
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";

export const useAdminStore = defineStore("admin", {
	state: () => ({
		// Edit Dashboard (for /admin/dashboard)
		dashboards: [],
		currentDashboard: null,
		// Edit Component (for /admin/edit-component)
		components: [],
		componentResults: 0,
		currentComponent: null,
		// Edit Issue (for /admin/issue)
		issues: [],
		issueResults: 0,
		currentIssue: null,
		// Edit Disaster (for /admin/disaster)
		disasters: [],
		disasterResults: 0,
		currentDisaster: null,
		// Edit User (for /admin/user)
		users: [],
		userResults: 0,
		currentUser: null,
		// Edit Contributor (for /admin/contributor)
		contributors: [],
		contributorResults: 0,
		currentContributor: null,
	}),
	actions: {
		/* Utility functions to access loading and error states in contentStore */
		setLoading(state) {
			const contentStore = useContentStore();
			contentStore.loading = state ? true : false;
		},
		setError(state) {
			const contentStore = useContentStore();
			contentStore.error = state ? true : false;
		},

		/* Dashboard */
		// 1. Get all public dashboards
		async getDashboards() {
			const response = await http.get(`/dashboard/`);
			this.dashboards = response.data.data.public;
			this.setLoading(false);
		},
		// 2. Get current dashboard components
		async getCurrentDashboardComponents() {
			const response = await http.get(
				`/dashboard/${this.currentDashboard.index}`
			);
			this.currentDashboard.components = response.data.data;
			this.setLoading(false);
		},
		// 3. Add a new public dashboard
		async addDashboard() {
			const dialogStore = useDialogStore();

			this.currentDashboard.components =
				this.currentDashboard.components.map((el) => el.id);

			const dashboard = JSON.parse(JSON.stringify(this.currentDashboard));

			await http.post(`/dashboard/public`, dashboard);
			this.getDashboards();
			dialogStore.showNotification("success", "公開儀表板新增成功");
		},
		// 4. Edit a public dashboard
		async editDashboard() {
			const dialogStore = useDialogStore();

			this.currentDashboard.components =
				this.currentDashboard.components.map((el) => el.id);

			const dashboard = JSON.parse(JSON.stringify(this.currentDashboard));

			await http.patch(`/dashboard/${dashboard.index}`, dashboard);
			this.getDashboards();
			dialogStore.showNotification("success", "儀表板更新成功");
		},
		// 5. Delete a public dashboard
		async deleteDashboard() {
			const dialogStore = useDialogStore();

			const dashboardIndex = this.currentDashboard.index;

			await http.delete(`/dashboard/${dashboardIndex}`);
			this.getDashboards();
			dialogStore.showNotification("success", "儀表板刪除成功");
		},

		/* Component */
		// 1. Get all public components
		async getPublicComponents(params) {
			const response = await http.get(`/component/`, {
				params,
			});
			this.components = response.data.data;
			this.componentResults = response.data.results;
			this.setLoading(false);
		},
		// 2. Get component chart / history data and append to component config
		async getComponentData(component) {
			this.currentComponent = JSON.parse(JSON.stringify(component));

			// 2.1 Get component chart data
			const response = await http.get(
				`/component/${component.id}/chart`,
				{
					params: !["static", "current", "demo"].includes(
						component.time_from
					)
						? getComponentDataTimeframe(
								component.time_from,
								component.time_to,
								true
						  )
						: {},
				}
			);
			this.currentComponent.chart_data = response.data.data;
			if (response.data.categories) {
				this.currentComponent.chart_config.categories =
					response.data.categories;
			}

			// 2.2 Get component history data if applicable
			if (component.history_config && component.history_config.range) {
				for (let i in component.history_config.range) {
					const response = await http.get(
						`/component/${component.id}/history`,
						{
							params: getComponentDataTimeframe(
								component.history_config.range[i],
								"now",
								true
							),
						}
					);
					if (i === "0") {
						this.currentComponent.history_data = [];
					}
					this.currentComponent.history_data.push(response.data.data);
				}
			}

			// 2.3 Format component config to ensure compatibility with component editor
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
			this.setLoading(false);
		},
		// 3. Update a public component
		async updateComponent(params) {
			const dialogStore = useDialogStore();

			// 3.1 Format component config to ensure compatibility with backend
			delete this.currentComponent.chart_data;
			delete this.currentComponent.history_data;
			delete this.currentComponent.chart_config.categories;

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
			// 3.2 Update component chart config
			await http.patch(`/component/${componentId}/chart`, chart_config);

			// 3.3 Update component component config (incl. history config)
			await http.patch(`/component/${componentId}`, component_config);

			// 3.4 Update component map config
			if (map_config[0] !== null) {
				for (let i = 0; i < map_config.length; i++) {
					await http.patch(
						`/component/${map_config[i].id}/map`,
						map_config[i]
					);
				}
			}
			dialogStore.showNotification("success", "組件更新成功");
			this.getPublicComponents(params);
		},

		/* Issue */
		// 1. Get all issues
		async getIssues(params) {
			const apiParams = JSON.parse(JSON.stringify(params));

			apiParams.filterbystatus = apiParams.filterbystatus.join(",");

			const response = await http.get(`/issue/`, {
				params: apiParams,
			});
			this.issues = response.data.data;
			this.issueResults = response.data.results;
			this.setLoading(false);
		},
		// 2. Update an issue
		async updateIssue(params) {
			const dialogStore = useDialogStore();
			const authStore = useAuthStore();

			await http.patch(`/issue/${this.currentIssue.id}`, {
				status: this.currentIssue.status,
				decision_desc: this.currentIssue.decision_desc,
				updated_by: authStore.user.name,
			});
			dialogStore.showNotification("success", "問題更新成功");
			this.getIssues(params);
			this.currentIssue = null;
		},

		/* Disaster */
		// 1. Get all disasters
		async getDisasters(params) {
			const apiParams = JSON.parse(JSON.stringify(params));

			apiParams.filterbystatus = apiParams.filterbystatus.join(",");

			const response = await http.get(`/incident/`, {
				params: apiParams,
			});

			this.disasters = response.data.data;
			this.disasterResults = response.data.results;
			this.setLoading(false);
		},
		// 2. Update a disaster
		async updateDisaster(id, disaster, params) {
			const dialogStore = useDialogStore();

			await http.patch(`/incident/${id}`, disaster);

			dialogStore.showNotification("success", "災害更新成功");
			this.getDisasters(params);
			this.currentDisaster = null;
		},
		async deleteDisaster(id, params) {
			const dialogStore = useDialogStore();
			await http.delete(`/incident/`, {
				data: { id: id },
			});
			dialogStore.showNotification("info", "災害刪除成功");
			this.getDisasters(params);
			this.currentDisaster = null;
		},

		/* User */
		// 1. Get all users
		async getUsers(params) {
			const apiParams = JSON.parse(JSON.stringify(params));

			const response = await http.get(`/user/`, {
				params: apiParams,
			});
			this.users = response.data.data;
			this.userResults = response.data.results;
			this.setLoading(false);
		},
		// 2. Update a user
		async updateUser(params) {
			const authStore = useAuthStore();
			const dialogStore = useDialogStore();

			const editedUser = JSON.parse(JSON.stringify(this.currentUser));

			await http.patch(`/user/${this.currentUser.user_id}`, editedUser);
			dialogStore.showNotification("success", "使用者更新成功");
			this.getUsers(params);

			// If the current user updates their own info, refresh the authStore
			if (authStore.user.user_id === this.currentUser.user_id)
				authStore.initialChecks();

			this.currentUser = null;
		},

		/* Contributor */
		// 1. Get all contributors
		async getContributors(params) {
			const apiParams = JSON.parse(JSON.stringify(params));

			const response = await http.get(`/contributor/`, {
				params: apiParams,
			});
			this.contributors = response.data.data;
			this.contributorResults = response.data.total;
			this.setLoading(false);
		},
		// 2. Update a contributor
		async updateContributor(params) {
			const dialogStore = useDialogStore();
			const contentStore = useContentStore();
			const editedContributor = JSON.parse(
				JSON.stringify(this.currentContributor)
			);

			await http.patch(
				`/contributor/${this.currentContributor.id}`,
				editedContributor
			);
			dialogStore.showNotification("success", "貢獻者更新成功");
			this.getContributors(params);

			this.currentContributor = null;
			contentStore.setContributors();
		},
		// 3. Add a contributor
		async addContributor(params) {
			const dialogStore = useDialogStore();
			const contentStore = useContentStore();
			const contributor = JSON.parse(
				JSON.stringify(this.currentContributor)
			);

			await http.post(`/contributor/`, contributor);
			dialogStore.showNotification("success", "貢獻者新增成功");
			this.getContributors(params);

			this.currentContributor = null;
			contentStore.setContributors();
		},

		// 4. Delete a contributor
		async deleteContributor(params) {
			const dialogStore = useDialogStore();

			await http.delete(`/contributor/${this.currentContributor.id}`);
			dialogStore.showNotification("success", "貢獻者刪除成功");
			this.getContributors(params);

			this.currentContributor = null;
		},
	},
});
