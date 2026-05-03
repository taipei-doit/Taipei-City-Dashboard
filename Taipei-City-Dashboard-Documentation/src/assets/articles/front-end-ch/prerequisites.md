## 開發環境

為了最佳的開發體驗，我們建議使用作業系統為 Windows 或 macOS 的電腦。我們也建議進行以下開發環境設定。

### 開發工具

如果您希望使用我們的[專案設定指南](/front-end/project-setup)，請確保您的電腦上有安裝了以下開發工具：[Node.js LTS](https://nodejs.org/en)、[Git](https://git-scm.com/)（也可以額外安裝 GitHub Desktop）、Docker (建議透過安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/))。如果您也會開發我們的後端，亦請安裝 [Go](https://golang.org/)、[Postman](https://www.postman.com/).

### 程式編輯器

[VScode](https://code.visualstudio.com/) 是我們首選的程式編輯器。我們建議安裝以下擴充工具：Prettier、ESLint、Vue Language Features (Volar)、Docker。如果您也會開發我們的後端，我們亦建議安裝 Go 擴充工具。如果您選擇其他程式編輯器，請確保它支持上述擴充工具。

## 前端核心庫與套件

### Vue

本專案選用 Vue 作為前端框架，並完全使用 Vue 3 發布的 Composition API 方法編寫。Vue 的文件可以在[這裡](https://vuejs.org/guide)找到。

### Vue-router

Vue-router 的文件可以在[這裡](https://router.vuejs.org/guide/)找到。

### Pinia

根據 Vue 官方建議，我們使用 Pinia 來實現全域狀態管理(Global State Management)，而不是使用 Vuex。Pinia 的文件可以在[這裡](https://pinia.vuejs.org/introduction.html)找到。

### Apexcharts

本專案中的大部分圖表使用 Apexcharts 建置。Apexcharts 的文件可以在[這裡](https://apexcharts.com/docs)找到。

### Mapbox

Mapbox 是基於 OpenStreetMap 架構的地圖渲染工具。Mapbox 的文件可以在[這裡](https://docs.mapbox.com/mapbox-gl-js/)找到。

### Axios

Axios 用於進行 HTTP 請求。Axios 的文件可以在[這裡](https://axios-http.com/docs/intro)找到。

> **t01**
> 如果您是前端開發的新手，我們建議您在學習像 Vue 的前端框架之前，先熟悉 HTML、CSS 和 JavaScript 的基礎知識。[Scrimba](https://scrimba.com/allcourses)、[Codecademy](https://www.codecademy.com/)、[W3Schools](https://www.w3schools.com/) 和 [FreeCodeCamp](https://www.freecodecamp.org/) 都是學習網頁開發的好資源。
