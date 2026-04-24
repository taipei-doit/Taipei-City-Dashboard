# Platform Model

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [儀表板簡介](../../raw/taipei-dashboard-frontend/儀表板簡介.md); [組件簡介](../../raw/taipei-dashboard-frontend/組件簡介.md); [畫面渲染策略](../../raw/taipei-dashboard-frontend/畫面渲染策略.md); [檔案儲存系統](../../raw/taipei-dashboard-frontend/檔案儲存系統.md)

## Overview

Taipei City Dashboard is organized around dashboards, components, Pinia stores, and supporting Vue views. Dashboards are collections of component IDs, while components define chart, map, history, metadata, source, city, and update behavior. Rendering work is split mainly between `contentStore` for dashboard/component UI and `mapStore` for Mapbox map initialization and layer rendering.

## Dashboards

Dashboard configuration is returned by `GET /api/v1/dashboard` and persisted in `dashboardmanager.dashboards`. Every dashboard object contains a display `name`, a unique English `index`, a `components` array of component IDs, and an `icon` using Google Icons naming.

The documentation distinguishes three dashboard types:

- General dashboards collect related or complementary components.
- Map information layer dashboards store only components with spatial data.
- Favorites behave like normal dashboards but are populated through each component's heart icon. The favorites dashboard is automatically created on first login and cannot be deleted.

## Components

Components are the core data unit. Every component contains statistical data that can be charted, and can optionally include spatial and historical data.

Each component is identified by `id`, `index`, and `city`. `index` is a unique English identifier for the component, `id` is shared by the same data type across cities, and `city` identifies the source city. Components with the same `id` across cities share the same `name` and `chart_config`, while source and content vary by city.

Important configuration fields include:

- `chart_config`: required for general components and linked to chart rendering.
- `query_type`: one of `two_d`, `three_d`, `time`, `percent`, or `map_legend`.
- `map_config`: optional map configuration for components with spatial data.
- `map_filter`: optional chart-to-map filtering configuration.
- `history_config`: optional history-axis configuration.
- `time_from` and `time_to`: query window declarations such as `current`, `month_ago`, `year_start`, `static`, or `demo`.
- `update_freq` and `update_freq_unit`: update cadence metadata.
- `source`, `links`, `tags`, `contributors`, and descriptions: metadata used in the UI.

## Rendering

The application rendering flow separates map and non-map responsibilities. `mapStore` initializes Mapbox and renders spatial data layers. `contentStore` performs the other dashboard and map interface rendering steps, including fetching and storing dashboard and component data.

## Project Structure

The front-end source layout is organized by responsibility:

- `/src/assets`: global styles, utility functions, images, chart and map configs, icon font assets.
- `/src/views`: page-level Vue views.
- `/src/components`: smaller UI Vue components, including `dialogs`, `map`, `utilities`, charts not rendered through dashboard components, and component layouts.
- `/src/dashboardComponent`: dynamic dashboard data visualization components, including chart templates and dashboard-component-specific utilities.
- `/src/store`: Pinia stores including `authStore`, `contentStore`, `mapStore`, `dialogStore`, and `adminStore`.
- `/src/router`: Vue Router and Axios configuration.
- `/public`: larger static data and assets, including map data, contributor data, and images.

## Backend Connection

The backend is a Go service whose `/app` package is split into router, middlewares, controllers, models, cache, and utilities. It connects to two PostgreSQL databases: `dashboard` for statistical, historical, and geographical component data, and `dashboardmanager` for management/configuration data such as users, roles, groups, dashboards, components, contributors, issues, viewpoints, and chat logs.

Dashboard visibility is tied to backend permission groups through `dashboard_groups`. Component responses are assembled from backend tables that separate component identity, city-specific query metadata, chart settings, and map settings.

## See Also

- [Hackathon Rules and Delivery Requirements](hackathon-rules-and-delivery-requirements.md)
- [AI Model and Tool Calling Integration](ai-model-and-tool-calling-integration.md)
- [Data and Visualization Formats](data-and-visualization-formats.md)
- [Map Features and Configuration](map-features-and-configuration.md)
- [Authentication, Admin, and Dashboard Operations](auth-admin-and-dashboard-operations.md)
- [Static Application Conversion](static-application-conversion.md)
- [Backend Architecture and Databases](../taipei-dashboard-backend/backend-architecture-and-databases.md)
- [Dashboard and Component APIs](../taipei-dashboard-backend/dashboard-and-component-apis.md)
