<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "../store/authStore";

const authStore = useAuthStore();

onMounted(() => {
	// const urlParams = new URLSearchParams(window.location.search);
	// const code = urlParams.get("code");
	// const state = urlParams.get("state");
	authStore.loginByTaipeiPass();
});
</script>

<template>
	<div>正在為您導向臺北城市儀表板...</div>
</template>

<style scoped></style>
