## APIs

### 回報問題

`POST` `/api/v1/issue`

| 項目 | 描述           |
| ---- | -------------- |
| 權限 | `User` `Admin` |

**Body:**

```json
{
	"title": "測試",
	"description": "測試",
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
		"title": "測試",
		"description": "測試",
		"user_name": "Chu",
		"user_id": 2,
		"context": "Chu Chu Train",
		"decision_desc": "",
		"status": "待處理",
		"updated_by": "",
		"created_at": "2021-07-01T00:00:00.000Z",
		"updated_at": "2021-07-01T00:00:00.000Z"
	},
	"status": "成功"
}
```

### 獲取所有回報問題

`GET` `/api/v1/issue`

| 項目     | 描述                                                                                                                                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 權限     | `Admin`                                                                                                                                                                                                                                                                   |
| 查詢參數 | `pagesize` ---------------- 每頁的回報問題數量。<br>`pagenum` ------------------ 頁碼。需要 `pagesize`。<br>`filterbystatus` ----- 以處理狀態篩選。例如 待處理, 已處理<br>`sort` ----------------------- 用來排序的欄位。<br>`order` --------------------- "asc", "desc". |

**Response:**

```json
{
	"data": [
		// 問題回報
	],
	"results": 1, // 回傳的問題數量
	"status": "成功",
	"total": 1 // 問題的總數量
}
```

### 更新問題回報狀態

`PATCH` `/api/v1/issue/:id`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 只有以下參數可以更新
	"status": "已處理",
	"decision_desc": "測試",
	"updated_by": "Igor"
}
```

**Response:**

```json
{
	"data": {
		"id": 1,
		"title": "測試",
		"description": "測試",
		"user_name": "Chu",
		"user_id": 2,
		"context": "Chu Chu Train",
		"decision_desc": "測試",
		"status": "已處理",
		"updated_by": "Igor",
		"created_at": "2021-07-01T00:00:00.000Z",
		"updated_at": "2021-07-02T00:00:00.000Z"
	},
	"status": "成功"
}
```
