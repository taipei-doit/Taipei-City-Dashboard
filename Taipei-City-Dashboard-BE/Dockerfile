# ====== Builder ======
FROM golang:1.24-bookworm AS builder
WORKDIR /go/src/app

COPY go.mod go.sum ./
RUN go mod download

# 複製程式碼並建置 (CGO_ENABLED=0 純靜態編譯)
COPY . .
RUN CGO_ENABLED=0 go build -o TaipeiCityDashboardBE .

# ====== Runtime (Prod) ======
FROM debian:bookworm-slim AS prod

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

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/

EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001

CMD ["/app/TaipeiCityDashboardBE"]

# ====== Dev Target ======
# 本地開發用：docker build --target dev
FROM golang:1.24-bookworm AS dev

ENV GOCACHE=/tmp/go-build-cache

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001
CMD ["go", "run", "main.go"]