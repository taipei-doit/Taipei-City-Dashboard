# Start with a base image
FROM node:21-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Install dependencies using npm ci for consistency
COPY package*.json ./
RUN npm ci

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

# 可選：匯入為環境變數（Vite 只會替換以 VITE_ 開頭的變數；其它例如 BACKEND_URL 要看你的程式碼怎麼取）
ENV NODE_ENV=$NODE_ENV \
    VITE_APP_TITLE=$VITE_APP_TITLE \
    VITE_API_URL=$VITE_API_URL \
    VITE_MAPBOXTOKEN=$VITE_MAPBOXTOKEN \
    VITE_MAPBOXTILE=$VITE_MAPBOXTILE \
    VITE_TAIPEIPASS_URL=$VITE_TAIPEIPASS_URL \
    VITE_TAIPEIPASS_CLIENT_ID=$VITE_TAIPEIPASS_CLIENT_ID \
    VITE_TAIPEIPASS_SCOPE=$VITE_TAIPEIPASS_SCOPE

# Build the application
RUN npm run build

# Use a lightweight node image
FROM nginx:alpine

# Copy the built files from the builder stage to the nginx server
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 8081

# Command to run nginx
CMD ["nginx", "-g", "daemon off;"]

