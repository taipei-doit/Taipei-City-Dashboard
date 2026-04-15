# Taipei City Dashboard DE

## 專案簡介

本資料夾為「台北城市儀表板」的資料工程（DE）模組，主要負責資料擷取、清理與入庫。
專案以 Airflow DAGs 管理 ETL 排程，並透過 Docker Compose 部署排程器、Web UI 與 Celery Workers。
資料會依排程頻率自動分流至不同 queue，讓即時任務與重任務互不干擾。

## 中文說明

### 快速啟動（可直接照做）

啟動入口：`docker/develop/docker-compose.yaml`

環境變數範本：`docker/develop/.env.template`

#### 0) 前置需求

- Docker Engine
- Docker Compose v2（`docker compose`）
- 建議至少 2 vCPU / 4GB RAM

#### 1) 建立 `.env`

```bash
cd docker/develop
cp .env.template .env
```

Linux 建議把 `AIRFLOW_UID` 設成目前使用者，避免 volume 權限問題：

```bash
cd docker/develop
sed -i "s/^AIRFLOW_UID=.*/AIRFLOW_UID=$(id -u)/" .env
```

#### 2) 啟動本機相依服務（PostgreSQL + Redis）

以下指令會建立 `de_default` 網路，讓 DE compose（`-p de`）可直接用 `de-postgres`、`de-redis` 連線。

```bash
docker network create de_default || true

docker rm -f de-postgres de-redis 2>/dev/null || true

docker run -d \
	--name de-postgres \
	--network de_default \
	-e POSTGRES_USER=postgres \
	-e POSTGRES_PASSWORD=postgres \
	-e POSTGRES_DB=airflow \
	postgres:16

docker run -d \
	--name de-redis \
	--network de_default \
	redis:7.2-alpine
```

#### 3) 啟動 DE Airflow

```bash
cd docker/develop
docker compose -p de -f docker-compose.yaml up -d --build
docker compose -p de -f docker-compose.yaml ps
```

#### 4) 開啟 Airflow Web UI

- URL: `http://localhost:8080/airflow-sit`
- 帳號密碼：使用 `.env` 內 `USERNAME` / `PASSWORD`

#### 5) 驗證 DAG 載入

```bash
cd docker/develop
docker compose -p de -f docker-compose.yaml exec airflow-webserver airflow dags list | head
docker compose -p de -f docker-compose.yaml logs -f airflow-scheduler
```

#### 6) 停止與清理

```bash
cd docker/develop
docker compose -p de -f docker-compose.yaml down
docker rm -f de-postgres de-redis
```

#### 使用外部 PostgreSQL / Redis

若你已有外部服務，僅需修改 `.env` 內以下欄位即可：

- `MATADATA_DATABASE`
- `CELERY_RESULT_BACKEND`
- `REDIS_CONN`
- `USERNAME`
- `PASSWORD`

#### 連到前後端共用 `docker-compose-db`

可以，建議用 override 檔把 DE 也接到 `br_dashboard` 網路。

1. 先確認根目錄 DB stack 正在執行：

```bash
cd /home/raylon/code/Taipei-City-Dashboard/docker
docker compose -f docker-compose-db.yaml up -d
```

2. 在 DE 建立 `.env`，改用共用服務名稱：

```bash
cd /home/raylon/code/Taipei-City-Dashboard/Taipei-City-Dashboard-DE/docker/develop
cp .env.template .env
sed -i "s#^MATADATA_DATABASE=.*#MATADATA_DATABASE=postgresql+psycopg2://postgres:YOUR_DB_PASSWORD@postgres-manager:5432/airflow#" .env
sed -i "s#^CELERY_RESULT_BACKEND=.*#CELERY_RESULT_BACKEND=db+postgresql://postgres:YOUR_DB_PASSWORD@postgres-manager:5432/airflow#" .env
sed -i "s#^REDIS_CONN=.*#REDIS_CONN=redis://redis:6379/0#" .env
```

請務必把 `YOUR_DB_PASSWORD` 換成 root `docker/.env` 內的 `DB_MANAGER_PASSWORD`。
若未替換，`airflow-init` 會以 `FATAL: password authentication failed for user "postgres"` 結束。

3. 用 override 啟動 DE（共用 `br_dashboard`）：

```bash
cd /home/raylon/code/Taipei-City-Dashboard/Taipei-City-Dashboard-DE/docker/develop
docker compose -p de -f docker-compose.yaml -f docker-compose.br-dashboard.yaml up -d --build
```

4. 若 `airflow` 資料庫尚未建立，可先建立一次：

```bash
docker exec -i postgres-manager psql -U postgres -d postgres -c "CREATE DATABASE airflow;" || true
```

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

### Quick Start (Runnable)

Entrypoint: `docker/develop/docker-compose.yaml`

Environment template: `docker/develop/.env.template`

#### 1) Create `.env`

```bash
cd docker/develop
cp .env.template .env
sed -i "s/^AIRFLOW_UID=.*/AIRFLOW_UID=$(id -u)/" .env
```

#### 2) Start local dependencies (PostgreSQL + Redis)

```bash
docker network create de_default || true

docker rm -f de-postgres de-redis 2>/dev/null || true

docker run -d \
	--name de-postgres \
	--network de_default \
	-e POSTGRES_USER=postgres \
	-e POSTGRES_PASSWORD=postgres \
	-e POSTGRES_DB=airflow \
	postgres:16

docker run -d \
	--name de-redis \
	--network de_default \
	redis:7.2-alpine
```

#### 3) Start DE services

```bash
cd docker/develop
docker compose -p de -f docker-compose.yaml up -d --build
docker compose -p de -f docker-compose.yaml ps
```

#### 4) Open Airflow UI

- URL: `http://localhost:8080/airflow-sit`
- Login: `USERNAME` / `PASSWORD` from `.env`

#### 5) Stop and clean up

```bash
cd docker/develop
docker compose -p de -f docker-compose.yaml down
docker rm -f de-postgres de-redis
```

#### Connect DE to shared docker-compose-db

Yes. Use the override file so DE services join `br_dashboard`.

```bash
cd /home/raylon/code/Taipei-City-Dashboard/docker
docker compose -f docker-compose-db.yaml up -d

cd /home/raylon/code/Taipei-City-Dashboard/Taipei-City-Dashboard-DE/docker/develop
cp .env.template .env
sed -i "s#^MATADATA_DATABASE=.*#MATADATA_DATABASE=postgresql+psycopg2://postgres:YOUR_DB_PASSWORD@postgres-manager:5432/airflow#" .env
sed -i "s#^CELERY_RESULT_BACKEND=.*#CELERY_RESULT_BACKEND=db+postgresql://postgres:YOUR_DB_PASSWORD@postgres-manager:5432/airflow#" .env
sed -i "s#^REDIS_CONN=.*#REDIS_CONN=redis://redis:6379/0#" .env

docker compose -p de -f docker-compose.yaml -f docker-compose.br-dashboard.yaml up -d --build
```

Make sure `YOUR_DB_PASSWORD` is replaced with `DB_MANAGER_PASSWORD` from root `docker/.env`.
If not replaced, `airflow-init` exits with `FATAL: password authentication failed for user "postgres"`.

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
