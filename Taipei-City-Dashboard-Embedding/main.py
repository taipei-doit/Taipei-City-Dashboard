"""multilingual-e5-base embedding service.

從後端 image 拉出來的獨立推論服務，數學與原本 Go 版 (app/models/qdrant.go GenVector)
逐步對齊：加 e5 prefix -> tokenize -> mean pooling (依 attention_mask) -> L2 normalize。
"""

import os

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tokenizers import Tokenizer

MODEL_DIR = os.getenv("LM_MODEL_PATH", "/opt/lm_model/onnx-e5")
MODEL_NAME = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-base")
# e5 要求輸入帶 prefix；後端原本寫死 "query: "，維持一致
DEFAULT_PREFIX = os.getenv("E5_PREFIX", "query: ")
MAX_BATCH = int(os.getenv("MAX_BATCH", "512"))
# 一次真正送進 ONNX 的筆數。請求再大也會切成這個大小，讓記憶體用量與請求大小脫鉤
MICRO_BATCH = int(os.getenv("MICRO_BATCH", "32"))
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", "512"))
MAX_CHARS = int(os.getenv("MAX_CHARS", "8192"))
# 容器有 CPU limit，讓 ORT 照著開執行緒，避免被 cgroup throttle
INTRA_THREADS = int(os.getenv("ORT_INTRA_THREADS", "2"))

# ponytail: 預設 false 是為了與後端現行 Go 版逐位相容。
# 後端用的 sugarme/tokenizer EncodeSingle 實際上不會加 <s> / </s>（與其註解相反），
# 已用相同 tokenizer.json 比對確認：sugarme 的 ids == HF add_special_tokens=False。
# Qdrant 現有 collection 是照這個行為建的，所以這裡跟著關掉才不會讓搜尋結果偏移。
# 天花板：這偏離 e5 訓練時的輸入格式，檢索品質略差（同一段文字兩種算法 cos ≈ 0.987）。
# 升級路徑：設 ADD_SPECIAL_TOKENS=true 並用同一支服務重建 Qdrant collection，兩邊要一起換。
ADD_SPECIAL_TOKENS = os.getenv("ADD_SPECIAL_TOKENS", "false").lower() == "true"

tokenizer = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
tokenizer.enable_truncation(max_length=MAX_SEQ_LEN)
# 不開全域 padding：改成分塊後各自 pad 到該塊最長，避免整批被最長的那筆拖著跑
tokenizer.no_padding()
PAD_ID = tokenizer.token_to_id("<pad>") or 1

_opts = ort.SessionOptions()
_opts.intra_op_num_threads = INTRA_THREADS
_opts.inter_op_num_threads = 1
session = ort.InferenceSession(
    os.path.join(MODEL_DIR, "model.onnx"),
    _opts,
    providers=["CPUExecutionProvider"],
)
DIM = session.get_outputs()[0].shape[-1]

app = FastAPI(title="Taipei City Dashboard Embedding", version="1.0.0")


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None
    # 非 OpenAI 標準欄位：覆蓋 e5 prefix（例如建索引時用 "passage: "）
    prefix: str | None = None


def _run(encodings) -> np.ndarray:
    """一塊送進 ONNX，pad 到這塊最長的長度。"""
    width = max(len(e.ids) for e in encodings)
    ids = np.full((len(encodings), width), PAD_ID, dtype=np.int64)
    mask = np.zeros((len(encodings), width), dtype=np.int64)
    for r, e in enumerate(encodings):
        n = len(e.ids)
        ids[r, :n] = e.ids
        mask[r, :n] = e.attention_mask

    hidden = session.run(
        ["last_hidden_state"], {"input_ids": ids, "attention_mask": mask}
    )[0]

    # mean pooling：只算 attention_mask=1 的 token
    m = mask[:, :, None].astype(np.float32)
    pooled = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)

    # L2 normalize
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    return pooled / np.clip(norms, 1e-12, None)


def _embed(texts: list[str]) -> tuple[np.ndarray, int]:
    encodings = tokenizer.encode_batch(texts, add_special_tokens=ADD_SPECIAL_TOKENS)

    # 依 token 數排序再切塊，讓每塊內長度相近。長短混在一起時，
    # 短的不會被 pad 到最長那筆的長度，省下大量無效算力。
    order = sorted(range(len(encodings)), key=lambda i: len(encodings[i].ids))

    out = np.empty((len(texts), DIM), dtype=np.float32)
    for s in range(0, len(order), MICRO_BATCH):
        idx = order[s : s + MICRO_BATCH]
        out[idx] = _run([encodings[i] for i in idx])

    # 回傳照原始輸入順序，呼叫端的 index 對得上
    return out, sum(sum(e.attention_mask) for e in encodings)


@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    texts = [req.input] if isinstance(req.input, str) else req.input

    if not texts:
        raise HTTPException(status_code=400, detail="input must not be empty")
    if len(texts) > MAX_BATCH:
        raise HTTPException(
            status_code=400, detail=f"batch size {len(texts)} exceeds MAX_BATCH={MAX_BATCH}"
        )
    for t in texts:
        if not isinstance(t, str):
            raise HTTPException(status_code=400, detail="input must be string or list of strings")
        if len(t) > MAX_CHARS:
            raise HTTPException(
                status_code=400, detail=f"input longer than MAX_CHARS={MAX_CHARS}"
            )

    prefix = DEFAULT_PREFIX if req.prefix is None else req.prefix
    vectors, tokens = _embed([prefix + t for t in texts])

    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vectors)
        ],
        "model": MODEL_NAME,
        "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
    }


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "dim": DIM,
        "add_special_tokens": ADD_SPECIAL_TOKENS,
        "max_batch": MAX_BATCH,
        "micro_batch": MICRO_BATCH,
    }
