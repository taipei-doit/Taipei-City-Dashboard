<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { onMounted, ref } from "vue";
import { useMapStore } from "../../../store/mapStore";

import SideBarTab from "../miscellaneous/SideBarTab.vue";

const mapStore = useMapStore();

// The expanded state is also stored in localstorage to retain the setting after refresh
const isExpanded = ref(true);

function toggleExpand() {
	isExpanded.value = isExpanded.value ? false : true;
	localStorage.setItem("isExpandedAdmin", isExpanded.value);
	if (!isExpanded.value) {
		mapStore.resizeMap();
	}
}

onMounted(() => {
	const storedExpandedState = localStorage.getItem("isExpandedAdmin");
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
      adminsidebar: true,
      'adminsidebar-collapse': !isExpanded,
    }"
  >
    <button
      class="adminsidebar-collapse-button"
      @click="toggleExpand"
    >
      <span>{{
        isExpanded
          ? "keyboard_double_arrow_left"
          : "keyboard_double_arrow_right"
      }}</span>
    </button>
    <h2>{{ isExpanded ? `儀表板設定` : `表板` }}</h2>
    <SideBarTab
      icon="dashboard"
      title="公開儀表板"
      :expanded="isExpanded"
      index="dashboard"
    />
    <h2>{{ isExpanded ? `組件設定` : `組件` }}</h2>
    <SideBarTab
      icon="edit_note"
      title="編輯公開組件"
      :expanded="isExpanded"
      index="edit-component"
    />
    <h2>{{ isExpanded ? `問題回報` : `問題` }}</h2>
    <SideBarTab
      icon="bug_report"
      title="待回覆問題"
      :expanded="isExpanded"
      index="issue"
    />
    <SideBarTab
      icon="flood"
      title="民眾災害通報"
      :expanded="isExpanded"
      index="disaster"
    />
    <h2>{{ isExpanded ? `系統總覽` : `系統` }}</h2>
    <SideBarTab
      icon="person"
      title="使用者資訊"
      :expanded="isExpanded"
      index="user"
    />
    <SideBarTab
      icon="handshake"
      title="貢獻者資訊"
      :expanded="isExpanded"
      index="contributor"
    />
  </div>
</template>

<style scoped lang="scss">
.adminsidebar {
	width: 170px;
	min-width: 170px;
	height: calc(100vh - 80px);
	height: calc(var(--vh) * 100 - 80px);
	max-height: calc(100vh - 80px);
	max-height: calc(var(--vh) * 100 - 80px);
	position: relative;
	margin-top: 20px;
	padding: 0 10px 0 var(--font-m);
	border-right: 1px solid var(--color-border);
	transition: min-width 0.2s ease-out;
	overflow-x: hidden;
	overflow-y: scroll;
	user-select: none;

	h2 {
		color: var(--color-complement-text);
		font-weight: 400;
	}

	&-sub {
		margin-bottom: var(--font-s);

		&-add {
			width: 100%;
			display: flex;

			button {
				display: flex;
				align-items: center;
				margin-left: 0.5rem;
				padding: 2px 6px;
				border-radius: 5px;
				background-color: var(--color-highlight);
				color: var(--color-normal-text);

				span {
					margin-right: 4px;
					font-family: var(--font-icon);
				}
			}
		}
	}

	&-collapse {
		width: 45px;
		min-width: 45px;

		h2 {
			margin-left: 5px;
		}

		&-button {
			height: fit-content;
			position: absolute;
			bottom: 10px;
			right: 10px;
			padding: 5px;
			border-radius: 5px;
			font-size: var(--font-ms);
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
</style>
