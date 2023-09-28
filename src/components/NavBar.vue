<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- Navigation will be hidden from the navbar in mobile mode and moved to the settingsbar -->

<script setup>
const { VITE_APP_TITLE } = import.meta.env;
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../store/authStore';
import { useDialogStore } from '../store/dialogStore';
import { useFullscreen } from '@vueuse/core';

import UserSettings from './dialogs/UserSettings.vue';

const route = useRoute();
const authStore = useAuthStore();
const dialogStore = useDialogStore();
const { isFullscreen, toggle } = useFullscreen();

const linkQuery = computed(() => {
	const { query } = route;
	return `?index=${query.index}`;
});
</script>

<template>
	<div class="navbar">
		<div class="navbar-logo">
			<div class="navbar-logo-image">
				<img src="../assets/images/TUIC.svg" alt="tuic logo" />
			</div>
			<div>
				<h1>{{ VITE_APP_TITLE }}</h1>
				<h2>Taipei City Dashboard Open Source</h2>
			</div>
		</div>
		<div class="navbar-tabs hide-if-mobile">
			<router-link :to="`/dashboard${linkQuery}`">儀表板總覽</router-link>
			<router-link :to="`/mapview${linkQuery}`">地圖交叉比對</router-link>
		</div>
		<div class="navbar-user">
			<a href="https://tuic.gov.taipei/documentation/front-end" target="_blank"
				rel="noreferrer"><button><span>help</span></button></a>
			<button class="hide-if-mobile" @click="toggle"><span>{{ isFullscreen ? 'fullscreen_exit' : 'fullscreen'
			}}</span></button>
			<div class="navbar-user-user hide-if-mobile">
				<button>{{ authStore.user.name }}</button>
				<ul>
					<li><button @click="dialogStore.showDialog('userSettings')">用戶設定</button></li>
					<li><button @click="authStore.handleLogout">登出</button></li>
				</ul>
				<teleport to="body">
					<user-settings />
				</teleport>
			</div>
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

		h1 {
			font-weight: 500;
		}

		h2 {
			font-size: var(--font-s);
			font-weight: 400;
		}

		&-image {
			width: 22.94px;
			height: 45px;
			margin: 0 var(--font-m);

			img {
				height: 45px;
				filter: invert(1);
			}
		}


	}

	&-tabs {
		display: flex;

		a {
			height: 59px;
			display: flex;
			align-items: center;
			margin-left: var(--font-s)
		}

		.router-link-active {
			border-bottom: solid 3px var(--color-highlight);
			color: var(--color-highlight);
		}
	}

	&-user {
		display: flex;
		align-items: center;

		button {
			display: flex;
			align-items: center;
			margin-right: var(--font-m);
			padding: 2px 4px;
			border-radius: 4px;
			font-size: var(--font-m);
			transition: background-color 0.25s;
		}

		button:hover {
			background-color: var(--color-complement-text);
		}

		span {
			font-family: var(--font-icon);
			font-size: calc(var(--font-l) * var(--font-to-icon));
		}

		&-user:hover ul {
			display: block;
			opacity: 1;
		}

		&-user {
			height: 60px;
			display: flex;
			align-items: center;

			ul {
				min-width: 100px;
				display: none;
				position: absolute;
				right: 20px;
				top: 55px;
				padding: 8px;
				border-radius: 5px;
				background-color: rgb(85, 85, 85);
				opacity: 0;
				transition: opacity 0.25s;
				z-index: 10;

				li {
					padding: 8px 4px;
					border-radius: 5px;
					transition: background-color 0.25s;
					cursor: pointer;
				}

				li:hover {
					background-color: var(--color-complement-text)
				}
			}
		}
	}
}
</style>