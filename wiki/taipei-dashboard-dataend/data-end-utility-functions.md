# Data-End Utility Functions

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [utility funtions overview](../../raw/taipei-dashboard-dataend/utility funtions overview.md); [utility functions - extract](../../raw/taipei-dashboard-dataend/utility functions - extract.md); [utility functions - transform time](../../raw/taipei-dashboard-dataend/utility functions - transform time.md); [utility functions - tranform spatial](../../raw/taipei-dashboard-dataend/utility functions - tranform spatial.md); [utility functions - tranform address](../../raw/taipei-dashboard-dataend/utility functions - tranform address.md); [utility functions - load](../../raw/taipei-dashboard-dataend/utility functions - load.md); [utility functions - create table](../../raw/taipei-dashboard-dataend/utility functions - create table.md); [utility functions - tdx token](../../raw/taipei-dashboard-dataend/utility functions - tdx token.md)

## Overview

Data-end utilities live under `/dags/utils` and package recurring ETL tasks by stage. They cover source extraction, time normalization, spatial normalization, address normalization, database loading, table SQL generation, and TDX authentication.

## Runtime Preconditions

Many utility examples assume the project has been deployed and configured. When testing inside Airflow, the docs note that importing `DAG` may be needed to access the environment. When testing outside Airflow, developers may need to append the local `dags` path to `sys.path` so imports from `utils` and `settings` resolve.

## Extract Utilities

`extract_stage.py` includes helpers for common open-data sources and file types:

- `get_data_taipei_api` retrieves all pages from a data.taipei API resource, working around the 1,000-row page limit.
- `get_data_taipei_file_last_modified_time` reads the file update time from a data.taipei dataset page.
- `get_data_taipei_page_change_time` reads a page change time from a data.taipei dataset page.
- `get_tdx_data` retrieves TDX API data.
- `get_moenv_json_data` retrieves Ministry of Environment JSON API data.
- `get_json_file`, `get_geojson_file`, `get_kml`, and `get_shp_file` download and parse common source formats.
- `download_file` and `unzip_file_to_target_folder` support file-based pipelines.

The examples cover JSON, GeoJSON, SHP, KML, KMZ-like workflows, data.taipei APIs, MOENV APIs, and TDX APIs.

## Time Utilities

`transform_time.py` includes `convert_str_to_time_format`, an extension around pandas datetime parsing that adds timezone-aware output, handles Republic of China calendar years, supports UTC input conversion, and can return date-level or string output. It also includes `omit_chinese_string_in_time`, which removes Chinese morning/afternoon markers from time strings before conversion.

## Spatial Utilities

`transform_geometry.py` standardizes spatial data for PostgreSQL/PostGIS storage. Documented helpers include:

- `convert_geometry_to_wkbgeometry`, which adds a `wkb_geometry` column and outputs `EPSG:4326`.
- `add_point_wkbgeometry_column_to_df`, which builds point geometry from coordinate columns and adds both `geometry` and `wkb_geometry`.
- `convert_3d_polygon_to_2d_polygon`.
- `convert_linestring_to_multilinestring`.
- `convert_polygon_to_multipolygon`.

These functions help enforce consistent geometry types before loading data into tables whose geometry column type must match the data.

## Address Utilities

`transform_address.py` provides Taipei-oriented address cleanup and parsing. `clean_data` normalizes full-width and half-width characters, strips punctuation and parentheses, fixes common address character issues, and normalizes section numbers. `main_process` parses cleaned addresses and returns confidence-oriented structured results. `save_data` packages raw, cleaned, parsed, output, and log fields into a DataFrame.

## Load Utilities

`load_stage.py` writes prepared data to PostgreSQL:

- `save_dataframe_to_postgresql` stores non-spatial DataFrames.
- `save_geodataframe_to_postgresql` stores GeoDataFrames and requires a matching geometry type.
- `update_lasttime_in_data_to_dataset_info` writes the latest data-content time for a DAG into `dataset_info`.
- `drop_duplicated_after_saving` wraps a duplicate-removal SQL pattern using a criterion and comparison column.

Both DataFrame and GeoDataFrame saves use the same documented `append`, `replace`, and `current+history` load behaviors.

## Table SQL and TDX Auth

`generate_sql_to_create_DB_table.py` emits SQL for standard dashboard data tables and related cleanup SQL. The docs recommend manual execution through pgAdmin or a similar database tool rather than automatic schema mutation from ETL code.

`auth_tdx.py` provides `TDXAuth`, which obtains TDX access tokens using `TDX_CLIENT_ID` and `TDX_CLIENT_SECRET` from Airflow Variables. Tokens are cached in `token.pickle` and reused until expiration.

## See Also

- [Airflow DAG Development](airflow-dag-development.md)
- [Data Tables and Metadata](data-tables-and-metadata.md)
- [Data-End Coding Standards](data-end-coding-standards.md)
