> **w01**
> This article only covers the coding style for the front-end. If you will also be developing our back-end, please refer to [the back-end coding style guide](/back-end/code-style).

## Code Linting
This project uses Prettier for formatting code and Eslint for linting code. In the root directory of this project, the configuration files for the two tools could be found. They are `.eslintrc.json` and `.prettierrc` respectively. Any modifications to the two configuration files are not allowed.

We recommend using [VS Code](https://code.visualstudio.com/) as your IDE and also installing the [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) and [Eslint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) extensions. In the root repository, there is a folder called `.vscode` which contains settings for VS Code that will enable you to format your code in accordance with our guidelines whenever you save your document.

Before opening a pull request, you must run `npm run lint` in the repository terminal and resolve any issues. The process of opening a pull request will be explained in greater detail [here](/front-end/open-a-pull-request).

## Variable and File Naming
As a general rule of thumb, all new variable and file names should be unique and descriptive. If your contribution contains variable or file names deemed unclear, you will be asked to modify them. Some more specified guidelines are listed below.

### Vue Components
In accordance with convention, Vue component names must consist of at least two words in Pascal case (e.g. `MapView`). 

### Functions
Function names should start with a verb such as set, handle, execute, show, etc in Camel case (e.g. `hideAllDialogs`).

### Constants
Constants can share the same name if within a different block scope. However, avoiding same-name constants in the same document is still encouraged. Constants as a general rule should be named in Camel case (e.g. `parsedChartData`).

>**w01**
>The `var` keyword for declaring variables is not permitted in this project unless absolutely necessary.

### CSS Class Names
As mentioned in [this previous article](/front-end/custom-styling), this project uses a mix of global and scoped local styles. All class names should be named in Kebab case (e.g. `settingsbar-title`). To ensure clarity, the root class of each Vue component should be the same as the Vue component’s name in lowercase (e.g. `SettingsBar` ***east*** `.settingsbar`). Subsequent classes should use the root class name as it's first word (e.g. `.settingsbar-title`).

## Document Structure
As a general rule of thumb, all documents should be formatted in a clear and logical order. Comments should be added if necessary to increase clarity. If your contribution contains documents not formatted to this project’s standards, you will be asked to modify them. Some more specified guidelines are listed below.

### Vue Components
All Vue components should be structured in the below format unless necessary.

```html
&lt;!-- Component Name: SampleComponent --&gt;
&lt;script setup&gt;
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
	/* ...styling; see below paragraph for more info */
}
&lt;/style&gt;
```

### CSS
CSS parameters in each bracket should be written in the following order. CSS selectors should be added after the main class.
```css
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
	&:hover {
		opacity: 0;
	}
}
```
