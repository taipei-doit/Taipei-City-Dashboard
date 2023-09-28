/* Developed By Taipei Urban Intelligence Center 2023 */

// Lead Developer:  Igor Ho (FE Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Systems: Ann Shih (Systems Engineer)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)

/* Department of Information Technology, Taipei City Government */

import { createRouter, createWebHistory } from "vue-router";
import { useContentStore } from "../store/contentStore";
import { useMapStore } from "../store/mapStore";
import DashboardView from "../views/DashboardView.vue";
import MapView from "../views/MapView.vue";

const routes = [
	{
		path: "/",
		redirect: "/dashboard",
	},
	{
		path: "/dashboard",
		name: "dashboard",
		component: DashboardView,
	},
	{
		path: "/mapview",
		name: "mapview",
		component: MapView,
	},
	{
		path: "/:pathMatch(.*)*",
		name: "notFoundRedirect",
		redirect: "/dashboard",
	},
];

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	base: import.meta.env.BASE_URL,
	routes,
});

router.beforeEach((to) => {
	const contentStore = useContentStore();
	const mapStore = useMapStore();
	// Pass in route info to contentStore if the path starts with /dashboard or /mapview
	if (
		to.path.toLowerCase() === "/dashboard" ||
		to.path.toLowerCase() === "/mapview"
	) {
		contentStore.setRouteParams(to.path, to.query.index);
	}
	// Clear the entire mapStore if the path doesn't start with /mapview
	if (to.path.toLowerCase() !== "/mapview") {
		mapStore.clearEntireMap();
	}
	// Clear only map layers if the path starts with /mapview
	else if (to.path.toLowerCase() === "/mapview") {
		mapStore.clearOnlyLayers();
	}
});

export default router;
