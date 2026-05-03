## APIs

### Create Issue

`POST` `/api/v1/issue`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `User` `Admin`     |

**Body:**

```json
{
    "title": "test",
    "description": "test",
    "user_name": "Chu",
    "user_id": 2,
    "context": "Chu Chu Train"
}
```

**Response:**

```json
{
	"data": {
		"id": 1,
		"title": "test",
		"description": "test",
		"user_name": "Chu",
		"user_id": 2,
		"context": "Chu Chu Train",
		"decision_desc": "",
        "status": "待處理",
        "updated_by": "",
		"created_at": "2021-07-01T00:00:00.000Z",
		"updated_at": "2021-07-01T00:00:00.000Z"
	},
	"status": "success"
}
```

### Get All Issues

`GET` `/api/v1/issue`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |
| Query Params       | `pagesize` ---------------- Number of issues per page.<br>`pagenum` ------------------ Page number. Requires `pagesize`.<br>`filterbystatus` ----- Statuses to filter by. e.g. 待處理, 已處理<br>`sort` ----------------------- Column to sort by.<br>`order` --------------------- "asc", "desc". |

**Response:**

```json
{
	"data": [
		// Issues
	],
	"results": 1, // Number of issues returned
	"status": "success",
	"total": 1 // Total number of issues
}
```

### Update Issue

`PATCH` `/api/v1/issue/:id`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin` |

**Body:**

```json
{
	// Only the following fields can be updated
	"status": "已處理",
	"decision_desc": "Test",
	"updated_by": "Igor"
}
```

**Response:**

```json
{
	"data": {
		"id": 1,
		"title": "test",
		"description": "test",
		"user_name": "Chu",
		"user_id": 2,
		"context": "Chu Chu Train",
		"decision_desc": "Test",
		"status": "已處理",
		"updated_by": "Igor",
		"created_at": "2021-07-01T00:00:00.000Z",
		"updated_at": "2021-07-02T00:00:00.000Z"
	},
	"status": "success"
}
```