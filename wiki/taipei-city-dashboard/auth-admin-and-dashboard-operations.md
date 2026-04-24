# Authentication, Admin, and Dashboard Operations

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [用戶驗證](../../raw/用戶驗證.md); [系統管理](../../raw/系統管理.md); [編輯儀表板](../../raw/編輯儀表板.md); [客製化彈跳視窗](../../raw/客製化彈跳視窗.md)

## Overview

Taipei City Dashboard uses TaipeiPASS as its primary authentication system, with a development-only email login fallback for external developers. Permission levels are visitor, user, and admin. Dashboard editing is handled through `contentStore` actions and dashboard APIs, while admin pages manage users, dashboards, components, issues, and contributors.

## Authentication

The official deployment uses TaipeiPASS. Sensitive TaipeiPASS authentication URLs and client IDs are not provided to external developers.

For development mode, the project includes email authentication. Developers open the login dialog, hold `shift`, and click the DOIT logo to switch to email login. Credentials come from the `.env` values configured during project setup.

Login uses `POST /api/v1/auth/login` and user records are backed by `dashboardmanager.users`.

## User Settings and Roles

Users can open settings from the navigation bar. `GET /api/v1/users/me` returns fields including `user_id`, `account`, `name`, `created_at`, `login_at`, and `is_admin`. Currently, only `name` is editable through `POST /api/v1/users/me`.

The documented permission model has three levels:

- Visitors can access dashboard and map pages but cannot modify dashboards.
- Users can access all non-admin pages and modify their own dashboards and settings.
- Admins can access admin pages and modify user permissions, public dashboards, public components, and issues. Admins cannot modify other users' personal dashboards.

## Dashboard Editing

Dashboard editing functions are in `contentStore`.

`createDashboard` uses `POST /api/v1/dashboard`. Users open the sidebar, click the add button, then enter dashboard name, icon, and components in a dialog.

`editCurrentDashboard` uses `PATCH /api/v1/dashboard/:index`. Users click the settings gear near the add-component icon to open dashboard settings.

`deleteCurrentDashboard` uses `DEL /api/v1/dashboard/:index`. Deletion is exposed inside dashboard settings after the user checks a confirmation checkbox.

`deleteComponent` uses `PATCH /api/v1/dashboard/:index` to remove a component from the current dashboard.

`favoriteComponent` and `unfavoriteComponent` use `PATCH /api/v1/dashboard/:favorite-dashboard-index`. The component heart icon toggles whether the component is present in the favorites dashboard.

## Admin Pages

Admin user management lives at `/admin/user` and uses user APIs to list, create, and update users.

Public dashboard management lives at `/admin/dashboard`. Public dashboards can have administrator-specified indexes, while personal dashboard indexes are generated automatically. Admin dashboard APIs list public dashboards, check index availability, create public dashboards by city, update dashboards, and delete dashboards.

Component management lives at `/admin/component`. The documentation says component creation and deletion are still under development, so components currently need to be created and deleted manually in the database. Admin APIs list components and update component, chart, and map settings.

Issue management lives at `/admin/issue` and uses APIs to list and update user-reported issues.

Contributor management lives at `/admin/contributor` and supports listing, creating, updating, and deleting contributors.

## Dialog Dependencies

Many operations surface through dialogs controlled by `dialogStore`, including login, dashboard settings, add/edit dashboards, add components, user settings, report issue, and admin dialogs. This makes dialog registration and placement part of the operational surface, not just UI styling.

## See Also

- [Platform Model](platform-model.md)
- [UI Customization and Dialogs](ui-customization-and-dialogs.md)
- [Static Application Conversion](static-application-conversion.md)
