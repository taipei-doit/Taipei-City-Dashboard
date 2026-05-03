## APIs

### Get All Dashboards

`GET` `/api/v1/dashboard`

<!-- _[Try out the API in our API Tester](/api)_ -->

| Item        | Description                                                                       |
| ----------- | --------------------------------------------------------------------------------- |
| Permissions | `Guest` Only public dashboards <br> `User` `Admin` Public and personal dashboards |

**Response:**

```json
{
	"data": {
		"public": [...], // Dashboard configs
		"personal": [...] // Dashboard configs
	},
	"status": "success"
}
```

### Get Dashboard By Index

`GET` `/api/v1/dashboard/:index`

| Item        | Description                                                                       |
| ----------- | --------------------------------------------------------------------------------- |
| Permissions | `Guest` Only public dashboards <br> `User` `Admin` Public and personal dashboards |

**Response:**

```json
{
	"data": [
		// Component configs that make up the dashboard
	],
	"status": "success"
}
```

### Create Personal Dashboard

`POST` `/api/v1/dashboard`

| Item        | Description    |
| ----------- | -------------- |
| Permissions | `User` `Admin` |

**Body:**

```json
{
	// Dashboard config fields except for `index` (auto-generated)
}
```

**Response:**

```json
{
	"data": {
		// Created dashboard config
	},
	"status": "success"
}
```

### Create Public Dashboard

`GET` `/api/v1/dashboard/check-index/:index`

Call this API first to check if the index is available.

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Response:**

```json
{
	"available": true,
	"status": "success"
}
```

`POST` `/api/v1/dashboard/public`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**

```json
{
	// Dashboard config fields (incl. index)
}
```

**Response:**

```json
{
	"data": {
		// Created dashboard config
	},
	"status": "success"
}
```

### Update Dashboard

`PATCH` `/api/v1/dashboard/:index`

| Item        | Description                                                                 |
| ----------- | --------------------------------------------------------------------------- |
| Permissions | `User` Only personal dashboards <br> `Admin` Personal and public dashboards |

**Body:**

```json
{
	// Dashboard config fields to update. e.g.
	"name": "New Name"
	// Cannot update `index`
	// The above field should be updated manually in the database
}
```

**Response:**

```json
{
	"data": {
		// Updated dashboard config
	},
	"status": "success"
}
```

### Delete Dashboard

`DEL` `/api/v1/dashboard/:index`

| Item        | Description                                                                 |
| ----------- | --------------------------------------------------------------------------- |
| Permissions | `User` Only personal dashboards <br> `Admin` Personal and public dashboards |

**Response:**

```json
{
	"status": "success"
}
```
