#!/bin/sh
set -e

# Set default backend URL if not provided
if [ -z "$BACKEND_URL" ]; then
    echo "Warning: BACKEND_URL not set, using default"
    export BACKEND_URL="http://taipei-city-dashboard-backend.dashboard.svc.cluster.local:8080"
fi

# Generate nginx config from template
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Remove template file
rm -f /etc/nginx/conf.d/nginx.conf.template

# Start nginx
exec nginx -g 'daemon off;'