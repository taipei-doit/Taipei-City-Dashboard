# Start with a base image
FROM node:21-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Install dependencies using npm ci for consistency
COPY package*.json ./
RUN npm ci
# test
# Copy the rest of the application code
COPY . .

# 宣告所有 build args（要和 workflow build-args 名稱一致）
ARG NODE_ENV
ARG VITE_APP_TITLE
ARG VITE_API_URL
ARG VITE_MAPBOXTOKEN
ARG VITE_MAPBOXTILE
ARG VITE_TAIPEIPASS_URL
ARG VITE_TAIPEIPASS_CLIENT_ID
ARG VITE_TAIPEIPASS_SCOPE

ENV NODE_ENV=$NODE_ENV \
    VITE_APP_TITLE=$VITE_APP_TITLE \
    VITE_API_URL=$VITE_API_URL \
    VITE_MAPBOXTOKEN=$VITE_MAPBOXTOKEN \
    VITE_MAPBOXTILE=$VITE_MAPBOXTILE \
    VITE_TAIPEIPASS_URL=$VITE_TAIPEIPASS_URL \
    VITE_TAIPEIPASS_CLIENT_ID=$VITE_TAIPEIPASS_CLIENT_ID \
    VITE_TAIPEIPASS_SCOPE=$VITE_TAIPEIPASS_SCOPE

RUN if [ "$NODE_ENV" = "test" ]; then npm run build:test; else npm run build; fi

# Use a lightweight node image
FROM nginx:alpine

# Copy the built files from the builder stage to the nginx server
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8081

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

