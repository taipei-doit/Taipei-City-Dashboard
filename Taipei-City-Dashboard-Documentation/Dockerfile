FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# We don't need to copy the project files as we'll use a volume mount
# COPY . .

# Expose port 8082
EXPOSE 8082

# Default command (can be overridden by docker-compose)
CMD ["npm", "run", "dev", "--", "--port", "8082", "--host", "0.0.0.0"]