<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import DistrictChart from "./DistrictChart.vue";

const props = defineProps(["activeChart"]);

const API_BASE = import.meta.env.VITE_API_URL || "/api/dev";

const loading = ref(false);
const errorMessage = ref("");
const modalVisible = ref(false);
const modalDistrictName = ref("");
const modalDistrictRestaurants = ref([]);
const districtRestaurantMap = ref({});
const districtWrapperRef = ref(null);
const districtLabels = ref([]);

const districtsTaipei = [
	"北投區",
	"士林區",
	"內湖區",
	"南港區",
	"松山區",
	"信義區",
	"中山區",
	"大同區",
	"中正區",
	"萬華區",
	"大安區",
	"文山區",
];

const districtChartConfig = computed(() => ({
	color: ["#2e6cae"],
	unit: "間",
	categories: districtsTaipei,
}));

const districtChartSeries = computed(() => [
	{
		name: "異國餐廳",
		data: districtsTaipei.map((district) => ({
			x: district,
			y: (districtRestaurantMap.value[district] || []).length,
		})),
	},
]);

const totalCount = computed(() =>
	districtsTaipei.reduce(
		(sum, district) => sum + (districtRestaurantMap.value[district] || []).length,
		0
	)
);

const selectedDistrictCount = computed(() => modalDistrictRestaurants.value.length);

function getCityFromURL() {
	const params = new URLSearchParams(globalThis.location?.search || "");
	const city = params.get("city") || "taipei";
	if (city === "metrotaipei") {
		return "metrotaipei";
	}
	return "taipei";
}

function normalizeDistrict(rawDistrict) {
	if (!rawDistrict) {
		return "";
	}
	if (districtsTaipei.includes(rawDistrict)) {
		return rawDistrict;
	}
	const found = districtsTaipei.find((district) => rawDistrict.includes(district.replace("區", "")));
	return found || "";
}

async function loadRestaurantPointsFromBackend() {
	const city = getCityFromURL();
	const response = await fetch(`${API_BASE}/foreign-cuisine/restaurants?city=${city}&limit=3500`);

	if (!response.ok) {
		throw new Error("無法從後端資料庫取得異國餐廳資料");
	}

	const payload = await response.json();
	return payload.data || [];
}

function buildDistrictRestaurantMap(rows) {
	const grouped = {};
	districtsTaipei.forEach((district) => {
		grouped[district] = [];
	});

	rows.forEach((row) => {
		const district = normalizeDistrict(row.district || "");
		if (!district || !grouped[district]) {
			return;
		}

		grouped[district].push({
			name: row.name || "未命名餐廳",
			cuisineZh: row.cuisine_zh || "其他異國料理",
			address: row.address || "",
		});
	});

	Object.keys(grouped).forEach((district) => {
		grouped[district].sort((a, b) => a.name.localeCompare(b.name, "zh-Hant"));
	});

	return grouped;
}

async function initializeComponentData() {
	loading.value = true;
	errorMessage.value = "";

	try {
		const rows = await loadRestaurantPointsFromBackend();
		districtRestaurantMap.value = buildDistrictRestaurantMap(rows);
		syncLabelsAfterRender();
	} catch (error) {
		console.error("ForeignRestaurantMapChart error:", error);
		errorMessage.value = "資料取得失敗，請稍後再試";
	} finally {
		loading.value = false;
		syncLabelsAfterRender();
	}
}

function openDistrictModal(districtName) {
	modalDistrictName.value = districtName;
	modalDistrictRestaurants.value = districtRestaurantMap.value[districtName] || [];
	modalVisible.value = true;
}

function closeDistrictModal() {
	modalVisible.value = false;
	modalDistrictName.value = "";
	modalDistrictRestaurants.value = [];
}

function handleDistrictClick(_filter, _mapConfig, districtName) {
	if (!districtName) {
		return;
	}
	openDistrictModal(districtName);
}

function updateDistrictLabelPositions() {
	const wrapper = districtWrapperRef.value;
	if (!wrapper) {
		return;
	}

	const svg = wrapper.querySelector(".districtchart-chart-taipei");
	if (!svg) {
		return;
	}

	const svgBox = svg.getBoundingClientRect();
	if (!svgBox.width || !svgBox.height) {
		return;
	}

	const labels = [];
	svg.querySelectorAll("path[data-name]").forEach((path) => {
		const name = path.dataset.name;
		if (!name || !districtsTaipei.includes(name)) {
			return;
		}

		const box = path.getBoundingClientRect();
		const centerX = box.left + box.width / 2;
		const centerY = box.top + box.height / 2;

		labels.push({
			name,
			left: `${((centerX - svgBox.left) / svgBox.width) * 100}%`,
			top: `${((centerY - svgBox.top) / svgBox.height) * 100}%`,
		});
	});

	districtLabels.value = labels;
}

function syncLabelsAfterRender() {
	nextTick(() => {
		requestAnimationFrame(() => {
			updateDistrictLabelPositions();
		});
	});
}

onMounted(() => {
	if (props.activeChart !== "ForeignRestaurantMapChart") {
		return;
	}
	initializeComponentData();
	window.addEventListener("resize", updateDistrictLabelPositions);
});

onBeforeUnmount(() => {
	window.removeEventListener("resize", updateDistrictLabelPositions);
});
</script>

