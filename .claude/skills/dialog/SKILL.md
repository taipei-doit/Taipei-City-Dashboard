---
name: dialog
description: >
  當使用者要新增、修改、除錯彈跳視窗（dialog），或涉及 dialogStore、DialogContainer、Teleport、MoreInfo、ReportIssue、NotificationBar 時觸發此技能。
  觸發情境：「新增彈跳視窗」「加一個 modal」「修改 dialog」「dialogStore 怎麼用」「用 DialogContainer 包」「新增 popup」「dialog 關不掉」等。
  不要使用：使用者只問圖表、地圖圖層、頁面路由等純非彈跳視窗問題。
---

# 客製化彈跳視窗

## Step 0：觀摩既有彈跳視窗（**強制**，開工前必做）

**任何新彈跳視窗動手前，必須先讀至少一個既有 dialog 元件**，確認 `DialogContainer` 用法、`Teleport`/`Transition` 模式、樣式命名一致。

建議讀：
- `Taipei-City-Dashboard-FE/src/components/dialogs/MoreInfo.vue`（標準 DialogContainer 用法）

讀完後，在對話中向使用者回報：打算沿用哪個殼、哪些偏離點。

## Step 0.5：盤點 `dialogs/` 現有彈跳視窗（**強制**）

掃 `Taipei-City-Dashboard-FE/src/components/dialogs/`，列出現有 dialog 元件。**不得自己生成已存在的彈跳視窗**。

判定：能直接用就 import；需小改先說明再改原檔；真不適用才自幹並列原因。

## 彈跳視窗運作原理

每個彈跳視窗都是一個Vue元件，其顯示與否由dialogStore控制。所有彈跳視窗Vue元件都儲存在資料夾/src/components/dialogs中。各個彈跳視窗在本專案中的名稱是其Vue元件檔名的Camel Case (camelCase) 形式。

## 彈跳視窗儲存

dialogStore儲存了所有彈跳視窗的渲染狀態。本專案中所有可用的彈跳視窗如下所示。

```js
dialogs: { // dialogStore 其中一個狀態
    // 管理員彈跳視窗: /components/dialogs/admin
    adminComponentSettings: false,
    adminAddEditDashboards: false,
    adminEditIssue: false,
    adminAddComponent: false,
    adminDeleteDashboard: false,
    adminEditUser: false,
    adminAddEditContributor: false,
    adminDeleteContributor: false,
    // 公共彈跳視窗: /components/dialogs
    addComponent: false,
    addDashboard: false,
    dashboardSettings: false,
    addEditDashboards: false,
    initialWarning: false,
    login: false,
    mobileLayers: false,
    mobileNavigation: false,
    moreInfo: false,
    notificationBar: false,
    reportIssue: false,
    userSettings: false,
    embedComponent: false,
    contributorsList: false,
    contributorInfo: false,
    addPin: false,
    addViewPoint: false,
    findClosestPoint: false,
},
```

彈跳視窗的Vue元件會根據在dialogStore的狀態條件性地渲染(conditionally render)，各彈跳視窗顯示狀態的預設值為false。

## 彈跳視窗Vue元件的結構

以下是一個典型的彈跳視窗Vue元件的架構。

```vue
<template>
 <!-- 一個將Vue組件遞送到body的Vue功能 -->
 <Teleport to="body">
  <!-- 一個添加進場和離場過渡效果的Vue功能 -->
  <Transition name="dialog">
   <!-- 根據dialogStore狀態條件性渲染 -->
   <div class="dialogcontainer" v-if="dialogStore.dialogs.mobileNavigation">
    <!-- 背景疊層，點擊時關閉彈跳視窗 -->
    <div
     class="dialogcontainer-background"
     @click="dialogStore.hideAllDialogs"
    ></div>
    <div class="dialogcontainer-dialog">
     <div class="mobilenavigation">
      <!-- 彈跳視窗的內容 -->
     </div>
    </div>
   </div>
  </Transition>
 </Teleport>
</template>
<style scoped lang="scss">
.dialogcontainer {
 /* 占滿整個畫面 */
 /* position absolute並置於頂層 */

 &-background {
  /* 模糊其餘用戶界面 */
 }

 &-dialog {
  /* 彈跳視窗的位置、尺寸、邊框、背景 */
 }
}

.mobilenavigation {
 /* 彈跳視窗主體的樣式 */
}

.dialog-enter-from,
.dialog-leave-to {
 /* 彈跳視窗進場效果 */
}

.dialog-enter-active,
.dialog-leave-active {
 /* 彈跳視窗離場效果 */
}
</style>
```

