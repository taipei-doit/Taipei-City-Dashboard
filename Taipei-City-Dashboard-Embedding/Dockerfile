# ====== Model Exporter ======
# 跑在 build 機原生架構即可（產出只是模型檔，與 target arch 無關），避免 QEMU 模擬拖慢
FROM --platform=$BUILDPLATFORM python:3.12-slim AS model_export
ENV HF_HOME=/root/.cache/huggingface
WORKDIR /w

RUN pip install --no-cache-dir \
      "transformers>=4.44" \
      "optimum[onnxruntime]>=1.20.0" \
      onnxruntime

# 產出 /out/onnx-e5（model.onnx + tokenizer.json）
COPY export_model_docker.py /w/export_model_docker.py
RUN python /w/export_model_docker.py

# ====== Runtime ======
FROM python:3.12-slim AS prod

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/
COPY --from=model_export /out/onnx-e5 /opt/lm_model/onnx-e5

ENV LM_MODEL_PATH=/opt/lm_model/onnx-e5 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

RUN useradd -r -u 10001 appuser
USER 10001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
