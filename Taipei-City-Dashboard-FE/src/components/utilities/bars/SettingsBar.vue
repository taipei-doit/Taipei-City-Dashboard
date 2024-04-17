<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- Adding new components and settings is disabled in public dashboards and the mobile version -->

<script setup>
import { useContentStore } from "../../../store/contentStore";
import { useDialogStore } from "../../../store/dialogStore";

import MobileNavigation from "../../dialogs/MobileNavigation.vue";
import AddEditDashboards from "../../dialogs/AddEditDashboards.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();

function handleOpenSettings() {
	contentStore.editDashboard = JSON.parse(
		JSON.stringify(contentStore.currentDashboard)
	);
	dialogStore.addEdit = "edit";
	dialogStore.showDialog("addEditDashboards");
}
</script>

<template>
  <div class="settingsbar">
    <div class="settingsbar-title">
      <span>{{ contentStore.currentDashboard.icon }}</span>
      <h2>{{ contentStore.currentDashboard.name }}</h2>
      <button
        class="show-if-mobile"
        @click="dialogStore.showDialog('mobileNavigation')"
      >
        <span class="settingsbar-title-navigation">arrow_drop_down_circle</span>
      </button>
      <MobileNavigation />
      <div
        v-if="
          contentStore.personalDashboards
            .map((el) => el.index)
            .includes(contentStore.currentDashboard.index) &&
            contentStore.currentDashboard.icon !== 'favorite'
        "
        class="settingsbar-settings hide-if-mobile"
      >
        <button @click="handleOpenSettings">
          <span>settings</span>
          <p>設定</p>
        </button>
      </div>
      <AddEditDashboards />
    </div>
  </div>
</template>

<style scoped lang="scss">
.settingsbar {
	width: calc(100% - 2 * var(--font-m));
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
				color: var(--color-highlight);
			}
		}
	}
}
</style>
