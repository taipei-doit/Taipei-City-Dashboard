## 1.

建立一個名為br_dashboard的 Docker network。

```
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1 br_dashboard
```

啟動與 DB 及 Qdrant 相關的容器。執行此指令後，檢查所有容器是否正在運行。在執行下一個指令之前，請等待資料庫完全初始化（檢查 docker logs 並檢查輸出中是否有 database system is ready to accept connections）。注意：本地環境必須啟用 Qdrant 容器才能正常使用 Chatbot 功能。

## 2.

```
docker-compose -f docker-compose-db.yaml up -d
```

初始化前端和後端環境。此指令建立的容器是暫時性的。請等待容器停止運行後再運行下一個指令。

## 3.

```
docker-compose -f docker-compose-init.yaml up -d
```
