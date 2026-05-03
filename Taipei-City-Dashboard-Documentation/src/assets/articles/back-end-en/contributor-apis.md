## APIs

### Create Contributor

`POST` `/api/v1/contributor`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**
```json
{
	"user_id": "Test",
	"user_name": "Test",
	"description": "Chu chu train",
	"identity": "Chu",
	"image": "https://...",
	"link": "https://...",
	"include": true
}
```

**Response:**

```json
{
    "data": {
        "id": 96,
        "user_id": "Test",
        "user_name": "Test",
        "image": "https://...",
        "link": "https://...",
        "identity": "Chu",
        "description": "Chu chu train",
        "include": true,
        "created_at": "2024-06-13T05:40:34.355047911Z",
        "updated_at": "2024-06-13T05:40:34.355048025Z"
    },
    "status": "success"
}
```

### Get All Contributors

`GET` `/api/v1/contributor`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Guest`     |
| Query Params       | `pagesize` ---------------- Number of issues per page.<br>`pagenum` ------------------ Page number. Requires `pagesize`.<br>`sort` ----------------------- Column to sort by.<br>`order` --------------------- "asc", "desc". |

**Response:**

```json
{
	"data": [
		// Contributors
	],
	"results": 1, // Number of contributors returned
	"status": "success",
	"total": 1 // Total number of contributors
}
```

### Update Contributor

`PATCH` `/api/v1/contributor/:id`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin` |

**Body:**

```json
{
	// Only the id field cannot be updated
	...
}
```

**Response:**

```json
{
	// Updated contributor
}
```

### Delete Contributor

`DEL` `/api/v1/contributor/:id`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin` |

**Response:**

```json
{
	"status": "success"
}
```