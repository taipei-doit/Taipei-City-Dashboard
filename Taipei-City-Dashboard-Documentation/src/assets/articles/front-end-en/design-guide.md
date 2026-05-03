## General UI and UX Principles

As a reminder, the main goal of Taipei City Dashboard is to provide a user-friendly urban data visualization platform that allows individuals to browse, explore, and cross-reference various datasets reflecting the historical and current status of Taipei City and New Taipei City.

In line with the above goal, we have laid out several design guidelines to ensure users have a great experience on our platform. It is advised for contributors to follow the below principles when developing to ensure the finished product is visually coherent with other elements in this project. Contributions that obviously disregard any principles below will be asked to be modified or in extreme cases rejected immediately.

### Keep it Minimal

Our data visualization philosophy embraces minimalism, presenting only essential chart types that best represent the dataset. We focus on concise infographics, avoiding chart overuse. Visualizations, encompassing charts and maps, offer detailed attributes through dialogs. User-friendly efficiency is achieved through brief text descriptions and streamlined interaction flows.

### Bear Users in Mind

User-friendliness drives our approach, achieved by clear and descriptive component names that replace ambiguity. "人潮變化" transforms into "信令人口分時統計", conveying data source, interval, and methods. Key actions feature large, blue text while prioritizing visual elements over excessive text enhances engagement.

### Provide Just Enough Information

Our data visualizations strike a balance, ensuring clear information presentation. Components follow a structured text hierarchy, including title, source, updates, and tags. Aiding user understanding of data reliability, interpretation guidance is available in the "more info" dialog, complete with descriptions, use cases, dataset links, and contributor info.

### Ensure Interoperability

Interoperability is paramount. For instance, the order of Taipei City districts displayed is consistent for seamless navigation. Users access downloadable data for extended analysis and integration. Chart and map types are designed for compatibility, accommodating various display options and data types.

### Maintain Coherence

Consistency underpins our design philosophy. Uniform coloring across the chart and map views ensure coherence. Clear, self-explanatory component names facilitate user comprehension. When introducing new components related to existing ones, the inheritance of previous names signifies relationships, culminating in a seamless user experience.

## Visual Guide

All contributors of this project should keep this visual guide in mind to ensure style coherence across this project. Contributions that obviously disregard any principles below will be asked to be modified or in extreme cases rejected immediately.

### System Colors

In this project, adhere to specific color rules based on `CSS` variables. The main background color is set to `#090909` using the `--color-background` variable, while all borders use the `--color-border` variable with a color value of `#494b4e`. Important elements are highlighted in a vibrant blue shade (`#5a9cf8`) with the `--color-highlight` variable. Normal text appears in white through the `--color-normal-text` variable, and less important texts complementing the main content use `#888787`, set by the `--color-complement-text` variable. The majority of UI elements utilize the `--color-component-background` variable with a background color of `#282a2c`, ensuring a cohesive design across the application.

![Color Guide](/images/front-end/color-guide-en.png)

### Chart and Map Colors

Prioritize mid to low-saturation colors for a balanced visual experience. Use similar hues to establish connections between categories with similar meanings, ensuring a cohesive representation. When categories indicate incremental values, opt for gradient colors to highlight the progression. On the other hand, distinct categories are differentiated using random colors for clear visual distinction.

### Text Hierarchy

The text hierarchy of this project follows `CSS` variables for consistency and structure. The `--font-l` variable with a size of `1.25rem` is used for the application title, while main titles utilize the `--font-m` variable set to `1rem` for a balanced appearance. Descriptions and labels rely on the `--font-s` variable with a font size of `0.75rem` to present information clearly and concisely. This approach ensures a cohesive and visually appealing text hierarchy within the application.

### Padding and Margins

The spacing for large elements in this project should be achieved via the same `CSS` variables used by text unless necessary. For smaller elements such as input blocks, links, and buttons, reference the styles of similar existing elements and try to replicate them.
