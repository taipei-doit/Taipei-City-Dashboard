<!-- eslint-disable no-mixed-spaces-and-tabs -->
<!-- eslint-disable indent -->
<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import http from "../router/axios";
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import { useContentStore } from "../store/contentStore";

import { getComponentDataTimeframe } from "../assets/utilityFunctions/dataTimeframe";

const contentStore = useContentStore();
const route = useRoute();

const content = ref(null);
const cities = computed(() => {
	const cities = contentStore.embedComponents.map((data) => data.city)
	return contentStore.cityManager.getCities(cities)
});

function changeCity(city) {
	const selectedComponent = contentStore.embedComponents.find(
		(data) => data.city === city
	);
	if (selectedComponent) {
		content.value = selectedComponent;
	}
};

onMounted(async () => {
	try {
		const res = await http.get(`/component/${route.params.id}/all`);
		const resData = res.data.data;

		for (const component of resData) {
			const response = await http.get(
				`/component/${component.id}/chart`,
				{
					params: {
						city: component.city,
						...!["static", "current", "demo"].includes(
							component.time_from
						)
						? getComponentDataTimeframe(
							component.time_from,
							component.time_to,
							true
						)
						: {}
					},
				}
			);
			component.chart_data = response.data.data;
			if (response.data.categories) {
				component.chart_config.categories = response.data.categories;
			}
		}
		contentStore.embedComponents = res.data.data;
		content.value = resData.find(
			(data) => data.city === route.params.city
		);
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
      :active-city="content.city"
      :select-btn="true"
      :select-btn-disabled="cities.length === 1"
      :select-btn-list="cities"
      :city-tag="cities"
      :style="{
        height: 'calc(100% - 36px)',
        maxHeight: 'calc(100% - 36px)',
      }"
      @change-city="changeCity"
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
