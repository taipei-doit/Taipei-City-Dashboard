# GitHub Container Registry 配置說明

本專案使用 GitHub Container Registry (ghcr.io) 來存放 Docker 映像檔。

## 映像檔位置

- Frontend: `ghcr.io/taipei-doit/taipei-city-dashboard-fe`
- Backend: `ghcr.io/taipei-doit/taipei-city-dashboard-be`

## 公開 vs 私有 Registry

### 公開 Registry（推薦）
如果您的 GitHub repository 和 packages 是公開的，則不需要額外的認證配置。

### 私有 Registry
如果您的 packages 是私有的，您需要設定 imagePullSecrets：

1. 建立 GitHub Personal Access Token (PAT)：
   - 到 GitHub Settings > Developer settings > Personal access tokens
   - 創建 token 並給予 `read:packages` 權限

2. 在 Kubernetes 中建立 Secret：
   ```bash
   kubectl create secret docker-registry ghcr-secret \
     --docker-server=ghcr.io \
     --docker-username=YOUR_GITHUB_USERNAME \
     --docker-password=YOUR_GITHUB_TOKEN \
     --docker-email=YOUR_EMAIL
   ```

3. 在 values.yaml 中配置：
   ```yaml
   imagePullSecrets:
     - name: ghcr-secret
   ```

## 標籤策略

- **Production**: 使用語義化版本標籤，如 `2.2.0`
- **Development**: 使用 `latest` 或 `main` 標籤
- **Feature branches**: 使用分支名稱作為標籤

## CI/CD 建議

建議在 GitHub Actions 中使用以下流程：

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v4
  with:
    context: .
    push: true
    tags: |
      ghcr.io/taipei-doit/taipei-city-dashboard-fe:latest
      ghcr.io/taipei-doit/taipei-city-dashboard-fe:${{ github.sha }}
      ghcr.io/taipei-doit/taipei-city-dashboard-fe:${{ github.ref_name }}
```

## 更新映像檔

要更新部署的映像檔版本：

1. 修改 values.yaml 或對應環境的 values 文件中的 `tag` 值
2. 執行 helm upgrade：
   ```bash
   helm upgrade taipei-dashboard ./helm-chart -f values-prod.yaml
   ```
