/* eslint-disable indent */

// Developed by Taipei Urban Intelligence Center 2023-2024

/* contentStore */
/*
The contentStore calls APIs to get content info and stores it.
*/
import { defineStore } from "pinia";
import http from "../router/axios";
import router from "../router/index";
import { useDialogStore } from "./dialogStore";
import { useAuthStore } from "./authStore";
import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";

export const useContentStore = defineStore("content", {
	state: () => ({
		// stores select options for city
		cityList: [
			{ name: "台北市", value: "taipei" },
			// { name: "新北市", value: "newtaipei" },
			{ name: "雙北", value: "metrotaipei" },
		],
		// Stores all dashboards data. (used in /dashboard, /mapview)
		publicDashboards: [],
		taipeiDashboards: [],
		metroTaipeiDashboards: [],
		personalDashboards: [],
		// Stores all components data. (used in /component)
		components: [],
		// Picks out the components that are map layers and stores them here
		mapLayers: [],
		taipeiMapLayers: [],
		metroTaipeiMapLayers: [],
		allMapLayers: [],
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
			city: null,
		},
		// Stores information of the current dashboard duplicated id data
		currentDashboardExcluded: {
			components: null,
		},
		// Stores information of the city dashboard
		cityDashboard: {
			components: null,
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
		ws: false,
	}),
	getters: {},
	actions: {
		setComponentData(index, component) {
			this.currentDashboard.components[index] = component;
		},
		setMapLayerData(index, component) {
			this.mapLayers[index] = component;
		},
		/* Steps in adding content to the application (/dashboard or /mapview) */
		// 1. Check the current path and execute actions based on the current path
		setRouteParams(mode, index, city) {
			this.currentDashboard.mode = mode;
			// 1-1. Don't do anything if the path is the same
			if (this.currentDashboard.index === index && this.currentDashboard.city === city) {
				if (
					this.currentDashboard.mode === "/mapview" &&
					index !== "map-layers"
				) {
					this.setMapLayers(city);
				} else {
					return;
				}
			}
			this.currentDashboard.city = city;
			this.currentDashboard.index = index;
			// 1-2. If there is no contributor info, call the setContributors method (5.)
			// if (Object.keys(this.contributors).length === 0) {
			// 	this.setContributors();
			// }
			// 1-3. If there is no dashboards info, call the setDashboards method (2.)
			if (this.taipeiDashboards.length === 0) {
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
			this.storeCurrentDashboardAllContentAndChartData();
			this.setCurrentDashboardContent();
		},
		// 2. Call an API to get all dashboard info and reroute the user to the first dashboard in the list
		async setDashboards(onlyDashboard = false) {
			const response = await http.get(`/dashboard/`);

			// Helper function to move map-layers to end
			const moveMapLayersToEnd = (array) => {
				if (!array || !Array.isArray(array)) return array;
				const mapLayersItem = array.find(item => item.index === 'map-layers');
				if (!mapLayersItem) return array;
				const otherItems = array.filter(item => item.index !== 'map-layers');
				return [...otherItems, mapLayersItem];
			};

			this.personalDashboards = response.data.data?.personal || [];
			this.publicDashboards = response.data.data?.public || [];
			this.taipeiDashboards = moveMapLayersToEnd(response.data.data?.taipei) || [];
			this.metroTaipeiDashboards = moveMapLayersToEnd(response.data.data?.metrotaipei) || [];

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
				this.currentDashboard.index = this.taipeiDashboards[0].index;
				this.currentDashboard.city = "taipei";
				router.replace({
					query: {
						index: this.currentDashboard.index,
						city: "taipei",
					},
				});
			}
			
			this.storeCurrentDashboardAllContentAndChartData();
			// After getting dashboard info, call the setCurrentDashboardContent (3.) method to get component info
			this.setCurrentDashboardContent();
		},
		async storeCurrentDashboardAllContentAndChartData() {

			// 針對目前index 取得不分city的資料
			const response = await http.get(`/dashboard/${this.currentDashboard.index}`);

			this.cityDashboard.components = response.data.data;

			// get chart data
			for (
				let index = 0;
				index < this.cityDashboard.components?.length;
				index++
			) {
				const component = this.cityDashboard.components[index];

				const response = await http.get(
					`/component/${component.id}/chart/${component.city}`,
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

				this.cityDashboard.components[index].chart_data =
					response.data.data;
				
				if (response.data.categories) {
					this.cityDashboard.components[
						index
					].chart_config.categories = response.data.categories;
				}
			}

			// get history data
			for (
				let index = 0;
				index < this.cityDashboard.components?.length;
				index++
			) {
				const component = this.cityDashboard.components[index];
				// Get history data if applicable
				if (
					component.history_config &&
					component.history_config.range
				) {
					for (let i in component.history_config.range) {
						const response = await http.get(
							`/component/${component.id}/history/${component.city}`,
							{
								params: getComponentDataTimeframe(
									component.history_config.range[i],
									"now",
									true
								),
							}
						);

						if (i === "0") {
							this.cityDashboard.components[
								index
							].history_data = [];
						}
						this.cityDashboard.components[
							index
						].history_data.push(response.data.data);
					}
				}
			}
		},

		// 3. Finds the info for the current dashboard based on the index and adds it to "currentDashboard"
		async setCurrentDashboardContent() {
			const dashboardSources = {
				taipei: this.taipeiDashboards,
				metrotaipei: this.metroTaipeiDashboards,
				personal: this.personalDashboards
			};
			const dashboard = dashboardSources[this.currentDashboard.city] || dashboardSources.personal;
			const currentDashboardInfo = dashboard.find(item => item.index === this.currentDashboard.index);

			if (!currentDashboardInfo) {
				router.replace({
					query: {
						index: this.taipeiDashboards[0].index,
						city: "taipei",
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
				const currentCityData = response.data.data.filter(item => item.city === this.currentDashboard.city);
				const notCurrentCityData = response.data.data.filter(item => item.city !== this.currentDashboard.city);

				if (this.currentDashboard.city) {
					this.currentDashboard.components = currentCityData;
					this.currentDashboardExcluded.components = notCurrentCityData;
				} else {
					const uniqueData = [...new Map(response.data.data.map(item => [item.id, item])).values()];

					// 找出被排除的重複資料（city 不同的資料）
					const excludedData = response.data.data.filter(item => {
						const uniqueItem = uniqueData.find(u => u.id === item.id);
						return uniqueItem && uniqueItem.city !== item.city;
					});
					this.currentDashboard.components = uniqueData;
					this.currentDashboardExcluded.components = excludedData;
				}
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
			try {
			  // 4-1. Loop through all the components of a dashboard
			  for (
				let index = 0;
				index < this.currentDashboard.components?.length;
				index++
			  ) {
				const component = this.currentDashboard.components[index];
		  
				try {
				  // 4-2. Get chart data
				  const response = await http.get(
					`/component/${component.id}/chart/${this.currentDashboard.city ? `${this.currentDashboard.city}` : `${component.city}`}`,
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
				} catch (error) {
				  console.error(`Failed to fetch chart data for component ${component.id}:`, error);
				  // Set empty chart data to avoid errors in subsequent operations
				  this.currentDashboard.components[index].chart_data = [];
				}
			  }
			  for (
				let index = 0;
				index < this.currentDashboard.components?.length;
				index++
			  ) {
				const component = this.currentDashboard.components[index];
				
				// 4-3. Get history data if applicable
				if (
				  component.history_config &&
				  component.history_config.range
				) {
				  for (let i in component.history_config.range) {
					try {
					  const response = await http.get(
						`/component/${component.id}/history/${this.currentDashboard.city ? `${this.currentDashboard.city}` : `${component.city}`}`,
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
					  this.currentDashboard.components[index].history_data.push(
						response.data.data
					  );
					} catch (error) {
					  console.error(`Failed to fetch history data for component ${component.id} (range ${i}):`, error);
					  // Add empty data to maintain data structure consistency
					  this.currentDashboard.components[index].history_data.push([]);
					}
				  }
				}
			  }
			  if (
				this.currentDashboard.mode === "/mapview" &&
				this.currentDashboard.index !== "map-layers"
			  ) {
				// In /mapview, map layer components are also present and need to be fetched
				try {
				  await this.setMapLayers(this.currentDashboard.city || "metrotaipei");
				} catch (error) {
				  console.error("Failed to fetch map layers:", error);
				  this.loading = false;
				}
			  } else {
				this.loading = false;
			  }
			} catch (error) {
			  console.error("Error setting dashboard chart data:", error);
			  this.loading = false;
			}
		  },
		// 5. Call an API to get contributor data (result consists of id, name, link)
		setContributors() {
			http.get(`/contributor/`)
				.then((rs) => {
					const contributors = {};
					rs.data.data.forEach((item) => {
						contributors[item.user_id] = {
							id: item.id,
							user_id: item.user_id,
							user_name: item.user_name,
							link: item.link,
							image: item.image,
							description: item.description,
							identity: item.identity,
							include: item.include,
						};
					});
					this.contributors = contributors;
				})
				.catch((e) => console.error(e));
		},
		// 6. Call an API to get map layer component info and store it (if in /mapview)
		async setMapLayers(city) {
			const cityValue = this.currentDashboard.city || city;
    
			// If not a valid city value, set empty mapLayers
			if (!['taipei', 'metrotaipei'].includes(cityValue)) {
				this.mapLayers = [];
				this.loading = false;
				return;
			}

			try {
				if (this.allMapLayers.length === 0) {
					// No layer data yet, fetch from API
					const response = await http.get(`/dashboard/map-layers`);
					this.allMapLayers = response.data.data || [];
					console.warn('allMapLayers', this.allMapLayers);
					
					// Get chart_data for all layers
					await this.setMapLayersContent(cityValue);
				} else {
					// Layer data already exists, filter directly by city
					this.filterMapLayersByCity(cityValue);
					console.warn('filterMapLayersByCity');
					this.loading = false;
				}
			} catch (error) {
				console.error("Error in setMapLayers:", error);
				this.mapLayers = [];
				this.loading = false;
			}
		},
		// Filter layers by city
		filterMapLayersByCity(city) {
			// Filter layers of the specified city from allMapLayers
			this.mapLayers = this.allMapLayers.filter(item => item.city === city);
		},
		// 7. Call an API for each map layer component to get its chart data and store it (if in /mapview)
		async setMapLayersContent(city) {
			try {
			  for (let index = 0; index < this.allMapLayers.length; index++) {
				const component = this.allMapLayers[index];
				
				try {
				  const response = await http.get(
					`/component/${component.id}/chart/${component.city}`
				  );
				  
				  this.allMapLayers[index].chart_data = response.data.data;
				} catch (error) {
				  console.error(`Failed to fetch data for component ${component.id}:`, error);
				  // Continue processing the next layer when an error occurs
				}
			  }
			  
			  // Filter layers by the specified city
			  this.filterMapLayersByCity(city);
			} catch (error) {
			  console.error("Error occurred during layer data processing:", error);
			} finally {
			  this.loading = false;
			}
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

			// Remove duplicates using Map, keeping the last occurrence of each id
			const uniqueData = [...new Map(response.data.data.map(item => [item.id, item])).values()];

			this.components = uniqueData;
			this.loading = false;
		},
		// 2. Get the info of a single component (used in /component/:index)
		async getCurrentComponentData(index, city) {
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
					city: city,
				},
			});

			if (response_1.data.results === 0) {
				this.loading = false;
				this.error = true;
				return;
			}

			dialogStore.moreInfoContent = response_1.data.data;
			
			for (let index = 0; index < dialogStore.moreInfoContent.length; index++) {

				const response_2 = await http.get(
					`/component/${dialogStore.moreInfoContent[index].id}/chart/${dialogStore.moreInfoContent[index].city}`,
					{
						params: !["static", "current", "demo"].includes(
							dialogStore.moreInfoContent[index].time_from
						)
							? getComponentDataTimeframe(
									dialogStore.moreInfoContent[index].time_from,
									dialogStore.moreInfoContent[index].time_to,
									true
							  )
							: {},
					}
				);

				dialogStore.moreInfoContent[index].chart_data = response_2.data.data;

				if (response_2.data.categories) {
					dialogStore.moreInfoContent[index].chart_config.categories =
						response_2.data.categories;
				}
	
				// 2-3. Get the component history data if applicable
				if (dialogStore.moreInfoContent[index].history_config) {
					for (let i in dialogStore.moreInfoContent[index].history_config
						.range) {
						const response = await http.get(
							`/component/${dialogStore.moreInfoContent[index].id}/history/${dialogStore.moreInfoContent[index].city}`,
							{
								params: getComponentDataTimeframe(
									dialogStore.moreInfoContent[index].history_config
										.range[i],
									"now",
									true
								),
							}
						);
	
						if (i === "0") {
							dialogStore.moreInfoContent[index].history_data = [];
						}
						dialogStore.moreInfoContent[index].history_data.push(
							response.data.data
						);
					}
				}
				this.loading = false;
			}
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
		/*
		wsConnect() {
			const dialogStore = useDialogStore();
			this.ws = new WebSocket("ws://192.168.88.193:8088/api/v1/ws");
			this.ws.onopen = function (event) {
				console.log("WebSocket connected");
			};

			this.ws.onmessage = function (event) {
				var message = event.data;
				// var messagesDiv = document.getElementById("messages");
				// messagesDiv.innerHTML += "<p>" + message + "</p>";
				dialogStore.showNotification("info", message, 10000);
			};
		},
		wsDisconnect() {
			this.ws.close();
		},
		sendMessage(message) {
			this.ws.send(message.inctype + ": 位於 " + message.place);
		},
		*/
	},
	debounce: {
		favoriteComponent: 500,
		unfavoriteComponent: 500,
	},
});
