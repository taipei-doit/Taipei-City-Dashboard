> **w01**
> 本文僅涵蓋前端的程式碼撰寫規範。如果您也將開發我們的後端，請參閱[後端程式碼撰寫規範](/back-end/code-style)。

## 程式檢查

本專案使用 Prettier 進行程式自動編排和 Eslint 進行程式檢查。在專案的根目錄中，可以找到這兩個工具的配置檔。它們分別是 `.eslintrc.json` 和 `.prettierrc`。請不要對這兩個配置文件進行修改。

我們建議使用 [VS Code](https://code.visualstudio.com/) 作為您的 IDE，並安裝 [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) 和 [Eslint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) 擴充功能。在根目錄中，也有一個名為 `.vscode` 的資料夾，其中包含 VS Code 的設定，這將使您在儲存檔案時程式即會自動編排。

在開立 pull request 之前，您必須在根目錄的終端執行 `npm run lint` 並解決任何問題。有關開立 pull request 的詳細過程將在 [這裡](/front-end/open-a-pull-request) 進行更詳細的解釋。

## 變量和檔案命名

所有新變量(variable)和檔案名都應該是獨特且具有描述性的。如果您的貢獻包含變量或檔案名不清楚或不合規的情況，我們將要求您進行修改。下面列出了一些更具體的規範。

### Vue 元件

按照慣例，Vue 元件的名稱必須由至少兩個英文字組成，並使用 Pascal case（例如 `MapView`）。

### 函式

函式名應盡量以動詞開頭，如 set、handle、execute、show 等，並使用 Camel case（例如 `hideAllDialogs`）。

### 一般變量

如果位於不同的區塊範疇(block scope)中，一般變量可以共享相同的名稱。但是，仍然應盡量避免在同一檔案中使用相同名稱的變量。一般變量應使用 Camel case 命名（例如 `parsedChartData`）。

> **w01**
> 在此專案中，除非絕對必要，不允許使用 `var` 來宣告變量。

### CSS 類名 (class name)

正如在[之前的文章](/front-end/custom-styling)中提到的，這個專案全域和局部樣式均有使用。所有類名(class name)都應使用 Kebab case 命名（例如 `settingsbar-title`）。每個 Vue 元件的根類(root class)應該與其 Vue 元件的名稱相同並轉為全小寫（例如 `SettingsBar` 對應 `.settingsbar`）。後續的類名應該使用根類名作為其第一個字（例如 `.settingsbar-title`）。

## 文件結構

所有文件應該按照清晰且合乎邏輯的順序進行編排。如果您的貢獻包含未按照本專案標準編排的文件，我們將要求您進行修改。下面列出了一些更具體的規範。

### Vue 元件

除非必要，所有 Vue 元件應該按照以下格式編排。

```js
&lt;!-- 本程式片段專有名詞多，如非必要不進行翻譯 --&gt;
&lt;!-- Component Name: SampleComponent --&gt;
&lt;script setup&gt;
// Library, package, and Pinia Store imports. Ex:
import { ref, computed, onMounted } from 'vue';
import { useContentStore } from '../store/contentStore';

// Component, config, utility function imports. Ex:
import AddComponent from './dialogs/AddComponent.vue';P

// Library, package, and Pinia Store constant declarations. Ex:
const contentStore = useContentStore();

// Props and Emits. Ex:
const props = defineProps('sample');

// Local Data. Ex:
const isDashboard = ref(false);

// Computed Properties. Ex:
const sampleComputed = computed(() =&gt; {
	return &quot;sample&quot;
})

// Methods. Ex:
handleSubmit() {
	return
}

// Life Cycle Hooks. Ex:
onMounted(() =&gt; {
	isDashboard.value = true;
})
&lt;/script&gt;

&lt;template&gt;
	&lt;div class=&quot;samplecomponent&quot;&gt;
		&lt;!-- Rest of the template --&gt;
	&lt;/div&gt;
&lt;/template&gt;

&lt;style scoped lang=&quot;scss&quot;&gt;
.samplecomponent {
	/* ...styling; 見以下有關CSS的段落 */
}
&lt;/style&gt;
```

### CSS

CSS 參數應按照以下順序進行撰寫。CSS selector 應加在該類(class)的主要樣式後面。

```css
/* 本程式片段專有名詞多，如非必要不進行翻譯 */
.samplecomponent {
	/* Dimensions, Ex: */
	width: 1rem;
	/* Display Related, Ex: */
	display: flex;
	flex-direction: column;
	/* Position Related, Ex: */
	position: absolute;
	top: 0;
	/* Margin and Padding, Ex: */
	margin: 0 1rem;
	padding: 0;
	/* Border related, Ex: */
	border: none;
	border-radius: 5px;
	/* Background related, Ex: */
	background-color: "red";
	opacity: 1;
	/* Font related, Ex: */
	color: "white";
	font-size: var(--font-s);
	/* Animation related, Ex: */
	animation: fade 1s;
	/* Transition, Ex: */
	transition: opacity 0.2s;
	/* Other, Ex: */
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
