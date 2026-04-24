# Airflow DAG Development

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [dag code](../../raw/taipei-dashboard-dataend/dag code.md); [dag config](../../raw/taipei-dashboard-dataend/dag config.md); [dag testing](../../raw/taipei-dashboard-dataend/dag testing.md); [dag metadata](../../raw/taipei-dashboard-dataend/dag metadata.md); [custom pipeline](../../raw/taipei-dashboard-dataend/custom pipeline.md)

## Overview

A Taipei City Dashboard data-end DAG is normally one Python file plus one `job_config.json` file. The Python file defines the ETL function and delegates Airflow integration to `CommonDag`; the JSON file defines execution behavior and display metadata.

## DAG Python Shape

The typical DAG file lives under a project and data-flow folder, for example `/dags/tutorial/simple_template/template_dag.py`. A normal DAG imports `CommonDag`, defines an `etl_function(**kwargs)`, and finishes by constructing `CommonDag(proj_folder=..., dag_folder=...)` and calling `dag.create_dag(etl_func=etl_function)`.

The ETL function is usually organized into six blocks:

- Pipeline setup through `CommonDag`.
- Imports for pandas, SQLAlchemy, and project utilities.
- Static variable declarations from `kwargs`, `job_config.json`, and source-specific constants.
- Extract, which should retrieve data while preserving raw shape as much as possible.
- Transform, which renames columns, converts types, standardizes time, standardizes geometry, and reshapes output.
- Load, which writes `ready_data` to PostgreSQL and updates `dataset_info`.

The documentation advises keeping raw extraction lightly processed and retaining data where possible. Data minimization is expected later in backend queries or presentation logic.

## Standard Transform Rules

Time columns should include timezone information and use ISO 8601-compatible handling. The project utility `convert_str_to_time_format` supports common Taipei open-data cases, including Republic of China calendar years and conversion to Asia/Taipei time.

Spatial data should use WGS84, `EPSG:4326`, and WKBGeometry for storage. When point data is built from `x` and `y`, `add_point_wkbgeometry_column_to_df` creates both a GeoPandas `geometry` column and a `wkb_geometry` column. Before loading, the ETL code should keep only one of `geometry` or `wkb_geometry`; keeping both can cause database write errors.

## DAG Configuration

Each DAG has a JSON configuration split into `dag_infos` and `data_infos`.

`dag_infos` controls execution. It includes fields such as `dag_id`, `start_date`, `schedule_interval`, `catchup`, Airflow tags, description, default arguments, database connection names, destination table names, raw-data table reservation, and `load_behavior`.

`data_infos` records display metadata for downstream use. It includes Chinese data name, human-readable update frequency, source URL, source type, source department, GIS format, output coordinate system, geometry flag, dataset description, ETL description, and sensitivity. These values are written into `db:dashboard/dashboard/dataset_info`.

The documented `load_behavior` values are:

- `append`: append all incoming rows to the target table.
- `replace`: truncate the target table and write the new data.
- `current+history`: replace the current/default table and append to a history table.

`current+history` is intended for datasets such as YouBike status, where the dashboard needs a fast current table while the project still preserves historical observations for later analysis.

## Metadata Planning

Before implementing a DAG, the documentation recommends recording enough source and target metadata to clarify data characteristics. The suggested checklist includes data-flow name, Chinese and English data names, source platform, source department or platform, source documentation URL, source location, transfer format, source range, update frequency, sensitivity, maintenance method, Airflow update frequency, database table name, primary key, and indexes.

Source range should be described with one of four categories:

- `snapshot`: a point-in-time state.
- `new event`: newly added events that exclude earlier history.
- `slice window`: a changing time window.
- `full history`: all available records up to the present.

Database table names should generally follow `<dept>_<data_name>` in snake case. The docs prefer source or agency labels over application-topic labels because one dataset can support multiple applications and application categories may change.

## Testing Workflow

After local deployment, the DAG can be tested in the Airflow web interface at `http://localhost:8080`. Developers enable the DAG, open its monitoring page, manually trigger it if needed, and inspect task status and logs. A fully successful run shows green task boxes.

Data persistence is checked through pgAdmin at `http://localhost:8889`. Developers inspect the destination table, often starting with the last 100 rows, and compare `_mtime` with the DAG run time. If the DAG succeeded but `_mtime` does not reflect the run, the ETL may have executed without storing data as expected.

## See Also

- [Data-End Architecture](data-end-architecture.md)
- [Data Tables and Metadata](data-tables-and-metadata.md)
- [Data-End Utility Functions](data-end-utility-functions.md)
- [Data-End Coding Standards](data-end-coding-standards.md)
