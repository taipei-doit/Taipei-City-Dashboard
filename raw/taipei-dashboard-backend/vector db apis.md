---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/back-end/vectordb-apis"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Vector DB APIs

## Vector DB

The input query is converted into a vector, and the vector database returns the most similar components.

## APIs

### Search Component

`POST` `/api/v1/vector/component`

| Item | Description |
| --- | --- |
| Permissions | `Guest` |
| Query Params | `query` ------------- query string |

**Response:**

```json
{
    "data": [
        {
            "id": 217,
            "index": "bike_map",
            "name": "自行車道路網圖資",
            "city": "taipei",
            "score": 0.8181
        },
        {
            "id": 213,
            "index": "bike_network",
            "name": "自行車道路統計資料",
            "city": "taipei",
            "score": 0.8158
        },
        {
            "id": 212,
            "index": "ebus_percent",
            "name": "電動巴士比例",
            "city": "taipei",
            "score": 0.814
        }
    ],
    "status": "success"
}
```

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/back-end-en/vectordb-apis.md)