<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref, watch } from "vue";
import { useContentStore } from "../../../store/contentStore";
import { useDialogStore } from "../../../store/dialogStore";
import { useMapStore } from "../../../store/mapStore";
import { useAuthStore } from "../../../store/authStore";

import SideBarTab from "../miscellaneous/SideBarTab.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const mapStore = useMapStore();
const authStore = useAuthStore();

// The expanded state is also stored in localstorage to retain the setting after refresh
const isExpanded = ref(true);

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

function handleOpenAddDashboard() {
	dialogStore.addEdit = "add";
	dialogStore.showDialog("addEditDashboards");
}

function toggleExpand() {
	isExpanded.value = isExpanded.value ? false : true;
	localStorage.setItem("isExpanded", isExpanded.value);
	if (!isExpanded.value) {
		mapStore.resizeMap();
	}
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
	const storedExpandedState = localStorage.getItem("isExpanded");
	if (storedExpandedState === "false") {
		isExpanded.value = false;
	} else {
		isExpanded.value = true;
	}
});
</script>

<template>
  <div
    :class="{
      sidebar: true,
      'sidebar-collapse': !isExpanded,
      'hide-if-mobile': true,
    }"
  >
    <div
      class="sidebar-collapse-btnContainer"
      :class="{ notExpanded: !isExpanded }"
    >
      <button
        class="sidebar-collapse-btnContainer-button"
        @click="toggleExpand"
      >
        <span>{{
          isExpanded
            ? "keyboard_double_arrow_left"
            : "keyboard_double_arrow_right"
        }}</span>
      </button>
    </div>
    <template v-if="authStore.token">
      <h1 @click="toggleCollapse(['favorites', 'personal'])">
        {{ isExpanded ? `私人儀表板 ` : `私人` }}
      </h1>
      <h2 @click="toggleCollapse('favorites')">
        {{ isExpanded ? `我的最愛` : `最愛` }}
      </h2>
      <transition name="collapse">
        <template v-if="!collapsedStates.favorites">
          <SideBarTab
            icon="favorite"
            title="收藏組件"
            :expanded="isExpanded"
            :index="contentStore.favorites?.index"
          />
        </template>
      </transition>
      <div class="sidebar-sub-add">
        <h2 @click="toggleCollapse('personal')">
          {{ isExpanded ? `個人儀表板 ` : `個人` }}
        </h2>
        <button
          v-if="isExpanded && !collapsedStates.personal"
          @click="handleOpenAddDashboard"
        >
          <span>add_circle_outline</span>新增
        </button>
      </div>
      <div
        v-if="
          contentStore.personalDashboards.filter(
            (item) => item.icon !== 'favorite'
          ).length === 0
        "
        class="sidebar-sub-no"
      >
        <p>{{ isExpanded ? `尚無個人儀表板 ` : `尚無` }}</p>
      </div>
      <transition name="collapse">
        <div
          v-if="
            !collapsedStates.personal &&
              contentStore.personalDashboards?.length > 0
          "
        >
          <SideBarTab
            v-for="item in contentStore.personalDashboards.filter(
              (item) => item.icon !== 'favorite'
            )"
            :key="item.index"
            :icon="item.icon"
            :title="item.name"
            :index="item.index"
            :expanded="isExpanded"
          />
        </div>
      </transition>
    </template>
    <h1 @click="toggleCollapse(contentStore.cityManager.activeCities)">
      {{ isExpanded ? `公共儀表板` : `公共` }}
    </h1>
    <template
      v-for="city in contentStore.cityManager.activeCities"
      :key="city"
    >
      <h2 @click="toggleCollapse(city)">
        {{ isExpanded ? `${contentStore.cityManager.getExpandedNameName(city)} ` : contentStore.cityManager.getCollapsedName(city) }}
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
            :city="city"
            :expanded="isExpanded"
          />
        </div>
      </transition>
    </template>
  </div>
</template>

<style scoped lang="scss">
.sidebar {
	width: 170px;
	min-width: 170px;
	height: calc(100vh - 80px);
	height: calc(var(--vh) * 100 - 80px);
	max-height: calc(100vh - 80px);
	max-height: calc(var(--vh) * 100 - 80px);
	position: relative;
	padding: 0 10px 0 var(--font-m);
	margin-top: 20px;
	border-right: 1px solid var(--color-border);
	transition: min-width 0.2s ease-out;
	overflow-x: hidden;
	overflow-y: scroll;
	user-select: none;

	h1 {
		cursor: pointer;
		margin: 12px 0;

		&:first-of-type {
			margin-top: 0;
		}
	}

	h2 {
		color: var(--color-complement-text);
		font-weight: 400;
		text-wrap: nowrap;
		cursor: pointer;
		margin-left: 1em;
	}

	&-sub {
		margin-bottom: var(--font-s);

		&-add {
			width: 100%;
			display: flex;
			text-wrap: nowrap;

			button {
				display: flex;
				align-items: center;
				flex-wrap: nowrap;
				margin-left: 0.5rem;
				padding: 2px 6px;
				border-radius: 5px;
				background-color: var(--color-highlight);
				color: var(--color-normal-text);
				text-wrap: nowrap;

				span {
					margin-right: 4px;
					font-family: var(--font-icon);
				}
			}
		}

		&-no p {
			margin: 0.5rem 0 0.5rem 18px;
			font-size: var(--font-s);
			font-style: italic;
		}
	}

	&-collapse {
		width: 45px;
		min-width: 45px;

		h2 {
			margin-left: 5px;
		}

		&-btnContainer {
			height: fit-content;
			position: fixed;
			top: 78px;
			left: calc(170px - 14px);
			display: flex;
			align-items: center;
			justify-content: center;
			width: fit-content;
			padding: 2px;

			&.notExpanded {
				position: sticky;
				left: 0;
				top: -2px;
				background-color: var(--color-background);
				width: 100%;
				padding-bottom: 8px;
			}

			&-button {
				background-color: var(--color-background);
				padding: 5px;
				border-radius: 5px;
				transition: background-color 0.2s;

				&:hover {
					background-color: var(--color-component-background);
				}

				span {
					font-family: var(--font-icon);
					font-size: var(--font-l);
				}
			}
		}
	}

	// Classes that are provided by vue transitions. Read the official docs for more instructions.
	// https://vuejs.org/guide/built-ins/transition.html
	.collapse-enter-from,
	.collapse-leave-to {
		opacity: 0;
		transform: translateY(-20px);
	}

	.collapse-enter-active,
	.collapse-leave-active {
		transition: opacity 0.2s ease, transform 0.2s ease;
	}
}
</style>
