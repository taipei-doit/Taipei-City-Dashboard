# Troubleshooting Guide - Taipei City Dashboard on AKS

This guide helps you troubleshoot common issues when deploying and running Taipei City Dashboard on Azure Kubernetes Service.

## Common Issues and Solutions

### 1. Azure Key Vault Secret Access Issues

#### Problem: Pods cannot access secrets from Azure Key Vault
```
Error: failed to mount secrets store objects for pod default/taipei-dashboard-backend-xxx
```

#### Solutions:

**Check Workload Identity Configuration:**
```bash
# Verify service account annotations
kubectl describe serviceaccount taipei-dashboard

# Check if workload identity label exists on pod
kubectl get pod <pod-name> -o yaml | grep azure.workload.identity

# Verify federated credential
az identity federated-credential list --identity-name taipei-dashboard-identity --resource-group taipei-dashboard-rg
```

**Check Key Vault Permissions:**
```bash
# Verify managed identity has access to Key Vault
IDENTITY_PRINCIPAL_ID=$(az identity show --name taipei-dashboard-identity --resource-group taipei-dashboard-rg --query principalId -o tsv)
az keyvault show --name taipei-dashboard-kv --query "properties.accessPolicies[?objectId=='$IDENTITY_PRINCIPAL_ID']"
```

**Check Secret Provider Class:**
```bash
# Verify SecretProviderClass configuration
kubectl describe secretproviderclass taipei-dashboard-secrets

# Check if CSI driver is installed
kubectl get daemonset -n kube-system | grep secrets-store
```

### 2. Image Pull Issues

#### Problem: Cannot pull container images from ACR
```
Error: ErrImagePull or ImagePullBackOff
```

#### Solutions:

**Check ACR Integration:**
```bash
# Verify AKS-ACR integration
az aks check-acr --name taipei-dashboard-aks --resource-group taipei-dashboard-rg --acr taipei-dashboard-acr

# Re-attach ACR if needed
az aks update --name taipei-dashboard-aks --resource-group taipei-dashboard-rg --attach-acr taipei-dashboard-acr
```

**Check Image Tags:**
```bash
# List available images in ACR
az acr repository list --name taipei-dashboard-acr
az acr repository show-tags --name taipei-dashboard-acr --repository taipei-city-dashboard-fe
```

### 3. Pod Startup Issues

#### Problem: Pods are crashing or not starting
```
Error: CrashLoopBackOff or Failed
```

#### Solutions:

**Check Pod Logs:**
```bash
# Get current logs
kubectl logs deployment/taipei-dashboard-backend

# Get previous container logs
kubectl logs deployment/taipei-dashboard-backend --previous

# Follow logs in real-time
kubectl logs -f deployment/taipei-dashboard-backend
```

**Check Pod Events:**
```bash
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Check Resource Limits:**
```bash
# Check if pod is being killed due to resource limits
kubectl top pods
kubectl describe pod <pod-name> | grep -A 5 -B 5 "Limits\|Requests"
```

### 4. Database Connection Issues

#### Problem: Backend cannot connect to database
```
Error: failed to connect to database
```

#### Solutions:

**Check Database Secrets:**
```bash
# Verify database secrets exist in Key Vault
az keyvault secret list --vault-name taipei-dashboard-kv | grep db-

# Check if secrets are mounted in pod
kubectl exec -it deployment/taipei-dashboard-backend -- env | grep DB_
```

**Test Database Connectivity:**
```bash
# Test from pod
kubectl exec -it deployment/taipei-dashboard-backend -- /bin/sh
# Inside pod: try to connect to database using environment variables
```

**Check Network Connectivity:**
```bash
# Check if database endpoint is reachable
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup your-database-host
```

### 5. Ingress Issues

#### Problem: Cannot access application through ingress
```
Error: 502 Bad Gateway or 404 Not Found
```

#### Solutions:

**Check Ingress Controller:**
```bash
# Verify nginx-ingress is running
kubectl get pods -n ingress-nginx

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

