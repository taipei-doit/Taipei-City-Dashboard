# 程式檢查

本專案使用 **ESLint 9（flat config）** 進行程式檢查，配置檔為 `Taipei-City-Dashboard-FE/eslint.config.js`。請不要修改此檔案（除非使用者明確要求）。

相關依賴（見 `Taipei-City-Dashboard-FE/package.json`）：`@eslint/js ^9.0.0` + `eslint-plugin-vue ^9.20.1`。

執行 `npm run lint` 會自動修正可修正的問題；`npm run build` 在 build 前也會先跑 `eslint --fix`。

> **注意**：本專案**不使用 Prettier**，也沒有 `.prettierrc` 或 `.eslintrc.json` 這兩個檔案。若過去文件有提及，請以 package.json 與 `eslint.config.js` 的實際狀態為準。

我們建議使用 VS Code 作為 IDE，並安裝 ESLint 擴充功能。根目錄的 `.vscode` 資料夾包含 VS Code 設定，儲存檔案時會自動 lint fix。

# 變量和檔案命名

所有新變量(variable)和檔案名都應該是獨特且具有描述性的。如果您的貢獻包含變量或檔案名不清楚或不合規的情況，我們將要求您進行修改。下面列出了一些更具體的規範。

## Vue 元件

按照慣例，Vue 元件的名稱必須由至少兩個英文字組成，並使用 Pascal case（例如 MapView）。

## 函式

函式名應盡量以動詞開頭，如 set、handle、execute、show 等，並使用 Camel case（例如 hideAllDialogs）。

## 一般變數

如果位於不同的區塊範疇(block scope)中，一般變量可以共享相同的名稱。但是，仍然應盡量避免在同一檔案中使用相同名稱的變量。一般變量應使用 Camel case 命名（例如 parsedChartData）。在此專案中，除非絕對必要，**Never**使用 var 來宣告變量。

## CSS 類名 (class name)

正如在之前的文章中提到的，這個專案全域和局部樣式均有使用。所有類名(class name)都應使用 Kebab case 命名（例如 settingsbar-title）。每個 Vue 元件的根類(root class)應該與其 Vue 元件的名稱相同並轉為全小寫（例如 SettingsBar 對應 .settingsbar）。後續的類名應該使用根類名作為其第一個字（例如 .settingsbar-title）。

# 文件結構

所有文件應該按照清晰且合乎邏輯的順序進行編排。如果您的貢獻包含未按照本專案標準編排的文件，我們將要求您進行修改。下面列出了一些更具體的規範。

## Vue 元件

除非必要，所有 Vue 元件應該按照以下格式編排。

```vue
<!-- Component Name: SampleComponent -->
<script setup>
// Library, package, and Pinia Store imports. Ex:
import { ref, computed, onMounted } from 'vue';
import { useContentStore } from '../store/contentStore';

// Component, config, utility function imports. Ex:
import AddComponent from './dialogs/AddComponent.vue';

// Library, package, and Pinia Store constant declarations. Ex:
const contentStore = useContentStore();

// Props and Emits. Ex:
const props = defineProps('sample');

// Local Data. Ex:
const isDashboard = ref(false);

// Computed Properties. Ex:
const sampleComputed = computed(() => {
    return "sample"
})

// Methods. Ex:
handleSubmit() {
    return
}

// Life Cycle Hooks. Ex:
onMounted(() => {
    isDashboard.value = true;
})
</script>

<template>
 <div class="samplecomponent">
  <!-- Rest of the template -->
 </div>
</template>

<style scoped lang="scss">
.samplecomponent {
 /* ...styling; 見以下有關CSS的段落 */
}
</style>
```

## CSS

CSS 參數應按照以下順序進行撰寫。CSS selector 應加在該類(class)的主要樣式後面。

```css
.samplecomponent {
/_ Dimensions, Ex: _/
width: 1rem;
/_ Display Related, Ex: _/
display: flex;
flex-direction: column;
/_ Position Related, Ex: _/
position: absolute;
top: 0;
/_ Margin and Padding, Ex: _/
margin: 0 1rem;
padding: 0;
/_ Border related, Ex: _/
border: none;
border-radius: 5px;
/_ Background related, Ex: _/
background-color: "red";
opacity: 1;
/_ Font related, Ex: _/
color: "white";
font-size: var(--font-s);
/_ Animation related, Ex: _/
animation: fade 1s;
/_ Transition, Ex: _/
transition: opacity 0.2s;
/_ Other, Ex: _/
overflow: hidden;
z-index: 2;
pointer-events: none;

    /* Selectors placed after main styles */
    /* CSS selector放在類(class)主要樣式後面 */
    &:hover {
        opacity: 0;
    }

}
```
