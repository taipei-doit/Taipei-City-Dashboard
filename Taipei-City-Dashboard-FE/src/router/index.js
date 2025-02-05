/* Developed by Taipei Urban Intelligence Center 2023-2024*/

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Systems: Ann Shih (Systems Engineer)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)

/* Department of Information Technology, Taipei City Government */

import { createRouter, createWebHistory } from "vue-router";
import { useContentStore } from "../store/contentStore";
import { useMapStore } from "../store/mapStore";
import { usePersonStore } from "../store/personStore";
import DashboardView from "../views/DashboardView.vue";
import MapView from "../views/MapView.vue";
import ComponentView from "../views/ComponentView.vue";
import ComponentInfoView from "../views/ComponentInfoView.vue";
import EmbedView from "../views/EmbedView.vue";

const routes = [
	{
		path: "/",
		redirect: "/dashboard",
	},
	{
		path: "/callback",
		name: "callback",
		component: () => import("../views/CallBack.vue"),
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
		path: "/component",
		name: "component",
		component: ComponentView,
	},
	{
		path: "/component/:index",
		name: "component-info",
		component: ComponentInfoView,
	},
	{
		path: "/embed/:id",
		name: "embed",
		component: EmbedView,
	},
	{
		path: "/embed",
		redirect: "/embed/0",
	},
	{
		path: "/admin",
		redirect: "/admin/dashboard",
	},
	{
		path: "/admin/user",
		name: "admin-user",
		component: () => import("../views/admin/AdminUser.vue"),
	},
	{
		path: "/admin/contributor",
		name: "admin-contributor",
		component: () => import("../views/admin/AdminContributor.vue"),
	},
	{
		path: "/admin/dashboard",
		name: "admin-dashboard",
		component: () => import("../views/admin/AdminDashboard.vue"),
	},
	{
		path: "/admin/edit-component",
		name: "admin-edit-component",
		component: () => import("../views/admin/AdminEditComponent.vue"),
	},
	{
		path: "/admin/issue",
		name: "admin-issue",
		component: () => import("../views/admin/AdminIssue.vue"),
	},
	{
		path: "/admin/disaster",
		name: "admin-disaster",
		component: () => import("../views/admin/AdminDisaster.vue"),
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

// Sets route name to currentPath in personStore
router.beforeEach((to) => {
	const personStore = usePersonStore();

	if (to.name.includes("admin")) {
		personStore.setCurrentPath("admin");
		return;
	}
	personStore.setCurrentPath(to.name);
});

// Redirects blocked routes in mobile mode
router.beforeEach((to) => {
	const personStore = usePersonStore();
	if (personStore.isMbDevice && personStore.isNarrowDevice) {
		if (
			!["dashboard", "component-info", "callback", "embed"].includes(
				to.name
			)
		) {
			router.push("/dashboard");
		}
	} else if (personStore.code) {
		if (to.name === "callback") {
			router.push("/dashboard");
		}
	}
});

// Redirects unauthenticated routes
router.beforeEach((to) => {
	const personStore = usePersonStore();
	if (to.name.includes("admin")) {
		if (!personStore.person.is_admin || !personStore.code) {
			if (personStore.person.is_admin === false) {
				router.push("/dashboard");
			} else {
				setTimeout(() => {
					if (!personStore.person.is_admin) {
						router.push("/dashboard");
					}
				}, 200);
			}
		}
	} else if (to.name === "component") {
		if (!personStore.code) {
			router.push("/dashboard");
		}
	} else if (to.name === "component-info") {
		if (!personStore.code && !personStore.isNarrowDevice) {
			router.push("/dashboard");
		}
	}
});

// Handles content related tasks (gets content for each route)
router.beforeEach((to) => {
	const contentStore = useContentStore();
	const mapStore = useMapStore();
	// Pass in route info to contentStore if the path starts with /dashboard or /mapview
	if (
		to.path.toLowerCase() === "/dashboard" ||
		to.path.toLowerCase() === "/mapview"
	) {
		contentStore.clearEditDashboard();
		contentStore.setRouteParams(to.path, to.query.index);
	} else if (
		to.path.toLowerCase() === "/component" ||
		to.name === "component-info"
	) {
		contentStore.setDashboards(true);
	} else {
		contentStore.clearCurrentDashboard();
	}
	// Get Component data if the path is component-info
	if (to.name === "component-info") {
		contentStore.getCurrentComponentData(to.params.index);
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
