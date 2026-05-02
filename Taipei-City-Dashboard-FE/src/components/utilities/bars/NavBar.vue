<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- Navigation will be hidden from the navbar in mobile mode and moved to the settingsbar -->

<script setup>
const { VITE_APP_TITLE } = import.meta.env;
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useFullscreen } from "@vueuse/core";
import { useAuthStore } from "../../../store/authStore";
import { useDialogStore } from "../../../store/dialogStore";
import { useThemeStore } from "../../../store/themeStore";
import { useBackendTranslation } from "../../../composables/useBackendTranslation";

import UserSettings from "../../dialogs/UserSettings.vue";
import ContributorsList from "../../dialogs/ContributorsList.vue";

const route = useRoute();
const authStore = useAuthStore();
const dialogStore = useDialogStore();
const themeStore = useThemeStore();
const { locale, setLocale, supportedLocales } = useBackendTranslation();
const { isFullscreen, toggle } = useFullscreen();

const linkQuery = computed(() => {
	const { query } = route;
	const indexQuery = `?index=${query.index}`;
	const cityQuery = query.city ? `&city=${query.city}` : '';
	return `${indexQuery}${cityQuery}`;
});

const location = computed(() => {
	return window.location;
});

const isLocalhost = computed(() => {
	return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
});
</script>