<template>
  <div
    v-if="activeChart === 'ForeignRestaurantMapChart'"
    class="foreign-restaurant-chart"
  >
    <div
      v-if="loading"
      class="foreign-restaurant-chart-loading"
    >
      讀取異國餐廳資料中...
    </div>

    <div
      v-else-if="errorMessage"
      class="foreign-restaurant-chart-error"
    >
      {{ errorMessage }}
    </div>

    <div
      v-else
      class="foreign-restaurant-chart-main"
    >
			<div
				ref="districtWrapperRef"
				class="foreign-restaurant-chart-district-wrapper"
			>
				<DistrictChart
					:active-chart="'DistrictChart'"
					:active-city="'taipei'"
					:chart_config="districtChartConfig"
					:series="districtChartSeries"
					:map_filter="{ mode: 'byParam' }"
					:map_filter_on="true"
					:map_config="[]"
					@filterByParam="handleDistrictClick"
				/>
				<div class="foreign-restaurant-chart-labels">
					<span
						v-for="item in districtLabels"
						:key="item.name"
						class="foreign-restaurant-chart-label"
						:style="{ left: item.left, top: item.top }"
					>
						{{ item.name }}
					</span>
				</div>
			</div>
    </div>

    <div
      v-if="modalVisible"
      class="foreign-restaurant-chart-modal"
      @click.self="closeDistrictModal"
    >
      <div class="foreign-restaurant-chart-modal-content">
        <header>
          <div>
            <h5>{{ modalDistrictName }} 餐廳清單</h5>
            <p>共 {{ selectedDistrictCount }} 間</p>
          </div>
          <button
            type="button"
            @click="closeDistrictModal"
          >
            關閉
          </button>
        </header>

        <ul v-if="modalDistrictRestaurants.length">
          <li
            v-for="restaurant in modalDistrictRestaurants"
            :key="`${restaurant.name}-${restaurant.address}`"
          >
            <h6>{{ restaurant.name }}</h6>
            <p>{{ restaurant.cuisineZh }}</p>
            <small v-if="restaurant.address">{{ restaurant.address }}</small>
          </li>
        </ul>
        <div
          v-else
          class="foreign-restaurant-chart-modal-empty"
        >
          此行政區目前沒有餐廳資料。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.foreign-restaurant-chart {
	width: 100%;
	height: 100%;
	display: grid;
	grid-template-rows: auto 1fr;
	gap: 10px;

	&-main {
		min-height: 560px;
	}

	&-district-wrapper {
		position: relative;
		height: 100%;
	}

	&-labels {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	&-label {
		position: absolute;
		transform: translate(-50%, -50%);
		font-size: 0.72rem;
		font-weight: 700;
		line-height: 1;
		padding: 2px 4px;
		border-radius: 5px;
		color: #ffffff;
		background: rgba(15, 23, 42, 0.55);
		text-shadow: 0 1px 1px rgba(0, 0, 0, 0.4);
		white-space: nowrap;
	}

	&-loading,
	&-error {
		font-size: 0.8rem;
		color: var(--color-normal-text);
		background: rgba(2, 6, 23, 0.2);
		padding: 8px 10px;
		border-radius: 8px;
	}

	&-modal {
		position: fixed;
		inset: 0;
		z-index: 1200;
		display: flex;
		justify-content: center;
		align-items: center;
		background: rgba(2, 6, 23, 0.55);
		padding: 16px;
	}

	&-modal-content {
		width: min(760px, 100%);
		max-height: min(72vh, 760px);
		overflow: auto;
		background: #0f172a;
		border: 1px solid rgba(148, 163, 184, 0.3);
		border-radius: 12px;
		padding: 12px;

		header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			gap: 12px;
			margin-bottom: 10px;

			h5 {
				font-size: 0.95rem;
				color: #f8fafc;
			}

			p {
				margin-top: 4px;
				font-size: 0.78rem;
				color: #cbd5e1;
			}

			button {
				border: 0;
				border-radius: 8px;
				padding: 6px 10px;
				font-size: 0.78rem;
				color: #e2e8f0;
				background: rgba(30, 93, 158, 0.6);
				cursor: pointer;
			}
		}

		ul {
			list-style: none;
			padding: 0;
			margin: 0;
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
			gap: 8px;
		}

		li {
			padding: 8px;
			border-radius: 8px;
			background: rgba(15, 23, 42, 0.75);
			border: 1px solid rgba(148, 163, 184, 0.18);
		}

		h6 {
			font-size: 0.82rem;
			color: #f8fafc;
		}

		p {
			margin-top: 4px;
			font-size: 0.75rem;
			color: #93c5fd;
		}

		small {
			display: block;
			margin-top: 4px;
			font-size: 0.72rem;
			color: #cbd5e1;
			line-height: 1.4;
		}
	}

	&-modal-empty {
		padding: 12px;
		font-size: 0.8rem;
		color: #cbd5e1;
		text-align: center;
	}

	:deep(.districtchart) {
		height: 100%;
		max-height: none;
		overflow: hidden !important;
	}

	:deep(.districtchart-title) {
		display: none;
	}

	:deep(.districtchart-chart) {
		height: 100%;
		min-height: 0;
		align-items: center;
	}

	:deep(.districtchart-chart svg) {
		display: block;
		width: 100% !important;
		height: 100% !important;
	}

	:deep(.districtchart-chart-taipei) {
		display: block;
		max-height: 100%;
		max-width: 100%;
		width: 100% !important;
		height: 100% !important;
	}
}
</style>
