# Embedding Service API

給後端串接用的規格書。服務把 `intfloat/multilingual-e5-base` 的推論從後端 image 拆出來獨立跑，
後端改用 HTTP 呼叫即可，**產出的向量與現行 `GenVector()` 逐位相同，Qdrant 既有 collection 不用重建**。

- 環境：SIT 已上線並驗證通過
- Base URL（叢集內）：`http://taipei-city-dashboard-embedding:8080`
- FQDN：`http://taipei-city-dashboard-embedding.dashboard.svc.cluster.local:8080`
- Service type：`ClusterIP`，只給叢集內部呼叫，不對外暴露，**無需認證**

---

## ⚠️ 串接前必讀：不要自己加 `query: `

後端現在的 `app/models/qdrant.go:155` 有這行：

```go
text := "query: " + inputText
```

**這個 prefix 已經由服務端負責了**，改用 API 時請把這行拿掉，直接傳原始文字。

沒拿掉會變成 `"query: query: 原始文字"`。實測這樣產出的向量與正確版本
`cos = 0.9939` —— 不會報錯、看起來也很像，但足以讓檢索排序跑掉，很難查。

如果真的需要自己控制 prefix，用 request 的 `prefix` 欄位覆蓋：

- `"prefix": ""` → 完全不加 prefix
- `"prefix": "passage: "` → 建索引用的 passage prefix

實測 `{"input": "query: 空氣品質", "prefix": ""}` 與 `{"input": "空氣品質"}`
產出的向量 `max abs diff = 0.0`，行為完全可預測。

---

## `POST /v1/embeddings`

OpenAI embeddings API 相容格式。

### Request

`Content-Type: application/json`

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| `input` | `string` \| `string[]` | ✅ | 要轉向量的文字。給陣列即為批次，一次最多 **512** 筆 |
| `model` | `string` | ❌ | 相容欄位，服務只載一個模型，傳什麼都會忽略 |
| `prefix` | `string` | ❌ | 覆蓋 e5 prefix。**不傳＝`"query: "`，與後端現行行為相同**。傳空字串 `""` 代表不加任何 prefix |

限制：

| 項目 | 值 | 超過的行為 |
| --- | --- | --- |
| 單次請求筆數 | 512 | 回 `400` |
| 單筆字元數 | 8192 | 回 `400` |
| 單筆 token 數 | 512 | **靜默截斷**（模型上限，不會報錯） |

截斷是靜默的：實測丟 6300 字進去回 `200`，`usage.prompt_tokens` 就是 `512`。
要偵測有沒有被截，看 `usage.prompt_tokens == 512` 即可。
（後端現行的 Go 版沒有截斷保護，超長輸入反而會出問題，這裡是修好的。）

### Response `200`

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [3.5371242120163515e-05, 0.035948336124420166, -0.014690718613564968]
    }
  ],
  "model": "intfloat/multilingual-e5-base",
  "usage": { "prompt_tokens": 8, "total_tokens": 8 }
}
```

- `embedding`：`float32` 陣列，長度 **768**，**已做 L2 normalize**（可直接丟進 Qdrant，不用再正規化）
- `data[i].index == i`，**保證對應 `input[i]` 的順序**
- `usage.prompt_tokens`：實際 token 數（不含 padding）

### 錯誤

| 情境 | HTTP | `detail` |
| --- | --- | --- |
| `input` 是空陣列 | `400` | `input must not be empty` |
| 超過 512 筆 | `400` | `batch size 513 exceeds MAX_BATCH=512` |
| 單筆超過 8192 字 | `400` | `input longer than MAX_CHARS=8192` |
| `input` 型別錯誤（數字、陣列元素非字串） | `422` | pydantic 驗證陣列，`type=string_type` |
| 缺 `input` 欄位 | `422` | pydantic 驗證陣列，`type=missing` |

`400` 的 body 是 `{"detail": "訊息字串"}`；
`422` 的 body 是 `{"detail": [ {...pydantic 錯誤物件...} ]}`，**`detail` 是陣列不是字串**，解析時要注意。

### 範例

```bash
# 單筆
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": "台北市的空氣品質"}'

# 批次
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": ["台北市的空氣品質", "youbike 站點"]}'

# 建索引時想用 passage prefix
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": ["長描述文字"], "prefix": "passage: "}'
```

---

## `GET /healthz`

```json
{
  "status": "ok",
  "model": "intfloat/multilingual-e5-base",
  "dim": 768,
  "add_special_tokens": false,
  "max_batch": 512,
  "micro_batch": 32
}
```

k8s 的 startup / liveness / readiness probe 都打這支。後端不需要主動呼叫。

---

## 效能與 timeout 設定

SIT 實測（1 replica、CPU limit 2000m、`ORT_INTRA_THREADS=2`）：

| 情境 | 耗時 | 吞吐 |
| --- | --- | --- |
| 單筆查詢 | 25 ms | 39 texts/s |
| 32 筆（短文字） | 292 ms | 110 texts/s |
| 32 筆（長描述） | 1520 ms | 21 texts/s |
| 300 筆（長短混雜） | 10.0 s | 30 texts/s |

**建議的 HTTP client timeout**：

- 使用者查詢路徑（單筆）：**3 秒**足夠，25ms 是常態
- 重建索引路徑（批次）：抓 **60 秒**，300 筆約 10 秒，留餘裕給冷啟動

Pod 冷啟動要載入 1.1GB ONNX 模型，約 20–30 秒。k8s 的 `startupProbe` 會擋住流量直到 ready，
但滾動更新期間仍建議加一次重試。

### 批次是怎麼處理的

服務內部會：

1. 先全部 tokenize，**依 token 數排序**
2. 每 32 筆切一塊送進 ONNX，各塊只 pad 到該塊最長的長度
3. 寫回**原始輸入順序**

排序分塊是為了避免長短混批時短文字被 pad 到最長那筆的長度而白燒算力
（實測 32 短 + 32 長：3001 ms → 1644 ms）。
切塊也讓峰值記憶體與請求大小脫鉤，送 512 筆和送 32 筆一樣。

**批次與單筆的向量逐位相同**（實測 50 筆混合長度 `max abs diff = 0.0`），
要不要打包純粹看呼叫端方便。

---

## 後端改法

### 1. 設定

新增一個環境變數指向服務，並移除 `LM_MODEL_PATH`：

```go
// global/global.go
type EmbeddingConfig struct {
	Url string
}

