<script setup>
import { ref, onMounted } from "vue";
import { useContentStore } from "../store/contentStore";
import ComponentPreview from "../components/components/ComponentPreview.vue";

const contentStore = useContentStore();

const searchParams = ref({
	searchbyindex: "",
	searchbyname: "",
	sort: "",
	order: "",
	pagesize: 200,
	pagenum: 1,
});

function handleNewQuery() {
	contentStore.getAllComponents(searchParams.value);
}

onMounted(() => {
	contentStore.getAllComponents(searchParams.value);
});
</script>

<template>
	<div class="componentview-search">
		<div>
			<input
				placeholder="以名稱搜尋"
				v-model="searchParams.searchbyname"
				@keypress.enter="handleNewQuery"
			/>
			<span
				v-if="searchParams.searchbyname !== ''"
				@click="
					() => {
						searchParams.searchbyname = '';
						handleNewQuery();
					}
				"
				>cancel</span
			>
		</div>
		<button @click="handleNewQuery">搜尋</button>
	</div>
	<!-- if dashboard is still loading -->
	<div
		v-if="contentStore.loading"
		class="componentview componentview-nodashboard"
	>
		<div class="componentview-nodashboard-content">
			<div></div>
		</div>
	</div>
	<div v-else-if="contentStore.components.length !== 0" class="componentview">
		<ComponentPreview
			v-for="item in contentStore.components"
			:content="item"
			:key="item.index"
		/>
	</div>
	<div
		v-else-if="contentStore.error"
		class="componentview componentview-nodashboard"
	>
		<div class="componentview-nodashboard-content">
			<span>sentiment_very_dissatisfied</span>
			<h2>發生錯誤，無法載入</h2>
		</div>
	</div>
	<div v-else class="componentview componentview-nodashboard">
		<div class="componentview-nodashboard-content">
			<span>search_off</span>
			<h2>查無組件</h2>
			<p>請重新搜尋或更改篩選條件</p>
		</div>
	</div>
</template>

<style scoped lang="scss">
.componentview {
	max-height: calc(100vh - 151px);
	max-height: calc(var(--vh) * 100 - 151px);
	display: grid;
	row-gap: var(--font-s);
	column-gap: var(--font-s);
	margin: var(--font-m) var(--font-m);
	overflow-y: scroll;

	@media (min-width: 720px) {
		grid-template-columns: 1fr 1fr;
	}

	@media (min-width: 1150px) {
		grid-template-columns: 1fr 1fr 1fr;
	}

	@media (min-width: 1800px) {
		grid-template-columns: 1fr 1fr 1fr 1fr;
	}

	@media (min-width: 2200px) {
		grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
	}

	&-search {
		display: flex;
		column-gap: 0.5rem;
		margin-top: var(--font-m);
		margin-left: var(--font-m);

		div {
			position: relative;

			span {
				position: absolute;
				right: 0;
				top: 0.3rem;
				margin-right: 4px;
				color: var(--color-complement-text);
				font-family: var(--font-icon);
				font-size: var(--font-m);
				cursor: pointer;
				transition: color 0.2s;

				&:hover {
					color: var(--color-highlight);
				}
			}
		}

		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			margin-right: 0.4rem;
			padding: 0px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-m);
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}
		}
	}

	&-nodashboard {
		grid-template-columns: 1fr;

		&-content {
			width: 100%;
			height: calc(100vh - 127px);
			height: calc(var(--vh) * 100 - 127px);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;

			span {
				margin-bottom: 1rem;
				font-family: var(--font-icon);
				font-size: 2rem;
			}

			div {
				width: 2rem;
				height: 2rem;
				border-radius: 50%;
				border: solid 4px var(--color-border);
				border-top: solid 4px var(--color-highlight);
				animation: spin 0.7s ease-in-out infinite;
			}

			p {
				color: var(--color-complement-text);
			}
		}
	}
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}
</style>
