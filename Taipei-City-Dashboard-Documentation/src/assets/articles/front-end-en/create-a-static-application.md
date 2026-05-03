## Introduction
This project is perfect for displaying statistical and geographical data in conjunction. If the data you are displaying is static, transforming this project into a completely static application may be a good choice.

## Steps
Currently, this project includes many functionalities that typically only are present in dynamic applications. These functionalities could be easily removed to create a completely static application.

### Modify Navigation and Pages
There are several navigation guards in place in router. Remove any restrictions that relate to user authentication. Then, remove all admin pages and the sidebar in the component and component-info pages.

### Remove Functionalies that Require a Backend
These include modifying dashboards, creating issues, user settings, etc. Remove all related components, dialogs, and functions. If you are unsure whether any functionality requires a backend, check if the specific function is only available if the user is logged in.

### Replace All API Calls
Some sample component, dashboard, chart, history, and map data are available in the `/public` folder. Replace all `GET` API calls to the backend with getting data from these files. Remove all other API calls.

### Isolate the Front-End
Move the `/Taipei-City-Dashboard-FE` folder to a new repository and add an `.env` file containing front-end variables to the root. Now, the application is completely static and can be deployed to any static hosting service.