Embedding = EmbeddingConfig{
	Url: getEnv("EMBEDDING_URL", "http://taipei-city-dashboard-embedding:8080"),
}
```

helm 那邊我已經把服務佈上去了，`EMBEDDING_URL` 要加進
`helm-chart/values-*.yaml` 的 `backend.env`（或 secret，看你們習慣）。

### 2. `GenVector()` 換成 HTTP 呼叫

回傳型別 `[]float32` 不變，兩個呼叫端（`componentConfig.go:263`、`services/qdrant.go:115`）都不用改：

```go
var embeddingClient = &http.Client{Timeout: 60 * time.Second}

func genVectors(texts []string) ([][]float32, error) {
	body, err := json.Marshal(map[string]any{"input": texts})
	if err != nil {
		return nil, fmt.Errorf("marshal embedding request: %w", err)
	}

	resp, err := embeddingClient.Post(
		global.Embedding.Url+"/v1/embeddings",
		"application/json",
		bytes.NewReader(body),
	)
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
			Index     int       `json:"index"`
			Embedding []float32 `json:"embedding"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode embedding response: %w", err)
	}
	if len(out.Data) != len(texts) {
		return nil, fmt.Errorf("embedding returned %d vectors, want %d", len(out.Data), len(texts))
	}

	// index 已保證照順序，但照著填比較保險
	vectors := make([][]float32, len(texts))
	for _, d := range out.Data {
		if d.Index < 0 || d.Index >= len(texts) {
			return nil, fmt.Errorf("embedding returned out-of-range index %d", d.Index)
		}
		vectors[d.Index] = d.Embedding
	}
	return vectors, nil
}

// 注意：不要再自己加 "query: "，服務端已經處理
func GenVector(inputText string) ([]float32, error) {
	vs, err := genVectors([]string{inputText})
	if err != nil {
		return nil, err
	}
	return vs[0], nil
}
```

### 3. `SyncQdrant` 建議改用批次

`app/services/qdrant.go:115` 現在是迴圈裡一筆一筆呼叫 `GenVector`。
改成先收集 `combinedText`、每 512 筆一組呼叫 `genVectors`，重建索引會快 2.8 倍。

### 4. 可以一起清掉的東西

- `Dockerfile` 的 `model_export` stage、ONNX Runtime 下載、`COPY --from=model_export`
- `export_model.py`、`export_model_docker.py`、`lm_model/`、`onnxruntime/`
- `go.mod` 的 `github.com/yalue/onnxruntime_go`、`github.com/sugarme/tokenizer`
- `global.LMSession`、`global.LMTokenizer`
- `models.InitLmSession()`、`models.InitTokenizer()`（`app/app.go:47-48`）
- `app/app.go:89-90` 的 `global.LMSession.Destroy()` 與 `ort.DestroyEnvironment()`
- `LM_MODEL_PATH` 環境變數與 secret

後端 image 會少掉約 1.1GB，記憶體也不用再常駐模型。

---

## 相容性驗證紀錄

改用這支 API **不會改變任何搜尋結果**，以下都在 SIT 對真實 Qdrant 驗過：

| 檢查 | 結果 |
| --- | --- |
| `model.onnx` / `tokenizer.json` sha256 vs 後端 pod | 完全相同 |
| `cos(Qdrant 既有向量 #174, 本服務重算)` | `1.00000002` |
| 三組查詢 top-5 分數與排序 vs 線上後端 `POST /api/v1/vector/component` | 小數第 4 位逐位相同 |
| 單筆 vs 批次同一段文字 | `max abs diff = 0.0` |

### 為什麼向量能對得起來（`ADD_SPECIAL_TOKENS=false`）

後端用的 `github.com/sugarme/tokenizer` 的 `EncodeSingle()`
**實際上不會加 `<s>` / `</s>`**（與 `qdrant.go:157` 註解寫的相反）。
用同一份 `tokenizer.json` 逐 id 比對已確認：

```
sugarme EncodeSingle(text).GetIds()  ==  HF tokenizers encode(text, add_special_tokens=False).ids
```

Qdrant 現有 collection 是照這個行為建的，所以服務預設跟著關掉。

這偏離 e5 訓練時的輸入格式，檢索品質其實略差（兩種算法同一段文字 cos ≈ 0.987，
會讓 top-5 的第 4、5 名換人）。要修的話得設 `ADD_SPECIAL_TOKENS=true`
**並用同一支服務重建 Qdrant collection**，query 與 passage 兩邊必須一起換。
這件事跟後端串接無關，可以之後再處理。

---

## 上線狀態

| 環境 | 狀態 |
| --- | --- |
| SIT | 已部署（`embedding.enabled: true`），可直接串接測試 |
| PROD | `helm-chart/values-prod.yaml` 目前 `embedding.enabled: false`，後端改完後開啟即可 |

有問題或要調參數（batch 上限、CPU、replica）再跟我說。
