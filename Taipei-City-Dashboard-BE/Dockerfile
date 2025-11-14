# ====== Builder ======
FROM golang:1.25.4-bookworm AS builder
WORKDIR /go/src/app

# 先把 go mod 拉好（可加快快取）
COPY go.mod go.sum ./
RUN go mod download

# 複製程式碼並建置
COPY . .
# 若你的程式用到 cgo，確保開啟（onnxruntime_go 會動態載入 so，這裡可保持 CGO_ENABLED=1 或 0 均可）
# ENV CGO_ENABLED=1
RUN go build -o TaipeiCityDashboardBE .

# ====== Runtime ======
FROM debian:bookworm-slim 

ARG TARGETARCH
# 安裝必要相依
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates wget libgomp1 && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 依照架構下載正確的 ONNX Runtime
RUN set -eux; \
    if [ "$TARGETARCH" = "amd64" ]; then \
        URL="https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-x64-1.23.2.tgz"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        URL="https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-aarch64-1.23.2.tgz"; \
    else \
        echo "Unsupported arch: $TARGETARCH" && exit 1; \
    fi; \
    wget -O /tmp/ort.tgz "$URL" && \
    tar -xzf /tmp/ort.tgz -C /tmp && \
    ORTDIR=$(find /tmp -maxdepth 1 -type d -name "onnxruntime-linux-*") && \
    cp "$ORTDIR/lib/libonnxruntime.so" /usr/lib/ && \
    rm -rf /tmp/ort.tgz "$ORTDIR"

# 讓動態連結器找得到 .so
ENV LD_LIBRARY_PATH=/usr/lib

# 你的機密設定
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

WORKDIR /app
COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/
COPY lm_model /opt/lm_model
EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001

CMD ["./TaipeiCityDashboardBE"]