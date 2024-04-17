<!-- Developed By Taipei Urban Intelligence Center 2023-2024 -->
<!-- 
Lead Developer:  Igor Ho (Full Stack Engineer)
Data Pipelines:  Iima Yu (Data Scientist)
Design and UX: Roy Lin (Fmr. Consultant), Chu Chen (Researcher)
Systems: Ann Shih (Systems Engineer)
Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern) 
-->
<!-- Department of Information Technology, Taipei City Government -->

<script setup>
import { ref, onMounted } from "vue";
import { DashboardComponent } from "city-dashboard-component";

import { useContentStore } from "../store/contentStore";
import router from "../router/index";

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

function toggleFavorite(id) {
	if (contentStore.favorites.components.includes(id)) {
		contentStore.unfavoriteComponent(id);
	} else {
		contentStore.favoriteComponent(id);
	}
}

onMounted(() => {
	contentStore.getAllComponents(searchParams.value);
});
</script>

<template>
  <!-- Search Bar that is always present -->
  <div class="componentview-search">
    <div>
      <input
        v-model="searchParams.searchbyname"
        placeholder="以名稱搜尋"
        @keypress.enter="handleNewQuery"
      >
      <span
        v-if="searchParams.searchbyname !== ''"
        @click="
          () => {
            searchParams.searchbyname = '';
            handleNewQuery();
          }
        "
      >cancel</span>
    </div>
    <button @click="handleNewQuery">
      搜尋
    </button>
  </div>
  <!-- 1. If the components are loaded -->
  <div
    v-if="contentStore.components.length !== 0"
    class="componentview"
  >
    <DashboardComponent
      v-for="item in contentStore.components"
      :key="item.index"
      :config="item"
      mode="preview"
      :info-btn="true"
      :add-btn="
        !contentStore.editDashboard.components
          .map((item) => item.id)
          .includes(item.id)
      "
      :favorite-btn="true"
      :is-favorite="contentStore.favorites?.components.includes(item.id)"
      info-btn-text="資訊頁面"
      @info="
        (item) => {
          router.push({
            name: 'component-info',
            params: { index: item.index },
          });
        }
      "
      @add="
        (id, name) => {
          contentStore.editDashboard.components.push({
            id,
            name,
          });
        }
      "
      @favorite="
        (id) => {
          toggleFavorite(id);
        }
      "
    />
  </div>
  <!-- 2. If the components are still loading -->
  <div
    v-else-if="contentStore.loading"
    class="componentview componentview-nodashboard"
  >
    <div class="componentview-nodashboard-content">
      <div />
    </div>
  </div>
  <!-- 3. If there is an error during loading -->
  <div
    v-else-if="contentStore.error"
    class="componentview componentview-nodashboard"
  >
    <div class="componentview-nodashboard-content">
      <span>sentiment_very_dissatisfied</span>
      <h2>發生錯誤，無法載入</h2>
    </div>
  </div>
  <!-- 4. If there are no components -->
  <div
    v-else
    class="componentview componentview-nodashboard"
  >
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

	@media (min-width: 1250px) {
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
			font-size: var(--font-ms);
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
				margin-bottom: var(--font-ms);
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
</style>
