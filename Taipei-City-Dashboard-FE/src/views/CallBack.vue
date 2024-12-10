<script setup>
import { onMounted } from "vue";
import router from "../router";
import { usePersonStore } from "../store/personStore";

const personStore = usePersonStore();

onMounted(() => {
	const urlParams = new URLSearchParams(window.location.search);
	const code = urlParams.get("code");

	if (!code || code.length !== 6 || personStore.code) {
		router.replace("/dashboard");
	} else {
		personStore.loginByTaipei(code);
	}
});
</script>

<template>
  <div>正在為您導向臺北城市儀表板...</div>
</template>

<style scoped></style>
