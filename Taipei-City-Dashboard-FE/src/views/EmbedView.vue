<!-- eslint-disable no-mixed-spaces-and-tabs -->
<!-- eslint-disable indent -->
<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import http from "../router/axios";
import { DashboardComponent } from "city-dashboard-component";
import { useContentStore } from "../store/contentStore";

import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";

const contentStore = useContentStore();
const route = useRoute();

const content = ref(null);

onMounted(async () => {
	try {
		const res = await http.get(`/component/${route.params.id}`);
		const resChart = await http.get(`/component/${route.params.id}/chart`, {
			params: !["static", "current", "demo"].includes(
				res.data.data.time_from
			)
				? getComponentDataTimeframe(
						res.data.data.time_from,
						res.data.data.time_to,
						true
				  )
				: {},
		});
		content.value = res.data.data;
		content.value.chart_data = resChart.data.data;
		if (resChart.data.categories) {
			content.value.chart_config.categories = resChart.data.categories;
		}
		contentStore.loading = false;
	} catch (error) {
		console.error(error);
		contentStore.loading = false;
	}
});
</script>

<template>
  <div class="embedview">
    <div
      v-if="contentStore.loading"
      class="embedview-loading"
    >
      <div />
    </div>
    <DashboardComponent
      v-else-if="content"
      :config="content"
      :footer="false"
      :style="{
        height: 'calc(100% - 36px)',
        maxHeight: 'calc(100% - 36px)',
      }"
    />
    <div
      v-else
      class="embedview-error"
    >
      <span>warning</span>
      <p>查無組件，請確認組件ID是否正確</p>
      <p>Component Not Found</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.embedview {
	height: calc(100 * var(--vh));
	max-height: calc(100 * var(--vh));
	display: flex;
	justify-content: center;

	&-loading {
		display: flex;
		align-self: center;
		align-items: center;
		justify-content: center;

		div {
			width: 2rem;
			height: 2rem;
			border-radius: 50%;
			border: solid 4px var(--color-border);
			border-top: solid 4px var(--color-highlight);
			animation: spin 0.7s ease-in-out infinite;
		}
	}

	&-error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;

		span {
			color: var(--color-complement-text);
			margin-bottom: 0.5rem;
			font-family: var(--font-icon);
			font-size: 2rem;
		}

		p {
			color: var(--color-complement-text);
		}
	}
}
@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
</style>
