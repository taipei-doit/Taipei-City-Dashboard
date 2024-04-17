 
/* eslint-disable indent */

// Developed by Taipei Urban Intelligence Center 2023-2024

/* contentStore */
/*
The contentStore calls APIs to get content info and stores it.
*/
import { defineStore } from "pinia";
import axios from "axios";
import http from "../router/axios";
import router from "../router/index";
import { useDialogStore } from "./dialogStore";
import { useAuthStore } from "./authStore";
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";

export const useContentStore = defineStore("content", {
	state: () => ({
		// Stores all dashboards data. (used in /dashboard, /mapview)
		publicDashboards: [],
		personalDashboards: [],
		// Stores all components data. (used in /component)
		components: [],
		// Picks out the components that are map layers and stores them here
		mapLayers: [],
		// Picks out the favorites dashboard
		favorites: null,
		// Stores information of the current dashboard
		currentDashboard: {
			// /mapview or /dashboard
			mode: null,
			index: null,
			name: null,
			components: null,
			icon: null,
		},
		// Stores information of a new dashboard or editing dashboard (/component)
		editDashboard: {
			index: "",
			name: "我的新儀表板",
			icon: "star",
			components: [],
		},
		// Stores all contributors data. Reference the structure in /public/dashboards/all_contributors.json
		contributors: {},
		// Stores whether dashboards are loading
		loading: false,
		// Stores whether an error occurred
		error: false,
	}),
	getters: {},
	actions: {
		/* Steps in adding content to the application (/dashboard or /mapview) */
		// 1. Check the current path and execute actions based on the current path
		setRouteParams(mode, index) {
			this.currentDashboard.mode = mode;
			// 1-1. Don't do anything if the path is the same
			if (this.currentDashboard.index === index) {
				if (
					this.currentDashboard.mode === "/mapview" &&
					index !== "map-layers"
				) {
					this.setMapLayers();
				} else {
					return;
				}
			}
			this.currentDashboard.index = index;
			// 1-2. If there is no contributor info, call the setContributors method (5.)
			if (Object.keys(this.contributors).length === 0) {
				this.setContributors();
			}
			// 1-3. If there is no dashboards info, call the setDashboards method (2.)
			if (this.publicDashboards.length === 0) {
				this.setDashboards();
				return;
			}
			// 1-4. If there is dashboard info but no index is defined, call the setDashboards method (2.)
			if (!index) {
				this.setDashboards();
				return;
			}
			// 1-5. If all info is present, skip steps 2, 3, 5 and call the setCurrentDashboardContent method (4.)
			this.currentDashboard.components = [];
			this.setCurrentDashboardContent();
		},
		// 2. Call an API to get all dashboard info and reroute the user to the first dashboard in the list
		async setDashboards(onlyDashboard = false) {
			const response = await http.get(`/dashboard/`);

			this.personalDashboards = response.data.data.personal;
			this.publicDashboards = response.data.data.public;

			if (this.personalDashboards.length !== 0) {
				this.favorites = this.personalDashboards.find(
					(el) => el.icon === "favorite"
				);
				if (!this.favorites.components) {
					this.favorites.components = [];
				}
			}

			if (onlyDashboard) return;

			if (!this.currentDashboard.index) {
				this.currentDashboard.index = this.publicDashboards[0].index;
				router.replace({
					query: {
						index: this.currentDashboard.index,
					},
				});
			}
			// After getting dashboard info, call the setCurrentDashboardContent (3.) method to get component info
			this.setCurrentDashboardContent();
		},
		// 3. Finds the info for the current dashboard based on the index and adds it to "currentDashboard"
		async setCurrentDashboardContent() {
			const allDashboards = this.publicDashboards.concat(
				this.personalDashboards
			);
			const currentDashboardInfo = allDashboards.find(
				(item) => item.index === this.currentDashboard.index
			);
			if (!currentDashboardInfo) {
				router.replace({
					query: {
						index: this.publicDashboards[0].index,
					},
				});
				return;
			}
			this.currentDashboard.name = currentDashboardInfo.name;
			this.currentDashboard.icon = currentDashboardInfo.icon;
			const response = await http.get(
				`/dashboard/${this.currentDashboard.index}`
			);

			if (response.data.data) {
				this.currentDashboard.components = response.data.data;
			} else {
				this.currentDashboard.components = [];
				this.loading = false;
				return;
			}
			this.setCurrentDashboardChartData();
		},
		// 4. Call an API for each component to get its chart data and store it
		// Will call an additional API if the component has history data
		async setCurrentDashboardChartData() {
			// 4-1. Loop through all the components of a dashboard
			for (
				let index = 0;
				index < this.currentDashboard.components.length;
				index++
			) {
				const component = this.currentDashboard.components[index];

				// 4-2. Get chart data
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
				this.currentDashboard.components[index].chart_data =
					response.data.data;

				if (response.data.categories) {
					this.currentDashboard.components[
						index
					].chart_config.categories = response.data.categories;
				}
			}
			for (
				let index = 0;
				index < this.currentDashboard.components.length;
				index++
			) {
				const component = this.currentDashboard.components[index];
				// 4-3. Get history data if applicable
				if (
					component.history_config &&
					component.history_config.range
				) {
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
							this.currentDashboard.components[
								index
							].history_data = [];
						}
						this.currentDashboard.components[
							index
						].history_data.push(response.data.data);
					}
				}
			}
			if (
				this.currentDashboard.mode === "/mapview" &&
				this.currentDashboard.index !== "map-layers"
			) {
				// In /mapview, map layer components are also present and need to be fetched
				this.setMapLayers();
			} else {
				this.loading = false;
			}
		},
		// 5. Call an API to get contributor data (result consists of id, name, link)
		setContributors() {
			axios
				.get(`/dashboards/all_contributors.json`)
				.then((rs) => {
					this.contributors = rs.data.data;
				})
				.catch((e) => console.error(e));
		},
		// 6. Call an API to get map layer component info and store it (if in /mapview)
		async setMapLayers() {
			if (this.mapLayers.length !== 0) {
				return;
			}
			const response = await http.get(`/dashboard/map-layers`);
			this.mapLayers = response.data.data;
			this.setMapLayersContent();
		},
		// 7. Call an API for each map layer component to get its chart data and store it (if in /mapview)
		async setMapLayersContent() {
			for (let index = 0; index < this.mapLayers.length; index++) {
				const component = this.mapLayers[index];

				const response = await http.get(
					`/component/${component.id}/chart`
				);

				this.mapLayers[index].chart_data = response.data.data;
			}
			this.loading = false;
		},

		/* Route Change Methods */
		// 1. Called whenever route changes except for between /dashboard and /mapview
		clearCurrentDashboard() {
			this.currentDashboard = {
				mode: null,
				index: null,
				name: null,
				components: [],
			};
		},

		/* /component methods */
		// 1. Search through all the components (used in /component)
		async getAllComponents(params) {
			const response = await http.get(`/component/`, {
				params,
			});

			this.components = response.data.data;
			this.loading = false;
		},
		// 2. Get the info of a single component (used in /component/:index)
		async getCurrentComponentData(index) {
			const dialogStore = useDialogStore();
			if (Object.keys(this.contributors).length === 0) {
				this.setContributors();
			}

			// 2-1. Get the component config
			const response_1 = await http.get(`/component/`, {
				params: {
					filtermode: "eq",
					filterby: "index",
					filtervalue: index,
				},
			});

			if (response_1.data.results === 0) {
				this.loading = false;
				this.error = true;
				return;
			}

			dialogStore.moreInfoContent = response_1.data.data[0];

			// 2-2. Get the component chart data
			const response_2 = await http.get(
				`/component/${dialogStore.moreInfoContent.id}/chart`,
				{
					params: !["static", "current", "demo"].includes(
						dialogStore.moreInfoContent.time_from
					)
						? getComponentDataTimeframe(
								dialogStore.moreInfoContent.time_from,
								dialogStore.moreInfoContent.time_to,
								true
						  )
						: {},
				}
			);

			dialogStore.moreInfoContent.chart_data = response_2.data.data;

			if (response_2.data.categories) {
				dialogStore.moreInfoContent.chart_config.categories =
					response_2.data.categories;
			}

			// 2-3. Get the component history data if applicable
			if (dialogStore.moreInfoContent.history_config) {
				for (let i in dialogStore.moreInfoContent.history_config
					.range) {
					const response = await http.get(
						`/component/${dialogStore.moreInfoContent.id}/history`,
						{
							params: getComponentDataTimeframe(
								dialogStore.moreInfoContent.history_config
									.range[i],
								"now",
								true
							),
						}
					);

					if (i === "0") {
						dialogStore.moreInfoContent.history_data = [];
					}
					dialogStore.moreInfoContent.history_data.push(
						response.data.data
					);
				}
			}
			this.loading = false;
		},

		/* Common Methods to Edit Dashboards */
		// 0. Call this function to clear the edit dashboard object
		clearEditDashboard() {
			this.editDashboard = {
				index: "",
				name: "我的新儀表板",
				icon: "star",
				components: [],
			};
		},
		// 1. Call this function to create a new dashboard. Pass in the new dashboard name and icon.
		async createDashboard() {
			const dialogStore = useDialogStore();
			const authStore = useAuthStore();

			this.editDashboard.components = this.editDashboard.components.map(
				(item) => item.id
			);
			this.editDashboard.index = "";

			const response = await http.post(`/dashboard/`, this.editDashboard);
			await this.setDashboards(true);

			if (
				authStore.currentPath === "dashboard" ||
				authStore.currentPath === "mapview"
			) {
				router.push({
					name: `${authStore.currentPath}`,
					query: {
						index: response.data.data.index,
					},
				});
			}

			dialogStore.showNotification("success", "成功新增儀表板");
		},
		// 2. Call this function to edit the current dashboard (only personal dashboards)
		async editCurrentDashboard() {
			const dialogStore = useDialogStore();

			this.editDashboard.components = this.editDashboard.components.map(
				(item) => item.id
			);

			await http.patch(
				`/dashboard/${this.editDashboard.index}`,
				this.editDashboard
			);

			dialogStore.showNotification("success", `成功更新儀表板`);

			this.setDashboards();
		},
		// 3. Call this function to delete the current active dashboard.
		async deleteCurrentDashboard() {
			const dialogStore = useDialogStore();

			await http.delete(`/dashboard/${this.currentDashboard.index}`);

			dialogStore.showNotification("success", `成功刪除儀表板`);
			this.setDashboards();
		},
		// 4. Call this function to delete a component in a dashboard.
		async deleteComponent(component_id) {
			const dialogStore = useDialogStore();

			const newComponents = this.currentDashboard.components
				.map((item) => item.id)
				.filter((item) => item !== component_id);

			await http.patch(`/dashboard/${this.currentDashboard.index}`, {
				components: newComponents,
			});
			dialogStore.showNotification("success", `成功刪除組件`);
			this.setDashboards();
		},
		// 5. Call this function to favorite a component.
		async favoriteComponent(component_id) {
			const dialogStore = useDialogStore();
			const authStore = useAuthStore();

			this.favorites.components.push(component_id);

			await http.patch(`/dashboard/${this.favorites.index}`, {
				components: this.favorites.components,
			});
			dialogStore.showNotification("success", `成功加入收藏組件`);

			if (
				authStore.currentPath === "dashboard" ||
				authStore.currentPath === "mapview"
			) {
				this.setDashboards();
			}
		},
		// 6. Call this function to unfavorite a component.
		async unfavoriteComponent(component_id) {
			const dialogStore = useDialogStore();
			const authStore = useAuthStore();

			this.favorites.components = this.favorites.components.filter(
				(item) => item !== component_id
			);

			await http.patch(`/dashboard/${this.favorites.index}`, {
				components: this.favorites.components,
			});
			dialogStore.showNotification("success", `成功從收藏組件移除`);
			if (
				authStore.currentPath === "dashboard" ||
				authStore.currentPath === "mapview"
			) {
				this.setDashboards();
			}
		},
	},
	debounce: {
		favoriteComponent: 500,
		unfavoriteComponent: 500,
	},
});
