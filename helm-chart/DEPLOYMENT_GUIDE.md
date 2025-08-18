# Taipei City Dashboard - Kubernetes 部署指南

本指南將協助您在 Kubernetes 集群中部署 Taipei City Dashboard。

## 目錄

- [前置需求](#前置需求)
- [快速開始](#快速開始)
- [部署選項](#部署選項)
- [配置說明](#配置說明)
- [部署步驟](#部署步驟)
- [驗證部署](#驗證部署)
- [故障排除](#故障排除)

## 前置需求

### 軟體需求
- Kubernetes 1.19+
- Helm 3.8+
- kubectl configured for your cluster

### 集群需求
- 至少 2 CPU 核心和 4GB RAM 可用資源
- 支援 LoadBalancer 或 Ingress Controller（用於外部存取）
- 如使用 Azure，需要 Azure Key Vault 和 Workload Identity

### 映像檔需求
- 應用程式映像檔已推送至 GitHub Container Registry
- 確保有適當的權限拉取映像檔

## 快速開始

### 1. 克隆專案
```bash
git clone https://github.com/taipei-doit/Taipei-City-Dashboard.git
cd Taipei-City-Dashboard/helm-chart
```

### 2. 更新 Helm 依賴
```bash
helm dependency update
```

### 3. 選擇部署配置

#### 開發環境（使用內建資料庫）
```bash
./deploy-prod.sh -f values-dev.yaml -n taipei-dashboard-dev
```

#### 生產環境（使用外部資料庫）
```bash
./deploy-prod.sh -f values-prod.yaml -n taipei-dashboard-prod
```

#### Azure 託管服務
```bash
./deploy-prod.sh -f values-azure-managed.yaml -n taipei-dashboard-prod
```

## 部署選項

### 選項 1: 開發環境
- **適用於**: 開發、測試、Demo
- **資料庫**: 內建 PostgreSQL 和 Redis
- **儲存**: 臨時儲存（Pod 重啟後資料會遺失）
- **配置檔案**: `values-dev.yaml`

### 選項 2: 生產環境（自建資料庫）
- **適用於**: 生產環境，使用 Kubernetes 內的資料庫
- **資料庫**: 內建 PostgreSQL 和 Redis with persistent storage
- **儲存**: 持久化儲存
- **配置檔案**: `values-prod.yaml`

### 選項 3: Azure 託管服務
- **適用於**: Azure 雲端生產環境
- **資料庫**: Azure Database for PostgreSQL + Azure Cache for Redis
- **秘密管理**: Azure Key Vault
- **配置檔案**: `values-azure-managed.yaml`

### 選項 4: 外部資料庫
- **適用於**: 使用現有資料庫服務
- **資料庫**: 外部 PostgreSQL 和 Redis
- **配置檔案**: `values-external-db.yaml`

## 配置說明

### 必要配置項目

#### 映像檔配置
```yaml
frontend:
  image:
    repository: ghcr.io/taipei-doit/taipei-city-dashboard-fe
    tag: "2.2.0"

backend:
  image:
    repository: ghcr.io/taipei-doit/taipei-city-dashboard-be
    tag: "2.2.0"
```

#### Ingress 配置
```yaml
ingress:
  enabled: true
  hosts:
    - host: your-domain.com
      paths:
        - path: /
          service: frontend
        - path: /api
          service: backend
```

#### Azure Key Vault 配置（如使用）
```yaml
azureKeyVault:
  enabled: true
  vaultName: "your-key-vault"
  tenantId: "your-tenant-id"
  clientId: "your-managed-identity-client-id"
```

### 環境變數配置

#### Frontend 環境變數
- `VITE_API_URL`: Backend API URL
- `VITE_MAPBOXTOKEN`: Mapbox 存取權杖
- `VITE_TAIPEIPASS_CLIENT_ID`: TaipeiPass OAuth Client ID

#### Backend 環境變數
- `GIN_DOMAIN`: 應用程式網域
- `JWT_SECRET`: JWT 加密金鑰
- `DB_*`: 資料庫連線設定
- `REDIS_*`: Redis 連線設定

## 部署步驟

### 步驟 1: 準備配置檔案
```bash
# 複製範例配置檔案
cp values-prod.yaml my-values.yaml

# 編輯配置檔案
vim my-values.yaml
```

### 步驟 2: 設定秘密（如需要）
```bash
# 建立 image pull secret（如使用私有 registry）
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=YOUR_EMAIL
```

### 步驟 3: 部署應用程式
```bash
# 使用部署腳本
./deploy-prod.sh -f my-values.yaml -n taipei-dashboard

# 或直接使用 Helm
helm install taipei-dashboard . \
  --namespace taipei-dashboard \
  --create-namespace \
  --values my-values.yaml
```

### 步驟 4: 驗證部署
```bash
# 檢查部署狀態
./deploy-prod.sh --status

# 或直接使用 kubectl
kubectl get pods -n taipei-dashboard
kubectl get services -n taipei-dashboard
kubectl get ingress -n taipei-dashboard
```

## 驗證部署

### 檢查 Pod 狀態
```bash
kubectl get pods -n taipei-dashboard
```
所有 Pod 都應該處於 `Running` 狀態。

### 檢查服務
```bash
kubectl get services -n taipei-dashboard
```

### 檢查 Ingress
```bash
kubectl get ingress -n taipei-dashboard
```

### 測試應用程式存取
```bash
# 透過 port-forward 測試 frontend
kubectl port-forward svc/taipei-dashboard-frontend 8080:80 -n taipei-dashboard

# 透過 port-forward 測試 backend
kubectl port-forward svc/taipei-dashboard-backend 8081:8080 -n taipei-dashboard
```

然後開啟瀏覽器存取 `http://localhost:8080`

## 更新部署

### 更新映像檔版本
```bash
# 編輯 values 檔案中的 tag
vim my-values.yaml

# 升級部署
helm upgrade taipei-dashboard . \
  --namespace taipei-dashboard \
  --values my-values.yaml
```

### 回滾部署
```bash
# 檢視部署歷史
helm history taipei-dashboard -n taipei-dashboard

# 回滾到前一版本
helm rollback taipei-dashboard -n taipei-dashboard
```

## 故障排除

### 常見問題

#### 1. Pod 無法啟動
```bash
# 檢查 Pod 詳細資訊
kubectl describe pod <pod-name> -n taipei-dashboard

# 檢查 Pod 日誌
kubectl logs <pod-name> -n taipei-dashboard
```

#### 2. 映像檔拉取失敗
- 確認映像檔存在於 GHCR
- 檢查 imagePullSecrets 設定
- 驗證網路連線

#### 3. 資料庫連線失敗
- 檢查資料庫 Pod 狀態
- 驗證資料庫連線參數
- 確認網路政策允許連線

#### 4. Ingress 無法存取
- 檢查 Ingress Controller 狀態
- 驗證 DNS 設定
- 確認防火牆規則

### 除錯命令
```bash
# 檢查所有資源
kubectl get all -n taipei-dashboard

# 檢查事件
kubectl get events -n taipei-dashboard --sort-by='.lastTimestamp'

# 進入 Pod 進行除錯
kubectl exec -it <pod-name> -n taipei-dashboard -- /bin/sh

# 檢查設定檔
kubectl get configmap -n taipei-dashboard -o yaml
kubectl get secret -n taipei-dashboard
```

## 監控和維護

### 資源監控
```bash
# 檢查資源使用量
kubectl top pods -n taipei-dashboard
kubectl top nodes
```

### 自動擴展
Chart 已配置 HPA（Horizontal Pod Autoscaler），會根據 CPU 和記憶體使用量自動擴展。

### 備份
定期備份重要資料：
- 資料庫資料
- 配置檔案
- 秘密資訊

## 進階配置

### 自訂網域和 SSL
```yaml
ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: dashboard.yourdomain.com
  tls:
    - secretName: dashboard-tls
      hosts:
        - dashboard.yourdomain.com
```

### 資源限制調整
```yaml
frontend:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi

backend:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi
```

### 多環境部署
使用不同的 namespace 和 values 檔案來部署多個環境：
```bash
# 開發環境
helm install taipei-dashboard-dev . -n dev -f values-dev.yaml

# 測試環境
helm install taipei-dashboard-staging . -n staging -f values-staging.yaml

# 生產環境
helm install taipei-dashboard-prod . -n prod -f values-prod.yaml
```
