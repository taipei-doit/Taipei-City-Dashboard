---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/back-end/component-config-apis"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Component Config APIs

## APIs

### Get All Components

`GET` `/component`

| Item | Description |
| --- | --- |
| Permissions | `Guest` |
| Query Params | `pagesize` ------------- Number of components per page.   `pagenum` --------------- Page number. Requires `pagesize`.   `searchbyname` ------ Text string to search name by.   `searchbyindex` ---- Text string to search index by.   `filterby` ------------- Column to filter by.   `filtermode` --------- "eq", "ne", "gt", "lt", "in".   `sort` -------------------- Column to sort by.   `order` ------------------ "asc", "desc".   `city` -------------------- "taipei", "metrotaipei". |

**Response:**

```json
{
    "data": [
        {
            // Component Config
        },...
    ],
    "results": 61, // Number of components returned
    "status": "success",
    "total": 61 // Total number of components
}
```

### Get Component By ID

`GET` `/component/:id`

| Item | Description |
| --- | --- |
| Permissions | `Guest` |

**Response:**

```json
{
    "data": {
        // Component Config
    },
    "status": "success"
}
```

### Update Component Config

`PATCH` `/component/:id`

| Item | Description |
| --- | --- |
| Permissions | `Admin` |

**Body:**

```json
{
    // Component config fields to update. e.g.
    "name": "New Name"
    // Cannot update \`id\`, \`index\`, \`map_config_ids\`, \`query_type\`, \`query_chart\`, \`query_history\`
    // The above fields should be updated manually in the database
}
```

**Response:**

```json
{
    "data": {
        // Updated component Config
    },
    "status": "success"
}
```

### Update Chart Config

`PATCH` `/component/:id/chart`

| Item | Description |
| --- | --- |
| Permissions | `Admin` |

**Body:**

```json
{
    // Chart config fields to update. e.g.
    "unit": "km"
    // Cannot update \`index\`
    // The above field should be updated manually in the database
}
```

**Response:**

```json
{
    "data": {
        // Updated chart Config
    },
    "status": "success"
}
```

### Update Map Config

`PATCH` `/component/:id/map`

| Item | Description |
| --- | --- |
| Permissions | `Admin` |

**Body:**

```json
{
    // Map config fields to update. e.g.
    "type": "line"
    // Cannot update \`id\`
    // The above field should be updated manually in the database
}
```

**Response:**

```json
{
    "data": {
        // Updated map Config
    },
    "status": "success"
}
```

### Delete Component

`DEL` `/component/:id`

> #### Warning - 1
> 
> In BETA. Currently not in use by the front-end.

| Item | Description |
| --- | --- |
| Permissions | `Admin` |

**Response:**

```json
{
    "status": "success"
}
```

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/back-end-en/component-config-apis.md)