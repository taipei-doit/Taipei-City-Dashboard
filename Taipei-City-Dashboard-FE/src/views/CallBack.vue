<script setup>
import { onMounted } from "vue";
import router from "../router";
import { useAuthStore } from "../store/authStore";

const authStore = useAuthStore();

onMounted(() => {
	const urlParams = new URLSearchParams(window.location.search);
	const code = urlParams.get("code");

	if (!code || code.length !== 6 || authStore.token) {
		router.replace("/dashboard");
	} else {
		authStore.loginByTaipeiPass(code);
	}
});
</script>

<template>
  <div>正在為您導向臺北城市儀表板...</div>
</template>

<style scoped></style>
