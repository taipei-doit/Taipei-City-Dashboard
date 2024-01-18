/* eslint-disable no-mixed-spaces-and-tabs */
/* eslint-disable indent */
// Cleaned

/* authStore */
/*
The contentStore calls APIs to get content info and stores it.
*/

import router from "../router/index";
import { defineStore } from "pinia";
import { useDialogStore } from "./dialogStore";
import axios from "axios";
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";
const { BASE_URL, VITE_API_URL } = import.meta.env;

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
		// Stores information of a new dashboard (/component)
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
		/* Steps in adding content to the application */

		// 1. Check the current path and execute actions based on the current path
		setRouteParams(mode, index) {
			this.error = false;
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
		setDashboards() {
			this.loading = true;
			axios
				.get(`${VITE_API_URL}/dashboard/`)
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
					// After getting dashboard info, call the setCurrentDashboardContent (3.) method to get component info
					this.setCurrentDashboardContent();
				})
				.catch((e) => {
					this.loading = false;
					this.error = true;
					console.error(e);
				});
		},
		// 3. Finds the info for the current dashboard based on the index and adds it to "currentDashboard"
		setCurrentDashboardContent() {
			this.loading = true;
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
			axios
				.get(`${VITE_API_URL}/dashboard/${this.currentDashboard.index}`)
				.then((rs) => {
					if (rs.data.data) {
						this.currentDashboard.components = rs.data.data;
					} else {
						this.currentDashboard.components = [];
						this.loading = false;
						return;
					}
					this.setCurrentDashboardChartData();
				})
				.catch((e) => {
					this.loading = false;
					this.error = true;
					console.error(e);
				});
		},
		// 4. Call an API for each component to get its chart data and store it
		// Will call an additional API if the component has history data
		async setCurrentDashboardChartData() {
			for (
				let index = 0;
				index < this.currentDashboard.components.length;
				index++
			) {
				const component = this.currentDashboard.components[index];
				if (component.chart_data) return;

				await axios
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
					.then((rs) => {
						this.currentDashboard.components[index].chart_data =
							rs.data.data;
					})
					.catch((e) => {
						console.error(e);
					});
				if (
					component.history_config &&
					component.history_config.range
				) {
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
									this.currentDashboard.components[
										index
									].history_data = [];
								}
								this.currentDashboard.components[
									index
								].history_data.push(rs.data.data);
							})
							.catch((e) => {
								console.error(e);
							});
					}
				}
			}
			if (
				this.currentDashboard.mode === "/mapview" &&
				this.currentDashboard.index !== "map-layers"
			) {
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
		setMapLayers() {
			this.loading = true;
			axios
				.get(`${VITE_API_URL}/dashboard/map-layers`)
				.then((rs) => {
					this.mapLayers = rs.data.data;
					this.setMapLayersContent();
				})
				.catch((e) => {
					this.error = true;
					console.error(e);
				});
		},
		// 7. Call an API for each map layer component to get its chart data and store it (if in /mapview)
		async setMapLayersContent() {
			for (let index = 0; index < this.mapLayers.length; index++) {
				const component = this.mapLayers[index];

				await axios
					.get(`${VITE_API_URL}/component/${component.id}/chart`)
					.then((rs) => {
						this.mapLayers[index].chart_data = rs.data.data;
					})
					.catch((e) => {
						console.error(e);
					});
			}
			this.loading = false;
		},
		clearCurrentDashboard() {
			this.currentDashboard = {
				mode: null,
				index: null,
				name: null,
				components: [],
			};
		},
		/* /component methods */
		async getAllComponents(params) {
			this.error = false;
			this.loading = true;
			try {
				const response = await axios.get(`${VITE_API_URL}/component/`, {
					params,
				});

				this.components = response.data.data;
				this.loading = false;
			} catch {
				this.loading = false;
				this.error = true;
			}
		},
		async getCurrentComponentData(index) {
			const dialogStore = useDialogStore();
			if (Object.keys(this.contributors).length === 0) {
				this.setContributors();
			}
			this.error = false;
			this.loading = true;

			try {
				const response = await axios.get(`${VITE_API_URL}/component/`, {
					params: {
						filtermode: "eq",
						filterby: "index",
						filtervalue: index,
					},
				});

				dialogStore.moreInfoContent = response.data.data[0];
			} catch {
				this.loading = false;
				this.error = true;
			}

			try {
				const response = await axios.get(
					`${VITE_API_URL}/component/${dialogStore.moreInfoContent.id}/chart`,
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

				dialogStore.moreInfoContent.chart_data = response.data.data;
			} catch {
				this.loading = false;
				this.error = true;
			}

			if (dialogStore.moreInfoContent.history_config) {
				for (let i in dialogStore.moreInfoContent.history_config
					.range) {
					try {
						const response = await axios.get(
							`${VITE_API_URL}/component/${dialogStore.moreInfoContent.id}/history`,
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
					} catch {
						this.loading = false;
						this.error = true;
					}
				}
			}
			this.loading = false;
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
