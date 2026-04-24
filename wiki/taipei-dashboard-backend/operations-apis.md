# Operations APIs

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [contributor apis](../../raw/taipei-dashboard-backend/contributor apis.md); [contributors db](../../raw/taipei-dashboard-backend/contributors db.md); [issue apis](../../raw/taipei-dashboard-backend/issue apis.md); [issues db](../../raw/taipei-dashboard-backend/issues db.md); [viewpoint apis](../../raw/taipei-dashboard-backend/viewpoint apis.md); [viewpoints db](../../raw/taipei-dashboard-backend/viewpoints db.md)

## Overview

The backend includes operational APIs for contributors, issues, and user viewpoints. Contributors and issue administration are mostly admin-facing, while viewpoints store user map camera locations and pins.

## Contributor APIs

`POST /api/v1/contributor` is admin-only and creates contributor records with user ID, user name, description, identity, image, link, and include flag.

`GET /api/v1/contributor` is guest-accessible and supports pagination, sorting, and ordering.

`PATCH /api/v1/contributor/:id` is admin-only and updates contributor fields except ID.

`DEL /api/v1/contributor/:id` is admin-only and deletes a contributor.

Contributor records include public display fields and an `include` flag that controls whether the contributor appears in the platform contributor list.

## Issue APIs

`POST /api/v1/issue` lets users and admins create issue reports with title, description, user identity fields, and context.

`GET /api/v1/issue` is admin-only and supports pagination, status filtering, sorting, and ordering.

`PATCH /api/v1/issue/:id` is admin-only and updates only `status`, `decision_desc`, and `updated_by`.

Issue statuses are `待處理`, `處理中`, `已處理`, and `不處理`. The data model requires `decision_desc` when an issue is completed or rejected.

## Viewpoint APIs

`POST /api/v1/user/:userid/viewpoint` lets a user save a viewpoint with center coordinates, zoom, pitch, bearing, name, and point type.

`GET /api/v1/user/:userid/viewpoint` is guest-accessible and returns a user's viewpoints.

`DEL /api/v1/user/:userid/viewpoint/:viewpointid` lets a user delete a saved viewpoint.

Viewpoint point types are `view` and `pin`.

## See Also

- [Data Model Reference](data-model-reference.md)
- [Authentication and User APIs](authentication-and-user-apis.md)
- [Authentication, Admin, and Dashboard Operations](../taipei-city-dashboard/auth-admin-and-dashboard-operations.md)
