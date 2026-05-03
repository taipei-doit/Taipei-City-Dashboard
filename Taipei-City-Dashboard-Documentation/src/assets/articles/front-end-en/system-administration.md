## User Management

Users are listed and managed in the `/admin/user` page.

[`GET` `/api/v1/user`](/back-end/user-apis) returns all users.

[`POST` `/api/v1/user/`](/back-end/user-apis) creates a user.

[`PATCH` `/api/v1/user/:id`](/back-end/user-apis) modifies a user.

## Dashboard Management

Public dashboards are listed and managed in the `/admin/dashboard` page. Unlike personal dashboards where indexes are auto-generated, admins are able to assign indexes to public dashboards.

[`GET` `/api/v1/dashboard`](/back-end/dashboard-apis) returns all public dashboards.

[`GET` `/api/v1/dashboard/check-index/:index-to-check`](/back-end/dashboard-apis) checks if an index is available.

[`POST` `/api/v1/dashboard/public/:city`](/back-end/dashboard-apis) creates a public dashboard.

[`PATCH` `/api/v1/dashboard/:index`](/back-end/dashboard-apis) modifies a public dashboard.

[`DEL` `/api/v1/dashboard/:index`](/back-end/dashboard-apis) deletes a public dashboard.

## Component Management

Components are listed and managed in the `/admin/component` page. Currently, creating and deleting components is still under development. For now, components still have to be manually created and deleted in the database.

[`GET` `/api/v1/component`](/back-end/component-config-apis) returns all components.

[`PATCH` `/api/v1/component/:id?city=`](/back-end/component-config-apis) modifies a component.

[`PATCH` `/api/v1/component/:id?city=/chart`](/back-end/component-config-apis) modifies a component's chart config.

[`PATCH` `/api/v1/component/:id?city=/map`](/back-end/component-config-apis) modifies a component's map config.

## Issue Management

Issues are listed and managed in the `/admin/issue` page.

[`GET` `/api/v1/issue`](/back-end/issue-apis) returns all issues.

[`PATCH` `/api/v1/issue/:id`](/back-end/issue-apis) modifies an issue.

## Contributor Management

Contributors are listed and managed in the `/admin/contributor` page.

[`GET` `/api/v1/contributor`](/back-end/contributor-apis) returns all contributors.

[`POST` `/api/v1/contributor`](/back-end/contributor-apis) creates a contributor.

[`PATCH` `/api/v1/contributor/:id`](/back-end/contributor-apis) modifies a contributor.

[`DEL` `/api/v1/contributor/:id`](/back-end/contributor-apis) deletes a contributor.