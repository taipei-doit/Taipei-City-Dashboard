import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../views/HomePage.vue";
import DocPage from "../views/DocPage.vue";
import RegistryPage from "../views/RegistryPage.vue";
import ApiPage from "../views/ApiPage.vue";

const routes = [
	{
		path: "/",
		component: HomePage,
		name: "home",
	},
	{
		path: "/front-end",
		redirect: "/front-end/introduction",
	},
	{
		path: "/front-end/:id",
		component: DocPage,
		name: "front-end",
		props: true,
	},
	{
		path: "/back-end",
		redirect: "/back-end/introduction",
	},
	{
		path: "/back-end/:id",
		component: DocPage,
		name: "back-end",
		props: true,
	},
	{
		path: "/data-end",
		redirect: "/data-end/introduction",
	},
	{
		path: "/data-end/:id",
		component: DocPage,
		name: "data-end",
		props: true,
	},
	{
		path: "/component-registry",
		component: RegistryPage,
		name: "component-registry",
	},
	{
		path: "/api",
		component: ApiPage,
		name: "api",
	},
	{
		path: "/:pathMatch(.*)*",
		redirect: "/",
	},
];

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	base: import.meta.env.BASE_URL,
	routes,
});

export default router;
