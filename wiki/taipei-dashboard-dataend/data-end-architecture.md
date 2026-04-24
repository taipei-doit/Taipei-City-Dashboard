# Data-End Architecture

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [dataend overview](../../raw/taipei-dashboard-dataend/dataend overview.md); [airflow overview](../../raw/taipei-dashboard-dataend/airflow overview.md); [database overview](../../raw/taipei-dashboard-dataend/database overview.md); [global variable](../../raw/taipei-dashboard-dataend/global variable.md); [custom pipeline](../../raw/taipei-dashboard-dataend/custom pipeline.md)

## Overview

The Taipei City Dashboard data end collects and lightly standardizes application data for the dashboard platform. It follows an Extract, Transform, Load flow, stores final data in PostgreSQL, and intentionally keeps its coupling with the backend at the database boundary.

## System Role

The data end is responsible for collecting and preparing data used by dashboard components. It does not own management, authentication, permission, or user-facing configuration data. Those concerns belong to other parts of the platform.

The source documents emphasize a low entry barrier for contributors: people who can process open data with Python should be able to contribute data flows without needing deep Airflow knowledge. Data filtering and selection for presentation is generally left to the backend so the data end can preserve broadly useful prepared data.

## Airflow Runtime

Airflow is used as the batch-oriented scheduler and workflow monitor. In this project, one DAG represents the full process for acquiring and storing one data source, even if that source writes to more than one destination table.

The Airflow platform is described as four cooperating parts:

- Scheduler and executor, which decide when to run work and execute tasks.
- Webserver, which exposes DAG state and logs.
- DAG files, which contain workflow definitions.
- Metadata database, which stores Airflow state and logs.

The repository structure separates DAGs by project, shared pipeline code, shared utilities, settings, tutorials, temporary data, and local environment configuration. Existing project DAGs live under folders such as `/dags/proj_city_dashboard` and `/dags/proj_new_taipei_city_dashboard`; tutorial examples live under `/dags/tutorial`.

## Common Pipeline

The data end hides most Airflow-specific code behind `/dags/operators/common_pipeline.py` and per-DAG `job_config.json` files. The design goals are to keep focus on data processing, reduce the Airflow learning curve, minimize coupling between ETL code and Airflow, and use Python operators consistently.

The common pipeline creates four tasks:

- `get_and_validate_config` reads and validates `job_config.json` during `CommonDag` initialization.
- `etl` calls the DAG-specific ETL function and passes configured database URIs, proxy settings, data path, and DAG metadata.
- `update_dataset_info` writes display metadata from `data_infos` into `db:dashboard/dashboard/dataset_info`.
- `dag_execution_success` marks the end of the pipeline.

`CommonDag` also resolves proxy settings and database URIs from Airflow Variables and Connections. Its email helper expands configured mailing-list keys from Airflow Variables, allowing shared recipient groups without hardcoding addresses in DAG files.

## Database Boundary

All data-end data lives under `db:dashboard`. The `airflow` schema/database area stores Airflow metadata and logs. The `dashboard` schema/database area stores application data used by dashboard components.

Prepared data in `db:dashboard/dashboard` can be queried by the backend for chart/statistical use or served through Geoserver for map-tile use. The data-end documentation repeats the platform constraint that Geoserver configuration is not fully open-sourced, so external developers may need alternatives such as Mapbox or static GeoJSON.

## Environment Configuration

Global configuration comes from three places:

- System settings in `/config/dockerfile`, mostly used to derive runtime paths.
- Airflow Connections, mainly for database connections.
- Airflow Variables, used for secrets and environment-dependent values such as API keys, credentials, email lists, proxy settings, and TDX credentials.

Documented optional variables include `CWA_API_KEY`, `MOENV_API_KEY`, `TDX_CLIENT_ID`, and `TDX_CLIENT_SECRET`. Shared Python access to project-level settings is centralized in `/dag/settings/global_config.py`.

## See Also

- [Airflow DAG Development](airflow-dag-development.md)
- [Data Tables and Metadata](data-tables-and-metadata.md)
- [Data-End Utility Functions](data-end-utility-functions.md)
- [Backend Architecture and Databases](../taipei-dashboard-backend/backend-architecture-and-databases.md)
