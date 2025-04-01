<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref, watch } from "vue";
import { useDialogStore } from "../../store/dialogStore";
import { useContentStore } from "../../store/contentStore";
import { useAuthStore } from "../../store/authStore";

import SideBarTab from "../utilities/miscellaneous/SideBarTab.vue";

const dialogStore = useDialogStore();
const contentStore = useContentStore();
const authStore = useAuthStore();

// The collapsed states are for each dashboard
const collapsedStates = ref({
	favorites: false,
	personal: false,
});

function initializeCollapsedStates() {
	contentStore.cityManager.activeCities.forEach((city) => {
		if (!(city in collapsedStates.value)) {
			collapsedStates.value[city] = false;
		}
	});
}

function toggleCollapse(cities) {
	cities = [cities].flat();
	const allCollapsed = cities.every((city) => collapsedStates.value[city]);

	cities.forEach((city) => {
		collapsedStates.value[city] = !allCollapsed;
	});
}

watch(
	() => contentStore.cityManager.activeCities,
	() => {
		initializeCollapsedStates();
	},
	{ immediate: true }
);

onMounted(() => {
	initializeCollapsedStates();
});
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
            <template v-if="authStore.token">
              <h1 @click="toggleCollapse(['favorites', 'personal'])">
                私人儀表板
              </h1>
              <h2 @click="toggleCollapse('favorites')">
                我的最愛
              </h2>
              <transition name="collapse">
                <template v-if="!collapsedStates.favorites">
                  <SideBarTab
                    icon="favorite"
                    title="收藏組件"
                    :expanded="true"
                    :index="contentStore.favorites?.index"
                    @click="dialogStore.hideAllDialogs"
                  />
                </template>
              </transition>

              <h2 @click="toggleCollapse('personal')">
                個人儀表板
              </h2>
              <div
                v-if="
                  contentStore.personalDashboards.filter(
                    (item) => item.icon !== 'favorite'
                  ).length === 0
                "
                class="mobilenavigation-sub-no"
              >
                <p>尚無個人儀表板</p>
              </div>
              <transition name="collapse">
                <div v-if="!collapsedStates.personal">
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
              </transition>
            </template>
            <h1 @click="toggleCollapse(contentStore.cityManager.activeCities)">
              公共儀表板
            </h1>
            <template
              v-for="city in contentStore.cityManager.activeCities"
              :key="city"
            >
              <h2 @click="toggleCollapse(city)">
                {{ `${contentStore.cityManager.getExpandedNameName(city)}` }}
              </h2>
              <transition name="collapse">
                <div
                  v-if="
                    !collapsedStates[city] &&
                      contentStore.getDashboardsByCity(city)?.length > 0
                  "
                >
                  <SideBarTab
                    v-for="item in contentStore.getDashboardsByCity(city)"
                    :key="item.index"
                    :icon="item.icon"
                    :title="item.name"
                    :index="item.index"
                    :expanded="true"
                    :city="city"
                  />
                </div>
              </transition>
            </template>
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

	// same as the sidebar in the SideBar.vue
	h1 {
		cursor: pointer;
		margin: 12px 0;

		&:first-of-type {
			margin-top: 0;
		}
	}

	// same as the sidebar in the SideBar.vue
	h2 {
		color: var(--color-complement-text);
		font-weight: 400;
		text-wrap: nowrap;
		cursor: pointer;
		margin-left: 1em;
	}

	&-sub-no {
		margin: 0.5rem 0 0.5rem 18px;
		font-size: var(--font-s);
		font-style: italic;
	}
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

// same as the sidebar in the SideBar.vue
.collapse-enter-from,
.collapse-leave-to {
	opacity: 0;
	transform: translateY(-20px);
}

.collapse-enter-active,
.collapse-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}
</style>
