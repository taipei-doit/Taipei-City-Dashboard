# ====== Model Exporter ======
FROM python:3.12-slim AS model_export
ARG HF_TOKEN   # 若你有 Hugging Face 私有模型或想提高速率，可傳 token（可留空）
ENV HF_HOME=/root/.cache/huggingface
WORKDIR /w

# 安裝匯出所需套件
RUN pip install --no-cache-dir \
      "transformers>=4.44" \
      "optimum[onnxruntime]>=1.20.0" \
      onnxruntime

# 匯出：feature-extraction
# 產出到 /out/onnx-e5
COPY export_model_docker.py /w/export_model_docker.py
RUN python /w/export_model_docker.py

# ====== Builder ======
FROM golang:1.25.4-bookworm AS builder
WORKDIR /go/src/app

COPY go.mod go.sum ./
RUN go mod download

# 複製程式碼並建置
COPY . .
RUN go build -o TaipeiCityDashboardBE .

# ====== Runtime ======
# Prod
FROM debian:bookworm-slim AS prod
# Dev
# FROM golang:1.25.4-bookworm  

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

ARG G1G2_CERT
ARG IDNO_SALT
ARG ISSO_CLIENT_ID
ARG ISSO_CLIENT_SECRET
ARG JWT_SECRET

ENV ISSO_CLIENT_ID=$ISSO_CLIENT_ID \
    IDNO_SALT=$IDNO_SALT \
    ISSO_CLIENT_SECRET=$ISSO_CLIENT_SECRET \
    JWT_SECRET=$JWT_SECRET \
    G1G2_CERT=$G1G2_CERT \
	GOCACHE=/tmp/go-build-cache

WORKDIR /app
COPY --from=builder /go/src/app/TaipeiCityDashboardBE /app/
COPY --from=model_export /out/onnx-e5 /opt/lm_model/onnx-e5
# COPY lm_model /opt/lm_model

EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001

CMD ["/app/TaipeiCityDashboardBE"]

# ====== Dev Target ======
# 本地開發用：docker build --target dev
# 搭配 volume mount + go run，不需要編譯
FROM golang:1.25.4-bookworm AS dev

ARG TARGETARCH
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates wget libgomp1 && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

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

ENV LD_LIBRARY_PATH=/usr/lib
ENV GOCACHE=/tmp/go-build-cache

COPY --from=model_export /out/onnx-e5 /opt/lm_model/onnx-e5

WORKDIR /app
EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001
CMD ["go", "run", "main.go"]