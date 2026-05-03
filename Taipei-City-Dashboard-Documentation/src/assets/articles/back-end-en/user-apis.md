## APIs

### Get Current User Info

`GET` `/api/v1/user/me`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `User`      |

**Response:**

```json
{
    "status": "success",
    "user": {
        "user_id": 1,
        "name": "Igor Ho",
        "account": "tuic@gov.taipei",
        "TpAccount": null,
        "is_admin": true,
        "is_active": true,
        "is_whitelist": true,
        "is_blacked": false,
        "expired_at": "2024-03-04T09:01:31.001728Z",
        "created_at": "2024-02-19T02:31:34.727546Z",
        "login_at": "2024-03-05T03:06:59.372152Z"
    }
}
```

### Update Current User Info

`PATCH` `/api/v1/user/me`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `User`      |

**Body:**

```json
{
	// Only the name field can be updated
	"name": "Igor"
}
```

**Response:**

```json
{
    "data": {
        "name": "Igor"
    },
    "status": "success"
}
```

### Get All Users

`GET` `/api/v1/user`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |
| Query Params | `pagesize` ---------------- Number of users per page.<br>`pagenum` ------------------ Page number. Requires `pagesize`.<br>`sort` ----------------------- Column to sort by.<br>`order` --------------------- "asc", "desc".<br>`searchbyname` --------- Search by name.<br>`searchbyid`------------- Search by user_id. |

**Response:**

```json
{
	"data": [
		// Users
	],
	"results": 1, // Number of users returned
	"status": "success",
	"total": 1 // Total number of users
}
```

### Edit User Info (Admin)

`PATCH` `/api/v1/user/:id`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Admin`     |

**Body:**

```json
{
	// Only the following fields can be updated
	"name": "Igor H",
	"is_admin": true,
	"is_active": true,
	"is_whitelist": true,
	"is_blacked": false,
}
```

**Response:**

```json
{
    "status": "success",
    "user": {
        "name": "Igor H",
        "is_admin": true,
        "is_active": true,
        "is_whitelist": true,
        "is_blacked": false,
        "expired_at": "0001-01-01T00:00:00Z" // Auto updated if is_active is false
    }
}
```