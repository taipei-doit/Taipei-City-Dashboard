## APIs

### 建立貢獻者

`POST` `/api/v1/contributor`

| 項目 | 描述           |
| ---- | -------------- |
| 權限 | `Admin` |

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

### 獲取所有貢獻者

`GET` `/api/v1/contributor`

| 項目     | 描述                                                                                                                                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 權限     | `Guest`                                                                                                                                                                                                                                                                   |
| 查詢參數 | `pagesize` ---------------- 每頁的回報問題數量。<br>`pagenum` ------------------ 頁碼。需要 `pagesize`。<br>`sort` ----------------------- 用來排序的欄位。<br>`order` --------------------- "asc", "desc". |

**Response:**

```json
{
	"data": [
		// 貢獻者
	],
	"results": 1, // 回傳的貢獻者數量
	"status": "成功",
	"total": 1 // 貢獻者的總數量
}
```

### 更新貢獻者

`PATCH` `/api/v1/contributor/:id`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 只有 id 欄位不能被更新
	...
}
```

**Response:**

```json
{
	// 更新後的貢獻者
}
```

### 刪除貢獻者

`DEL` `/api/v1/contributor/:id`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Response:**

```json
{
	"status": "成功"
}
```