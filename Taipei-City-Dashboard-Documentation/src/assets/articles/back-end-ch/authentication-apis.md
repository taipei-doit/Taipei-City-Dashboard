## 認證系統

本專案使用台北通作為其主要認證系統。然而，基於資安考量，我們無法提供台北通認證相關的網址、客戶端 ID 等給外部開發者。

因此，我們也為外部開發者建置了一個基本的電子郵件認證系統，該系統只有在開發模式下可用。在開發過程中，像往常一樣打開登入彈跳視窗，按下 `shift` 並點擊 DOIT 標誌。這將切換登入模式為電子郵件認證。

使用的電子郵件和密碼是您在首次設定專案時填入 .env 檔案的資訊，更多資訊請參閱[此先前文章](/back-end/project-setup)。

## APIs

### 電子郵件和密碼認證

`POST` `/auth/login`

| 項目 | 描述                   |
| ---- | ---------------------- |
| 權限 | `Guest`                |
| 認證 | `username`, `password` |

**Response:**

```json
{
	"token": "ey...",
	"user": {
		"user_id": 1,
		"account": "tuic@gov.taipei",
		"name": "Taipei",
		"is_active": {
			"Bool": true,
			"Valid": true
		},
		"is_whitelist": {
			"Bool": false,
			"Valid": true
		},
		"is_blacked": {
			"Bool": false,
			"Valid": true
		},
		"expired_at": null,
		"created_at": "2024-01-22T09:48:21.717122+08:00",
		"login_at": "2024-02-02T09:06:52.622091+08:00",
		"roles": [
			{
				"role_id": 1,
				"role_name": "admin"
			}
		],
		"groups": [
			{
				"group_id": 2,
				"group_name": "employee"
			}
		]
	}
}
```

### 臺北通認證

> **w01**
> 臺北通認證不對外部開發者開放。

`GET` `/auth/callback`

| 項目     | 描述                                 |
| -------- | ------------------------------------ |
| 權限     | `Guest`                              |
| 查詢參數 | `code` 臺北通伺服器回傳的 6 位數金鑰 |

**Response:**

```json
{
	"isso_token": "...", // 臺北通回傳的金鑰
	"token": "ey...", // 儀表板後端回傳的金鑰
	"user": {} // 同電子郵件驗證回傳的用戶格式
}
```

`POST` `/auth/logout`

| Item     | Description                   |
| -------- | ----------------------------- |
| 權限     | `User`                        |
| 查詢參數 | `isso_token` 臺北通回傳的金鑰 |

## Middleware

### ValidateJWT

驗證 request header 中的 JWT token，並將用戶訊息（`accountType`、`accountID`、`roles`、`groups`、`expiresAt`）加入 context。

### IsLoggedIn & IsSysAdm

前者檢查用戶是否已登入，後者檢查用戶是否為系統管理員。兩者都用於路徑權限控制。
