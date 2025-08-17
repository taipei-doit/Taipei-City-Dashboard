# Start with a base image
FROM node:21-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies (reproducible)
RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the application with different modes based on environment variable
# Use CI-specific scripts that don't fail the build on ESLint warnings/errors
ARG NODE_ENV=production
RUN if [ "$NODE_ENV" = "test" ]; then npm run build:test:ci; else npm run build:ci; fi


# Use a lightweight node image
FROM nginx:alpine

# Copy the built files from the builder stage to the nginx server
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Command to run nginx
CMD ["nginx", "-g", "daemon off;"]

