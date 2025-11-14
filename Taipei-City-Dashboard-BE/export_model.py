from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction

from pathlib import Path
Path("./lm_model").mkdir(parents=True, exist_ok=True)

MODEL_ID = "intfloat/multilingual-e5-base"
OUT_DIR  = "./lm_model/onnx-e51"   # 匯出資料夾

# 1) 匯出成 ONNX（FeatureExtraction 會輸出 last_hidden_state）
model = ORTModelForFeatureExtraction.from_pretrained(
    MODEL_ID,
    # export=True,                     # 叫它幫你匯出 ONNX
    provider="CPUExecutionProvider"  # 先用 CPU 版，之後也能換 GPU Provider
)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

# 2) 保存模型與 tokenizer
model.save_pretrained(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)

print("Exported to:", OUT_DIR)