from pathlib import Path
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction

MODEL_ID = "intfloat/multilingual-e5-base"
OUT_DIR  = Path("/out/onnx-e5")
OUT_DIR.mkdir(parents=True, exist_ok=True)

model = ORTModelForFeatureExtraction.from_pretrained(
    MODEL_ID,
    export=True,
    provider="CPUExecutionProvider"
)
tok = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

model.save_pretrained(OUT_DIR)
tok.save_pretrained(OUT_DIR)
print("Exported to:", OUT_DIR)
