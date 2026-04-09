# Taipei City Dashboard Docker 啟動手冊

## 1) 前置條件

- 已安裝 Docker Desktop（或可用的 Docker Engine + Compose）
- 可使用以下指令：
  - `docker compose version`
- 目前路徑在專案的 `docker/` 資料夾

```bash
cd docker
```

## 2) 設定環境變數

第一次請先建立 `.env`：

```bash
cp .env.template .env
```

> 請依實際環境調整 `.env` 內容（DB 帳密、Qdrant API key、前後端參數等）。

## 3) 建立外部 Docker Network（只需一次）

```bash
docker network inspect br_dashboard >/dev/null 2>&1 || \
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1 br_dashboard
```

## 4) 啟動 DB 與 Qdrant

```bash
docker compose -f docker-compose-db.yaml up -d
docker compose -f docker-compose-db.yaml ps
```

等待兩個 PostgreSQL 服務初始化完成（看到ps `database system is ready to accept connections`）：

```bash
until docker logs postgres-data 2>&1 | grep -q "database system is ready to accept connections"; do sleep 2; done
until docker logs postgres-manager 2>&1 | grep -q "database system is ready to accept connections"; do sleep 2; done
```

## 5) 執行一次性初始化容器

```bash
docker compose -f docker-compose-init.yaml up -d
docker wait dashboard-fe-init dashboard-be-init-manager dashboard-be-init-dashboard
```

確認三個容器都成功結束（應為 `Exited (0)`）：

```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -E 'dashboard-fe-init|dashboard-be-init-manager|dashboard-be-init-dashboard'
```

### 初始化容器任務說明

- `dashboard-fe-init`：執行前端 `npm install`
- `dashboard-be-init-manager`：初始化 `dashboardmanager` DB
- `dashboard-be-init-dashboard`：初始化 `dashboard` DB

## 6) 啟動主服務（前端/後端/Nginx）

```bash
docker compose up -d --build
docker compose ps
```

## 7) 常用服務與連線埠

- 前端（直接）：`http://localhost:8081`
- 前端（經 Nginx）：`http://localhost`
- 後端 API：`http://localhost:8088`
- Qdrant：`http://localhost:6333`
- pgAdmin：`http://localhost:8889`
- PostgreSQL（manager，對外）：`localhost:5433`

## 8) 停止與清理

只停止主服務：

```bash
docker compose down
```

停止 DB/Qdrant：

```bash
docker compose -f docker-compose-db.yaml down
```

停止 init 專用容器（若仍存在）：

```bash
docker compose -f docker-compose-init.yaml down
```
