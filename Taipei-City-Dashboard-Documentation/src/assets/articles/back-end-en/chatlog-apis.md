## Chat Log

Keep the log of the conversation with chatbox.

## APIs

### Create Chat Log

`POST` `/api/v1/chatlog`

| Item     | Description                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Permissions     | `User`                                                                                                                                                                                                                                                                                                                                                                                      |
| Query Params | `session` ------------- sessionid。<br>`question` --------------- question。<br>`answer` ------ answer。<br> |



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
        "id": 1,
        "session": "bike",
        "question": "show me bike components",
        "answer": "There are 5 bike components, 1 = .. 2= ..",
        "ip_address": "192.168.65.1",
        "created_at": "2026-01-27T07:31:40.07163905Z"
    },
    "status": "success"
}
```

### List All Chat Logs

`GET` `/api/v1/chatlog/session/`

| Item | Description    |
| ---- | ------- |
| Permissions | `User` |                                                                              

**Response:**

```json
{
    "data": [
        {
            "session": "bike",
            "created_at": "2025-11-27T09:36:09.374536Z"
        },
		{
            "session": "bus",
            "created_at": "2025-11-27T09:36:09.374536Z"
        },
		{
            "session": "building",
            "created_at": "2025-11-27T09:36:09.374536Z"
        }
    ],
    "status": "success"
}
```

### Get One Chat Log

`GET` `/api/v1/chatlog/session/:session`

| Item | Description    |
| ---- | ------- |
| Permissions | `User` |
| Query Params | `session` ------------- sessionid。<br>|

**Response:**

```json
{
    "data": [
        {
			"id": 1,
			"session": "bike",
			"question": "Do you have bike components",
			"answer": "Yes. There are 5 bike components",
			"ip_address": "192.168.65.1",
			"created_at": "2026-01-27T07:31:40.07163905Z"
		},
        {
			"id": 2,
			"session": "bike",
			"question": "show me all the bike components",
			"answer": "components 1 = .. 2= ..",
			"ip_address": "192.168.65.1",
			"created_at": "2026-01-27T07:31:40.07163905Z"
		},
    ],
    "status": "success"
}
```