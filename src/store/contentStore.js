/* eslint-disable no-mixed-spaces-and-tabs */
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
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";
const { BASE_URL } = import.meta.env;

export const useContentStore = defineStore("content", {
	state: () => ({
		// Stores all dashboards data. (used in /dashboard, /mapview)
		dashboards: [],
		// Stores all components data. (used in /component)
		components: [],
		// Picks out the components that are map layers and stores them here
		mapLayers: [],
		// Picks out the components that are favorites and stores them here
		favorites: [],
		// Stores information of the current dashboard
		currentDashboard: {
			// /mapview or /dashboard
			mode: null,
			index: null,
			name: null,
			components: null,
		},
		// Stores information of a new dashboard or editting dashboard (/component)
		editDashboard: {
			index: "",
			name: "",
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
			if (this.dashboards.length === 0) {
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
			this.mapLayers = [];
			this.setCurrentDashboardContent();
		},
		// 2. Call an API to get all dashboard info and reroute the user to the first dashboard in the list
		async setDashboards() {
			const response = await http.get(`/dashboard/`);

			this.dashboards = response.data.data;
			if (!this.currentDashboard.index) {
				this.currentDashboard.index = this.dashboards[0].index;
				router.replace({
					query: {
						index: this.currentDashboard.index,
					},
				});
			}
			// Pick out the list of favorite components
			const favorites = this.dashboards.find(
				(item) => item.index === "favorites"
			);
			this.favorites = [...favorites.components];
			// After getting dashboard info, call the setCurrentDashboardContent (3.) method to get component info
			this.setCurrentDashboardContent();
		},
		// 3. Finds the info for the current dashboard based on the index and adds it to "currentDashboard"
		async setCurrentDashboardContent() {
			const currentDashboardInfo = this.dashboards.find(
				(item) => item.index === this.currentDashboard.index
			);
			if (!currentDashboardInfo) {
				router.replace({
					query: {
						index: this.dashboards[0].index,
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
						headers: !["static", "current", "demo"].includes(
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

				// 4-3. Get history data if applicable
				if (
					component.history_config &&
					component.history_config.range
				) {
					for (let i in component.history_config.range) {
						const response = await http.get(
							`/component/${component.id}/history`,
							{
								headers: getComponentDataTimeframe(
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
				.get(`${BASE_URL}/dashboards/all_contributors.json`)
				.then((rs) => {
					this.contributors = rs.data.data;
				})
				.catch((e) => console.error(e));
		},
		// 6. Call an API to get map layer component info and store it (if in /mapview)
		async setMapLayers() {
			const resposne = await http.get(`/dashboard/map-layers`);
			this.mapLayers = resposne.data.data;
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
					headers: !["static", "current", "demo"].includes(
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

			// 2-3. Get the component history data if applicable
			if (dialogStore.moreInfoContent.history_config) {
				for (let i in dialogStore.moreInfoContent.history_config
					.range) {
					const response = await http.get(
						`/component/${dialogStore.moreInfoContent.id}/history`,
						{
							headers: getComponentDataTimeframe(
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
		// Call this function to create a new dashboard. Pass in the new dashboard name and icon.
		createNewDashboard(name, index, icon) {
			const dialogStore = useDialogStore();

			this.dashboards.push({
				name: name,
				index: index,
				components: [],
				icon: icon,
			});

			router.replace({
				query: {
					index: index,
				},
			});

			dialogStore.showNotification(
				"success",
				`成功加入${name}儀表板（因爲是展示版，僅暫存）`
			);
		},
		// Call this function to change the dashboard name. Pass in the new dashboard name.
		changeCurrentDashboardName(name) {
			const dialogStore = useDialogStore();

			this.currentDashboard.name = name;
			this.dashboards.forEach((item) => {
				if (item.index === this.currentDashboard.index) {
					item.name = name;
				}
			});

			dialogStore.showNotification(
				"success",
				`成功更改儀表板名稱至${name}（因爲是展示版，僅暫存）`
			);
		},
		// Call this function to delete the current active dashboard.
		deleteCurrentDashboard() {
			const dialogStore = useDialogStore();

			if (this.dashboards.length <= 3) {
				dialogStore.showNotification("fail", `應至少保有一個儀表板`);
				return;
			}

			this.dashboards = this.dashboards.filter(
				(item) => item.index !== this.currentDashboard.index
			);
			router.replace({
				query: {
					index: this.dashboards[0].index,
				},
			});

			dialogStore.showNotification(
				"success",
				`成功刪除儀表板（因爲是展示版，僅暫存）`
			);
		},
		// Call this function to delete a component. Pass in related info.
		deleteComponent(component_id) {
			const dialogStore = useDialogStore();

			this.dashboards.forEach((item) => {
				if (item.index === this.currentDashboard.index) {
					item.components = item.components.filter(
						(element) => +element !== component_id
					);
				}
			});

			this.setCurrentDashboardContent();

			if (this.currentDashboard.index === "favorites") {
				this.favorites = this.favorites.filter(
					(item) => +item !== component_id
				);
				dialogStore.showNotification(
					"success",
					`成功從收藏移除（因爲是展示版，僅暫存）`
				);
			} else {
				dialogStore.showNotification(
					"success",
					`成功刪除組件（因爲是展示版，僅暫存）`
				);
			}
		},
		// Call this function to add components to the current dashboard. Pass in an array of component ids.
		addComponents(component_ids) {
			const dialogStore = useDialogStore();

			this.dashboards.forEach((item) => {
				if (item.index === this.currentDashboard.index) {
					item.components = item.components.concat(component_ids);
				}
			});
			this.setCurrentDashboardContent();

			dialogStore.showNotification(
				"success",
				`成功加入組件（因爲是展示版，僅暫存）`
			);
		},
		favoriteComponent(component_id) {
			const dialogStore = useDialogStore();

			this.favorites.push(component_id.toString());
			this.dashboards.forEach((item) => {
				if (item.index === "favorites") {
					item.components.push(component_id.toString());
				}
			});

			dialogStore.showNotification(
				"success",
				`成功加入收藏（因爲是展示版，僅暫存）`
			);
		},
		unfavoriteComponent(component_id) {
			const dialogStore = useDialogStore();

			this.favorites = this.favorites.filter(
				(item) => +item !== component_id
			);
			this.dashboards.forEach((item) => {
				if (item.index === "favorites") {
					item.components = item.components.filter(
						(item) => +item !== component_id
					);
				}
			});
			dialogStore.showNotification(
				"success",
				`成功從收藏移除（因爲是展示版，僅暫存）`
			);
		},
	},
});
