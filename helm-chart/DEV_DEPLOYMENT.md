# 開發環境快速部署指南

這個指南幫助您在本地 Kubernetes 環境中快速部署台北市儀表板，不需要 Azure Key Vault。

## 🎯 適用場景

- 本地開發和測試
- 不需要 Azure 雲端資源
- 快速原型驗證
- CI/CD 測試環境

## 📋 先決條件

1. **本地 Kubernetes 集群** (選擇其中一種)：
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) (推薦)
   - [minikube](https://minikube.sigs.k8s.io/docs/start/)
   - [kind](https://kind.sigs.k8s.io/docs/user/quick-start/)

2. **必要工具**：
   ```bash
   # 檢查工具是否安裝
   kubectl version --client
   helm version
   docker --version
   ```

## 🚀 快速部署 (5 分鐘)

### 1. 準備環境
```bash
cd helm-chart

# 確保 Kubernetes 集群運行
kubectl cluster-info
```

### 2. 一鍵部署
```bash
# 執行開發環境部署腳本
./deploy-dev.sh
```

腳本會詢問是否要建置 Docker 映像，選擇 `y` 來建置本地映像。

### 3. 訪問應用程式
部署完成後，您可以通過以下 URL 訪問：

- **前端**: http://localhost:30080
- **後端**: http://localhost:30088
- **PostgreSQL**: localhost:30432 (用戶名: postgres, 密碼: password)
- **Redis**: localhost:30379

## 🔧 手動部署步驟

如果您喜歡手動控制每個步驟：

### 1. 建置 Docker 映像
```bash
# 建置前端映像
docker build -f docker/frontend.Dockerfile -t taipei-city-dashboard-fe:latest ../Taipei-City-Dashboard-FE

# 建置後端映像
docker build -f docker/backend.Dockerfile -t taipei-city-dashboard-be:latest ../Taipei-City-Dashboard-BE
```

### 2. 載入映像到集群 (如果使用 kind)
```bash
kind load docker-image taipei-city-dashboard-fe:latest
kind load docker-image taipei-city-dashboard-be:latest
```

### 3. 新增 Helm 儲存庫
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 4. 部署應用程式
```bash
helm upgrade --install taipei-dashboard-dev . \
    --namespace default \
    --values values-dev.yaml \
    --wait
```

## 📊 監控部署狀態

### 檢查 Pod 狀態
```bash
kubectl get pods -l app.kubernetes.io/name=taipei-city-dashboard
```

### 檢查服務
```bash
kubectl get svc -l app.kubernetes.io/name=taipei-city-dashboard
```

### 查看日誌
```bash
# 前端日誌
kubectl logs -f deployment/taipei-dashboard-dev-frontend

# 後端日誌
kubectl logs -f deployment/taipei-dashboard-dev-backend
```

## 🔧 配置說明

### 環境變數配置
所有配置都在 `values-dev.yaml` 中，主要包含：

#### 前端配置
- `NODE_ENV`: development
- `VITE_API_URL`: 後端 API 地址
- `VITE_MAPBOXTOKEN`: Mapbox 開發權杖

#### 後端配置
- `GIN_MODE`: debug
- `JWT_SECRET`: 開發用 JWT 密鑰
- `DB_*`: 資料庫連接設定
- `REDIS_*`: Redis 連接設定

### 資料庫配置
- **PostgreSQL**: 內建在集群中，使用 Bitnami chart
- **Redis**: 內建在集群中，使用 Bitnami chart
- **持久化**: 關閉（適合開發環境）

## 🛠️ 常用操作

### 更新部署
```bash
# 修改 values-dev.yaml 後更新
./deploy-dev.sh update
```

### 重建映像
```bash
# 只重建映像
./deploy-dev.sh build
```

### 檢查狀態
```bash
# 檢查部署狀態
./deploy-dev.sh status
```

### 清理環境
```bash
# 完全清理部署
./deploy-dev.sh cleanup
```

## 🐛 常見問題

### 1. Pod 無法拉取映像
```bash
# 檢查映像是否存在
docker images | grep taipei-city-dashboard

# 重新載入映像到 kind (如果使用 kind)
kind load docker-image taipei-city-dashboard-fe:latest
kind load docker-image taipei-city-dashboard-be:latest
```

### 2. 服務無法訪問
```bash
# 檢查 NodePort 服務
kubectl get svc -o wide

# 使用 port-forward 作為替代
kubectl port-forward svc/taipei-dashboard-dev-frontend 8080:80
kubectl port-forward svc/taipei-dashboard-dev-backend 8081:8080
```

### 3. 資料庫連接失敗
```bash
# 檢查 PostgreSQL Pod
kubectl get pods | grep postgresql

# 檢查 PostgreSQL 日誌
kubectl logs deployment/taipei-dashboard-dev-postgresql
```

### 4. 映像建置失敗
確保您在正確的目錄中運行建置命令：
```bash
# 應該在 helm-chart 目錄中
pwd  # 應該顯示 .../Taipei-City-Dashboard/helm-chart

# 檢查源碼目錄是否存在
ls -la ../Taipei-City-Dashboard-FE
ls -la ../Taipei-City-Dashboard-BE
```

## 📝 開發工作流程

### 1. 代碼修改後重新部署
```bash
# 重建映像並更新部署
./deploy-dev.sh build
kubectl rollout restart deployment/taipei-dashboard-dev-frontend
kubectl rollout restart deployment/taipei-dashboard-dev-backend
```

### 2. 配置修改後更新
```bash
# 修改 values-dev.yaml 後
./deploy-dev.sh update
```

### 3. 除錯
```bash
# 進入 Pod 內部
kubectl exec -it deployment/taipei-dashboard-dev-backend -- /bin/sh

# 查看環境變數
kubectl exec deployment/taipei-dashboard-dev-backend -- env
```

## 🔄 完全重置

如果遇到問題需要完全重置：

```bash
# 1. 清理部署
./deploy-dev.sh cleanup

# 2. 清理映像 (可選)
docker rmi taipei-city-dashboard-fe:latest taipei-city-dashboard-be:latest

# 3. 重新部署
./deploy-dev.sh
```

## 🌐 Port Forward 訪問

如果 NodePort 不工作，可以使用 port-forward：

```bash
# 前端
kubectl port-forward svc/taipei-dashboard-dev-frontend 8080:80 &

# 後端  
kubectl port-forward svc/taipei-dashboard-dev-backend 8081:8080 &

# 訪問
open http://localhost:8080
```

這樣您就可以在不依賴 Azure Key Vault 的情況下，快速在本地環境中運行台北市儀表板進行開發和測試！
