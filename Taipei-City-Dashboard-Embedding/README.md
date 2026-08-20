# Taipei City Dashboard — Embedding Service

把原本綁在後端 image 裡的 `intfloat/multilingual-e5-base` 推論拆成獨立的 k8s Pod，
後端改用 HTTP 呼叫，不再自己載 ONNX Runtime 與 1.1GB 模型。

推論數學與後端原本的 `app/models/qdrant.go` `GenVector()` **逐步對齊**：

```
"query: " + text  →  tokenize  →  mean pooling (依 attention_mask)  →  L2 normalize  →  768 維
```

模型檔由同一支 `export_model_docker.py`（與後端 Dockerfile 內那支相同）匯出，
tokenizer 也是同一份 `tokenizer.json`，所以產出的向量與現行後端一致，
Qdrant 既有的 collection **不需要重建**。

### 已驗證的相容性（SIT）

| 檢查 | 結果 |
| --- | --- |
| `model.onnx` / `tokenizer.json` sha256 vs 後端 pod | 完全相同 |
| `cos(Qdrant 既有向量 #174, 新服務重算)` | `1.00000002` |
| 三組查詢的 top-5 分數與排序 vs 線上後端 `POST /api/v1/vector/component` | 小數第 4 位逐位相同 |
| 單筆 vs 批次同一段文字 | `max abs diff = 0.0` |

### ⚠️ `ADD_SPECIAL_TOKENS` 為什麼預設 `false`

後端 Go 版用的 `github.com/sugarme/tokenizer` 的 `EncodeSingle()`
**實際上不會加 `<s>` / `</s>`**（與程式裡「預設 addSpecialTokens = true」的註解相反）。
用同一份 `tokenizer.json` 逐一比對 token ids 已確認：

```
sugarme EncodeSingle(text).GetIds()  ==  HF tokenizers encode(text, add_special_tokens=False).ids
```

Qdrant 現有的 collection 是照這個行為建出來的，所以本服務預設跟著關掉，才能維持 drop-in。

**天花板**：這偏離 e5 訓練時的輸入格式，檢索品質略差 —
同一段文字用兩種算法出來的向量 cos ≈ 0.987，實測會讓 top-5 的第 4、5 名換人。

**升級路徑**：設 `ADD_SPECIAL_TOKENS=true`，並用**同一支服務**重建 Qdrant collection。
兩邊必須一起換，只換單邊會讓 query 與 passage 落在不同空間、分數系統性偏移。

---

## API

Base URL（叢集內）：`http://taipei-city-dashboard-embedding.dashboard.svc.cluster.local:8080`
同 namespace 可直接用 `http://taipei-city-dashboard-embedding:8080`

服務只開 ClusterIP，不對外暴露。

### `POST /v1/embeddings`

OpenAI embeddings API 相容格式，方便日後換成 TEI / vLLM 等現成服務而不用改後端。

Request：

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| `input` | `string` 或 `string[]` | ✅ | 要轉向量的文字。給陣列即為批次，一次最多 `MAX_BATCH`（預設 512）筆 |
| `model` | `string` | ❌ | 相容欄位，服務只載一個模型，傳什麼都會忽略 |
| `prefix` | `string` | ❌ | 覆蓋 e5 prefix。**不傳就是 `"query: "`，與後端現行行為相同**；建索引想用 `"passage: "` 才需要傳 |

Response（`embedding` 已做 L2 normalize，長度 768）：

```json
{
  "object": "list",
  "data": [
    { "object": "embedding", "index": 0, "embedding": [0.0123, -0.0456, ...] }
  ],
  "model": "intfloat/multilingual-e5-base",
  "usage": { "prompt_tokens": 12, "total_tokens": 12 }
}
```

錯誤回應為 `{"detail": "..."}`，狀態碼 `400`（輸入不合法）／`422`（欄位型別錯誤）。

範例：

```bash
# 單筆
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": "台北市的空氣品質"}'

# 批次
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": ["台北市的空氣品質", "youbike 站點"]}'
```

### `GET /healthz`

```json
{ "status": "ok", "model": "intfloat/multilingual-e5-base", "dim": 768 }
```

k8s 的 startup / liveness / readiness probe 都打這支。

---

## 後端接法

後端只要把 `GenVector()` 換成一次 HTTP 呼叫即可，回傳型別 `[]float32` 不變：

