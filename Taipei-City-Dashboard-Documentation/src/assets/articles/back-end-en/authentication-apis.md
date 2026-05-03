## Auth System

This project uses Taipei Pass (台北通) as its primary authentication system. However, due to security concerns, we are unable to provide the relevant urls, client ids, and scopes to external developers.

As such, we have also implemented a basic email authentication system for external developers to use which is only available in development mode. During development, open up the login popup as usual, press down `shift` and click on the DOIT logo. This will switch the login mode to email authentication.

The email and password to use are the ones you filled into the .env file when first setting up the project. For more information, please refer to [this previous article](/back-end/project-setup).

## APIs

### Email and Password Authentication

`POST` `/auth/login`

| Item        | Description            |
| ----------- | ---------------------- |
| Permissions | `Guest`                |
| Auth        | `username`, `password` |

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

### TaipeiPass Authentication

> **w01**
> TaipeiPass authentication is not available for external developers.

`GET` `/auth/callback`

| Item         | Description                                             |
| ------------ | ------------------------------------------------------- |
| Permissions  | `Guest`                                                 |
| Query Params | `code` 6 digit code that the Taipei Pass server returns |

**Response:**

```json
{
	"isso_token": "...", // Token returned by Taipei Pass
	"token": "ey...", // Token returned by the backend
	"user": {} // Same as email auth
}
```

`POST` `/auth/logout`

| Item         | Description                                     |
| ------------ | ----------------------------------------------- |
| Permissions  | `User`                                          |
| Query Params | `isso_token` The auth token sent by Taipei Pass |

## Middlewares

### ValidateJWT

Validate the JWT token in the request header and set the user information (`accountType`, `accountID`, `roles`, `groups`, `expiresAt`) to the context.

### IsLoggedIn & IsSysAdm

The former checks if the user is logged in and the latter checks if the user is a system administrator. Both are used to control route access.
