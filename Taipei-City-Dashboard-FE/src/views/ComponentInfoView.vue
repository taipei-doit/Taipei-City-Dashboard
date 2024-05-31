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
import router from "../router";
import { DashboardComponent } from "city-dashboard-component";
import { useContentStore } from "../store/contentStore";
import { useDialogStore } from "../store/dialogStore";
import { useAuthStore } from "../store/authStore";

import HistoryChart from "../components/charts/HistoryChart.vue";
import ReportIssue from "../components/dialogs/ReportIssue.vue";
import DownloadData from "../components/dialogs/DownloadData.vue";
import EmbedComponent from "../components/dialogs/EmbedComponent.vue";

const contentStore = useContentStore();
const dialogStore = useDialogStore();
const authStore = useAuthStore();

const searchParams = ref({
	searchbyindex: "",
	searchbyname: "",
	sort: "",
	order: "",
	pagesize: 200,
	pagenum: 1,
});

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
  <!-- Button to navigate back to /component -->
  <div class="componentinfoview-header">
    <button
      v-if="
        authStore.isMobileDevice ||
          authStore.isNarrowDevice ||
          !authStore.token
      "
      @click="router.back()"
    >
      <span>arrow_circle_left</span>
      <p>返回儀表板</p>
    </button>
    <RouterLink
      v-else
      to="/component"
    >
      <span>arrow_circle_left</span>
      <p>返回組件瀏覽平台</p>
    </RouterLink>
  </div>

  <!-- 1. If the component is found -->
  <div
    v-if="dialogStore.moreInfoContent"
    :class="{
      componentinfoview: true,
      'no-history': !dialogStore.moreInfoContent.history_data,
    }"
  >
    <!-- 1-1. View the entire component and its chart data -->
    <div class="componentinfoview-component">
      <DashboardComponent
        :key="dialogStore.moreInfoContent.index"
        :config="dialogStore.moreInfoContent"
        :style="{ height: '350px', width: '400px' }"
        :add-btn="
          !contentStore.editDashboard.components
            .map((item) => item.id)
            .includes(dialogStore.moreInfoContent.id) &&
            !!authStore.token
        "
        :favorite-btn="!!authStore.token"
        :is-favorite="
          contentStore.favorites?.components.includes(
            dialogStore.moreInfoContent.id
          )
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
    <!-- 1-2. View the component's information -->
    <div class="componentinfoview-content">
      <div :style="{ overflowY: 'scroll' }">
        <h3>組件 ID | Index</h3>
        <p>
          {{
            ` ID: ${dialogStore.moreInfoContent.id}｜Index: ${dialogStore.moreInfoContent.index} `
          }}
        </p>
        <h3>組件說明</h3>
        <p>{{ dialogStore.moreInfoContent.long_desc }}</p>
        <h3>範例情境</h3>
        <p>{{ dialogStore.moreInfoContent.use_case }}</p>
      </div>
      <div class="componentinfoview-content-control">
        <button
          v-if="authStore.token"
          @click="
            dialogStore.showReportIssue(
              dialogStore.moreInfoContent.id,
              dialogStore.moreInfoContent.index,
              dialogStore.moreInfoContent.name
            )
          "
        >
          <span>flag</span>回報
        </button>
        <button
          v-if="
            dialogStore.moreInfoContent.chart_config.types[0] !==
              'MetroChart'
          "
          @click="dialogStore.showDialog('downloadData')"
        >
          <span>download</span>下載
        </button>
        <button @click="dialogStore.showDialog('embedComponent')">
          <span>code</span>內嵌
        </button>
      </div>
    </div>
    <!-- 1-3. View the component's history data -->
    <div
      v-if="dialogStore.moreInfoContent.history_data"
      class="componentinfoview-history"
    >
      <h3>歷史資料</h3>
      <HistoryChart
        :chart_config="dialogStore.moreInfoContent.chart_config"
        :series="dialogStore.moreInfoContent.history_data"
        :history_config="dialogStore.moreInfoContent.history_config"
      />
    </div>
    <!-- 1-4. View the component's source links and contributors -->
    <div
      :class="{
        'componentinfoview-source': true,
        'no-links': !dialogStore.moreInfoContent.links[0],
      }"
    >
      <div
        v-if="dialogStore.moreInfoContent.links[0]"
        class="componentinfoview-source-links"
      >
        <h3>相關資料</h3>
        <a
          v-for="(link, index) in dialogStore.moreInfoContent.links"
          :key="`${link}-${index}`"
          :href="link"
          target="_blank"
          rel="noreferrer"
        ><div>{{ index + 1 }}</div>
          <p>{{ link }}</p></a>
      </div>
      <div
        v-if="dialogStore.moreInfoContent.contributors"
        class="componentinfoview-source-contributors"
      >
        <h3>協作者</h3>
        <div>
          <div
            v-for="contributor in dialogStore.moreInfoContent
              .contributors"
            :key="contributor"
          >
            <a
              :href="contentStore.contributors[contributor].link"
              target="_blank"
              rel="noreferrer"
            ><img
               :src="
                 contentStore.contributors[
                   contributor
                 ].image.includes('http')
                   ? contentStore.contributors[contributor]
                     .image
                   : `/images/contributors/${contentStore.contributors[contributor].image}`
               "
               :alt="`協作者-${contentStore.contributors[contributor].user_name}`"
             >
              <p>
                {{
                  contentStore.contributors[contributor]
                    .user_name
                }}
              </p>
            </a>
          </div>
        </div>
      </div>
    </div>
    <ReportIssue />
    <DownloadData />
    <EmbedComponent />
  </div>
  <!-- 2. If the page is still loading -->
  <div
    v-else-if="contentStore.loading"
    class="componentinfoview componentinfoview-nodashboard"
  >
    <div class="componentinfoview-nodashboard-content">
      <div />
    </div>
  </div>
  <!-- 3. If the component is not found or an error happened -->
  <div
    v-else
    class="componentinfoview componentinfoview-nodashboard"
  >
    <div class="componentinfoview-nodashboard-content">
      <span>sentiment_very_dissatisfied</span>
      <h2>發生錯誤，無法載入。請確認組件Index是否正確。</h2>
    </div>
  </div>
