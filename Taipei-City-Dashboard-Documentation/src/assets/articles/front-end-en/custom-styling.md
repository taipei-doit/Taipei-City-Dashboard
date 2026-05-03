## Scope

With the exception of elements rendered by third-party packages (e.g Mapbox, Apexcharts), this entire project was styled via vanilla `css` or `scss`. The absence of a UI library allows for a high degree of customizability. A mix of global styles and local styles was utilized to achieve the styling of this project.

If you are interested in styling maps (Mapbox), please refer to the [Custom Maps](/front-end/custom-maps) article.

> **w01**
> For contributors, please note that when modifying this project, there are certain global and local styles that we don’t allow to be modified. In addition, there are also certain style guidelines put in place that you should follow if you would like to contribute new elements to this project. Be sure to read through our [Design Guide](/front-end/design-guide) in the next section.

## Global Styles

Global styles include base styles for `HTML` elements and styles that are shared across Vue components. All global styles were written in `css` and can be found in the folder `/src/assets/styles`.

### Style Variables

This project heavily uses style variables to ensure uniformity of colors, fonts, and various spacings. The complete list of style variables used can be found below and modified in the file `globalStyles.css`.

```css
:root {
	--color-background: #090909; /* main background color */
	--color-border: #494b4e; /* color for all borders */
	--color-highlight: #5a9cf8; /* color for important elements (blue) */
	--color-normal-text: white;
	--color-complement-text: #888787; /* color for less important texts */
	--color-component-background: #282a2c; /* background color for most UI elements */
	--color-overlay: rgba(0, 0, 0, 0.66); /* overlay for dialogs */
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
> All icons in this project are rendered using a special icon font (material icons) provided by [Google Fonts](https://fonts.google.com/icons?icon.style=Rounded&icon.set=Material+Icons). The icon style chosen for this project is “rounded”. The font is fetched via `CDN` when `index.html` is loaded.

## Local Styles

Local styles are scoped to the Vue component it belongs to. This means that the effects of the styles specified are limited to `HTML` elements within that Vue component. All local styles were written in `scss` and are located at the bottom of all Vue components. As a convention, the root class of each Vue component is the same as its file name without spaces and all lowercase.
