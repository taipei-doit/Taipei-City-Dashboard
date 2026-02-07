# Taipei City Dashboard DE

## 專案簡介

本資料夾為「台北城市儀表板」的資料工程（DE）模組，主要負責資料擷取、清理與入庫。
專案以 Airflow DAGs 管理 ETL 排程，並透過 Docker Compose 部署排程器、Web UI 與 Celery Workers。
資料會依排程頻率自動分流至不同 queue，讓即時任務與重任務互不干擾。

## 中文說明

### Airflow 排程與資源設定紀錄

本專案已針對 Airflow 在長時間運行後 CPU 飆高、排程延遲的情況，調整以下設定。

#### 1) Scheduler 解析節流（降低 DAG 掃描 CPU）

已在 compose 環境變數加入：

- `AIRFLOW__SCHEDULER__PARSING_PROCESSES=2`
- `AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=120`
- `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=300`
- `AIRFLOW__SCHEDULER__MAX_THREADS=2`

目的：降低 `DagFileProcessor` 反覆解析造成的 CPU 壓力。

#### 2) Compose CPU / Memory 限制（非 swarm 也生效）

已在 `docker-compose.yaml` 服務中加入 `cpus` / `mem_limit`，避免單一服務吃滿主機資源。

#### 3) DAG 掃描排除清單

已在 `dags/` 加上 `.airflowignore`，排除非 DAG 內容（例如 `test/`、`tutorial/`、`__pycache__/`）。

#### 4) DAG Queue 自動分流規則

在 DAG 建立時自動依 `schedule_interval` 分配 queue（實作於 `dags/operators/common_pipeline.py`）：

- 10 分鐘內（例如 `*/5 * * * *`, `*/10 * * * *`）→ `realtime`
- daily（每日一次）→ 依 DAG ID 穩定分成一半 `default` / 一半 `heavy`
- 每月以上（例如 `@monthly`, `0 0 1 * *`）→ `heavy`
- 其他（例如每小時、每週）→ `default`

> **注意**：上述規則會覆寫 `default_args.queue`。

---

## English

## Project Overview

This folder is the Data Engineering (DE) module for the Taipei City Dashboard.
It manages data ingestion, transformation, and loading into databases using Airflow DAGs.
Deployment is based on Docker Compose (scheduler, webserver, and Celery workers),
and tasks are auto‑routed to queues by schedule frequency to isolate realtime and heavy workloads.

### Airflow Scheduling & Resource Tuning Notes

These changes address long‑running CPU saturation and scheduling delays in Airflow.

#### 1) Scheduler parsing throttling (reduce DAG scan CPU)

Added environment variables in compose:

- `AIRFLOW__SCHEDULER__PARSING_PROCESSES=2`
- `AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=120`
- `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=300`
- `AIRFLOW__SCHEDULER__MAX_THREADS=2`

Goal: reduce repeated DAG parsing CPU load from `DagFileProcessor`.

#### 2) Compose CPU / Memory limits (effective without swarm)

Added `cpus` / `mem_limit` to compose services to prevent any single service from consuming the whole host.

#### 3) DAG scan ignore list

Added `dags/.airflowignore` to exclude non‑DAG folders (e.g., `test/`, `tutorial/`, `__pycache__/`).

#### 4) Automatic queue routing for DAGs

Queue is auto‑assigned based on `schedule_interval` in `dags/operators/common_pipeline.py`:

- ≤10 minutes (e.g., `*/5 * * * *`, `*/10 * * * *`) → `realtime`
- Daily (once per day) → split 50/50 into `default` and `heavy` by DAG ID
- Monthly or above (e.g., `@monthly`, `0 0 1 * *`) → `heavy`
- Others (e.g., hourly, weekly) → `default`

> **Note**: The rule above overrides `default_args.queue`.
