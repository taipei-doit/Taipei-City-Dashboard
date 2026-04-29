---
trigger: always_on
---

# Coding & Interaction Standards (Taipei City Dashboard FE)

本文件定義此專案的程式碼規範與 AI 互動原則。這些規範為 **Always On** 狀態，Agent 必須優先遵循。

## 1) 核心變更原則
- **優先修根因**：避免表面 workaround。
- **變更範圍要小**：不順手重構不相關代碼、不隨意改命名或搬移檔案。
- **依照現有寫法**：新增功能前先參考同類型檔案（尤其圖表、地圖、Store）的既有模式。
- **嚴禁未授權依賴**：不可引入新 npm 套件、UI 庫（Element Plus 等）、CSS 框架（Tailwind 等）或替換圖表/地圖核心庫。

## 2) Vue / SFC 規範
- **Composition API**：一律使用 `<script setup>`。
- **明確定義**：Props/Emits 需有明確定義與型別註解。
- **生命週期管理**：Side effects（監聽器、計時器）必須在 `onUnmounted()` 清理。

## 3) Pinia 狀態管理
- **職責單一**：資料、UI 狀態、地圖狀態應在各自的 Store（如 contentStore, mapStore）中管理。
- **邏輯下放**：Action 負責資料轉換；UI 元件不應重複轉換邏輯。
- **效能優化**：高頻事件觸發 Action 時必須使用 `lodash.debounce`。

## 4) 樣式與響應式
- **BEM 命名**：Class 命名遵循 BEM 風格（如 `.dashboardcomponent-header__title`）。
- **設計變數**：顏色與間距優先使用 `globalStyles.css` 中的 CSS Variables。
- **現有 Class**：優先沿用 `hide-if-mobile` / `show-if-mobile` 進行響應式處理。

## 5) 圖表與地圖 (ApexCharts / Mapbox)
- **統一渲染**：僅限使用 `<apexchart>`；新圖表需在 `chartTypes.ts` 與 `DashboardComponent.vue` 註冊。
- **地圖安全**：操作 layer/source 需處理「尚未載入 style」之情況，並在 unmount 時清理實例。
- **時間處理**：僅限使用 Day.js，禁止引入 moment.js。

## 6) AI 交付與 Diff 規範 (跨 Agent 強制)
- **強制 Git Diff**：修改現有代碼時，**嚴禁**輸出全量代碼。必須使用 `diff` 語法標註新增 (`+`) 與刪除 (`-`)。
- **保留上下文**：Diff 必須包含至少 3 行上下文以便定位。
- **邏輯原子化**：變更應視為一個潛在的 Git Commit，並附帶符合規範的 Commit Message 建議。
- **Mock 優先**：若後端 API 未就緒，必須依據 `data-schemas.md` 產生 Mock 資料並加上 `// API_STUB` 註解。