本專案有撰寫一個用來包裝彈跳視窗的 Vue 元件 DialogContainer 可用於將彈跳視窗置於螢幕中間。此包裝Vue元件負責處理teleport、過渡(transition)效果、條件式渲染和背景覆蓋(overlay)。下面是一個使用此包裝元件的彈跳視窗 Vue 元件的架構。

```vue
<template>
 <!-- dialog: 彈跳視窗的名稱 -->
 <!-- @on-close: 處理彈跳視窗關閉的函式 -->
 <DialogContainer dialog="initialWarning" @on-close="handleClose">
  <div class="initialwarning">
   <!-- 彈跳視窗的內容 -->
  </div>
 </DialogContainer>
</template>
```

## 開啟和關閉彈跳視窗

一般打開彈跳視窗的流程始於按鈕或函數呼叫 dialogStore 的 showDialog 函式。該函式以彈跳視窗名稱作為參數，並將指定彈跳視窗的渲染狀態切換為 true。

關閉彈跳視窗則需呼叫 dialogStore 的 hideAllDialogs 函式。該函式會將除了 notificationBar 之外的所有彈跳視窗狀態切換為 false。

## 特殊彈跳視窗

此專案中有三個與其他彈跳視窗稍有不同的特殊彈跳視窗。這是因為需要在這些彈跳視窗中顯示額外的資訊。

moreInfo 彈跳視窗可透過呼叫 dialogStore 的 showMoreInfo 函式來打開。該函式以目標組件的組件配置作為參數，並渲染顯示更詳細組件資訊的視窗。

reportIssue 彈跳視窗可透過呼叫 dialogStore 的 showReportIssue 函式來打開。該函式以目標組件的名稱(name)和ID作為參數，並渲染一個表單供使用者提交問題回報。

notificationBar 彈跳視窗可透過呼叫 dialogStore 的 showNotification 函式來打開。該函式接收兩個參數：狀態(status)（可為 「success」 或 「fail」）和要顯示的訊息(message)。這將在用戶介面上方渲染一個推播通知。

# 建立新的彈跳視窗

首先，決定彈跳視窗名稱並創建一個遵循彈跳視窗 Vue 元件結構的 Vue 元件。接著，在 dialogStore 中註冊該彈跳視窗，將其名稱添加到現有的彈跳視窗列表中。最後，將該彈跳視窗 Vue 元件添加到應用程式中。建議將彈跳視窗 Vue 元件放在觸發它的元素旁邊，例如按鈕。

不要將彈跳視窗 Vue 元件添加到應用程式中的多個位置，不然啟用該彈跳視窗時會有重複渲染情形。

## 完成後檢查

- [ ] 已讀既有 dialog 元件（Step 0）確認風格一致
- [ ] 已掃 `src/components/dialogs/` 確認沒重複建已存在的彈窗（Step 0.5）
- [ ] 在 `dialogStore` 的 `dialogs` 物件中新增該名稱（預設 `false`）
- [ ] 使用 `DialogContainer` 包裝（或手動 `Teleport` + `Transition`）
- [ ] Vue 元件**只放一個地方**，避免重複渲染
- [ ] 無 hardcoded 顏色（用 `var(--color-*)`）
- [ ] `npm run lint` 無錯誤
