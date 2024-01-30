<!-- Developed By Taipei Urban Intelligence Center 2023-2024 -->
<!-- 
Lead Developer:  Igor Ho (Full Stack Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<script setup>
import { onBeforeMount, onMounted } from "vue";
import { useAuthStore } from "./store/authStore";
import { useDialogStore } from "./store/dialogStore";

import NavBar from "./components/utilities/bars/NavBar.vue";
import SideBar from "./components/utilities/bars/SideBar.vue";
import AdminSideBar from "./components/utilities/bars/AdminSideBar.vue";
import SettingsBar from "./components/utilities/bars/SettingsBar.vue";
import NotificationBar from "./components/dialogs/NotificationBar.vue";
import InitialWarning from "./components/dialogs/InitialWarning.vue";
import ComponentSideBar from "./components/utilities/bars/ComponentSideBar.vue";
import LogIn from "./components/dialogs/LogIn.vue";

const authStore = useAuthStore();
const dialogStore = useDialogStore();

onBeforeMount(() => {
	authStore.initialChecks();

	let vh = window.innerHeight * 0.01;
	document.documentElement.style.setProperty("--vh", `${vh}px`);

	window.addEventListener("resize", () => {
		let vh = window.innerHeight * 0.01;
		document.documentElement.style.setProperty("--vh", `${vh}px`);
	});
});
onMounted(() => {
	const showInitialWarning = localStorage.getItem("initialWarning");
	if (!showInitialWarning) {
		dialogStore.showDialog("initialWarning");
	}
});
</script>

<template>
	<div class="app-container">
		<NotificationBar />
		<NavBar />
		<!-- /mapview, /dashboard layouts -->
		<div
			class="app-content"
			v-if="
				authStore.currentPath === 'mapview' ||
				authStore.currentPath === 'dashboard'
			"
		>
			<SideBar />
			<div class="app-content-main">
				<SettingsBar />
				<RouterView></RouterView>
			</div>
		</div>
		<!-- /admin layouts -->
		<div class="app-content" v-else-if="authStore.currentPath === 'admin'">
			<AdminSideBar />
			<div class="app-content-main">
				<RouterView></RouterView>
			</div>
		</div>
		<!-- /component, /component/:index layouts -->
		<div
			class="app-content"
			v-else-if="authStore.currentPath.includes('component')"
		>
			<ComponentSideBar />
			<div class="app-content-main">
				<RouterView></RouterView>
			</div>
		</div>
		<div v-else-if="authStore.currentPath === 'callback'">
			<router-view></router-view>
		</div>
		<InitialWarning />
		<LogIn />
	</div>
</template>

<style scoped lang="scss">
.app {
	&-container {
		max-width: 100vw;
		max-height: 100vh;
		max-height: calc(var(--vh) * 100);
	}

	&-content {
		width: 100vw;
		max-width: 100vw;
		height: calc(100vh - 60px);
		height: calc(var(--vh) * 100 - 60px);
		display: flex;

		&-main {
			width: 100%;
			display: flex;
			flex-direction: column;
		}
	}
}
</style>
