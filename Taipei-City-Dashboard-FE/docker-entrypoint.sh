#!/bin/sh
set -e

# Set default backend URL if not provided
if [ -z "$BACKEND_URL" ]; then
    echo "Warning: BACKEND_URL not set, using default"
    export BACKEND_URL="http://taipei-city-dashboard-backend.dashboard.svc.cluster.local:8080"
fi

# Create writable directory
mkdir -p /tmp/nginx

# Generate nginx config from template to writable location
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /tmp/nginx/default.conf

# Create main nginx config file
cat > /tmp/nginx.conf << 'NGINXCONF'
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    sendfile on;
    keepalive_timeout 65;
    
    include /tmp/nginx/*.conf;
}
NGINXCONF

# Start nginx with custom config
exec nginx -c /tmp/nginx.conf -g 'daemon off;'