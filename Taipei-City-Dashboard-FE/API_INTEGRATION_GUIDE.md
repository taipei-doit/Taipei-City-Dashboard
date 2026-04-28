# Taipei City Dashboard - API 串接與資料連接指南

這份指南旨在說明台北城市儀表板（Taipei City Dashboard）前端如何進行資料連線與 API 串接。開發者可以參考此文件，了解如何新增資料來源或修改現有的串接邏輯。

---

## 1. 專案架構概覽 (Architecture Overview)

本專案採用的核心技術棧如下：
- **框架**: [Vue 3](https://vuejs.org/) (Composition API)
- **建構工具**: [Vite](https://vitejs.dev/)
- **狀態管理**: [Pinia](https://pinia.vuejs.org/) (用於跨組件共用資料)
- **HTTP 用戶端**: [Axios](https://axios-http.com/)

### 關鍵資料路徑
- `src/router/axios.js`: 中央 Axios 實例配置（含拦截器）。
- `src/store/`: 存放所有 Pinia Stores（如 `contentStore`, `authStore`）。
- `src/dashboardComponent/`: 儀表板核心組件與其子組件。
- `vite.config.js`: 開發環境的代理（Proxy）配置。

---

## 2. 通訊層：Axios 配置

專案使用一個統一的 Axios 實例，位於 `src/router/axios.js`。

### 基礎配置
```javascript
const http = axios.create({
    baseURL: import.meta.env.VITE_API_URL, // 從 .env 讀取 API 地址
    headers: {
        "Content-Type": "application/json",
    },
});
```

### 請求攔截器 (Request Interceptor)
- 自動從 `authStore` 提取 Token 並注入 `Authorization` Header。
- 自動將 `contentStore.loading` 設為 `true`。

### 回應攔截器 (Response Interceptor)
- 處理常見錯誤碼（如 401 逾時登出、403 無權限、500 伺服器錯誤）。
- 錯誤發生時透過 `dialogStore` 顯示通知訊息。

---

## 3. 身分驗證流程 (Authentication)

身分驗證主要由 `src/store/authStore.js` 管理。

- **登入**: 呼叫 `/auth/login` 或 `/auth/callback` (Taipei Pass)。
- **Token 管理**: 登入成功後，Token 會存入 `localStorage`，並由 Axios 攔截器自動讀取。
- **持久化**: 應用程式啟動時，`initialChecks()` 會檢查 `localStorage` 並恢復登錄狀態。

---

## 4. 標準資料流 (Standard Data Flow)

這是儀表板大部分組件採用的「內容管理系統 (CMS)」驅動模式。主要邏輯位於 `src/store/contentStore.js`。

### 核心動作步驟：
1. **獲取配置 (`setDashboards`)**: 呼叫 `/dashboard/` 獲取當前可用的儀表板清單。
2. **獲取組件清單 (`setCurrentDashboardAllContent`)**: 根據選定的儀表板 ID，呼叫 `/dashboard/:index` 獲取該儀表板下所有的組件 meta data（含 ID, 名稱, 來源等）。
3. **獲取圖表資料 (`setCurrentDashboardAllChartData`)**:
   - 遍歷組件清單，為每個組件呼叫 `/component/:id/chart`。
   - 將回傳的 `chart_data` 存入該組件的物件中。
4. **渲染組件**:
   - 資料透過 `props` 傳遞給具體的圖表組件（如 `BarChart.vue`）。
   - 組件內部的 `series` 會根據 `chart_data` 動態計算。

---

## 5. 環境變數與代理 (Vite Proxy)

為了避免開發時的跨域（CORS）問題，並簡化網址，我們在 `vite.config.js` 設定了代理。

### 常見 Proxy 路徑：
- `/api`: 轉發至 `https://citydashboard.taipei/api/v1` (或 Docker 環境下的 `dashboard-be`)。
- `/nhi-api`: 轉發至健保署官方 API `https://info.nhi.gov.tw/api`。

> [!TIP]
> 如果要串接新的外部 API，應先在 `vite.config.js` 的 `server.proxy` 區塊新增對應的路徑，這樣前端只需請求 `/new-api/...` 即可。

---

## 6. 直接串接範例 (Direct Integration)

有時資料不經過主後端 CMS，而是由前端組件直接向外部 API 請求（適合即時性極高的資料）。

**範例: `NhiEmergencyChart.vue`**
```javascript
// 在組件內直接使用 axios 請求代理路徑
const fetchNhiData = async () => {
    try {
        const response = await axios.post("/nhi-api/inae4000/inae4001s01/SQL0002", {
            AREA_NO: "",
            CONT_TYPE: "",
        });
        nhiData.value = response.data.data;
    } catch (error) {
        console.error("無法取得健保署資料:", error);
    }
};
```

---

## 7. 如何將後端資料連上前端 (Step-by-Step)

### 方法 A：透過主後端 CMS (推薦)
1. 在後端資料庫/CMS 新增組件配置，記下 `component_id`。
2. 前端 `contentStore` 會自動在切換儀表板時抓取此組件配置。
3. 確保你的圖表組件能接收 `props.chart_data` 並進行渲染。

### 方法 B：直接在前端新增串接
1. **設定 Proxy**: 若 API 在外部，至 `vite.config.js` 新增路由。
2. **建立組件**: 在 `src/dashboardComponent/components/` 建立新的 `.vue` 檔案。
3. **資料抓取**: 在組件的 `onMounted` 週期呼叫 API。
4. **註冊組件**: 在 `DashboardComponent.vue` 的動態組件渲染處註冊該組件（通常是根據 `chart_config.types`）。

---

## 8. 除錯建議 (Debugging)

- **網路請求**: 使用瀏覽器 DevTools 的 `Network` 標籤，搜尋 `/api` 或對應的路徑。
- **State 檢查**: 安裝 **Vue Devtools** 擴充功能，查看 Pinia 中的 `content` 狀態，確認 `chart_data` 是否正確填入。
- **攔截器追蹤**: 在 `src/router/axios.js` 中暫時加入 `console.log` 以追蹤 Token 是否成功注入。

---
*Developed by Taipei Urban Intelligence Center*