```go
func GenVector(inputText string) ([]float32, error) {
	body, _ := json.Marshal(map[string]any{"input": inputText})

	resp, err := http.Post(global.Embedding.Url+"/v1/embeddings",
		"application/json", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("embedding request error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("embedding returned %s: %s", resp.Status, b)
	}

	var out struct {
		Data []struct {
			Embedding []float32 `json:"embedding"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode embedding response: %w", err)
	}
	if len(out.Data) == 0 {
		return nil, fmt.Errorf("embedding returned no data")
	}
	return out.Data[0].Embedding, nil
}
```

`app/services/qdrant.go` 的重建索引流程（`SyncQdrant`）本來是一筆一筆呼叫 `GenVector`，
可以改成一次送整批 `input` 陣列。SIT 實測（1 replica、CPU limit 2000m、`ORT_INTRA_THREADS=2`）：

| batch | 每次請求 | 吞吐量 |
| --- | --- | --- |
| 1 | 25 ms | 39 texts/s |
| 8 | 107 ms | 75 texts/s |
| 32 | 292 ms | 110 texts/s |
| 300（長短混雜） | 8.7 s | 35 texts/s |

單筆查詢維持 25ms 等級；重建索引改用批次快 2.8 倍。

### 批次是怎麼處理的

一次可以送到 `MAX_BATCH`（512）筆。服務內部會：

1. 先全部 tokenize，**依 token 數排序**
2. 每 `MICRO_BATCH`（32）筆切一塊送進 ONNX，各塊只 pad 到該塊最長的長度
3. 寫回**原始輸入順序**，`data[i].index` 一定對得上第 i 筆輸入

排序分塊是為了避免長短混批時，短文字被 pad 到最長那筆的長度而白燒算力。
實測 32 短 + 32 長混在一起：3001 ms → 1644 ms（**省 45%**）。

切塊也讓記憶體用量與請求大小脫鉤 —— 送 512 筆和送 32 筆的峰值記憶體一樣。

批次與單筆的向量是逐位相同的（實測 50 筆混合長度 `max abs diff = 0.0`），
所以要不要打包純粹看呼叫端方便。

後端拔掉推論後可以一起清掉：

- `Dockerfile` 的 `model_export` stage、ONNX Runtime 下載、`COPY --from=model_export`
- `export_model.py`、`export_model_docker.py`、`lm_model/`、`onnxruntime/`
- `go.mod` 的 `github.com/yalue/onnxruntime_go`、`github.com/sugarme/tokenizer`
- `global.LMSession`、`global.LMTokenizer`、`InitLmSession()`、`InitTokenizer()`
- `LM_MODEL_PATH` 環境變數（改成 embedding service 的 URL）

---

## 環境變數

| 變數 | 預設 | 說明 |
| --- | --- | --- |
| `LM_MODEL_PATH` | `/opt/lm_model/onnx-e5` | 模型目錄（image 內已備好，通常不用改） |
| `E5_PREFIX` | `query: ` | 預設 e5 prefix，與後端現行行為對齊 |
| `MAX_BATCH` | `512` | 單次請求最多幾筆，超過回 400 |
| `MICRO_BATCH` | `32` | 內部一次送進 ONNX 的筆數，記憶體用量由此決定，與請求大小無關 |
| `MAX_SEQ_LEN` | `512` | 超過就截斷（模型上限） |
| `MAX_CHARS` | `8192` | 單筆字數上限，超過回 400 |
| `ADD_SPECIAL_TOKENS` | `false` | 是否加 `<s>` / `</s>`。**改動前務必先看上面那段** |
| `ORT_INTRA_THREADS` | `2` | ONNX Runtime 執行緒數，配合容器 CPU limit 設定 |

`ORT_INTRA_THREADS` 要跟 helm 的 `embedding.resources.limits.cpu` 一起調：
設太高會被 cgroup throttle 反而更慢。目前 limit 2000m 配 2 執行緒。

---

## 本機開發

```bash
docker build --target prod -t emb:dev .
docker run --rm -p 8080:8080 emb:dev
curl -s localhost:8080/healthz
```

## 部署

Helm chart 在 `helm-chart/`，由 `.github/workflows/build-and-push.yml` 自動 build + deploy：

- SIT：`helm-chart/values-sit.yaml`，`embedding.enabled: true`
- PROD：`helm-chart/values-prod.yaml`，目前 `embedding.enabled: false`，
  待 SIT 驗證且後端改完再開
