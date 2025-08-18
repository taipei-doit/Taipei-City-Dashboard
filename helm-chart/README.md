# Taipei City Dashboard Helm Chart

這個 Helm chart 用於在 Azure Kubernetes Service (AKS) 上部署台北市儀表板應用程式，並整合 Azure Key Vault 來管理機密資訊。

## 先決條件

1. **Azure Kubernetes Service (AKS) 叢集**
2. **Azure Key Vault**
3. **Azure Container Registry (ACR)** 或其他容器映像倉庫
4. **Helm 3.x**
5. **Azure CLI**
6. **kubectl**

## 必要的 Azure 元件設定

### 1. Azure Key Vault 設定

建立 Azure Key Vault 並新增以下密鑰：

#### Frontend 密鑰
- `vite-api-url`: API 伺服器的 URL
- `vite-mapbox-token`: Mapbox 存取權杖
- `vite-mapbox-tile`: Mapbox 圖磚 URL
- `taipeipass-url`: TaipeiPass 服務 URL
- `taipeipass-client-id`: TaipeiPass 用戶端 ID
- `taipeipass-scope`: TaipeiPass 權限範圍

#### Backend 密鑰
- `gin-domain`: 後端伺服器網域
- `jwt-secret`: JWT 簽章密鑰
- `idno-salt`: ID 號碼加密鹽值
- `isso-client-id`: ISSO 用戶端 ID
- `isso-client-secret`: ISSO 用戶端密鑰
- `db-dashboard-host`: 儀表板資料庫主機
- `db-dashboard-user`: 儀表板資料庫使用者
- `db-dashboard-password`: 儀表板資料庫密碼
- `db-dashboard-dbname`: 儀表板資料庫名稱
- `db-dashboard-port`: 儀表板資料庫連接埠
- `db-manager-host`: 管理資料庫主機
- `db-manager-user`: 管理資料庫使用者
- `db-manager-password`: 管理資料庫密碼
- `db-manager-dbname`: 管理資料庫名稱
- `db-manager-port`: 管理資料庫連接埠
- `redis-host`: Redis 主機
- `redis-port`: Redis 連接埠
- `redis-password`: Redis 密碼
- `redis-db`: Redis 資料庫編號

### 2. Azure Managed Identity 設定

建立使用者指派的 Managed Identity 並授予 Key Vault 存取權限：

```bash
# 建立資源群組
az group create --name taipei-dashboard-rg --location eastasia

# 建立 Managed Identity
az identity create --name taipei-dashboard-identity --resource-group taipei-dashboard-rg

# 取得 Managed Identity 的 Client ID 和 Principal ID
IDENTITY_CLIENT_ID=$(az identity show --name taipei-dashboard-identity --resource-group taipei-dashboard-rg --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --name taipei-dashboard-identity --resource-group taipei-dashboard-rg --query principalId -o tsv)

# 建立 Key Vault
az keyvault create --name taipei-dashboard-kv --resource-group taipei-dashboard-rg --location eastasia

# 授予 Managed Identity 對 Key Vault 的存取權限
az keyvault set-policy --name taipei-dashboard-kv --object-id $IDENTITY_PRINCIPAL_ID --secret-permissions get list
```

### 3. AKS 叢集設定

確保 AKS 叢集啟用 Workload Identity 和 Azure Key Vault CSI 驅動程式：

```bash
# 建立 AKS 叢集（如果尚未存在）
az aks create \
  --resource-group taipei-dashboard-rg \
  --name taipei-dashboard-aks \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --enable-addons azure-keyvault-secrets-provider \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3

# 取得 AKS 認證
az aks get-credentials --resource-group taipei-dashboard-rg --name taipei-dashboard-aks
```

### 4. Workload Identity 聯合設定

建立 Workload Identity 聯合：

```bash
# 取得 AKS 的 OIDC Issuer URL
AKS_OIDC_ISSUER=$(az aks show --name taipei-dashboard-aks --resource-group taipei-dashboard-rg --query "oidcIssuerProfile.issuerUrl" -o tsv)

# 建立聯合認證
az identity federated-credential create \
  --name taipei-dashboard-federated-identity \
  --identity-name taipei-dashboard-identity \
  --resource-group taipei-dashboard-rg \
  --issuer $AKS_OIDC_ISSUER \
  --subject system:serviceaccount:default:taipei-dashboard
```

