> **i01**
> All of the methods (titles) in this article are located in the `contentStore`.

## createDashboard

[`POST` `/api/v1/dashboard`](/back-end/dashboard-apis)

In the user interface, expand the sidebar and click on the blue text. This will open up a dialog where the new dashboard name, icon, and components are to be inputted. Click on the blue button to confirm.

## editCurrentDashboard

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

In the user interface, locate the settings bar and click on the gear icon **_settings_** next to the add components icon. This will open up a dialog where dashboard settings could be made.

## deleteCurrentDashboard

[`DEL` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

In dashboard settings, click on the check box to indicate your desire to delete the current dashboard. A red delete button will appear. Click to delete the dashboard.

## deleteComponent

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis)

In the dashboard, there is a delete icon **_delete_** in the upper right corner of each component. Clicking the icon will remove the component from the current dashboard.

## favoriteComponent / unfavoriteComponent

[`PATCH` `/api/v1/dashboard/:favorite-dashboard-index`](/back-end/dashboard-apis)

In the dashboard view, there is a heart icon **_favorite_** in the upper right corner of each component. If the icon is gray, clicking it will favorite the component. Conversely, if the icon is red, clicking it will unfavorite the component.
