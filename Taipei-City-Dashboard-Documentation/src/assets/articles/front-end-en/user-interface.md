## Overview

Before diving into the codebase of this project, it is recommended to have a thorough understanding of the user interface.

If a user is not logged in, only the Dashboard view and Map view are available, displaying public dashboards and components.

If the user wants to quickly understand which components are relevant to their needs, they can use the assistant located in the bottom-right corner of the interface.

![User Interface Dashboard Page Not Logged In](/images/front-end/user-interface-1.png)

After clicking the assistant button and opening the chat box, users can input the topics they are interested in. The assistant will filter the relevant components accordingly and display the results in a table.

![TCD ChatBox Not Logged In](/images/front-end/user-interface-1-1.png)

> **i01**
> In frontend frameworks, components can also refer to reusable templates that could be used to build user interfaces. For this project, we feel that the word "component" is the most appropriate name to give to the elements that make up a dashboard.
>
> To disambiguate between the two terms, frontend framework components will be henceforth always referred to as "Vue components", while dashboard components will simply be referred to as "components".

If a user is logged in, in addition to the dashboard view and map view, the user can also access their own dashboards. A component view and component-info view will also be made available to the user. If the user is an admin, they will also be able to access the admin view by hovering over their username in the navigation bar.

![User Interface Dashboard Page Logged In](/images/front-end/user-interface-2.png)

Logged-in users can use the assistant in the bottom-right corner not only to inquire about components related to specific topics, but also to click “Create Dashboard.” The assistant will automatically aggregate recommended components into a suggested dashboard and add it to the user’s private dashboards.

![TCD ChatBox Logged In](/images/front-end/user-interface-2-1.png)

## /dashboard

The dashboard view shows components in their basic chart configuration. Here, users can get a comprehensive glance at all the statistics a component has to offer.

In the dashboard view, a "more information" (組件資訊 **_arrow_circle_right_**) option is also available in the bottom right corner of most components. Clicking on the button will show a dialog that displays a more detailed description of the component, including historical data if available. There will also be the option to report problems (回報問題 **_flag_**) and download the statistical data displayed (下載資料 **_download_**).

## /mapview

The map view by default lists all components in a collapsed form on the left and displays a larger map to the right. By clicking on the toggle, the component expands and renders geographical data (if available) to the map. To learn more about a data point on the map, simply click and a helpful popup will appear.

![User Interface Map Page](/images/front-end/user-interface-3.png)

## /component

The component view lists all available components in a table. On the left of a page, a panel is available to add components to an exising dashboard or create a new dashboard. Click on the **_add_circle_** icon on the top right of each component preview will add it to the panel. Clicking on "component-info" (資訊頁面 **_arrow_circle_right_**) will open up the component-info view.

![User Interface Component Page](/images/front-end/user-interface-4.png)

## /component/:index

The component-info view shows a component in its full glory. Here, users can view all the statistics a component has to offer, including historical data if available. There will also be the option to report problems (回報問題 **_flag_**) and download the statistical data displayed (下載資料 **_download_**).

![User Interface Component Info Page](/images/front-end/user-interface-5.png)

## /admin

The admin view is only available to users with admin privileges. Here, admins can create, edit, and delete public dashboards and components. Admins can also view all users and their privileges.

![User Interface Admin Page](/images/front-end/user-interface-6.png)

## Mobile Version

This application is designed for tablets or computers. As such, the mobile version of this application only supports previewing the chart and history data of components. Users are also not able to log in on mobile devices.

![User Interface Mobile Version](/images/front-end/user-interface-7.png)