## 容器映像建置

### Frontend Dockerfile
請參考 `docker/frontend.Dockerfile`

### Backend Dockerfile  
請參考 `docker/backend.Dockerfile`

建置並推送映像到 ACR：

```bash
# 登入 ACR
az acr login --name your-acr-name

# 建置並推送 Frontend 映像
docker build -f docker/frontend.Dockerfile -t your-acr-name.azurecr.io/taipei-city-dashboard-fe:2.2.0 ./Taipei-City-Dashboard-FE
docker push your-acr-name.azurecr.io/taipei-city-dashboard-fe:2.2.0

# 建置並推送 Backend 映像
docker build -f docker/backend.Dockerfile -t your-acr-name.azurecr.io/taipei-city-dashboard-be:2.2.0 ./Taipei-City-Dashboard-BE
docker push your-acr-name.azurecr.io/taipei-city-dashboard-be:2.2.0
```

## 安裝 Helm Chart

### 1. 新增必要的 Helm 儲存庫

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 2. 建立 values 檔案

建立 `values-prod.yaml` 檔案：

```yaml
# Azure Key Vault 設定
azureKeyVault:
  enabled: true
  vaultName: "taipei-dashboard-kv"
  tenantId: "your-tenant-id"
  subscriptionId: "your-subscription-id" 
  resourceGroup: "taipei-dashboard-rg"
  clientId: "your-managed-identity-client-id"

# 映像設定
image:
  registry: "your-acr-name.azurecr.io"

# Service Account 設定
serviceAccount:
  create: true
  annotations:
    azure.workload.identity/client-id: "your-managed-identity-client-id"

# Ingress 設定
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: dashboard.taipei.gov.tw
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: backend
  tls:
    - secretName: taipei-dashboard-tls
      hosts:
        - dashboard.taipei.gov.tw

# 自動擴展設定
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

# 資源設定
frontend:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi

backend:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

### 3. 安裝 Helm Chart

```bash
# 安裝 nginx-ingress（如果尚未安裝）
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# 安裝 cert-manager（如果需要 SSL 憑證）
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 安裝台北市儀表板
helm upgrade --install taipei-dashboard ./helm-chart \
  --namespace default \
  --values values-prod.yaml
```

## 驗證部署

檢查所有 Pod 是否正常運行：

```bash
kubectl get pods -l app.kubernetes.io/name=taipei-city-dashboard
kubectl get svc -l app.kubernetes.io/name=taipei-city-dashboard
kubectl get ingress
```

檢查密鑰是否正確掛載：

```bash
kubectl exec -it deployment/taipei-dashboard-backend -- env | grep -E "(JWT_SECRET|DB_)"
```

## 監控與日誌

如果啟用了監控功能：

```bash
# 檢查 ServiceMonitor
kubectl get servicemonitor

# 檢查日誌
kubectl logs -f deployment/taipei-dashboard-frontend
kubectl logs -f deployment/taipei-dashboard-backend
```

## 故障排除

### 常見問題

1. **Secret 無法載入**
   - 檢查 Managed Identity 權限
   - 檢查 Key Vault 密鑰名稱
   - 檢查 Workload Identity 設定

2. **Pod 無法啟動**
   - 檢查映像拉取權限
   - 檢查資源限制
   - 檢查環境變數

3. **Ingress 無法存取**
   - 檢查 DNS 設定
   - 檢查憑證設定
   - 檢查 nginx-ingress 設定

### 有用的除錯指令

```bash
# 檢查 Secret Provider Class
kubectl describe secretproviderclass

# 檢查 Pod 事件
kubectl describe pod <pod-name>

# 檢查密鑰載入
kubectl exec -it <pod-name> -- ls -la /mnt/secrets-store

# 檢查服務端點
kubectl get endpoints
```

## 升級

升級應用程式：

```bash
helm upgrade taipei-dashboard ./helm-chart \
  --namespace default \
  --values values-prod.yaml \
  --set frontend.image.tag=2.3.0 \
  --set backend.image.tag=2.3.0
```

## 清理

移除部署：

```bash
helm uninstall taipei-dashboard --namespace default
```
