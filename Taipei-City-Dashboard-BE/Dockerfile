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
ARG IDNO_SALT
ARG ISSO_CLIENT_ID
ARG ISSO_CLIENT_SECRET
ARG JWT_SECRET

ENV ISSO_CLIENT_ID=$ISSO_CLIENT_ID \
    IDNO_SALT=$IDNO_SALT \
    ISSO_CLIENT_SECRET=$ISSO_CLIENT_SECRET \
    JWT_SECRET=$JWT_SECRET \
	G1G2_CERT=$G1G2_CERT

COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/
WORKDIR /app
EXPOSE 8080
CMD ["./TaipeiCityDashboardBE"]