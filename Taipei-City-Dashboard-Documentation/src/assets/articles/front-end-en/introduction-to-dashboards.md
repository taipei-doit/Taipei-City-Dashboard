## Overview

Dashboards are collections of components that are related to or complement each other in some way. In addition to the default dashboard type, two additional types have been created to better categorize special component types.

### Map Layers

The map layers dashboard is a special dashboard where components that only contain geographical data are stored.

### Favorites

The favorites dashboard works similarly to the default dashboard type with its only difference being the way components are added. Users could click on the heart icon in the top right corner of any component to quickly add the component to the favorites dashboard. The favorites dashboard is created by default for each user and cannot be deleted.

## Dashboard Configuration

Regardless of type, all dashboard configurations (Object) are stored in a single array in the same format. The complete list of parameters could be seen below.

[`GET` `/api/v1/dashboard`](/back-end/dashboard-apis) [`DB` `dashboardmanager.dashboards`](/back-end/dashboards-db)

<!-- _[Try out the API in our API Tester](/api)_ -->

```json
{
    "name": "民情熱議", // String; the name of the dashboard
    "index": "public-opinion", // String; a unique identifier
    "components": [4, 5, 72], // Array; of component IDs
    "icon": "mic" // String; icon name (All Google Icons supported)
},
```
