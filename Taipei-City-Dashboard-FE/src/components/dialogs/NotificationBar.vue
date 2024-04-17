<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- This component has two modes "success" and "fail". The modes are controlled via the mapStore -->

<script setup>
import { useDialogStore } from "../../store/dialogStore";

const dialogStore = useDialogStore();

const statusToIcon = {
	success: "check_circle",
	fail: "error",
	info: "lightbulb",
};
</script>

<template>
  <Teleport to="body">
    <Transition name="notification">
      <div
        v-if="dialogStore.dialogs.notificationBar"
        class="notificationbar"
      >
        <span
          :class="{
            success: dialogStore.notification.status === 'success',
            fail: dialogStore.notification.status === 'fail',
            info: dialogStore.notification.status === 'info',
          }"
        >{{ statusToIcon[dialogStore.notification.status] }}</span>
        <h5
          :class="{
            success: dialogStore.notification.status === 'success',
            fail: dialogStore.notification.status === 'fail',
            info: dialogStore.notification.status === 'info',
          }"
        >
          {{ dialogStore.notification.message }}
        </h5>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
.notificationbar {
	height: 3rem;
	width: fit-content;
	position: fixed;
	top: 20px;
	left: 50%;
	z-index: 100;
	display: flex;
	align-items: center;
	padding: 0 var(--font-ms);
	border: solid 1px var(--color-border);
	border-radius: 5px;
	box-shadow: 0px 5px 10px black;
	background-color: rgb(63, 63, 63);
	transform: translateX(-50%);

	span {
		margin-right: 10px;
		font-family: var(--font-icon);
		font-size: var(--font-l);
	}

	h5 {
		font-weight: 400;
	}
}

.success {
	color: greenyellow;
}

.fail {
	color: rgb(237, 90, 90);
}

.info {
	color: var(--color-highlight);
}

// Classes that are provided by vue transitions. Read the official docs for more instructions.
// https://vuejs.org/guide/built-ins/transition.html
.notification-enter-from,
.notification-leave-to {
	top: -60px;
}

.notification-enter-active,
.notification-leave-active {
	transition: top 0.3s ease;
}
</style>
