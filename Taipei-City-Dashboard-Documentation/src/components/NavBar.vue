<script setup>
import { onMounted, ref } from 'vue';
import { useAppStore } from '../store/appStore';
import { useI18n } from "vue-i18n";

const { BASE_URL } = import.meta.env;
const appStore = useAppStore();
const { locale } = useI18n();

const mode = ref(true);

function toggleLang() {
	const changeTo = appStore.lang === 'en' ? 'ch' : 'en';
	localStorage.setItem("lang", changeTo);
	locale.value = changeTo;
	appStore.toggleLang(changeTo);
	location.reload();
}

onMounted(() => {
	mode.value = appStore.mode === 'dark' ? true : false;
});
</script>

<template>
	<div class="navbar">
		<a class="navbar-logo" :href="`${BASE_URL}/`">
			<img 
			src="/images/contributors/doit.png" 
			alt="doit logo"
			:style="{
				height: '40px',
				width: 'auto'
			}"
			/>
			<div>
				<h1>臺北城市儀表板文件</h1>
				<h2>Taipei City Dashboard Documentation</h2>
			</div>
		</a>
		<div class="navbar-control">
			<button @click="toggleLang">
				<p :style="{ marginTop: appStore.lang === 'en' ? '0px' : '1px' }">{{ appStore.lang === 'en' ? '中' : 'EN'
					}}
				</p>
			</button>
			<label class="doc-toggleswitch">
				<label for="light-dark-mode-toggle" :style="{ display: 'none' }">light-dark-mode-toggle</label>
				<input type="checkbox" id="light-dark-mode-toggle" @change="appStore.toggleMode" v-model="mode">
				<span class="doc-toggleswitch-slider"></span>
			</label>
		</div>
	</div>
</template>

<style scoped lang="scss">
.navbar {
	height: 60px;
	width: 100vw;
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 1px solid var(--color-border);
	background-color: var(--color-component-background);
	user-select: none;

	&-logo {
		display: flex;
		// position: relative;
		// overflow: visible;

		h1 {
			font-weight: 500;
		}

		h2 {
			font-size: var(--font-s);
			font-weight: 400;
		}

		img {
			height: 45px;
			width: 22.94px;
			margin: 0 var(--font-m);
		}
	}

	&-control {
		display: flex;
		align-items: center;
		margin-right: var(--font-m);

		button {
			height: 2rem;
			display: flex;
			align-items: center;
			margin-right: var(--font-s);

			p {
				color: var(--color-complement-text);
				font-size: var(--font-m);
				transition: color 0.2s;

				&:hover {
					color: var(--color-normal-text)
				}
			}
		}
	}
}
</style>