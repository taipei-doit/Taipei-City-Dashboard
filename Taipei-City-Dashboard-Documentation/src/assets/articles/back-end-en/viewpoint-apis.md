## APIs

### Create Viewpoint for A User

`POST` `/api/v1/user/:userid/viewpoint`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `User`     |

**Body:**
```json
{
	"bearing": -56.75256000000002,
	"center_x": 121.51684,
	"center_y": 25.049266999999972,
	"name": "Test",
	"pitch": 70.56765000000001,
	"point_type": "view",
	"zoom": 12.036047,
}
```

**Response:**

```json
{
    "data": {
        "id": 19,
        "user_id": 24,
        "center_x": 121.51684,
        "center_y": 25.049267,
        "zoom": 12.036047,
        "pitch": 70.56765,
        "bearing": -56.75256,
        "name": "Test",
        "point_type": "view",
    },
    "status": "success"
}
```

### Get All Viewpoints of A User

`GET` `/api/v1/user/:userid/viewpoint`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `Guest`     |

**Response:**

```json
{
	"data": [
		// Viewpoints
	],
	"results": 1, // Number of viewpoints returned
	"status": "success",
	"total": 1 // Total number of viewpoints
}
```

### Delete A Viewpoint of A User

`DEL` `/api/v1/user/:userid/viewpoint/:viewpointid`

| Item        | Description |
| ----------- | ----------- |
| Permissions | `User` |

**Response:**

```json
{
	"status": "success"
}
```