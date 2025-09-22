FROM golang:1.21.3-alpine3.18 as builder
WORKDIR /go/src/app
COPY . .
RUN go build 

FROM alpine:3.18
# Install ca-certificates for SSL support
RUN apk --no-cache add ca-certificates && \
    mkdir -p /etc/ssl/certs

# Add certificate from build argument
ARG G1G2_CERT
RUN if [ -n "$G1G2_CERT" ]; then \
        echo "$G1G2_CERT" > /etc/ssl/certs/g1g2.crt && \
        update-ca-certificates; \
    fi

COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/
WORKDIR /app
EXPOSE 8080
CMD ["./TaipeiCityDashboardBE"]