**Check Ingress Configuration:**
```bash
# Verify ingress resource
kubectl describe ingress taipei-dashboard

# Check backend services
kubectl get svc
kubectl get endpoints
```

**Check Service Connectivity:**
```bash
# Test service connectivity
kubectl port-forward svc/taipei-dashboard-frontend 8080:80
kubectl port-forward svc/taipei-dashboard-backend 8081:8080
```

### 6. SSL/TLS Certificate Issues

#### Problem: HTTPS not working or certificate errors

#### Solutions:

**Check cert-manager:**
```bash
# Verify cert-manager is running
kubectl get pods -n cert-manager

# Check certificate status
kubectl get certificate
kubectl describe certificate taipei-dashboard-tls
```

**Check Certificate Issuer:**
```bash
# Verify cluster issuer
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-prod
```

### 7. Performance Issues

#### Problem: Application is slow or unresponsive

#### Solutions:

**Check Resource Usage:**
```bash
# Monitor resource usage
kubectl top pods
kubectl top nodes

# Check HPA status
kubectl get hpa
kubectl describe hpa taipei-dashboard-frontend
```

**Check Application Metrics:**
```bash
# If monitoring is enabled
kubectl port-forward svc/prometheus-server 9090:80
# Access Prometheus at http://localhost:9090
```

## Debugging Commands

### Essential kubectl Commands
```bash
# Get all resources
kubectl get all -l app.kubernetes.io/name=taipei-city-dashboard

# Check pod status and restarts
kubectl get pods -o wide

# Get detailed pod information
kubectl describe pod <pod-name>

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/sh

# Port forward for testing
kubectl port-forward pod/<pod-name> 8080:8080

# Check resource usage
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory
```

### Helm Debugging
```bash
# Check release status
helm status taipei-dashboard

# Get release history
helm history taipei-dashboard

# Debug template rendering
helm template taipei-dashboard ./helm-chart --debug

# Dry run upgrade
helm upgrade taipei-dashboard ./helm-chart --dry-run --debug
```

### Azure CLI Debugging
```bash
# Check AKS cluster status
az aks show --name taipei-dashboard-aks --resource-group taipei-dashboard-rg

# Check node status
az aks nodepool list --cluster-name taipei-dashboard-aks --resource-group taipei-dashboard-rg

# Check Key Vault access
az keyvault secret list --vault-name taipei-dashboard-kv
```

## Log Collection

### Collect All Logs
```bash
#!/bin/bash
# Collect logs for troubleshooting

mkdir -p debug-logs
cd debug-logs

# Collect pod logs
kubectl get pods -l app.kubernetes.io/name=taipei-city-dashboard -o name | while read pod; do
    kubectl logs $pod > "${pod//\//-}.log"
    kubectl logs $pod --previous > "${pod//\//-}-previous.log" 2>/dev/null || true
done

# Collect pod descriptions
kubectl get pods -l app.kubernetes.io/name=taipei-city-dashboard -o name | while read pod; do
    kubectl describe $pod > "${pod//\//-}-describe.txt"
done

# Collect events
kubectl get events --sort-by=.metadata.creationTimestamp > events.txt

# Collect ingress info
kubectl describe ingress taipei-dashboard > ingress-describe.txt

# Collect service info
kubectl get svc -l app.kubernetes.io/name=taipei-city-dashboard -o yaml > services.yaml

echo "Debug information collected in debug-logs directory"
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** using the commands above
2. **Review the configuration** in your values files
3. **Verify Azure resources** are properly configured
4. **Test individual components** (database, Redis, Key Vault access)
5. **Check Azure status** for any service outages
6. **Consult the documentation** in the README.md file

For specific errors, search for the exact error message in:
- Kubernetes documentation
- Azure AKS documentation
- Helm documentation
- Application-specific logs and error messages
