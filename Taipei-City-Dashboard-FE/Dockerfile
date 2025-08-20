# Start with a base image
FROM node:21-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application with different modes based on environment variable
ARG NODE_ENV=production
RUN if [ "$NODE_ENV" = "test" ]; then npm run build:test; else npm run build; fi

# Use a lightweight node image
FROM nginx:alpine

# Copy the built files from the builder stage to the nginx server
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx template and entrypoint script
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8081

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

