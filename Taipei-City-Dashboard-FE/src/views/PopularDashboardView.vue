<!-- src/views/PopularDashboardView.vue -->
<script setup>
import PopularDashboard from "../dashboardComponent/components/PopularDashboard.vue";
</script>

<template>
  <div class="popular-dashboard-page">
    <h1 class="page-title">熱門儀表板</h1>
    <PopularDashboard />
  </div>
</template>

<style scoped>
.popular-dashboard-page {
  padding: var(--font-m);
  background-color: var(--color-background, #111);
  color: var(--color-normal-text, #eee);
}
.page-title {
  font-size: var(--font-xl, 1.5rem);
  color: var(--color-highlight, #ffd54f);
  margin-bottom: var(--font-m);
}
</style>
