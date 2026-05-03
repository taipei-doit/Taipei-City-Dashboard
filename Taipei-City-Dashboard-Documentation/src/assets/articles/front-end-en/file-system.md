## /src

### /assets

The `/assets` folder stores static items such as global styles, utility functions, images, chart configurations, map configurations, and the icon font used throughout the project.

### /views

The `/views` folder stores the Vue components that make up entire pages.

### /components

The `/components` folder stores smaller Vue components that make up the user interface.

The `/components` sub-folder stores templates for components; the `/charts` sub-folder stores chart templates that are not rendered through the dashboardComponent component; the `/map` sub-folder stores any map-related Vue components; the `/dialogs` sub-folder stores templates for all the dialogs; and the `/utilities` sub-folder stores navigation, form, and miscellaneous elements.

### /dashboardComponent

The `/dashboardComponent` folder stores various chart templates that are rendered through the dashboardComponent component, serving as the main component for dynamically displaying data on the dashboard.

The `/assets` sub-folder stores static resources specifically for the dashboardComponent component, such as images, icons, etc.; the `/components` sub-folder contains all template components used by dashboardComponent to render various types of charts; and the `/utilities` sub-folder provides calculation functions and data processing tools required by the dashboardComponent component.

### /store

The `/store` folder is where all the Pinia stores are located. Global state management is achieved in this application by referencing data and invoking methods located in these stores.

The `authStore` stores user authentication-related information and methods; the `contentStore` is in charge of getting and storing dashboards and components; the `mapStore` stores the Mapbox map instance and related methods; the `dialogStore` controls which dialogs are shown and when; the `adminStore` stores methods that are used by the admin pages.

### /router

The `/router` folder contains the configuration files for Vue-router and Axios.

## /public

The `/public` folder stores static data that have larger file sizes. This includes static map data, contributor data, images, and other resources used in the project.
