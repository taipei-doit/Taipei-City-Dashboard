# Knowledge Base Index

## taipei-city-dashboard

Official front-end documentation for Taipei City Dashboard, covering platform structure, data formats, maps, UI customization, contribution standards, authentication/admin workflows, and static deployment.

| Article | Summary | Updated |
|---------|---------|---------|
| [Platform Model](taipei-city-dashboard/platform-model.md) | Explains dashboards, components, stores, rendering responsibilities, and source tree organization. | 2026-04-24 |
| [Data and Visualization Formats](taipei-city-dashboard/data-and-visualization-formats.md) | Summarizes supported chart data shapes, chart components, historical configuration, and data-cleaning rules. | 2026-04-24 |
| [Map Features and Configuration](taipei-city-dashboard/map-features-and-configuration.md) | Covers spatial data, map filtering, Mapbox configuration, default layers, and map-dialog connections. | 2026-04-24 |
| [UI Customization and Dialogs](taipei-city-dashboard/ui-customization-and-dialogs.md) | Describes global/local styling, design fit, dialog state, dialog implementation, and special dialogs. | 2026-04-24 |
| [Design and Code Standards](taipei-city-dashboard/design-and-code-standards.md) | Records visual, UX, linting, naming, file-structure, CSS-order, and data hygiene standards. | 2026-04-24 |
| [Authentication, Admin, and Dashboard Operations](taipei-city-dashboard/auth-admin-and-dashboard-operations.md) | Documents authentication modes, permissions, dashboard editing actions, and admin management pages. | 2026-04-24 |
| [Static Application Conversion](taipei-city-dashboard/static-application-conversion.md) | Explains how to remove backend-dependent behavior and serve static dashboard data from `/public`. | 2026-04-24 |
| [Hackathon Rules and Delivery Requirements](taipei-city-dashboard/hackathon-rules-and-delivery-requirements.md) | Summarizes 2026 hackathon themes, component requirements, scoring, data rules, technical constraints, and post-award obligations. | 2026-04-24 |
| [AI Model and Tool Calling Integration](taipei-city-dashboard/ai-model-and-tool-calling-integration.md) | Documents the Taiwan AI Cloud model, API key flow, backend gateway, tool-calling architecture, and chat-log governance. | 2026-04-24 |

## taipei-dashboard-backend

Backend documentation for Taipei City Dashboard, covering Go service architecture, PostgreSQL data models, authentication, dashboard/component APIs, component query parsing, AI chat services, operational APIs, and Go coding standards.

| Article | Summary | Updated |
|---------|---------|---------|
| [Backend Architecture and Databases](taipei-dashboard-backend/backend-architecture-and-databases.md) | Explains the Go backend package structure, global services, database connections, Redis cache, and `dashboard` versus `dashboardmanager` responsibilities. | 2026-04-24 |
| [Data Model Reference](taipei-dashboard-backend/data-model-reference.md) | Summarizes backend tables for users, roles, groups, dashboards, components, contributors, issues, viewpoints, and chat logs. | 2026-04-24 |
| [Authentication and User APIs](taipei-dashboard-backend/authentication-and-user-apis.md) | Documents Taipei Pass, development email login, JWT middleware, user/admin endpoints, permission roles, and route-path conflicts. | 2026-04-24 |
| [Dashboard and Component APIs](taipei-dashboard-backend/dashboard-and-component-apis.md) | Covers dashboard CRUD, public dashboard index checks, component config reads/updates, permissions, and table coupling. | 2026-04-24 |
| [Component Data Querying](taipei-dashboard-backend/component-data-querying.md) | Explains SQL query strings, placeholder rules, query-type parsing, chart/history APIs, and vector component search. | 2026-04-24 |
| [AI Chat and Chatlog Services](taipei-dashboard-backend/ai-chat-and-chatlog-services.md) | Documents TWCC chat API parameters, streaming/tool-calling runtime, environment variables, AI logs, and chatlog session APIs. | 2026-04-24 |
| [Operations APIs](taipei-dashboard-backend/operations-apis.md) | Summarizes contributor, issue, and viewpoint APIs with permissions and related operational table rules. | 2026-04-24 |
| [Backend Coding Standards](taipei-dashboard-backend/backend-coding-standards.md) | Records backend Go linting, naming, file structure, and responsibility-placement conventions. | 2026-04-24 |

## taipei-dashboard-dataend

Data-end documentation for Taipei City Dashboard, covering Airflow orchestration, DAG development, PostgreSQL table conventions, dataset metadata, ETL utilities, and Python coding standards.

| Article | Summary | Updated |
|---------|---------|---------|
| [Data-End Architecture](taipei-dashboard-dataend/data-end-architecture.md) | Explains the data end's ETL role, Airflow runtime, common pipeline, database boundary, and environment configuration. | 2026-04-28 |
| [Data-End Project Setup](taipei-dashboard-dataend/data-end-project-setup.md) | Documents local Docker setup for Airflow, the shared dashboard network, required Airflow connection and variables, and PostgreSQL/pgAdmin initialization. | 2026-04-28 |
| [Airflow DAG Development](taipei-dashboard-dataend/airflow-dag-development.md) | Summarizes DAG Python structure, job configuration, metadata planning, load behavior, and Airflow/pgAdmin testing workflow. | 2026-04-28 |
| [Data Tables and Metadata](taipei-dashboard-dataend/data-tables-and-metadata.md) | Documents standard data-end table fields, `dataset_info`, load behaviors, table SQL generation, and source metadata conventions. | 2026-04-24 |
| [Data-End Utility Functions](taipei-dashboard-dataend/data-end-utility-functions.md) | Catalogs extraction, time, spatial, address, load, table-SQL, and TDX authentication utilities under `/dags/utils`. | 2026-04-24 |
| [Data-End Coding Standards](taipei-dashboard-dataend/data-end-coding-standards.md) | Records data-end Python style rules, linting/formatting expectations, naming conventions, and Airflow-specific code placement notes. | 2026-04-24 |
