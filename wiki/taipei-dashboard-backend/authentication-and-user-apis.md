# Authentication and User APIs

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [authentication apis](../../raw/taipei-dashboard-backend/authentication apis.md); [user apis](../../raw/taipei-dashboard-backend/user apis.md); [users, roles, groups db](../../raw/taipei-dashboard-backend/users, roles, groups db.md)

## Overview

The backend uses Taipei Pass as the primary authentication system and provides a development-only email/password fallback for external developers. Authenticated requests use JWT validation middleware, and user access is modeled through users, groups, roles, and admin flags.

## Authentication Modes

Taipei Pass authentication is the production path, but the backend documentation does not provide external developers with Taipei Pass URLs, client IDs, or scopes.

In development, the login popup can be switched to email authentication by holding `shift` and clicking the DOIT logo. The email and password come from the setup `.env` file.

## Auth Endpoints

`POST /auth/login` accepts `username` and `password` for development email authentication. It returns a backend JWT plus user data including roles and groups.

`GET /auth/callback` accepts the six-digit Taipei Pass `code` query parameter and returns the Taipei Pass token, backend JWT, and user object. The docs explicitly warn that Taipei Pass auth is unavailable for external developers.

`POST /auth/logout` requires a logged-in user and accepts the `isso_token` query parameter returned by Taipei Pass.

## User Endpoints

`GET /api/v1/user/me` returns the current logged-in user's profile, including name, account, Taipei Pass account, admin flag, active/whitelist/blacklist flags, expiration, creation, and last-login timestamps.

`PATCH /api/v1/user/me` lets a logged-in user update only `name`.

`GET /api/v1/user` is admin-only and supports pagination, sorting, ordering, search by name, and search by user ID.

`PATCH /api/v1/user/:id` is admin-only and can update `name`, `is_admin`, `is_active`, `is_whitelist`, and `is_blacked`. If `is_active` is set false, `expired_at` is automatically updated.

## Middleware and Permissions

`ValidateJWT` reads the JWT from the request header and adds `accountType`, `accountID`, `roles`, `groups`, and `expiresAt` to request context.

`IsLoggedIn` checks whether the caller is authenticated. `IsSysAdm` checks whether the caller is a system administrator. These middlewares are route-level access gates.

## Route Naming Conflict

The existing front-end article records current-user operations as `/api/v1/users/me`, while the backend API documentation uses `/api/v1/user/me`. Treat this as a documented source conflict unless verified in code or runtime routing.

## See Also

- [Data Model Reference](data-model-reference.md)
- [Authentication, Admin, and Dashboard Operations](../taipei-city-dashboard/auth-admin-and-dashboard-operations.md)
