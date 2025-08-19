# 資料庫配置指南 - Database Configuration Guide

This guide explains the different database configuration options available in the Taipei City Dashboard Helm chart.

## 🎯 配置選項概覽 (Configuration Options Overview)

The Helm chart supports three main deployment scenarios:

### 1. 🔵 Azure 託管服務 (Azure Managed Services)
- **適用場景**: 台北市政府生產環境
- **資料庫**: Azure Database for PostgreSQL
- **快取**: Azure Cache for Redis
- **密鑰管理**: Azure Key Vault
- **認證**: Azure Workload Identity

### 2. 🟡 外部資料庫 (External Databases)
- **適用場景**: 開源社群用戶
- **資料庫**: 自有 PostgreSQL 伺服器
- **快取**: 自有 Redis 伺服器
- **密鑰管理**: Kubernetes Secrets 或明文配置
- **認證**: 標準 Kubernetes 服務帳戶

### 3. 🟢 叢集內部署 (In-Cluster Deployment)
- **適用場景**: 測試環境、小型部署
- **資料庫**: 叢集內 PostgreSQL (Bitnami Chart)
- **快取**: 叢集內 Redis (Bitnami Chart)
- **密鑰管理**: Kubernetes ConfigMap/Secret
- **認證**: 標準 Kubernetes 服務帳戶

## 📋 配置文件說明 (Configuration Files)

### Azure 託管服務配置
**文件**: `values-azure-managed.yaml`

```yaml
externalDatabase:
  enabled: true
  dashboard:
    host: "your-postgres-server.postgres.database.azure.com"
    azure:
      enabled: true
      useAAD: true  # 使用 Azure AD 認證

externalRedis:
  enabled: true
  host: "your-redis-cache.redis.cache.windows.net"
  azure:
    enabled: true

azureKeyVault:
  enabled: true
```

### 外部資料庫配置
**文件**: `values-external-db.yaml`

```yaml
externalDatabase:
  enabled: true
  dashboard:
    host: "your-postgres-host.example.com"
    username: "dashboard_user"
    password: "your-secure-password"

externalRedis:
  enabled: true
  host: "your-redis-host.example.com"

azureKeyVault:
  enabled: false
```

### 叢集內部署配置
**文件**: `values-in-cluster.yaml`

```yaml
externalDatabase:
  enabled: false

externalRedis:
  enabled: false

postgresql:
  enabled: true

redis:
  enabled: true

azureKeyVault:
  enabled: false
```

## 🚀 部署指令 (Deployment Commands)

### Azure 託管服務部署
```bash
# 1. 設定 Azure 資源 (參考 deploy.sh)
./deploy.sh

# 2. 配置 Key Vault 密鑰
./setup-secrets.sh

# 3. 使用 Azure 配置部署
helm upgrade --install taipei-dashboard . \
  --values values-azure-managed.yaml \
  --namespace production
```

### 外部資料庫部署
```bash
# 1. 編輯配置文件
cp values-external-db.yaml my-values.yaml
# 編輯 my-values.yaml 中的資料庫連接資訊

# 2. 部署應用程式
helm upgrade --install taipei-dashboard . \
  --values my-values.yaml \
  --namespace default
```

### 叢集內部署
```bash
# 1. 新增 Bitnami Helm 儲存庫
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 2. 編輯配置（可選）
cp values-in-cluster.yaml my-values.yaml

# 3. 部署完整堆疊
helm upgrade --install taipei-dashboard . \
  --values my-values.yaml \
  --namespace default \
  --wait
```

## 🔐 密鑰管理 (Secret Management)

### Azure Key Vault 模式
密鑰自動從 Azure Key Vault 載入：
```yaml
azureKeyVault:
  enabled: true
  vaultName: "your-key-vault"
```

### Kubernetes Secret 模式
手動建立 Kubernetes Secret：
```bash
kubectl create secret generic database-credentials \
  --from-literal=username=your-user \
  --from-literal=password=your-password
```

### 明文配置模式（僅適用於開發環境）
```yaml
externalDatabase:
  dashboard:
    username: "dashboard_user"
    password: "your-password"  # 不建議用於生產環境
```

## 📊 資料庫架構選項 (Database Architecture Options)

### 單一資料庫模式
使用同一個資料庫實例：
```yaml
externalDatabase:
  dashboard:
    host: "your-db-host"
    database: "dashboard"
  manager:
    enabled: false  # 使用相同的資料庫
```

### 分離資料庫模式
使用不同的資料庫實例：
```yaml
externalDatabase:
  dashboard:
    host: "dashboard-db-host"
    database: "dashboard"
  manager:
    enabled: true
    host: "manager-db-host"
    database: "manager"
```

## 🔧 連接參數調整 (Connection Tuning)

### PostgreSQL 連接池設定
```yaml
externalDatabase:
  dashboard:
    maxOpenConns: 25      # 最大開放連接數
    maxIdleConns: 5       # 最大空閒連接數
    connMaxLifetime: "5m" # 連接最大生命週期
    sslMode: "require"    # SSL 模式
```

### Redis 配置選項
```yaml
externalRedis:
  port: 6379              # 標準端口
  database: 0             # Redis 資料庫編號
  tls:
    enabled: true         # 啟用 SSL/TLS
    insecureSkipVerify: false
```

## 🔍 故障排除 (Troubleshooting)

### 檢查資料庫連接
```bash
# 檢查後端 Pod 日誌
kubectl logs deployment/taipei-dashboard-backend

# 測試資料庫連接
kubectl exec -it deployment/taipei-dashboard-backend -- env | grep DB_
```

### 檢查 Redis 連接
```bash
# 檢查 Redis 環境變數
kubectl exec -it deployment/taipei-dashboard-backend -- env | grep REDIS_

# 測試 Redis 連接（如果有 redis-cli）
kubectl exec -it deployment/taipei-dashboard-backend -- redis-cli -h $REDIS_HOST ping
```

### 常見錯誤解決

#### 1. 資料庫連接被拒絕
- 檢查防火牆設定
- 確認資料庫伺服器允許來自 Kubernetes 的連接
- 檢查 SSL 設定

#### 2. 認證失敗
- 確認用戶名和密碼正確
- 檢查資料庫用戶權限
- 確認 SSL 憑證設定

#### 3. Azure Key Vault 存取失敗
- 檢查 Workload Identity 設定
- 確認 Managed Identity 有 Key Vault 權限
- 檢查 Secret Provider Class 配置

## 📈 效能調整建議 (Performance Recommendations)

### 生產環境建議
```yaml
# 後端資源配置
backend:
  replicaCount: 3
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

# 資料庫連接池
externalDatabase:
  dashboard:
    maxOpenConns: 25
    maxIdleConns: 5
```

### 高可用性配置
```yaml
# 自動擴展
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15

# Pod 反親和性
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        topologyKey: kubernetes.io/hostname
```

## 🔄 遷移指南 (Migration Guide)

### 從叢集內資料庫遷移到外部資料庫

1. **備份現有資料**：
```bash
kubectl exec -it deployment/taipei-dashboard-postgresql -- pg_dump -U dashboard dashboard > backup.sql
```

2. **設定外部資料庫**：
```bash
# 在外部資料庫中建立資料庫和用戶
# 匯入備份資料
```

3. **更新配置**：
```yaml
externalDatabase:
  enabled: true
  # 配置外部資料庫連接

postgresql:
  enabled: false  # 停用叢集內資料庫
```

4. **重新部署**：
```bash
helm upgrade taipei-dashboard . --values new-values.yaml
```

這個配置系統讓您可以根據不同的需求和環境選擇最適合的部署方式！
