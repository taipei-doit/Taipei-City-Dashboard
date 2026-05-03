## Auth System

This project uses Taipei Pass (台北通) as its primary authentication system. However, due to security concerns, we are unable to provide the relevant urls, client ids, and scopes to external developers.

As such, we have also implemented a basic email authentication system for external developers to use which is only available in development mode. During development, open up the login popup as usual, press down `shift` and click on the DOIT logo. This will switch the login mode to email authentication.

The email and password to use are the ones you filled into the .env file when first setting up the project. For more information, please refer to [this previous article](/front-end/project-setup).

[`POST` `/api/v1/auth/login`](/back-end/authentication-apis) [`DB` `dashboardmanager.users`](/back-end/users-roles-groups-db)

## User Settings

Users are able to view and edit their account settings by hovering over their name on the navbar and clicking on "user settings" (用戶設定). The complete object of user details are as follows. Currently, only the name can be edited.

[`GET` `/api/v1/users/me`](/back-end/user-apis)

```json
{
	"user_id": 1,
	"account": "tuic@gov.taipei",
	"name": "Taipei",
	"created_at": "2024-01-22T09:48:21.717122+08:00",
	"login_at": "2024-01-31T16:19:17.489969+08:00",
	"is_admin": true
}
```

[`POST` `/api/v1/users/me`](/back-end/user-apis)

## User Permissions

This project has three tiers of users: guest, user, and admin. Each tier has its own set of permissions.

### Guest

Guests are only able to access the dashboard view and map view. Guests are also not permitted to modify the dashboard in any way.

### User

Users can access all pages except for the admin page. Users are able to modify their own dashboards and settings.

### Admin

In addition to the permissions of a user, admins are able to access the admin page and modify user permissions, public dashboards, public components, and issues. Admins are not able to access or modify personal dashboards belonging to other users.
