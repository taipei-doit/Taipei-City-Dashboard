<!-- Developed by Taipei Urban Intelligence Center 2023 -->

<!-- Navigation between dashboard and mapview will switch here in the mobile version -->
<!-- Adding new components and settings is disabled in the map layer dashboard and the mobile version -->

<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useContentStore } from '../store/contentStore';
import { useDialogStore } from '../store/dialogStore';

import AddComponent from './dialogs/AddComponent.vue';
import DashboardSettings from './dialogs/DashboardSettings.vue';
import MobileNavigation from './dialogs/MobileNavigation.vue';

const route = useRoute();
const router = useRouter();
const contentStore = useContentStore();
const dialogStore = useDialogStore();

// The following are controls for the mobile version to toggle between dashboard and mapview
const isDashboard = ref(false);

watch(route, (newRoute) => {
	if (newRoute.path === '/dashboard') {
		isDashboard.value = false;
	} else {
		isDashboard.value = true;
	}
});

function handleToggle() {
	if (isDashboard.value) {
		router.replace({ name: 'mapview', query: { index: route.query.index } });
	} else {
		router.replace({ name: 'dashboard', query: { index: route.query.index } });
	}
}
</script>

<template>
	<div class="settingsbar">
		<div class="settingsbar-title">
			<span>{{ contentStore.currentDashboard.icon }}</span>
			<h2>{{ contentStore.currentDashboard.name }}
			</h2>
			<button @click="dialogStore.showDialog('mobileNavigation')" class="show-if-mobile">
				<span class="settingsbar-title-navigation">arrow_drop_down_circle</span>
			</button>
			<MobileNavigation />
			<div class="settingsbar-settings hide-if-mobile"
				v-if="contentStore.currentDashboard.index !== 'map-layers' && contentStore.currentDashboard.index !== 'favorites'">
				<button @click="dialogStore.showDialog('addComponent')"><span>add_chart</span>
					<p>新增組件</p>
				</button>
				<AddComponent />
				<button @click="dialogStore.showDialog('dashboardSettings')"><span>settings</span>
					<p>設定</p>
				</button>
				<DashboardSettings />
			</div>
		</div>
		<div class="settingsbar-navigation show-if-mobile">
			<p>圖表</p>
			<div>
				<!-- The class "toggleswitch is slightly modified below, further changes could be made in /assets/styles/toggleswitch.css" -->
				<label class="toggleswitch">
					<input type="checkbox" @change="handleToggle" v-model="isDashboard">
					<span class="toggleswitch-slider"></span>
				</label>
			</div>
			<p>地圖</p>
		</div>
	</div>
</template>

<style scoped lang="scss">
.settingsbar {
	width: calc(100% - 2*var(--font-m));
	min-height: 1.6rem;
	display: flex;
	justify-content: space-between;
	margin: 20px var(--font-m) 0;
	padding-bottom: 0.5rem;
	border-bottom: solid 1px var(--color-border);
	user-select: none;

	&-title {
		display: flex;
		align-items: center;
		overflow: hidden;

		span {
			font-family: var(--font-icon);
			font-size: calc(var(--font-m) * var(--font-to-icon));
		}

		h2 {
			margin: 0 var(--font-s);
			font-weight: 400;
			font-size: var(--font-m);
			white-space: nowrap;
		}

		&-navigation {
			margin-left: 4px;
			color: var(--color-complement-text);
		}
	}

	&-settings {
		display: flex;
		align-items: center;

		span {
			margin-right: 4px;
			font-family: var(--font-icon);
			font-size: calc(var(--font-m) * var(--font-to-icon));
		}

		button {
			display: flex;
			align-items: center;
			border-radius: 5px;
			margin-left: 4px;

			p {
				width: 0px;
				max-height: 1.2rem;
				font-size: 0.8rem;
				text-align: left;
				transition: width 0.2s, color 0.2s;
				overflow-x: hidden;
			}

			&:hover p {
				width: 55px;
				color: var(--color-highlight);
			}

			span {
				color: var(--color-complement-text);
				transition: color 0.2s;


			}

			&:hover span {
				color: var(--color-highlight)
			}
		}
	}

	&-navigation {
		min-width: 90px;
		display: flex;
		align-items: center;
		margin-left: var(--font-m);

		p {
			color: var(--color-complement-text)
		}
	}
}




.toggleswitch {
	margin: 0 4px;
	align-self: baseline;

	input:checked+&-slider {
		background-color: var(--color-complement-text);
	}

	input:focus+&-slider {
		box-shadow: 0 0 1px var(--color-complement-text);
	}

	input:checked+&-slider:before {
		background-color: var(--color-border);
	}
}
</style>