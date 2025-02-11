<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";
import { useAuthStore } from "../../store/authStore";

import SideBarTab from "../utilities/miscellaneous/SideBarTab.vue";

const dialogStore = useDialogStore();
const contentStore = useContentStore();
const authStore = useAuthStore();
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div
        v-if="dialogStore.dialogs.mobileNavigation"
        class="dialogcontainer"
      >
        <div
          class="dialogcontainer-background"
          @click="dialogStore.hideAllDialogs"
        />
        <div class="dialogcontainer-dialog">
          <div class="mobilenavigation">
            <div v-if="authStore.token">
              <h2>我的最愛</h2>
              <SideBarTab
                icon="favorite"
                title="收藏組件"
                :expanded="true"
                :index="contentStore.favorites?.index"
              />
              <h2>個人儀表板</h2>
              <SideBarTab
                v-for="item in contentStore.personalDashboards.filter(
                  (item) => item.icon !== 'favorite'
                )"
                :key="item.index"
                :icon="item.icon"
                :title="item.name"
                :index="item.index"
                :expanded="true"
                @click="dialogStore.hideAllDialogs"
              />
            </div>
            <h2>公共儀表板</h2>
            <SideBarTab
              v-for="item in contentStore.publicDashboards.filter(
                (item) => item.index !== 'map-layers'
              )"
              :key="item.index"
              :icon="item.icon"
              :title="item.name"
              :index="item.index"
              :expanded="true"
              @click="dialogStore.hideAllDialogs"
            />
            <h2>基本地圖圖層</h2>
            <SideBarTab
              :icon="`public`"
              :title="`圖資資訊`"
              index="map-layers"
              :expanded="true"
              @click="dialogStore.hideAllDialogs"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
.dialogcontainer {
	width: 100vw;
	height: 100vh;
	height: calc(var(--vh) * 100);
	display: flex;
	align-items: center;
	justify-content: center;
	position: fixed;
	top: 0;
	left: 0;
	opacity: 1;
	z-index: 10;

	&-dialog {
		width: fit-content;
		height: fit-content;
		position: absolute;
		top: 110px;
		left: 45px;
		padding: var(--font-m);
		border: solid 1px var(--color-border);
		border-radius: 5px;
		background-color: rgb(30, 30, 30);
		transform: translateY(0);
		z-index: 2;
	}

	&-background {
		width: 100vw;
		height: 100vh;
		height: calc(var(--vh) * 100);
		position: absolute;
		top: 0;
		left: 0;
		background-color: rgba(0, 0, 0, 0.66);
	}
}

.mobilenavigation {
	width: 170px;
	max-height: 350px;
	overflow-y: scroll;
}

// Classes that are provided by vue transitions. Read the official docs for more instructions.
// https://vuejs.org/guide/built-ins/transition.html
.dialog-enter-from,
.dialog-leave-to {
	opacity: 0;

	.dialogcontainer-dialog {
		transform: translateY(-2.25rem);
	}
}

.dialog-enter-active,
.dialog-leave-active {
	transition: opacity 0.3s ease;

	.dialogcontainer-dialog {
		transition: transform 0.3s ease;
	}
}
</style>
