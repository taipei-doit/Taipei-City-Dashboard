<script setup>
import { computed } from 'vue';
import { useDialogStore } from '../../store/dialogStore';
import DialogContainer from './DialogContainer.vue';

const dialogStore = useDialogStore();

// 計算 API URL
const apiUrl = computed(() => {
	const { url } = dialogStore.trafficCamCoordinates;
	return url;
});

const handleClose = () => {
	dialogStore.hideAllDialogs();
};
</script>

<template>
  <DialogContainer
    dialog="trafficCamInfo"
    @on-close="handleClose"
  >
    <div class="traffic-cam-info">
      <div class="traffic-cam-info-header">
        <h2>
          雙北道路監控資訊
          <!-- <small v-if="dialogStore.trafficCamCoordinates.lat">
            ({{ dialogStore.trafficCamCoordinates.lat }}, {{ dialogStore.trafficCamCoordinates.lon }})
          </small> -->
        </h2>
        <a 
          :href="apiUrl" 
          target="_blank"
          class="external-link"
        >
          開啟新視窗
        </a>
      </div>
      
      <div 
        v-if="dialogStore.trafficCamCoordinates.url"
        class="traffic-cam-content"
      >
        <iframe 
          :src="apiUrl"
          width="100%"
          height="500"
          frameborder="0"
        />
      </div>
      
      <div 
        v-else 
        class="error"
      >
        缺少經緯度資訊
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.traffic-cam-info {
  width: 1000px;
  max-height: 800px;
  
  &-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    
    h2 {
      small {
        font-size: 12px;
        color: var(--color-complement-text);
        font-weight: normal;
      }
    }
    
    .external-link {
      padding: 4px 12px;
      background-color: var(--color-highlight);
      color: white;
      text-decoration: none;
      border-radius: 4px;
      font-size: 14px;
      
      &:hover {
        opacity: 0.8;
      }
    }
  }
}

.traffic-cam-content {
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  
  iframe {
    display: block;
  }
}

.error {
  text-align: center;
  padding: 2rem;
  color: #ff6b6b;
}
</style>