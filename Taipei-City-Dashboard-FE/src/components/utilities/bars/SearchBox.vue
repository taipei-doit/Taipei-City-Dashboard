<script setup>
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useContentStore } from '../../../store/contentStore';

const router = useRouter();
const contentStore = useContentStore();
const searchQuery = ref('');
const isLoading = ref(false);
const searchResults = ref([]);
const showResults = ref(false);
const searchDashBoardIndex = 'caf2a5f40cf3'

// 直接的搜尋函數 - 立即發送請求
async function performSearch(query) {
  if (!query.trim()) {
    searchResults.value = [];
    showResults.value = false;
    return;
  }

  isLoading.value = true;
  try {
    // 調用搜尋API
    const results = await contentStore.searchContent(query);
    searchResults.value = results;
    showResults.value = true;
  } catch (error) {
    console.error('搜尋錯誤:', error);
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
}

// 監聽搜尋輸入 - 偵測到文字更動就切換到"尋找"dashboard
watch(searchQuery, (newValue) => {
  // 如果有輸入文字，切換到"尋找"dashboard
  if (newValue.trim()) {
    console.log('🔍 偵測到搜尋輸入，切換到尋找dashboard:', {
      query: newValue,
      targetIndex: 'caf2a5f40cf3'
    });
    
    // 切換到"尋找"dashboard
    router.push({
      query: {
        index: searchDashBoardIndex
      }
    });
  }
  
  // 執行原本的搜尋功能
  performSearch(newValue);
});

// 處理搜尋結果點擊
function handleResultClick(result) {
  // 根據搜尋結果類型進行導航
  console.log('點擊搜尋結果:', result);
  showResults.value = false;
  searchQuery.value = '';
}

// 處理輸入框失去焦點
function handleBlur() {
  // 延遲隱藏結果，讓用戶有時間點擊
  setTimeout(() => {
    showResults.value = false;
  }, 200);
}

// 處理輸入框獲得焦點
function handleFocus() {
  if (searchResults.value.length > 0) {
    showResults.value = true;
  }
}
</script>

<template>
  <div class="search-box">
    <div class="search-input-container">
      <span class="search-icon">search</span>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜尋組件..."
        class="search-input"
        @focus="handleFocus"
        @blur="handleBlur"
      >
      <span 
        v-if="isLoading" 
        class="loading-icon"
      >hourglass_empty</span>
    </div>
    
    <!-- 搜尋結果下拉選單 -->
    <div 
      v-if="showResults && searchResults.length > 0"
      class="search-results"
    >
      <div
        v-for="result in searchResults"
        :key="result.id"
        class="search-result-item"
        @click="handleResultClick(result)"
      >
        <span class="result-icon">{{ result.icon || 'dashboard' }}</span>
        <div class="result-content">
          <div class="result-title">{{ result.name }}</div>
          <div class="result-subtitle">{{ result.type }}</div>
        </div>
      </div>
    </div>
    
    <!-- 無結果提示 -->
    <div 
      v-else-if="showResults && searchResults.length === 0 && searchQuery.trim()"
      class="search-results"
    >
      <div class="no-results">
        找不到相關結果
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.search-box {
  position: relative;
  width: 300px;
  
  .search-input-container {
    position: relative;
    display: flex;
    align-items: center;
    background-color: var(--color-component-background);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0 12px;
    height: 36px;
    transition: border-color 0.2s ease;
    
    &:focus-within {
      border-color: var(--color-highlight);
      box-shadow: 0 0 0 2px rgba(var(--color-highlight-rgb), 0.1);
    }
    
    .search-icon {
      color: var(--color-complement-text);
      font-size: 18px;
      margin-right: 8px;
      font-family: var(--font-icon);
    }
    
    .search-input {
      flex: 1;
      border: none;
      background: transparent;
      color: var(--color-text);
      font-size: 14px;
      outline: none;
      
      &::placeholder {
        color: var(--color-complement-text);
      }
    }
    
    .loading-icon {
      color: var(--color-complement-text);
      font-size: 16px;
      font-family: var(--font-icon);
      animation: spin 1s linear infinite;
    }
  }
  
  .search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: var(--color-component-background);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
    margin-top: 4px;
    
    .search-result-item {
      display: flex;
      align-items: center;
      padding: 12px;
      cursor: pointer;
      border-bottom: 1px solid var(--color-border);
      transition: background-color 0.2s ease;
      
      &:hover {
        background-color: var(--color-highlight);
      }
      
      &:last-child {
        border-bottom: none;
      }
      
      .result-icon {
        color: var(--color-complement-text);
        font-size: 20px;
        font-family: var(--font-icon);
        margin-right: 12px;
      }
      
      .result-content {
        flex: 1;
        
        .result-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text);
          margin-bottom: 2px;
        }
        
        .result-subtitle {
          font-size: 12px;
          color: var(--color-complement-text);
        }
      }
    }
    
    .no-results {
      padding: 16px;
      text-align: center;
      color: var(--color-complement-text);
      font-size: 14px;
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 響應式設計
@media (max-width: 768px) {
  .search-box {
    width: 200px;
  }
}
</style> 