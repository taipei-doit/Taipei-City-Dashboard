# Data-End Project Setup

> Sources: Taipei Urban Intelligence Center, 2026-04-28
> Raw: [DataEnd Project Settings](../../raw/taipei-dashboard-dataend/DataEnd Project Settings.md)

## Overview

The data-end setup creates a local Airflow environment with Docker, connects it to the dashboard PostgreSQL database, and configures the minimum Airflow Connections and Variables required for DAG execution. The setup assumes Docker and Docker Compose are installed, and Docker Desktop should allocate at least 6 GB of RAM, preferably 8 GB or more.

## Airflow Image and Environment

The documented setup builds a custom Airflow image from the directory containing the Airflow Dockerfile:

```bash
docker build -t myairflow:2.7.3 .
```

The Airflow compose directory needs a `.env` file containing the image name, Airflow UID, project directory, and web UI credentials:

```bash
AIRFLOW_IMAGE_NAME=myairflow:2.7.3
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=../
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

`AIRFLOW_PROJ_DIR` should point to the Airflow project root relative to the compose file. The username and password are used to sign in to the Airflow web UI.

## Docker Network

Before starting Airflow, the Docker bridge network `br_dashboard` should exist. Check it with:

```bash
docker network ls
```

If it is missing, create it with:

```bash
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1 br_dashboard
```

This shared network lets Airflow, PostgreSQL, pgAdmin, and related dashboard services resolve each other by container name.

## Starting Airflow

From the directory containing the Airflow `docker-compose.yaml`, start the Airflow containers:

```bash
docker-compose up -d
```

Then inspect status with:

```bash
docker-compose ps
```

When running, Airflow is available at `http://localhost:8080` and uses the credentials from `.env`.

## Required Airflow Settings

Airflow needs at least one database connection and two variables. In the web UI, add the PostgreSQL connection under `Admin -> Connections`:

```yaml
Connection Id: postgres_default
Connection Type: Postgres
Host: dashboard-data
Database: dashboard
Login: airflow
Password: airflow
Port: 5432
```

The connection values should match the PostgreSQL values in `.env`.

Add these Airflow Variables under `Admin -> Variables`:

```text
DEFAULT_EMAIL_LIST: ['your_email_1@mail', 'your_email_2@mail']
HTTPS_PROXY_ENABLED: false
PROXY_URL: {'https': '{ip}:{port}'}
```

`DEFAULT_EMAIL_LIST` controls error notification recipients. `HTTPS_PROXY_ENABLED` controls whether data flows can use a proxy for external requests. `PROXY_URL` is only needed when proxy access is enabled.

## Local PostgreSQL and pgAdmin

When a sample Taipei City Dashboard PostgreSQL database is not already available, extend `.env` with database and pgAdmin settings:

```bash
POSTGRES_DB=dashboard
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
PGADMIN_DEFAULT_EMAIL=default@gmail.com
PGADMIN_DEFAULT_PASSWORD=default
```

Start PostgreSQL and pgAdmin with:

```bash
docker-compose -f docker-compose-db.yaml up -d
```

pgAdmin is available at `http://localhost:8889`. Use the configured pgAdmin email and password to sign in, then create a server connection with:

```yaml
Host name/address: dashboard-data
Port: 5432
Maintenance database: dashboard
Username: airflow
Password: airflow
```

The setup guide describes restoring a provided database backup after connecting through pgAdmin. During restore, disable restoring object ownership and privileges so local users do not need to match the original database environment.

## See Also

- [Data-End Architecture](data-end-architecture.md)
- [Airflow DAG Development](airflow-dag-development.md)
- [Data Tables and Metadata](data-tables-and-metadata.md)
