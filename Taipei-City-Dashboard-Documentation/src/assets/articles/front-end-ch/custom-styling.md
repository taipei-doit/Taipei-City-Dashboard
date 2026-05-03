## 範圍

除了由第三方套件（e.g Mapbox, Apexcharts）渲染的元素之外，本專案都使用純 `css` 或 `scss` 進行樣式設計(Styling)。因爲未使用 UI 庫，本專案能輕易被客製化。本專案全域樣式和局部樣式均有使用。

如果您對地圖（Mapbox）的樣式感興趣，請參考[客製化地圖](/front-end/custom-maps)文章。

> **w01**
> 協作者請注意，在修改本專案時，有一些全域和局部樣式是不允許被修改的。另外，我們也制定了[設計指南](/front-end/design-guide)，如果您希望對本專案貢獻新元素，應遵循該指南。

## 全域樣式

全域樣式包括`HTML`元素的基本樣式和在 Vue 組件間共享的樣式。所有全域樣式均以`css`編寫，位於資料夾`/src/assets/styles`中。

### 樣式變量

本專案大量使用樣式變量來確保顏色、字體和各種間距的統一性。下方條列所有本專案的樣式變量，位於`globalStyles.css`檔案。

```css
:root {
	--color-background: #090909; /* 主背景顏色 */
	--color-border: #494b4e; /* 所有邊框的顏色 */
	--color-highlight: #5a9cf8; /* 重要元素的顏色（藍色） */
	--color-normal-text: white;
	--color-complement-text: #888787; /* 不太重要文字的顏色 */
	--color-component-background: #282a2c; /* 大多數UI元素的背景顏色 */
	--color-overlay: rgba(0, 0, 0, 0.66); /* 對話框的遮罩 */
	--font-to-icon: 1.2;
	--font-xl: 1.5rem;
	--font-l: 1.25rem;
	--font-m: 18px;
	--font-ms: 1rem;
	--font-s: 0.75rem;
	--font-icon: "Material Icons Round";
    --vh: 1vh;
}
```

> **i01**
> 本專案中的所有圖示都使用一個特殊的圖示字體（Material Icons）來渲染，該字體由[Google Fonts](https://fonts.google.com/icons?icon.style=Rounded&icon.set=Material+Icons)提供。本專案選擇了「圓角(Rounded)」的圖示風格。本字體是在`index.html`初次載入時透過`CDN`獲取的。

## 局部樣式

局部樣式的效果限縮於所屬的 Vue 元件，並均以`scss`編寫，位於 Vue 元件的底部。在本專案中，每個 Vue 元件的 root class 應與其文件名相同，但不含空格且全部小寫。