<template>
  <div class="navbar">
    <a href="/">
      <div class="navbar-logo">
        <div class="navbar-logo-image">
          <img
            src="../../../assets/images/TUIC.svg"
            alt="tuic logo"
          >
        </div>
        <div>
          <h1>{{ VITE_APP_TITLE }}</h1>
          <h2>Taipei City Dashboard</h2>
        </div>
      </div>
    </a>
    <div
      v-if="
        authStore.currentPath !== 'admin'
      "
      class="navbar-tabs"
    >
      <router-link
        v-if="authStore.token"
        :to="`/component`"
        :class="{
          'router-link-active':
            authStore.currentPath.includes('component'),
        }"
      >
        組件瀏覽平台
      </router-link>
      <router-link
        :to="`/dashboard${
          linkQuery.includes('undefined') ? '' : linkQuery
        }`"
      >
        儀表板總覽
      </router-link>
      <router-link
        :to="`/mapview${
          linkQuery.includes('undefined') ? '' : linkQuery
        }`"
      >
        地圖交叉比對
      </router-link>
    </div>
    <div class="navbar-user">
      <div
        class="navbar-locale"
        title="語系 / Language"
      >
        <span class="navbar-locale-icon">translate</span>
        <label class="navbar-locale-sr">語系</label>
        <select
          class="navbar-locale-select"
          :value="locale"
          aria-label="語系"
          @change="setLocale($event.target.value)"
        >
          <option
            v-for="opt in supportedLocales"
            :key="opt.code"
            :value="opt.code"
          >
            {{ opt.label }}
          </option>
        </select>
      </div>
      <button
        type="button"
        class="navbar-theme"
        :title="themeStore.isLight ? '切換深色模式' : '切換淺色模式'"
        @click="themeStore.toggle()"
      >
        <span>{{ themeStore.isLight ? "dark_mode" : "light_mode" }}</span>
      </button>
      <button
        v-if="!(authStore.isMobileDevice && authStore.isNarrowDevice)"
        class="hide-if-mobile"
        @click="toggle"
      >
        <span>{{
          isFullscreen ? "fullscreen_exit" : "fullscreen"
        }}</span>
      </button>
      <div class="navbar-user-info">
        <button><span>info</span></button>
        <ul>
          <li>
            <a
              :href="isLocalhost ? 'https://citydashboard.taipei/documentation/' : `${location.origin}/documentation/`"
              target="_blank"
              rel="noreferrer"
            >技術文件</a>
          </li>
          <li>
            <button
              @click="dialogStore.showDialog('contributorsList')"
            >
              專案貢獻者
            </button>
          </li>
        </ul>
        <teleport to="body">
          <ContributorsList />
        </teleport>
      </div>
      <div
        v-if="
          authStore.token &&
            !(authStore.isMobileDevice && authStore.isNarrowDevice)
        "
        class="navbar-user-user"
      >
        <button>
          {{ authStore.user.name }}
        </button>
        <ul>
          <li>
            <button @click="dialogStore.showDialog('userSettings')">
              用戶設定
            </button>
          </li>
          <li
            v-if="
              authStore.currentPath !== 'admin' &&
                authStore.user.is_admin
            "
            class="hide-if-mobile"
          >
            <router-link to="/admin">
              管理員後臺
            </router-link>
          </li>
          <li
            v-else-if="authStore.user.is_admin"
            class="hide-if-mobile"
          >
            <router-link to="/dashboard">
              返回儀表板
            </router-link>
          </li>
          <li>
            <button @click="authStore.handleLogout">
              登出
            </button>
          </li>
        </ul>
        <teleport to="body">
          <user-settings />
        </teleport>
      </div>
      <div
        v-else-if="
          !(authStore.isMobileDevice && authStore.isNarrowDevice)
        "
        class="navbar-user-user"
      >
        <button @click="dialogStore.showDialog('login')">
          登入
        </button>
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
			
			@media screen and (max-width: 500px) {
				display: none;
			}
		}

		h2 {
			font-size: var(--font-s);
			font-weight: 400;

			@media screen and (max-width: 500px) {
				display: none;
			}
		}

		&-image {
			width: 22.94px;
			height: 45px;
			margin: 0 var(--font-m);

			img {
				height: 45px;
				filter: var(--navbar-logo-filter);
			}
		}
	}

	&-tabs {
		display: flex;

		a {
			height: 59px;
			display: flex;
			align-items: center;
			margin-left: var(--font-s);
			transition: opacity 0.2s, border-bottom 0.2s;
			border-bottom: solid 3px transparent;

			&:hover {
				opacity: 0.8;
			}
		}

		.router-link-active {
			border-bottom: solid 3px var(--color-highlight);
			color: var(--color-highlight);

			&:hover {
				opacity: 1;
			}
		}

		// @media screen and (max-width: 750px) {
		// 	display: none;
		// }
		// @media screen and (max-height: 500px) {
		// 	display: none;
		// }
	}

	&-locale {
		display: flex;
		align-items: center;
		margin-right: var(--font-s);
		min-width: 0;
		gap: 4px;

		&-icon {
			flex-shrink: 0;
			font-family: var(--font-icon);
			font-size: calc(var(--font-m) * var(--font-to-icon));
			color: var(--color-complement-text);
		}

		&-sr {
			position: absolute;
			width: 1px;
			height: 1px;
			padding: 0;
			margin: -1px;
			overflow: hidden;
			clip: rect(0, 0, 0, 0);
			white-space: nowrap;
			border: 0;
		}

		&-select {
			min-width: 0;
			max-width: 7.5rem;
			padding: 4px 6px;
			border-radius: 4px;
			border: solid 1px var(--color-border);
			background-color: var(--color-background);
			color: var(--color-normal-text);
			font-size: var(--font-s);
			cursor: pointer;
			outline: none;
		}

		&-select:focus {
			border-color: var(--color-highlight);
		}
	}

	&-user {
		display: flex;
		align-items: center;

		li a,
		button {
			display: flex;
			align-items: center;
			margin-right: var(--font-m);
			padding: 2px 4px;
			border-radius: 4px;
			font-size: var(--font-m);
			transition: background-color 0.25s;
		}

		span {
			font-family: var(--font-icon);
			font-size: calc(var(--font-l) * var(--font-to-icon));
		}

		&-user:hover ul,
		&-info:hover ul {
			display: block;
			opacity: 1;
		}

		&-user,
		&-info {
			height: 60px;
			min-width: 100px;
			display: flex;
			align-items: center;
			justify-content: center;

			@media screen and (max-width: 750px) {
				display: none;
			}
			@media screen and (max-height: 500px) {
				display: none;
			}

			ul {
				min-width: 100px;
				display: none;
				position: absolute;
				right: 20px;
				top: 55px;
				padding: 8px;
				border-radius: 5px;
				background-color: var(--color-menu-dropdown);
				opacity: 0;
				transition: opacity 0.25s;
				z-index: 10;

				li {
					border-radius: 5px;
					transition: background-color 0.25s;

					a,
					button {
						padding: 8px 6px;
						width: 100%;
						height: 100%;
					}
				}

				li:hover {
					background-color: var(--color-complement-text);
				}
			}
		}

		&-info {
			min-width: 0;

			ul {
				right: 120px;
				top: 55px;
			}

			@media screen and (max-width: 750px) {
				display: flex;

				ul {
					right: 20px;
					top: 55px;
				}
			}
			@media screen and (max-height: 500px) {
				display: flex;
			}
		}
	}
}
</style>
