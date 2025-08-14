# 🚀 快速部署指南

## 最簡單的開始方式

### 1. 確認前置需求
```bash
# 檢查工具是否已安裝
kubectl version --client
helm version
docker --version
```

### 2. 準備映像檔

首先您需要建置並推送 Docker 映像檔到 GitHub Container Registry：

```bash
# 建置 Frontend 映像檔
cd Taipei-City-Dashboard-FE
docker build -t ghcr.io/taipei-doit/taipei-city-dashboard-fe:2.2.0 .
docker push ghcr.io/taipei-doit/taipei-city-dashboard-fe:2.2.0

# 建置 Backend 映像檔  
cd ../Taipei-City-Dashboard-BE
docker build -t ghcr.io/taipei-doit/taipei-city-dashboard-be:2.2.0 .
docker push ghcr.io/taipei-doit/taipei-city-dashboard-be:2.2.0
```

**或者使用 GitHub Actions 自動建置：**
- Push 程式碼到 GitHub，GitHub Actions 會自動建置並推送映像檔

### 3. 部署到開發環境（推薦初次使用）

```bash
cd helm-chart

# 更新依賴
helm dependency update

# 部署
helm install taipei-dashboard . -f values-dev.yaml

# 等待部署完成
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=taipei-city-dashboard --timeout=300s
```

### 4. 檢查部署狀態

```bash
# 查看所有資源
kubectl get all -l app.kubernetes.io/name=taipei-city-dashboard

# 查看 Pod 狀態
kubectl get pods

# 查看服務
kubectl get services
```

### 5. 存取應用程式

開發環境使用 NodePort，您可以透過以下方式存取：

```bash
# 取得節點 IP（如果是本地 minikube）
minikube ip

# 或者使用 port-forward
kubectl port-forward service/taipei-dashboard-frontend 8080:80
kubectl port-forward service/taipei-dashboard-backend 8081:8080
```

然後在瀏覽器中開啟：
- Frontend: http://localhost:8080
- Backend API: http://localhost:8081

## 🔧 如果遇到問題

### 映像檔拉取失敗
```bash
# 檢查映像檔是否存在
docker pull ghcr.io/taipei-doit/taipei-city-dashboard-fe:2.2.0

# 如果是權限問題，設定 GitHub token
docker login ghcr.io -u USERNAME -p TOKEN
```

### Pod 無法啟動
```bash
# 查看 Pod 詳細資訊
kubectl describe pod <pod-name>

# 查看日誌
kubectl logs <pod-name>
```

### 資料庫連線問題
```bash
# 檢查資料庫 Pod
kubectl get pods -l app.kubernetes.io/name=postgresql

# 查看資料庫日誌
kubectl logs -l app.kubernetes.io/name=postgresql
```

## 🎯 準備生產部署

1. **複製生產配置**：
   ```bash
   cp values-prod.yaml my-production-values.yaml
   ```

2. **修改配置**：
   - 設定正確的域名
   - 配置 SSL 憑證
   - 設定 Azure Key Vault（如果使用）
   - 調整資源限制和副本數

3. **部署到生產**：
   ```bash
   helm install taipei-dashboard . -f my-production-values.yaml
   ```

## 📞 需要幫助？

如果部署過程中遇到問題，請檢查：
1. `DEPLOYMENT_CHECKLIST.md` - 詳細的部署檢查清單
2. `TROUBLESHOOTING.md` - 故障排除指南
3. Pod 日誌和事件

---

**簡答您的問題：是的，您現在可以部署了！建議先用開發環境測試。**
