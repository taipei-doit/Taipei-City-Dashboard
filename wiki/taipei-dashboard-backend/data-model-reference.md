# Data Model Reference

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [users, roles, groups db](../../raw/taipei-dashboard-backend/users, roles, groups db.md); [dashboards db](../../raw/taipei-dashboard-backend/dashboards db.md); [components db](../../raw/taipei-dashboard-backend/components db.md); [contributors db](../../raw/taipei-dashboard-backend/contributors db.md); [issues db](../../raw/taipei-dashboard-backend/issues db.md); [viewpoints db](../../raw/taipei-dashboard-backend/viewpoints db.md); [chatlog db](../../raw/taipei-dashboard-backend/chatlog db.md); [database overview](../../raw/taipei-dashboard-backend/database overview.md)

## Overview

The backend data model separates dashboard content data in `dashboard` from management and configuration data in `dashboardmanager`. Most documented tables in the backend docs live in `dashboardmanager` and define users, groups, dashboards, components, contributors, issues, viewpoints, and chat conversation history.

## Users, Roles, and Groups

`auth_users` stores login and profile information. Besides local email fields, it stores Taipei Pass identifiers such as ID number, UUID, Taipei Pass account, member type, and verification level. User flags include admin, active, whitelist, blacklist, expiration, creation, and last-login timestamps.

`roles` has three predefined roles:

- `admin`: access control, modify, and read.
- `editor`: modify and read.
- `viewer`: read only.

`groups` stores permission groups and marks whether a group is personal. Version `3.0.0` added public groups named `taipei` and `metrotaipei`.

`auth_user_group_roles` links users, groups, and roles, allowing users to belong to multiple groups and groups to carry multiple role assignments.

## Dashboards

`dashboards` stores dashboard configuration: unique `index`, display `name`, component ID array, icon, and timestamps. `dashboard_groups` links dashboards to permission groups, and dashboard lookup joins through this table to return only dashboards available to a user's groups.

The backend docs state that `dashboard.index` cannot be updated through the dashboard update API and must be changed manually in the database.

## Components

Component configuration is split across `components`, `query_charts`, `component_charts`, and `component_maps`.

`components` stores the main component identity: `id`, `index`, and `name`. In version `3.0.0`, a single component name can have different query/chart information per city while using an index for association.

`query_charts` stores the front-end-facing component metadata and data-query fields, including `history_config`, `map_config_ids`, `map_config`, `chart_config`, `map_filter`, time range fields, update frequency, source metadata, descriptions, links, contributors, `query_type`, SQL strings for chart/history data, and `city`. The documented city values are `taipei` and `metrotaipei`.

`component_charts` stores chart color, chart type names, and display unit by component index. `component_maps` stores map layer configuration such as title, type, source, size, icon, paint, and property.

## Operational Tables

`contributors` stores public contributor metadata. The `user_id` field is intended to match contributor IDs referenced from component configuration, and `include` controls whether the contributor appears in the platform contributor list.

`issues` stores user-reported issues. Status values are `待處理`, `處理中`, `已處理`, and `不處理`; `decision_desc` is required when status is completed or rejected.

`viewpoints` stores saved user map camera positions and pins, including center coordinates, zoom, pitch, bearing, name, and point type. The documented point types are `view` and `pin`.

`chatlog` stores chatbot conversation history by session, question, answer, IP address, user, and timestamps.

## See Also

- [Backend Architecture and Databases](backend-architecture-and-databases.md)
- [Data Tables and Metadata](../taipei-dashboard-dataend/data-tables-and-metadata.md)
- [Dashboard and Component APIs](dashboard-and-component-apis.md)
- [Component Data Querying](component-data-querying.md)
- [Authentication and User APIs](authentication-and-user-apis.md)
