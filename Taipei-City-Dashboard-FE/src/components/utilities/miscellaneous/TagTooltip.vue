<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<!-- The little dialog that pops up when you hover over component tags -->
<script setup>
import { useAuthStore } from "../../../store/authStore";

const props = defineProps({
	position: { type: Object },
	hasFilter: { type: Boolean, default: false },
	hasMapLayer: { type: Boolean, default: false },
	hasHistory: { type: Boolean, default: false },
});

const authStore = useAuthStore();
</script>

<template>
	<div :style="props.position" class="chart-tooltip tagtooltip">
		<h6>組件資訊與功能</h6>
		<p>
			<span>{{ props.hasFilter ? "check" : "clear" }}</span
			>用圖表篩選地圖({{
				authStore.isMobileDevice ? "手機版不支援" : "地圖交叉比對"
			}})
		</p>
		<p>
			<span>{{ props.hasMapLayer ? "check" : "clear" }}</span
			>具備空間資料({{
				authStore.isMobileDevice ? "手機版不支援" : "地圖交叉比對"
			}})
		</p>
		<p>
			<span>{{ props.hasHistory ? "check" : "clear" }}</span
			>具備歷史資料({{
				authStore.isMobileDevice ? "資訊頁面" : "組件資訊"
			}})
		</p>
	</div>
</template>

<style scoped lang="scss">
.tagtooltip {
	position: fixed;
	box-shadow: 0px 0px 5px black;
	z-index: 30;

	p {
		display: flex;
		align-items: center;
		font-size: 16px;

		span {
			font-family: var(--font-icon);
			color: var(--color-highlight);
			font-size: var(--font-m);
		}
	}
}
</style>
