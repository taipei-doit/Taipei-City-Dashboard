# Dashboard and Component APIs

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [dashboards apis](../../raw/taipei-dashboard-backend/dashboards apis.md); [dashboards db](../../raw/taipei-dashboard-backend/dashboards db.md); [component config apis](../../raw/taipei-dashboard-backend/component config apis.md); [components db](../../raw/taipei-dashboard-backend/components db.md)

## Overview

Dashboard and component APIs expose the configuration layer consumed by the front end. Guests can read public dashboards and component configs, users can create and manage personal dashboards, and admins can manage public dashboards and component settings.

## Dashboard APIs

`GET /api/v1/dashboard` returns public dashboards to guests and both public and personal dashboards to logged-in users and admins.

`GET /api/v1/dashboard/:index` returns the component configs that make up a dashboard. Guest access is limited to public dashboards.

`POST /api/v1/dashboard` creates a personal dashboard for a user or admin. The dashboard index is auto-generated and should not be provided.

Public dashboard creation is admin-only and uses two steps:

- `GET /api/v1/dashboard/check-index/:index` verifies that a public dashboard index is available.
- `POST /api/v1/dashboard/public` creates the public dashboard with an explicit index.

`PATCH /api/v1/dashboard/:index` updates dashboard config fields except `index`. Users can update personal dashboards; admins can update personal and public dashboards.

`DEL /api/v1/dashboard/:index` deletes dashboards. Users can delete personal dashboards; admins can delete personal and public dashboards.

## Component Config APIs

`GET /component` returns component configs and supports pagination, search by name/index, filtering, sorting, ordering, and city filtering for `taipei` or `metrotaipei`.

`GET /component/:id` returns one component config.

Admin-only update endpoints are split by config area:

- `PATCH /component/:id` updates editable component config fields, but not `id`, `index`, `map_config_ids`, `query_type`, `query_chart`, or `query_history`.
- `PATCH /component/:id/chart` updates chart config fields but not `index`.
- `PATCH /component/:id/map` updates map config fields but not `id`.

`DEL /component/:id` is admin-only and marked beta; the docs say it is currently not used by the front end.

## Permission and Data Model Coupling

Dashboard visibility is resolved through `dashboard_groups`, which maps dashboards to permission groups and is checked against the groups assigned to a user.

Component API responses are assembled from the split component tables. `components` provides identity, `query_charts` provides city-specific query and metadata fields, `component_charts` provides chart settings, and `component_maps` provides map layer settings.

## See Also

- [Data Model Reference](data-model-reference.md)
- [Component Data Querying](component-data-querying.md)
- [Platform Model](../taipei-city-dashboard/platform-model.md)
