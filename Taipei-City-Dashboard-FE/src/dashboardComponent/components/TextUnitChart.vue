
<script setup>
const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

// const emits = defineEmits([
// 	"filterByParam",
// 	"filterByLayer",
// 	"clearByParamFilter",
// 	"clearByLayerFilter",
// 	"fly"
// ]);
</script>

<template>
  <div
    v-if="activeChart === 'TextUnitChart'"
    class="TextUnitChart"
  >
    <div class="TextUnitChart__container">
      <div
        v-for="item in series"
        :key="item.name"
        class="TextUnitChart__content"
      >
        <div
          class="TextUnitChart__name"
          :style="{ color: props.chart_config.color[0] }"
        >
          {{ item.name }}
        </div>
        <div>
          <span
            class="TextUnitChart__value"
            :style="{ color: props.chart_config.color[1] }"
          >{{ item.data[0] }}</span>
          <span
            class="TextUnitChart__unit"
            :style="{ color: props.chart_config.color[2] }"
          >{{ item.icon }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.TextUnitChart {
	position: relative;
	max-height: 100%;
	height: 100%;
	flex: 1;
	color: var(--color-normal-text);
	overflow-y: auto;

	&__container {
		display: grid;
		grid-template-columns: 1fr 1fr;
		min-height: 100%
	}
	&__content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		border-bottom: 1px solid var(--color-border);

		// 右邊框（不包括每行最後一個）
		&:not(:nth-child(2n)) {
			border-right: 1px solid var(--color-border);
		}
    
		// 移除最後一個項目的底部邊框
		&:last-child {
			border-bottom: none;
		}
    
		// 倒數第二個如果在右邊（偶數位置），移除底部邊框
		&:nth-last-child(2):nth-child(2n-1) {
			border-bottom: none;
		}
	}
	&__value {
		font-size: 1.5rem;
		padding-right: 0.25rem;
	}
}
</style>
