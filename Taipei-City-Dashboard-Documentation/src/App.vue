<script setup>
import { onBeforeMount, onMounted } from 'vue';
import { useAppStore } from './store/appStore';
import { useI18n } from 'vue-i18n';

import NavBar from './components/NavBar.vue';

const appStore = useAppStore();
const { locale } = useI18n();

onBeforeMount(() => {
	appStore.checkIfMobile();

	let vh = window.innerHeight * 0.01;
	document.documentElement.style.setProperty('--vh', `${vh}px`);

	window.addEventListener('resize', () => {
		let vh = window.innerHeight * 0.01;
		document.documentElement.style.setProperty('--vh', `${vh}px`);
	});
});

onMounted(() => {
	document.title = appStore.lang === 'en' ? 'Docs | Taipei City Dashboard' : '文件｜臺北城市儀表板';
	locale.value = appStore.lang;
});
</script>

<template>
	<div :class="`app ${appStore.mode}`">
		<NavBar />
		<RouterView></RouterView>
	</div>
</template>

<style scoped>
.app {
	background-color: var(--color-background);
	height: 100vh;
	height: calc(var(--vh) * 100);
	max-height: 100vh;
	max-height: calc(var(--vh) * 100);
	min-width: 100vw;
	overflow-x: hidden;
}
</style>
