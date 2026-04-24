# Backend Architecture and Databases

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [Go Backend](../../raw/taipei-dashboard-backend/Go Backend.md); [database overview](../../raw/taipei-dashboard-backend/database overview.md)

## Overview

The Taipei City Dashboard backend is a Go service organized around Cobra commands, global logging and environment configuration, an application package with router/middleware/controller/model/cache/utility responsibilities, PostgreSQL database access, and Redis caching. It connects to two PostgreSQL databases: `dashboard` for dashboard data and `dashboardmanager` for management configuration.

## Runtime Structure

Cobra commands live in `/cmd/root.go`. Starting the app without a command prefix runs the main `TaipeiCityDashboardBE` command, while other commands such as `migrateDB` handle database schema migration.

Global logging is configured in `/logs/logs.go`. Global constants and environment-derived variables live in `/global/consts.go` and `/global/vars.go`.

The main application entry is `/app/app.go`, where `StartApplication` initializes the application and starts the server.

## App Package Responsibilities

The `/app` directory is split by request lifecycle responsibility:

- `/app/router/router.go` defines available routes.
- `/app/middlewares` handles rate limiting, authentication, permission checks, and common response headers.
- `/app/controllers` handles authentication and business logic for client responses.
- `/app/models` contains database models and handlers, with file names aligned to controller domains.
- `/app/cache/redis.go` creates the global Redis connection.
- `/app/utils` contains shared helpers used across middlewares, controllers, and models.

The backend convention is to place new request pre-processing logic in middlewares, response/business logic in controllers, database interaction in models, and general shared helpers in utilities.

## Database Roles

The `dashboard` database stores statistical, historical, and geographical data used by dashboard components. It is designed to work with Airflow for data updates and includes PostGIS for spatial data. Statistical and historical data is queried through the backend, while geographical data is normally queried and cached through Geoserver and transformed into map tiles.

The `dashboardmanager` database stores management data: users, roles, groups, dashboards, component configs, contributors, issues, viewpoints, and chat logs. The backend queries and mutates this database directly.

## External Developer Constraints

The documentation notes that Airflow and Geoserver configurations were still in the process of being open-sourced. External developers should therefore populate `dashboard` manually or with an alternative service, and may use alternative map-serving approaches such as Mapbox or static GeoJSON files.

## See Also

- [Platform Model](../taipei-city-dashboard/platform-model.md)
- [Data Model Reference](data-model-reference.md)
- [Backend Coding Standards](backend-coding-standards.md)
