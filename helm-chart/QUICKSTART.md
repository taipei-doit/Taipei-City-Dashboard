# Quick Start Guide - Taipei City Dashboard on AKS

This guide provides the fastest path to deploy Taipei City Dashboard on Azure Kubernetes Service.

## Prerequisites ✅

- Azure CLI installed and logged in
- kubectl installed
- Helm 3.x installed
- Docker installed
- An Azure subscription with contributor access

## Quick Deployment (30 minutes)

### Step 1: Clone and Navigate
```bash
git clone https://github.com/taipei-doit/Taipei-City-Dashboard.git
cd Taipei-City-Dashboard/helm-chart
```

### Step 2: Set Environment Variables
```bash
export RESOURCE_GROUP="taipei-dashboard-rg"
export LOCATION="eastasia"
export AKS_CLUSTER_NAME="taipei-dashboard-aks"
export ACR_NAME="youracr$(date +%s)"  # Must be unique
export KEY_VAULT_NAME="taipei-kv-$(date +%s)"  # Must be unique
```

### Step 3: Run Automated Deployment
```bash
# This script creates all Azure resources and deploys the application
./deploy.sh
```

The script will:
- ✅ Create Azure resource group
- ✅ Create Azure Container Registry (ACR)
- ✅ Create Azure Key Vault
- ✅ Create Managed Identity
- ✅ Create AKS cluster with required add-ons
- ✅ Build and push container images
- ✅ Install ingress controller and cert-manager
- ✅ Deploy the application

### Step 4: Configure Secrets
```bash
# Setup all required secrets in Azure Key Vault
./setup-secrets.sh
```

### Step 5: Validate Deployment
```bash
# Validate that everything is working
./validate.sh
```

## Manual Deployment (if you prefer step-by-step)

### 1. Create Azure Resources
```bash
# Login to Azure
az login

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create ACR
az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic
az acr login --name $ACR_NAME

# Create Key Vault
az keyvault create --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP --location $LOCATION

# Create Managed Identity
az identity create --name taipei-dashboard-identity --resource-group $RESOURCE_GROUP

# Get identity info
IDENTITY_CLIENT_ID=$(az identity show --name taipei-dashboard-identity --resource-group $RESOURCE_GROUP --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --name taipei-dashboard-identity --resource-group $RESOURCE_GROUP --query principalId -o tsv)

# Grant Key Vault permissions
az keyvault set-policy --name $KEY_VAULT_NAME --object-id $IDENTITY_PRINCIPAL_ID --secret-permissions get list
```

### 2. Create AKS Cluster
```bash
# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER_NAME \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --enable-addons azure-keyvault-secrets-provider \
  --attach-acr $ACR_NAME \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME
```

### 3. Setup Workload Identity
```bash
# Get AKS OIDC issuer
AKS_OIDC_ISSUER=$(az aks show --name $AKS_CLUSTER_NAME --resource-group $RESOURCE_GROUP --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create federated credential
az identity federated-credential create \
  --name taipei-dashboard-federated \
  --identity-name taipei-dashboard-identity \
  --resource-group $RESOURCE_GROUP \
  --issuer $AKS_OIDC_ISSUER \
  --subject system:serviceaccount:default:taipei-dashboard
```

### 4. Build and Push Images
```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)

# Build and push frontend
docker build -f docker/frontend.Dockerfile -t $ACR_LOGIN_SERVER/taipei-city-dashboard-fe:2.2.0 ../Taipei-City-Dashboard-FE
docker push $ACR_LOGIN_SERVER/taipei-city-dashboard-fe:2.2.0

# Build and push backend
docker build -f docker/backend.Dockerfile -t $ACR_LOGIN_SERVER/taipei-city-dashboard-be:2.2.0 ../Taipei-City-Dashboard-BE
docker push $ACR_LOGIN_SERVER/taipei-city-dashboard-be:2.2.0
```

### 5. Install Dependencies
```bash
# Install nginx-ingress
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 6. Create Production Values
```bash
# Get required values
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create production values file
cat > values-production.yaml << EOF
global:
  imageRegistry: "$ACR_LOGIN_SERVER"

azureKeyVault:
  enabled: true
  vaultName: "$KEY_VAULT_NAME"
  tenantId: "$TENANT_ID"
  subscriptionId: "$SUBSCRIPTION_ID"
  resourceGroup: "$RESOURCE_GROUP"
  clientId: "$IDENTITY_CLIENT_ID"

serviceAccount:
  create: true
  annotations:
    azure.workload.identity/client-id: "$IDENTITY_CLIENT_ID"

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: dashboard.example.com  # Update with your domain
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: backend
EOF
```

### 7. Deploy Application
```bash
# Add required Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy the application
helm upgrade --install taipei-dashboard . \
  --namespace default \
  --values values-production.yaml \
  --wait
```

### 8. Setup Secrets
```bash
# Use the interactive setup script
./setup-secrets.sh

# Or manually add secrets to Key Vault
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "vite-api-url" --value "https://api.yourdomain.com"
# ... add all other required secrets
```

## Verification

### Check Deployment Status
```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check ingress
kubectl get ingress

# Validate with script
./validate.sh
```

### Access Application
```bash
# Get ingress IP
kubectl get ingress taipei-dashboard

# Port-forward for testing
kubectl port-forward svc/taipei-dashboard-frontend 8080:80
kubectl port-forward svc/taipei-dashboard-backend 8081:8080

# Test in browser
open http://localhost:8080
```

## Common Next Steps

### Update Domain
1. Point your domain to the ingress IP
2. Update `values-production.yaml` with your actual domain
3. Redeploy: `helm upgrade taipei-dashboard . --values values-production.yaml`

### Add SSL Certificate
```bash
# Create cluster issuer for Let's Encrypt
kubectl apply -f - << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Scale Application
```bash
# Enable autoscaling in values file and redeploy
# Or manually scale
kubectl scale deployment taipei-dashboard-frontend --replicas=5
kubectl scale deployment taipei-dashboard-backend --replicas=3
```

### Monitor Application
```bash
# View logs
kubectl logs -f deployment/taipei-dashboard-frontend
kubectl logs -f deployment/taipei-dashboard-backend

# Check resource usage
kubectl top pods
kubectl top nodes

# View events
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Cleanup

To remove everything:
```bash
# Delete Helm release
helm uninstall taipei-dashboard

# Delete AKS cluster
az aks delete --name $AKS_CLUSTER_NAME --resource-group $RESOURCE_GROUP --yes

# Delete entire resource group (WARNING: This deletes everything!)
az group delete --name $RESOURCE_GROUP --yes
```

## Getting Help

- **Troubleshooting**: See `TROUBLESHOOTING.md`
- **Health Checks**: See `HEALTH_CHECKS.md`
- **Full Documentation**: See `README.md`
- **Validation Script**: Run `./validate.sh`
- **Secrets Setup**: Run `./setup-secrets.sh`

## Quick Commands Reference

```bash
# Check everything
kubectl get all

# Pod logs
kubectl logs -f deployment/taipei-dashboard-backend

# Describe pod issues
kubectl describe pod <pod-name>

# Port forward for testing
kubectl port-forward svc/taipei-dashboard-frontend 8080:80

# Update deployment
helm upgrade taipei-dashboard . --values values-production.yaml

# Check Helm status
helm status taipei-dashboard

# Validate deployment
./validate.sh quick
```

That's it! Your Taipei City Dashboard should now be running on AKS! 🎉
