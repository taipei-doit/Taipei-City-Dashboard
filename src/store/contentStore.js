// Cleaned

/* authStore */
/*
The contentStore calls APIs to get content info and stores it.
*/

import router from "../router/index";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
import axios from "axios";
const { BASE_URL } = import.meta.env;

export const useContentStore = defineStore("content", {
	state: () => ({
		// Stores all dashboards data. Reference the structure in /public/dashboards/all_dashboards.json
		dashboards: [],
		// Stores all components data. Reference the structure in /public/dashboards/all_components.json
		components: {},
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
			content: [],
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
		/* Steps in adding content to the application */

		// 1. Check the current path and execute actions based on the current path
		setRouteParams(mode, index) {
			this.error = false;
			this.currentDashboard.mode = mode;
			// 1-1. Don't do anything if the path is the same
			if (this.currentDashboard.index === index) {
				return;
			}
			this.currentDashboard.index = index;
			// 1-2. If there is no contributor info, call the setContributors method (7.)
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
			// 1-5. If all info is present, skip steps 2, 3, 4, 7 and call the setCurrentDashboardContent method (5.)
			this.setCurrentDashboardContent();
		},
		// 2. Call an API to get all dashboard info and reroute the user to the first dashboard in the list
		setDashboards() {
			this.loading = true;
			axios
				.get(`${BASE_URL}/dashboards/all_dashboards.json`)
				.then((rs) => {
					this.dashboards = rs.data.data;
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
					// After getting dashboard info, call the setComponents (3.) method to get component info
					this.setComponents();
				})
				.catch((e) => {
					this.loading = false;
					this.error = true;
					console.error(e);
				});
		},
		// 3. Call and API to get all components info
		setComponents() {
			axios
				.get(`${BASE_URL}/dashboards/all_components.json`)
				.then((rs) => {
					this.components = rs.data.data;
					// Step 4.
					this.setMapLayers();
					// Step 5.
					this.setCurrentDashboardContent();
					this.loading = false;
				})
				.catch((e) => console.error(e));
		},
		// 4. Adds components that are map layers into a separate store to be used in mapview
		setMapLayers() {
			const mapLayerInfo = this.dashboards.find(
				(item) => item.index === "map-layers"
			);
			mapLayerInfo.components.forEach((component) => {
				this.mapLayers.push(this.components[component]);
			});
		},
		// 5. Finds the info for the current dashboard based on the index and adds it to "currentDashboard"
		setCurrentDashboardContent() {
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
			this.currentDashboard.content = currentDashboardInfo.components.map(
				(item) => {
					return this.components[item];
				}
			);
			// no need to call additional chart data APIs for the map layers dashboard
			if (this.currentDashboard.index === "map-layers") {
				return;
			}
			this.setCurrentDashboardChartData();
		},
		// 6. Call an API for each component to get its chart data and store it
		// Will call an additional API if the component has history data
		setCurrentDashboardChartData() {
			this.currentDashboard.content.forEach((component, index) => {
				if (this.currentDashboard.content[index].chart_data) return;
				axios
					.get(`${BASE_URL}/chartData/${component.id}.json`)
					.then((rs) => {
						this.currentDashboard.content[index].chart_data =
							rs.data.data;
					})
					.catch((e) => {
						console.error(e);
					});
				if (this.currentDashboard.content[index].history_data) {
					axios
						.get(`${BASE_URL}/historyData/${component.id}.json`)
						.then((rs) => {
							this.currentDashboard.content[index].history_data =
								rs.data.data;
						})
						.catch((e) => {
							console.error(e);
						});
				}
			});
		},
		// 7. Call an API to get contributor data (result consists of id, name, link)
		setContributors() {
			axios
				.get(`${BASE_URL}/dashboards/all_contributors.json`)
				.then((rs) => {
					this.contributors = rs.data.data;
				})
				.catch((e) => console.error(e));
		},

		/* Dummy Functions to demonstrate the logic of some functions that require a backend */
		// Connect a backend to actually implement the following functions or remove altogether

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
