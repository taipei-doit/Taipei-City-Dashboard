<!-- src/dashboardComponent/components/PopularDashboard.vue -->
<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const popularList = ref([
  { id: 1, name: "扶養比及老化指數", index: "i_taipei_001", city: "taipei", clickCount: 42 },
  { id: 2, name: "高齡就業人口之年增結構", index: "i_taipei_002", city: "taipei", clickCount: 35 },
  { id: 3, name: "全市年齡分區", index: "i_taipei_003", city: "taipei", clickCount: 28 },
  { id: 4, name: "長照指標", index: "i_taipei_004", city: "taipei", clickCount: 22 },
  { id: 5, name: "某假設組件A", index: "i_taipei_005", city: "taipei", clickCount: 15 },
]);

const incrementClick = (componentId) => {
  const item = popularList.value.find((x) => x.id === componentId);
  if (item) item.clickCount += 1;
  popularList.value.sort((a,b) => b.clickCount - a.clickCount);
};

const goToComponentInfo = (item) => {
  router.push({
    name: "component-info",
    params: { index: item.index },
    query: { city: item.city },
  });
};
</script>

<template>
  <section class="popular-dashboard">
    <h2 class="pd-header">🔥 熱門儀表板（假資料）</h2>
    <ul class="pd-list">
      <li v-if="!popularList.length" class="pd-empty">
        尚無熱門組件
      </li>
      <li v-for="(item, idx) in popularList" :key="item.id" class="pd-item">
        <span class="pd-rank">{{ idx + 1 }}.</span>
        <span class="pd-name" @click="goToComponentInfo(item)">{{ item.name }}</span>
        <span class="pd-count">{{ item.clickCount }} 次</span>
        <button class="pd-btn-plus" @click="incrementClick(item.id)">+1</button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.popular-dashboard {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border, #444);
  border-radius: 4px;
  background-color: var(--color-component-background, #222);
  color: var(--color-normal-text, #eee);
}
.pd-header {
  font-size: var(--font-l, 1.2rem);
  color: var(--color-highlight, #ffd54f);
}
.pd-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.pd-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--color-border, #444);
}
.pd-item:last-child {
  border-bottom: none;
}
.pd-rank {
  width: 1.5rem;
  font-weight: bold;
  color: var(--color-highlight, #ffd54f);
}
.pd-name {
  flex: 1;
  font-size: var(--font-s, 1rem);
  color: var(--color-normal-text, #eee);
  cursor: pointer;
  text-decoration: underline;
}
.pd-name:hover {
  color: var(--color-highlight, #ffd54f);
}
.pd-count {
  width: 4.5rem;
  font-size: var(--font-s, 0.9rem);
  color: var(--color-complement-text, #bbb);
  text-align: right;
}
.pd-btn-plus {
  background-color: var(--color-primary, #42b983);
  color: var(--color-primary-contrast, #fff);
  border: none;
  border-radius: 3px;
  padding: 0.2rem 0.6rem;
  font-size: var(--font-s, 0.9rem);
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.pd-btn-plus:hover {
  background-color: var(--color-primary-dark, #369f6e);
}
.pd-empty {
  font-size: var(--font-s, 0.95rem);
  color: var(--color-complement-text, #aaa);
  text-align: center;
  padding: 0.5rem 0;
}
</style>
