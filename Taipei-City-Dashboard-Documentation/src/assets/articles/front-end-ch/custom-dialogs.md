## 彈跳視窗運作原理
每個彈跳視窗都是一個Vue元件，其顯示與否由`dialogStore`控制。所有彈跳視窗Vue元件都儲存在資料夾`/src/components/dialogs`中。各個彈跳視窗在本專案中的名稱是其Vue元件檔名的Camel Case (camelCase) 形式。

### 彈跳視窗儲存
`dialogStore`儲存了所有彈跳視窗的渲染狀態。本專案中所有可用的彈跳視窗如下所示。

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

彈跳視窗的Vue元件會根據在`dialogStore`的狀態條件性地渲染(conditionally render)，各彈跳視窗顯示狀態的預設值為`false`。

### 彈跳視窗Vue元件的結構
以下是一個典型的彈跳視窗Vue元件的架構。

```html
&lt;template&gt;
    &lt;!-- 一個將Vue組件遞送到body的Vue功能 --&gt;
    &lt;Teleport to=&quot;body&quot;&gt; 
        &lt;!-- 一個添加進場和離場過渡效果的Vue功能 --&gt;
        &lt;Transition name=&quot;dialog&quot;&gt; 
            &lt;!-- 根據dialogStore狀態條件性渲染 --&gt;
            &lt;div class=&quot;dialogcontainer&quot; v-if=&quot;dialogStore.dialogs.mobileNavigation&quot;&gt; 
                &lt;!-- 背景疊層，點擊時關閉彈跳視窗 --&gt;
                &lt;div class=&quot;dialogcontainer-background&quot; @click=&quot;dialogStore.hideAllDialogs&quot;&gt;&lt;/div&gt;
                &lt;div class=&quot;dialogcontainer-dialog&quot;&gt;
                    &lt;div class=&quot;mobilenavigation&quot;&gt;
                        &lt;!-- 彈跳視窗的內容 --&gt;
                    &lt;/div&gt;
                &lt;/div&gt;
            &lt;/div&gt;
        &lt;/Transition&gt;
    &lt;/Teleport&gt;
&lt;/template&gt;
```

```html
&lt;style scoped lang=&quot;scss&quot;&gt;
    .dialogcontainer {
        /* 占滿整個畫面 */
        /* position absolute並置於頂層 */

        &amp;-background {
            /* 模糊其餘用戶界面 */
        }
        
        &amp;-dialog {
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
&lt;/style&gt;
```

>**t01**
>了解更多有關 Vue teleport [的資訊](https://vuejs.org/guide/built-ins/teleport.html)。
>了解更多有關 Vue transitions [的資訊](https://vuejs.org/guide/built-ins/transition.html)。

本專案有撰寫一個用來包裝彈跳視窗的 Vue 元件 `DialogContainer` 可用於將彈跳視窗置於螢幕中間。此包裝Vue元件負責處理teleport、過渡(transition)效果、條件式渲染和背景覆蓋(overlay)。下面是一個使用此包裝元件的彈跳視窗 Vue 元件的架構。


```html
&lt;template&gt;
    &lt;!-- dialog: 彈跳視窗的名稱 --&gt;
    &lt;!-- @on-close: 處理彈跳視窗關閉的函式 --&gt;
    &lt;DialogContainer dialog=&quot;initialWarning&quot; @on-close=&quot;handleClose&quot;&gt;
        &lt;div class=&quot;initialwarning&quot;&gt;
            &lt;!-- 彈跳視窗的內容 --&gt;
        &lt;/div&gt;
    &lt;/DialogContainer&gt;
&lt;/template&gt;
```

### 開啟和關閉彈跳視窗
一般打開彈跳視窗的流程始於按鈕或函數呼叫 `dialogStore` 的 `showDialog` 函式。該函式以彈跳視窗名稱作為參數，並將指定彈跳視窗的渲染狀態切換為 `true`。

關閉彈跳視窗則需呼叫 `dialogStore` 的 `hideAllDialogs` 函式。該函式會將除了 `notificationBar` 之外的所有彈跳視窗狀態切換為 `false`。

### 特殊彈跳視窗
此專案中有三個與其他彈跳視窗稍有不同的特殊彈跳視窗。這是因為需要在這些彈跳視窗中顯示額外的資訊。

**`moreInfo`** 彈跳視窗可透過呼叫 `dialogStore` 的 `showMoreInfo` 函式來打開。該函式以目標組件的**組件配置**作為參數，並渲染顯示更詳細組件資訊的視窗。

**`reportIssue`** 彈跳視窗可透過呼叫 `dialogStore` 的 `showReportIssue` 函式來打開。該函式以目標組件的**名稱(name)**和**ID**作為參數，並渲染一個表單供使用者提交問題回報。

**`notificationBar`** 彈跳視窗可透過呼叫 `dialogStore` 的 `showNotification` 函式來打開。該函式接收兩個參數：**狀態(status)**（可為 「success」 或 「fail」）和要顯示的**訊息(message)**。這將在用戶介面上方渲染一個推播通知。

## 建立新的彈跳視窗
首先，決定彈跳視窗名稱並創建一個遵循彈跳視窗 Vue 元件結構的 Vue 元件。接著，在 `dialogStore` 中註冊該彈跳視窗，將其名稱添加到現有的彈跳視窗列表中。最後，將該彈跳視窗 Vue 元件添加到應用程式中。建議將彈跳視窗 Vue 元件放在觸發它的元素旁邊，例如按鈕。

>**w01**
>不要將彈跳視窗 Vue 元件添加到應用程式中的多個位置，不然啟用該彈跳視窗時會有重複渲染情形。
