# Taipei City Dashboard - Health Check Endpoints

This document describes the health check endpoints that should be implemented in the application for proper Kubernetes health monitoring.

## Backend Health Checks

The backend application should implement the following endpoints:

### 1. Liveness Probe Endpoint
- **URL**: `GET /health`
- **Purpose**: Indicates if the application is running
- **Expected Response**: HTTP 200 with basic status

Example implementation (Go):
```go
func healthHandler(c *gin.Context) {
    c.JSON(200, gin.H{
        "status": "ok",
        "timestamp": time.Now().Unix(),
    })
}
```

### 2. Readiness Probe Endpoint
- **URL**: `GET /ready`
- **Purpose**: Indicates if the application is ready to serve traffic
- **Expected Response**: HTTP 200 when ready, HTTP 503 when not ready
- **Should Check**: Database connectivity, Redis connectivity, essential services

Example implementation (Go):
```go
func readinessHandler(c *gin.Context) {
    // Check database connection
    if err := db.Ping(); err != nil {
        c.JSON(503, gin.H{"status": "not ready", "reason": "database unavailable"})
        return
    }
    
    // Check Redis connection
    if err := redisClient.Ping().Err(); err != nil {
        c.JSON(503, gin.H{"status": "not ready", "reason": "redis unavailable"})
        return
    }
    
    c.JSON(200, gin.H{
        "status": "ready",
        "timestamp": time.Now().Unix(),
    })
}
```

### 3. Startup Probe Endpoint (Optional)
- **URL**: `GET /startup`
- **Purpose**: Indicates if the application has finished starting up
- **Expected Response**: HTTP 200 when startup is complete

## Frontend Health Checks

For the frontend (nginx), the default health check on root path `/` should be sufficient.

If needed, you can create a simple health check endpoint:

### Custom Health Check
- **URL**: `GET /health`
- **Implementation**: Simple static file or nginx location block

Example nginx configuration:
```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

## Kubernetes Configuration

The health checks are already configured in the Helm chart:

### Backend Deployment
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health  # Should be /ready when implemented
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Frontend Deployment
```yaml
livenessProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Implementation Steps

1. **Backend**: Add health check routes to your Gin router
2. **Frontend**: Ensure nginx serves the root path correctly
3. **Update Helm Chart**: Modify probe paths if implementing separate endpoints
4. **Test**: Verify health checks work before deployment

## Testing Health Checks

Test the endpoints locally:

```bash
# Test backend health
curl http://localhost:8080/health

# Test backend readiness
curl http://localhost:8080/ready

# Test frontend health
curl http://localhost:80/health
```

In Kubernetes, you can check probe status:

```bash
# Check pod status and events
kubectl describe pod <pod-name>

# Check probe failures
kubectl get events --field-selector involvedObject.name=<pod-name>
```
