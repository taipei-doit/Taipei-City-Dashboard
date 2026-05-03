<script setup>
import { onMounted, ref } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

const { VITE_BE_URL } = import.meta.env;

const { t } = useI18n();

const components = ref([]);
const hasError = ref(false);

onMounted(() => {
	axios.get(`${VITE_BE_URL}/component`, {
		params: {
			pagenum: 1,
			pagesize: 1000,
			sort: "id",
			order: "asc"
		}
	})
		.then((response) => {
			components.value = response.data.data;
		})
		.catch((error) => {
			console.error(error);
			hasError.value = true;
		});
});
</script>

<template>
	<div class="registrypage">
		<div class="registrypage-positioner">
			<h1>{{ t('component-registry.name') }}</h1>
			<div class="registrypage-table">
				<div class="registrypage-table-legend">
					<h2>{{ t('component-registry.legend') }}</h2>
					<div>
						<div class="registrypage-table-compstatus">
							<span>bar_chart</span>
							<p>{{ t('component-registry.chart') }}</p>
						</div>
						<div class="registrypage-table-compstatus">
							<span>map</span>
							<p>{{ t('component-registry.map') }}</p>
						</div>
						<div class="registrypage-table-compstatus">
							<span>tune</span>
							<p>{{ t('component-registry.map-filter') }}</p>
						</div>
						<div class="registrypage-table-compstatus">
							<span>insights</span>
							<p>{{ t('component-registry.history-data') }}</p>
						</div>
					</div>
				</div>
				<table>
					<thead>
						<tr>
							<th>{{ t('component-registry.compname') }}</th>
							<th>{{ t('component-registry.id') }}</th>
							<th>{{ t('component-registry.status') }}</th>
							<th>{{ t('component-registry.source') }}</th>
							<th>{{ t('component-registry.features') }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="component in components" :key="component.id">
							<td>{{ component.name }}</td>
							<td>{{ component.id }} - {{ component.index }}</td>
							<td>
								<div :style="{ display: 'flex', justifyContent: 'center' }">
									<div class="registrypage-table-compstatus warning"
										v-if="component.time_from === 'maintain'">
										<span>cancel</span>
										<p>{{ t('component-registry.maintaining') }}</p>
									</div>
									<div class="registrypage-table-compstatus demo"
										v-else-if="component.time_from === 'demo'">
										<span>watch_later</span>
										<p>{{ t('component-registry.demo') }}</p>
									</div>
									<div class="registrypage-table-compstatus online" v-else>
										<span>check_circle</span>
										<p>{{ t('component-registry.online') }}</p>
									</div>
								</div>
							</td>
							<td>{{ component.source }}</td>
							<td>
								<div
									:style="{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', columnGap: '4px', rowGap: '4px' }">
									<div class="registrypage-table-compstatus"
										v-if="component.chart_config.types[0] !== 'MapLegend'">
										<span>bar_chart</span>
									</div>
									<div class="registrypage-table-compstatus" v-if="component.map_config[0]">
										<span>map</span>
									</div>
									<div class="registrypage-table-compstatus" v-if="component.map_filter">
										<span>tune</span>
									</div>
									<div class="registrypage-table-compstatus" v-if="component.history_config?.range">
										<span>insights</span>
									</div>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
.registrypage {
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

	&-table {
		width: 100%;
		align-self: flex-start;
		height: calc(100vh - 120px);
		height: calc(var(--vh) * 100 - 120px);
		border-top: dashed 1px var(--color-border);
		padding-top: 2rem;
		overflow-x: scroll;
		overflow-y: scroll;

		&-legend {
			display: flex;
			flex-direction: column;
			margin-bottom: 1rem;
			padding: 0.75rem;
			border-radius: 5px;
			background-color: var(--color-border);
			border: dashed 1px var(--color-complement-text);

			h2 {
				margin-bottom: 0.5rem;
			}

			&>div {
				display: flex;
				flex-wrap: wrap;
				column-gap: 4px;
				row-gap: 4px;
			}
		}

		table {
			width: 100%;
			border-collapse: collapse;
			margin-bottom: 1.5rem;
			border-top-left-radius: 5px;
			border-top-right-radius: 5px;

			th,
			td {
				border: solid 1px var(--color-border);
				padding: 0.5rem;
				text-align: center;
			}

			th {
				background-color: var(--color-border);
			}

			td {
				min-width: 180px;
			}
		}

		&-compstatus {
			width: fit-content;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 4px;
			border-radius: 5px;
			background-color: var(--color-component-background);

			span {
				font-family: var(--font-icon);
				color: var(--color-complement-text);
			}

			p {
				margin-left: 4px;
				font-size: var(--font-ms);
				color: var(--color-complement-text);
			}
		}

		.online {
			background-color: rgba(29, 187, 29, 0.2);

			span,
			p {
				color: rgb(29, 187, 29);
			}
		}

		.warning {
			background-color: rgba(227, 42, 42, 0.4);

			span,
			p {
				color: rgb(227, 42, 42);
			}
		}

		.demo {
			background-color: rgba(255, 207, 35, 0.4);

			span,
			p {
				color: rgb(228, 178, 0);
			}
		}
	}

	h1 {
		align-self: flex-start;
		margin-bottom: 2rem;
		font-size: 2rem;
		height: 3rem;
	}

	hr {
		margin: 3rem 0;
		width: 100%;
		height: 0;
		border: none;
		border-top: 1px dashed var(--color-border);
	}
}
</style>