# Backend Dockerfile for production
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install git and ca-certificates
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage
FROM alpine:latest

# Install ca-certificates for SSL/TLS
RUN apk --no-cache add ca-certificates && \
    mkdir -p /etc/ssl/certs

# Add certificate from build argument
ARG G1G2_CERT
ARG IDNO_SALT
ARG ISSO_CLIENT_ID
ARG ISSO_CLIENT_SECRET
ARG JWT_SECRET

ENV ISSO_CLIENT_ID=$ISSO_CLIENT_ID \
    IDNO_SALT=$IDNO_SALT \
    ISSO_CLIENT_SECRET=$ISSO_CLIENT_SECRET \
    JWT_SECRET=$JWT_SECRET \
	G1G2_CERT=$G1G2_CERT

WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/main .

# Create non-root user
RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE 8080

CMD ["./main"]
