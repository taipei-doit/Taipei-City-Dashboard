## APIs

### 獲取所有組件

`GET` `/component`

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

| 項目     | 描述                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 權限     | `Guest`                                                                                                                                                                                                                                                                                                                                                                                      |
| 查詢參數 | `pagesize` ------------- 每頁的組件數量。<br>`pagenum` --------------- 頁碼。需要 `pagesize`。<br>`searchbyname` ------ 透過組件名稱搜尋。<br>`searchbyindex` ---- 透過組件 Index 搜尋。 <br>`filterby` ------------- 用來篩選的欄位。 <br>`filtermode` --------- "eq", "ne", "gt", "lt", "in".<br>`sort` -------------------- 用來排序的欄位。<br>`order` ------------------ "asc", "desc".<br>`city` -------------------- "taipei", "metrotaipei". |

**Response:**

```json
{
	"data": [
		{
			// 組件配置
        },...
	],
    "results": 61, // 回傳的組件數量
    "status": "success",
    "total": 61 // 組件總數
}
```

### 透過 ID 獲取組件

`GET` `/component/:id`

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Guest` |

**Response:**

```json
{
	"data": {
		// 組件配置
	},
	"status": "success"
}
```

### 更新組件配置

`PATCH` `/component/:id`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 更新的組件配置參數。例如
	"name": "New Name"
	// 不能更新 `id`, `index`, `map_config_ids`, `query_type`, `query_chart`, `query_history`
	// 上述參數應在資料庫中手動更新
}
```

**Response:**

```json
{
	"data": {
		// 更新的組件配置
	},
	"status": "success"
}
```

### 更新圖表配置

`PATCH` `/component/:id/chart`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 更新的圖表配置參數。例如
	"unit": "km"
	// 不能更新 `index`
	// 上述參數應在資料庫中手動更新
}
```

**Response:**

```json
{
	"data": {
		// 更新的圖表配置
	},
	"status": "success"
}
```

### 更新地圖配置

`PATCH` `/component/:id/map`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 更新的地圖配置參數。例如
	"type": "line"
	// 不能更新 `id`
	// 上述參數應在資料庫中手動更新
}
```

**Response:**

```json
{
	"data": {
		// 更新的地圖配置
	},
	"status": "success"
}
```

### 刪除組件

`DEL` `/component/:id`

> **w01**
> 本 API 仍在 beta 中。前端目前未使用。

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Response:**

```json
{
	"status": "success"
}
```