</template>

<style scoped lang="scss">
.componentinfoview {
	width: calc(100% - 26px);
	max-width: 1300px;
	height: calc(100vh - 60px);
	height: calc(var(--vh) * 100 - 60px);
	display: grid;
	grid-template-columns: 400px 400px 400px;
	grid-template-rows: 386px max-content max-content;
	grid-template-areas:
		"info content source"
		"history history history";
	column-gap: var(--font-s);
	row-gap: var(--font-s);
	margin-top: var(--font-ms);
	padding: 0 12px var(--font-m) 10px;
	overflow-y: scroll;

	h3 {
		flex-shrink: 0;
		font-size: var(--font-m);
	}

	p {
		margin-bottom: var(--font-ms);
		color: var(--color-complement-text);
		font-size: var(--font-ms);
	}

	&::-webkit-scrollbar {
		width: 4px;
	}
	&::-webkit-scrollbar-thumb {
		border-radius: 4px;
		background-color: rgba(136, 135, 135, 0.5);
	}
	&::-webkit-scrollbar-thumb:hover {
		background-color: rgba(136, 135, 135, 1);
	}

	@media (max-width: 1550px) {
		grid-template-columns: 1fr 1fr 1fr;
	}

	@media (max-width: 1300px) {
		grid-template-columns: 1fr 1fr;
		grid-template-areas:
			"info content"
			"history history"
			"source source";
	}

	@media (max-width: 1000px) {
		width: calc(100% - 20px);
		padding-right: 10px;
	}

	@media (max-width: 600px) {
		grid-template-columns: 1fr;
		grid-template-rows: 386px max-content max-content max-content;
		grid-template-areas:
			"info"
			"content"
			"history"
			"source";
	}

	&-header {
		margin: 20px var(--font-m) 0 10px;

		a,
		button {
			display: flex;
			align-items: center;
			transition: opacity 0.2s;

			&:hover {
				opacity: 0.8;
			}

			span {
				margin-right: 4px;
				color: var(--color-highlight);
				font-size: var(--font-m);
				font-family: var(--font-icon);
				user-select: none;
			}

			p {
				color: var(--color-highlight);
				font-size: var(--font-ms);
				user-select: none;
			}
		}
	}

	&-component {
		border-radius: 5px;
		background-color: var(--color-component-background);
	}

	&-content {
		grid-area: content;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: var(--font-m);
		border-radius: 5px;
		background-color: var(--color-component-background);
		overflow-y: scroll;

		&-control {
			align-self: flex-end;
			max-height: 26px;
			min-height: 26px;
			display: flex;
			flex: 1;
			margin-top: var(--font-s);

			span {
				margin-right: 4px;
				font-family: var(--font-icon);
				font-size: var(--font-m);
			}

			button {
				display: flex;
				align-items: center;
				margin-right: 8px;
				padding: 2px 4px;
				border-radius: 5px;
				background-color: var(--color-highlight);
				font-size: var(--font-ms);
				transition: opacity 0.2s;

				&:hover {
					opacity: 0.8;
				}
			}
		}
	}

	&-history {
		height: 220px;
		width: calc(100% - var(--font-m) * 2);
		grid-area: history;
		padding: var(--font-m);
		border-radius: 5px;
		background-color: var(--color-component-background);
	}

	&-source {
		grid-area: source;
		display: grid;
		grid-template-rows: 1fr 1fr;
		grid-template-areas:
			"links"
			"contributors";
		row-gap: var(--font-s);
		column-gap: var(--font-s);
		border-radius: 5px;

		@media (max-width: 1300px) {
			grid-template-rows: 200px;
			grid-template-columns: 1fr 1fr;
			grid-template-areas: "links contributors";
		}

		@media (max-width: 600px) {
			grid-template-columns: 1fr;
			grid-template-rows: 1fr 1fr;
			grid-template-areas:
				"links"
				"contributors";
		}

		&-links {
			height: calc(100% - 36px);
			grid-area: links;
			display: flex;
			flex-direction: column;
			padding: var(--font-m);
			border-radius: 5px;
			background-color: var(--color-component-background);
			overflow-y: scroll;

			a {
				display: flex;
				flex-shrink: 0;
				column-gap: 4px;
				margin-top: 8px;

				div {
					min-width: var(--font-l);
					height: var(--font-l);
					display: flex;
					align-items: center;
					justify-content: center;
					border-radius: 50%;
					background-color: var(--color-complement-text);
				}

				p {
					margin-bottom: 0;
					transition: color 0.2s;
					&:hover {
						color: var(--color-highlight);
					}
				}
			}
		}

		&-contributors {
			height: calc(100% - 36px);
			grid-area: contributors;
			display: flex;
			flex-direction: column;
			padding: var(--font-m);
			border-radius: 5px;
			background-color: var(--color-component-background);

			& > div {
				overflow-y: scroll;
				display: flex;
				column-gap: 8px;
				row-gap: 4px;
				flex-wrap: wrap;
				margin: 8px 0 0;
			}

			a {
				min-width: 100px;
				display: flex;
				align-items: center;

				p {
					margin: 0;
					transition: color 0.2s;
				}

				img {
					height: var(--font-xl);
					width: var(--font-xl);
					margin-right: 8px;
					border-radius: 50%;
				}

				&:hover p {
					color: var(--color-highlight);
				}
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

.no-history {
	grid-template-areas: "info content source";

	@media (max-width: 1300px) {
		grid-template-columns: 1fr 1fr;
		grid-template-areas:
			"info content"
			"source source";
	}

	@media (max-width: 600px) {
		grid-template-columns: 1fr;
		grid-template-areas:
			"info"
			"content"
			"source";
	}
}

.no-links {
	grid-template-areas:
		"contributors"
		"contributors";

	@media (max-width: 1300px) {
		grid-template-areas: "contributors contributors";
	}
	@media (max-width: 600px) {
		grid-template-areas: "contributors";
	}
}
</style>
