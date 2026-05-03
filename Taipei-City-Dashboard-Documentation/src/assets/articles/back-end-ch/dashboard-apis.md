## APIs

### 獲取所有儀表板

`GET` `/api/v1/dashboard`

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

| 項目 | 描述                                                        |
| ---- | ----------------------------------------------------------- |
| 權限 | `Guest` 只有公開儀表板 <br> `User` `Admin` 公開和個人儀表板 |

**Response:**

```json
{
	"data": {
		"public": [...], // 儀表板配置
		"personal": [...] // 儀表板配置
	},
	"status": "success"
}
```

### 透過 Index 獲取儀表板

`GET` `/api/v1/dashboard/:index`

| 項目 | 描述                                                        |
| ---- | ----------------------------------------------------------- |
| 權限 | `Guest` 只有公開儀表板 <br> `User` `Admin` 公開和個人儀表板 |

**Response:**

```json
{
	"data": [
		// 組成儀表板的組件配置
	],
	"status": "success"
}
```

### 建立個人儀表板

`POST` `/api/v1/dashboard`

| 項目 | 描述           |
| ---- | -------------- |
| 權限 | `User` `Admin` |

**Body:**

```json
{
	// 儀表板配置參數，除 `index`（自動生成）
}
```

**Response:**

```json
{
	"data": {
		// 新建立的儀表板配置
	},
	"status": "success"
}
```

### 建立公開儀表板

`GET` `/api/v1/dashboard/check-index/:index`

首先呼叫此 API 以檢查 Index 是否可用。

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Response:**

```json
{
	"available": true,
	"status": "success"
}
```

`POST` `/api/v1/dashboard/public`

| 項目 | 描述    |
| ---- | ------- |
| 權限 | `Admin` |

**Body:**

```json
{
	// 儀表板配置參數（包括 Index）
}
```

**Response:**

```json
{
	"data": {
		// 新建立的儀表板配置
	},
	"status": "success"
}
```

### 更新儀表板

`PATCH` `/api/v1/dashboard/:index`

| 項目 | 描述                                                |
| ---- | --------------------------------------------------- |
| 權限 | `User` 只有個人儀表板 <br> `Admin` 個人和公開儀表板 |

**Body:**

```json
{
	// 要更新的儀表板配置參數。例如
	"name": "新名稱"
	// 不能更新 `index`
	// 上述參數應在資料庫中手動更新
}
```

**Response:**

```json
{
	"data": {
		// 更新的儀表板配置
	},
	"status": "success"
}
```

### 刪除儀表板

`DEL` `/api/v1/dashboard/:index`

| 項目 | 描述                                                |
| ---- | --------------------------------------------------- |
| 權限 | `User` 只有個人儀表板 <br> `Admin` 個人和公開儀表板 |

**Response:**

```json
{
	"status": "success"
}
```
