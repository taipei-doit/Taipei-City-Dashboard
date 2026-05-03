## /src

### /assets

`/assets` 資料夾儲存靜態項目，例如全域樣式(Global Styles)、計算函式(Utility Functions)、圖片、圖表配置、地圖配置以及專案中使用的圖示字體檔。

### /views

`/views` 資料夾儲存儀表板各個用戶介面的頁面 Vue 元件。

### /components

`/components` 資料夾儲存較小的 Vue 元件，用於組成使用者介面。

子資料夾 `/components` 儲存組件的版型；子資料夾 `/charts` 儲存非透過 dashboardComponent 組件去 render 的圖表版型；子資料夾 `/map` 儲存與地圖相關的 Vue 元件；子資料夾 `/dialogs` 儲存所有彈跳視窗的版型；子資料夾 `/utilities` 儲存與導航、表單等相關的 Vue 元件。

### /dashboardComponent

`/dashboardComponent` 資料夾儲存各種透過 dashboardComponent 組件 render 的圖表版型，作為儀表板上動態呈現數據的主要元件。

子資料夾 `/assets` 儲存 dashboardComponent 組件專用的靜態資源，如圖片、圖示等；子資料夾 `/components` 包含所有 dashboardComponent 組件用於渲染各類圖表的版型元件；子資料夾 `/utilities` 提供 dashboardComponent 組件所需的計算函式與資料處理工具。

### /store

`/store` 資料夾是所有 Pinia Store 的所在地。本專案透過調閱這些 Pinia Stores 中的函式與資料，實現全域狀態管理。

`authStore` 儲存與使用者驗證相關的資訊和函式；`contentStore` 負責呼叫和儲存儀表板和組件；`mapStore` 儲存 Mapbox 地圖和相關函式；`dialogStore` 控制何時顯示哪些彈跳視窗；`adminStore`儲存管理員介面會用到的資訊與函式。

### /router

`/router` 資料夾包含 Vue-router 和 Axios 的配置。

## /public

`/public` 資料夾儲存較大檔案與靜態資料。這包含靜態地圖資料、貢獻者資訊、圖片等資源。
