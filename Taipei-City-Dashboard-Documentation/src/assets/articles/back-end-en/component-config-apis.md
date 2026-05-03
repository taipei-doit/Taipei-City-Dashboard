## APIs

### Get All Components

`GET` `/component`

<!-- _[Try out the API in our API Tester](/api)_ -->

| Item         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Permissions  | `Guest`                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Query Params | `pagesize` ------------- Number of components per page.<br>`pagenum` --------------- Page number. Requires `pagesize`.<br>`searchbyname` ------ Text string to search name by.<br>`searchbyindex` ---- Text string to search index by. <br>`filterby` ------------- Column to filter by. <br>`filtermode` --------- "eq", "ne", "gt", "lt", "in".<br>`sort` -------------------- Column to sort by.<br>`order` ------------------ "asc", "desc".<br>`city` -------------------- "taipei", "metrotaipei".|

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

<!-- _[Try out the API in our API Tester](/api)_ -->

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Guest`     |

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

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**

```json
{
	// Component config fields to update. e.g.
	"name": "New Name"
	// Cannot update `id`, `index`, `map_config_ids`, `query_type`, `query_chart`, `query_history`
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

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**

```json
{
	// Chart config fields to update. e.g.
	"unit": "km"
	// Cannot update `index`
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

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**

```json
{
	// Map config fields to update. e.g.
	"type": "line"
	// Cannot update `id`
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

> **w01**
> In BETA. Currently not in use by the front-end.

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Response:**

```json
{
	"status": "success"
}
```
