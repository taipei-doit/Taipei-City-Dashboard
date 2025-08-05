# Taipei City Dashboard 部署檢查清單

## 🎯 部署前準備

### 1. 確認 Docker 映像檔已準備好
- [ ] Frontend 映像檔：`ghcr.io/taipei-doit/taipei-city-dashboard-fe:2.2.0`
- [ ] Backend 映像檔：`ghcr.io/taipei-doit/taipei-city-dashboard-be:2.2.0`

**檢查方式：**
```bash
# 檢查映像檔是否存在（需要有適當權限）
docker pull ghcr.io/taipei-doit/taipei-city-dashboard-fe:2.2.0
docker pull ghcr.io/taipei-doit/taipei-city-dashboard-be:2.2.0
```

### 2. Kubernetes 叢集準備
- [ ] Kubernetes 叢集已就緒
- [ ] kubectl 已配置並可連接到叢集
- [ ] Helm 3.x 已安裝

**檢查方式：**
```bash
kubectl cluster-info
helm version
```

### 3. 網域和 SSL 憑證（生產環境）
- [ ] DNS 記錄已設定（例如：dashboard.taipei.gov.tw）
- [ ] SSL 憑證管理器已安裝（如使用 cert-manager）

### 4. Azure Key Vault（如果啟用）
- [ ] Azure Key Vault 已建立
- [ ] Managed Identity 已設定
- [ ] Secrets Store CSI Driver 已安裝
- [ ] 所需的 secrets 已在 Key Vault 中建立

### 5. 外部資料庫（如果使用）
- [ ] PostgreSQL 資料庫已準備好
- [ ] Redis 已準備好
- [ ] 網路連線已設定

## 🚀 部署步驟

### 方案 1：開發環境部署（最簡單）

```bash
cd helm-chart

# 更新 dependencies
helm dependency update

# 部署到開發環境
helm install taipei-dashboard . -f values-dev.yaml

# 檢查部署狀態
kubectl get pods
kubectl get services
```

**存取方式：**
- Frontend: `http://localhost:30080` (NodePort)
- Backend: `http://localhost:30088` (NodePort)

### 方案 2：生產環境部署

1. **複製並修改配置文件：**
```bash
cp values-prod.yaml my-values.yaml
```

2. **編輯 my-values.yaml 設定：**
- Azure Key Vault 資訊
- 域名配置
- 資源限制
- 副本數量

3. **部署：**
```bash
helm dependency update
helm install taipei-dashboard . -f my-values.yaml
```

### 方案 3：使用外部託管服務

```bash
# 使用 Azure 託管服務
helm install taipei-dashboard . -f values-azure-managed.yaml
```

## 🔍 部署後驗證

### 檢查 Pods 狀態
```bash
kubectl get pods -l app.kubernetes.io/name=taipei-city-dashboard
```

### 檢查服務
```bash
kubectl get services
```

### 檢查 Ingress（生產環境）
```bash
kubectl get ingress
```

### 查看日誌
```bash
# 查看 Frontend 日誌
kubectl logs -l app.kubernetes.io/component=frontend

# 查看 Backend 日誌
kubectl logs -l app.kubernetes.io/component=backend
```

## 🛠️ 故障排除

### 常見問題

1. **映像檔拉取失敗**
   - 檢查映像檔是否存在
   - 檢查 imagePullSecrets 設定

2. **資料庫連線失敗**
   - 檢查資料庫服務是否正常
   - 檢查環境變數設定
   - 檢查網路政策

3. **應用程式無法存取**
   - 檢查 Ingress 設定
   - 檢查 DNS 解析
   - 檢查防火牆規則

### 有用的除錯指令

```bash
# 檢查事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 詳細檢查 Pod
kubectl describe pod <pod-name>

# 進入容器除錯
kubectl exec -it <pod-name> -- /bin/sh

# 檢查配置
helm get values taipei-dashboard
```

## 📋 環境變數清單

### Frontend 必要環境變數
- `VITE_API_URL`: Backend API URL
- `VITE_MAPBOXTOKEN`: Mapbox 地圖 token
- `VITE_TAIPEIPASS_CLIENT_ID`: TaipeiPass 客戶端 ID

### Backend 必要環境變數
- `GIN_DOMAIN`: 應用程式域名
- `JWT_SECRET`: JWT 簽名密鑰
- `DB_DASHBOARD_*`: 資料庫連線資訊
- `REDIS_*`: Redis 連線資訊

## ✅ 部署完成確認

- [ ] 所有 Pods 狀態為 Running
- [ ] 服務可以正常存取
- [ ] 資料庫連線正常
- [ ] 日誌沒有錯誤訊息
- [ ] Health check 通過

## 🔄 更新部署

```bash
# 更新映像檔版本
helm upgrade taipei-dashboard . -f values-prod.yaml --set frontend.image.tag=2.3.0

# 查看更新狀態
helm status taipei-dashboard
```

## 🗑️ 移除部署

```bash
# 移除應用程式
helm uninstall taipei-dashboard

# 清理 PVC（注意：這會刪除資料）
kubectl delete pvc -l app.kubernetes.io/name=taipei-city-dashboard
```
