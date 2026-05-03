<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

const { VITE_BE_URL } = import.meta.env;

const { t } = useI18n();

const loading = ref(false);
const componentQuery = ref(5);
const component = ref('');
const componentChartQuery = ref(5);
const componentChart = ref('');
const componentHistoryQuery = ref(5);
const componentHistory = ref('');
const dashboard = ref('');


async function getAllComponents() {
	loading.value = true;
	try {
		const res = await axios.get(`${VITE_BE_URL}/component/${componentQuery.value}`);
		component.value = JSON.stringify(res.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	} catch (error) {
		component.value = JSON.stringify(error.response.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	}
}

async function getComponentChart() {
	loading.value = true;
	try {
		const res = await axios.get(`${VITE_BE_URL}/component/${componentChartQuery.value}/chart`);
		componentChart.value = JSON.stringify(res.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	} catch (error) {
		componentChart.value = JSON.stringify(error.response.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	}
}

async function getComponentHistory() {
	loading.value = true;
	try {
		const res = await axios.get(`${VITE_BE_URL}/component/${componentHistoryQuery.value}/history`);
		componentHistory.value = JSON.stringify(res.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	} catch (error) {
		componentHistory.value = JSON.stringify(error.response.data, null, 4).trimStart();
		setTimeout(() => {
			loading.value = false;
		}, 1000);
	}
}

async function getAllDashboards() {
	loading.value = true;
	const res = await axios.get(`${VITE_BE_URL}/dashboard`);
	dashboard.value = JSON.stringify(res.data, null, 4).trimStart();
	setTimeout(() => {
		loading.value = false;
	}, 1000);
}
</script>

<template>
	<div class="apipage">
		<div class="apipage-positioner">
			<h1>{{ t('api-tester.name') }}</h1>
			<div class="apipage-tester">
				<!-- Get Component Config By ID -->
				<h2>{{ t('api-tester.config') }}</h2>
				<div class="apipage-tester-url">
					<code style="background-color: #6bdd9a; color: black; font-weight: bold">GET</code>
					<code>/component/</code>
					<input v-model="componentQuery" @keypress.enter="getAllComponents">
				</div>
				<div class="apipage-tester-button">
					<button @click="getAllComponents" :disabled="loading">{{ t('api-tester.call') }}</button>
					<RouterLink to="/back-end/component-config-apis">{{ t('api-tester.doc') }}</RouterLink>
				</div>
				<textarea :value="component" disabled>
				</textarea>
				<!-- Get Component Chart Data -->
				<h2>{{ t('api-tester.chart') }}</h2>
				<div class="apipage-tester-url">
					<code style="background-color: #6bdd9a; color: black; font-weight: bold">GET</code>
					<code>/component/</code>
					<input v-model="componentChartQuery" @keypress.enter="getComponentChart">
					<code>/chart</code>
				</div>
				<div class="apipage-tester-button">
					<button @click="getComponentChart" :disabled="loading">{{ t('api-tester.call') }}</button>
					<RouterLink to="/back-end/component-data-apis">{{ t('api-tester.doc') }}</RouterLink>
				</div>
				<textarea :value="componentChart" disabled>
				</textarea>
				<!-- Get Component History Data -->
				<h2>{{ t('api-tester.history') }}</h2>
				<div class="apipage-tester-url">
					<code style="background-color: #6bdd9a; color: black; font-weight: bold">GET</code>
					<code>/component/</code>
					<input v-model="componentHistoryQuery" @keypress.enter="getComponentHistory">
					<code>/history</code>
				</div>
				<div class="apipage-tester-button">
					<button @click="getComponentHistory" :disabled="loading">{{ t('api-tester.call') }}</button>
					<RouterLink to="/back-end/component-data-apis">{{ t('api-tester.doc') }}</RouterLink>
				</div>
				<textarea :value="componentHistory" disabled>
				</textarea>
				<!-- Get All Dashboards -->
				<h2>{{ t('api-tester.dashboard') }}</h2>
				<div class="apipage-tester-url">
					<code style="background-color: #6bdd9a; color: black; font-weight: bold">GET</code>
					<code>/dashboard</code>
				</div>
				<div class="apipage-tester-button">
					<button @click="getAllDashboards" :disabled="loading">{{ t('api-tester.call') }}</button>
					<RouterLink to="/back-end/dashboard-apis">{{ t('api-tester.doc') }}</RouterLink>
				</div>
				<textarea :value="dashboard" disabled>
				</textarea>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.apipage {
	display: flex;
	justify-content: center;
	width: 100%;
	height: calc(100vh - 60px);
	height: calc(var(--vh) * 100 - 60px);
	max-height: calc(100vh - 60px);
	max-height: calc(var(--vh) * 100 - 60px);

	@media screen and (max-width: 850px) {
		height: calc(100% - 60px);
	}

	&-positioner {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2rem 1.5rem 1.5rem 3rem;
		width: 100%;

		@media screen and (min-width: 1000px) {
			width: 1000px
		}

		@media screen and (max-width: 850px) {
			padding: 2rem 1rem 1rem 1rem;
		}
	}

	&-tester {
		width: 100%;
		align-self: flex-start;
		height: calc(100vh - 120px);
		height: calc(var(--vh) * 100 - 120px);
		border-top: dashed 1px var(--color-border);
		overflow-y: scroll;

		&-url {
			display: flex;
			overflow-x: scroll;
			margin: 1rem 0 0.5rem;
			column-gap: 4px;

			&::-webkit-scrollbar {
				height: 4px;
			}

			&::-webkit-scrollbar-thumb {
				background-color: var(--color-complement-text);
				border-radius: 8px;
			}

			&::-webkit-scrollbar-corner {
				background-color: rgba(0, 0, 0, 0);
			}
		}

		&-button {
			display: flex;
			column-gap: 0.5rem;
			margin-bottom: 0.75rem;
			align-items: center;

			button {
				display: flex;
				align-items: center;
				padding: 6px;
				border-radius: 5px;
				background-color: var(--color-highlight);
				color: white;
				transition: opacity 0.2s;

				&:hover {
					opacity: 0.7;
				}

				&:disabled {
					opacity: 0.5;
					cursor: not-allowed;
				}
			}

			a {
				color: var(--color-highlight);
				transition: opacity 0.2s;
				font-size: var(--font-ms);

				&:hover {
					opacity: 0.7;
				}
			}
		}

		code {
			font-family: var(--font-code);
			background-color: var(--color-component-background);
			padding: 2px 4px;
			border-radius: 5px;
			color: var(--color-normal-text);
			overflow-y: scroll;
			text-wrap: nowrap;
			flex-shrink: 0;
		}

		textarea {
			height: 150px;
			width: calc(100% - 2rem);
			font-family: var(--font-code);
			background-color: var(--color-component-background);
			padding: 1rem;
			border-radius: 5px;
			border: none;
			text-wrap: nowrap;
			color: var(--color-normal-text);
			overflow-y: scroll;
			overflow-x: scroll;
			outline: none;
			resize: vertical;

			&::-webkit-scrollbar {
				width: 8px;
				height: 8px;
			}

			&::-webkit-scrollbar-thumb {
				background-color: var(--color-complement-text);
				border-radius: 8px;
			}

			&::-webkit-scrollbar-corner {
				background-color: rgba(0, 0, 0, 0);
			}
		}

		input {
			width: 1.5rem;
			font-size: var(--font-ms);
			padding: 2px 4px;
			flex-shrink: 0;
		}
	}

	h1 {
		align-self: flex-start;
		margin-bottom: 2rem;
		font-size: 2rem;
		height: 3rem;
	}

	h2 {
		font-size: var(--font-l);
		text-align: justify;
		margin-top: 2rem;
	}
}
</style>