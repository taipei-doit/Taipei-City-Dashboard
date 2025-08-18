# Azure 託管服務設定指南

本指南說明如何設定 Azure 託管的 PostgreSQL 和 Redis 服務，以及相關的 Key Vault 配置。

## 🏗️ Azure 資源架構

```
Azure Resource Group: taipei-dashboard-dev-rg
├── Azure Database for PostgreSQL Flexible Server
├── Azure Cache for Redis
├── Azure Key Vault
├── Azure Kubernetes Service (AKS)
└── Managed Identity
```

## 📋 Azure 資源建立步驟

### 1. 建立資源群組

```bash
az group create --name taipei-dashboard-dev-rg --location eastasia
```

### 2. 建立 Azure Database for PostgreSQL

```bash
# 建立 PostgreSQL 伺服器
az postgres flexible-server create \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-postgres-dev \
  --location eastasia \
  --admin-user dashboard_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14 \
  --storage-size 32 \
  --public-access 0.0.0.0

# 建立資料庫
az postgres flexible-server db create \
  --resource-group taipei-dashboard-dev-rg \
  --server-name taipei-dashboard-postgres-dev \
  --database-name dashboard
```

### 3. 建立 Azure Cache for Redis

```bash
az redis create \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-redis-dev \
  --location eastasia \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false
```

### 4. 建立 Azure Key Vault

```bash
az keyvault create \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-dev-kv \
  --location eastasia \
  --enable-rbac-authorization
```

### 5. 建立 Managed Identity

```bash
az identity create \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-identity
```

## 🔐 Key Vault Secrets 設定

### 取得連線資訊

```bash
# 取得 PostgreSQL 連線資訊
POSTGRES_HOST=$(az postgres flexible-server show \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-postgres-dev \
  --query "fullyQualifiedDomainName" -o tsv)

# 取得 Redis 連線資訊
REDIS_HOST=$(az redis show \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-redis-dev \
  --query "hostName" -o tsv)

REDIS_PASSWORD=$(az redis list-keys \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-redis-dev \
  --query "primaryKey" -o tsv)
```

### 設定 Key Vault Secrets

```bash
# Database secrets
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "db-dashboard-host" --value "$POSTGRES_HOST"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "db-dashboard-password" --value "YourSecurePassword123!"

# Redis secrets
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "redis-host" --value "$REDIS_HOST"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "redis-password" --value "$REDIS_PASSWORD"

# Application secrets
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "gin-domain-dev" --value "test-citydashboard.taipei"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "jwt-secret-dev" --value "your-jwt-secret-key"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "idno-salt-dev" --value "your-idno-salt"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "isso-client-id-dev" --value "your-isso-client-id"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "isso-client-secret-dev" --value "your-isso-client-secret"

# Frontend secrets
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "vite-api-url-dev" --value "https://test-citydashboard.taipei/api"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "vite-mapbox-token" --value "your-mapbox-token"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "vite-mapbox-tile" --value "mapbox://styles/mapbox/light-v10"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "taipeipass-url-dev" --value "https://id-dev.taipei.gov.tw"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "taipeipass-client-id-dev" --value "your-taipeipass-client-id"
az keyvault secret set --vault-name taipei-dashboard-dev-kv --name "taipeipass-scope" --value "openid profile"
```

## 🔑 Managed Identity 權限設定

```bash
# 取得 Managed Identity 的 Client ID 和 Principal ID
IDENTITY_CLIENT_ID=$(az identity show \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-identity \
  --query "clientId" -o tsv)

IDENTITY_PRINCIPAL_ID=$(az identity show \
  --resource-group taipei-dashboard-dev-rg \
  --name taipei-dashboard-identity \
  --query "principalId" -o tsv)

# 給予 Key Vault Secrets User 權限
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/taipei-dashboard-dev-rg/providers/Microsoft.KeyVault/vaults/taipei-dashboard-dev-kv"
```

## 🎯 更新 values-dev.yaml 配置

在您的 `values-dev.yaml` 文件中更新以下值：

```yaml
azureKeyVault:
  enabled: true
  vaultName: "taipei-dashboard-dev-kv"
  tenantId: "YOUR_TENANT_ID"          # az account show --query tenantId -o tsv
  subscriptionId: "YOUR_SUBSCRIPTION_ID"   # az account show --query id -o tsv
  resourceGroup: "taipei-dashboard-dev-rg"
  clientId: "MANAGED_IDENTITY_CLIENT_ID"   # 上面取得的 $IDENTITY_CLIENT_ID

externalDatabase:
  enabled: true
  dashboard:
    host: "POSTGRES_HOST"              # 上面取得的 $POSTGRES_HOST
    port: 5432
    database: "dashboard"
    username: "dashboard_admin"
    password: ""                       # 會從 Key Vault 讀取
    sslMode: "require"

externalRedis:
  enabled: true
  host: "REDIS_HOST"                   # 上面取得的 $REDIS_HOST
  port: 6380
  database: 0
  password: ""                         # 會從 Key Vault 讀取
  tls:
    enabled: true
    insecureSkipVerify: false

serviceAccount:
  create: true
  annotations:
    azure.workload.identity/client-id: "MANAGED_IDENTITY_CLIENT_ID"
```

## 🚀 AKS 部署設定

如果您使用 AKS，需要啟用 Workload Identity：

```bash
# 啟用 Workload Identity
az aks update \
  --resource-group taipei-dashboard-dev-rg \
  --name your-aks-cluster \
  --enable-workload-identity \
  --enable-oidc-issuer

# 取得 OIDC Issuer URL
AKS_OIDC_ISSUER=$(az aks show \
  --resource-group taipei-dashboard-dev-rg \
  --name your-aks-cluster \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)

# 建立 Federated Identity Credential
az identity federated-credential create \
  --name "taipei-dashboard-federated-credential" \
  --identity-name taipei-dashboard-identity \
  --resource-group taipei-dashboard-dev-rg \
  --issuer $AKS_OIDC_ISSUER \
  --subject "system:serviceaccount:default:taipei-dashboard" \
  --audience api://AzureADTokenExchange
```

## 📊 監控和日誌

### 檢查連線狀態

```bash
# 檢查 PostgreSQL 連線
az postgres flexible-server execute \
  --name taipei-dashboard-postgres-dev \
  --admin-user dashboard_admin \
  --admin-password "YourSecurePassword123!" \
  --database-name dashboard \
  --querytext "SELECT version();"

# 檢查 Redis 連線
redis-cli -h $REDIS_HOST -p 6380 --tls -a $REDIS_PASSWORD ping
```

### Azure Monitor 設定

建議啟用以下監控：
- PostgreSQL 的 Query Performance Insight
- Redis 的 Metrics 和 Diagnostic logs
- Key Vault 的 Access logs

## 💰 成本最佳化

對於開發環境，建議使用：
- PostgreSQL: Burstable tier (Standard_B1ms)
- Redis: Basic C0
- 在非工作時間停止資源以節省成本

## 🔄 自動化腳本

您可以將上述步驟整合到一個自動化腳本中，請參考 `scripts/setup-azure-resources.sh`。
