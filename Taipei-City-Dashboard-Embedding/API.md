# 向量嵌入服務 API 規格書

## 文件資訊

| 項目 | 內容 |
| --- | --- |
| 文件名稱 | 向量嵌入服務 API 規格書 |
| 文件版本 | 1.0.0 |
| 服務版本 | 1.0.0 |
| 對應映像檔 | `taipei-city-dashboard-embedding:sit-bf3d10ff` |
| 更新日期 | 2026-08-20 |
| 適用環境 | SIT（已上線）、PROD（待啟用） |
| 機器可讀規格 | [`openapi.yaml`](./openapi.yaml)（OpenAPI 3.0.3） |

## 修訂紀錄

| 版本 | 日期 | 修訂內容 |
| --- | --- | --- |
| 1.0.0 | 2026-08-20 | 初版發布 |

---

## 1. 概述

### 1.1 服務說明

本服務提供 `intfloat/multilingual-e5-base` 模型的文字向量化能力，供後端進行語意檢索
及 Qdrant 索引建置。原推論邏輯內嵌於後端 image，現拆分為獨立服務，以降低後端資源負載。

處理流程如下：

```
輸入文字 → 加入 e5 前綴 → tokenize → mean pooling（依 attention_mask）
        → L2 正規化 → 768 維向量
```

本服務與既有後端實作使用相同的模型檔與 tokenizer，產出向量逐位相容，
**Qdrant 既有 collection 無須重建**。驗證紀錄詳見附錄 A。

### 1.2 服務位址

| 項目 | 內容 |
| --- | --- |
| 叢集內部位址 | `http://taipei-city-dashboard-embedding:8080` |
| 完整網域名稱 | `http://taipei-city-dashboard-embedding.dashboard.svc.cluster.local:8080` |
| Kubernetes Service 型別 | `ClusterIP` |
| 對外開放 | 否 |

服務僅供叢集內部呼叫，不經由 Ingress 或 LoadBalancer 對外暴露。

### 1.3 認證方式

無。服務不對外開放，依賴叢集網路隔離。呼叫端無須提供任何憑證或 API Key。

### 1.4 資料格式

| 項目 | 內容 |
| --- | --- |
| 請求格式 | `application/json` |
| 回應格式 | `application/json` |
| 字元編碼 | UTF-8 |

---

## 2. 端點規格

### 2.1 產生文字向量

| 項目 | 內容 |
| --- | --- |
| 方法 | `POST` |
| 路徑 | `/v1/embeddings` |
| 說明 | 將文字轉換為 768 維向量 |
| 相容性 | OpenAI Embeddings API 格式 |

#### 2.1.1 請求參數

| 參數名稱 | 型別 | 必填 | 預設值 | 說明 |
| --- | --- | :---: | --- | --- |
| `input` | `string` 或 `string[]` | 是 | — | 待向量化的文字。傳入陣列即為批次處理，上限 512 筆 |
| `model` | `string` | 否 | — | 相容性欄位。本服務僅載入單一模型，傳入任何值均予忽略 |
| `prefix` | `string` | 否 | `"query: "` | 覆寫 e5 模型輸入前綴。傳入空字串表示不加前綴。詳見 5.1 節 |

#### 2.1.2 回應參數（HTTP 200）

| 參數名稱 | 型別 | 說明 |
| --- | --- | --- |
| `object` | `string` | 固定為 `"list"` |
| `data` | `object[]` | 向量結果陣列，依請求中 `input` 的原始順序排列 |
| `data[].object` | `string` | 固定為 `"embedding"` |
| `data[].index` | `integer` | 對應請求中 `input` 的索引位置 |
| `data[].embedding` | `float[]` | 768 維向量，**已完成 L2 正規化** |
| `model` | `string` | 模型名稱 |
| `usage.prompt_tokens` | `integer` | 實際處理的 token 數，不含 padding |
| `usage.total_tokens` | `integer` | 同 `prompt_tokens`，為相容性欄位 |

回應範例：

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

#### 2.1.3 錯誤回應

| HTTP 狀態碼 | 觸發條件 | `detail` 內容 |
| :---: | --- | --- |
| `400` | `input` 為空陣列 | `input must not be empty` |
| `400` | 批次筆數超過上限 | `batch size {n} exceeds MAX_BATCH=512` |
| `400` | 單筆字元數超過上限 | `input longer than MAX_CHARS=8192` |
| `422` | `input` 型別錯誤 | Pydantic 驗證物件陣列，`type` 為 `string_type` |
| `422` | 缺少 `input` 欄位 | Pydantic 驗證物件陣列，`type` 為 `missing` |

> **注意**：`400` 回應的 `detail` 為**字串**，`422` 回應的 `detail` 為**物件陣列**，
> 兩者型別不同，呼叫端解析錯誤訊息時須分別處理。

錯誤回應範例：

```json
// HTTP 400
{ "detail": "batch size 513 exceeds MAX_BATCH=512" }

// HTTP 422
{ "detail": [ { "type": "string_type", "loc": ["body", "input", "str"], "msg": "..." } ] }
```

#### 2.1.4 呼叫範例

```bash
# 單筆
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": "台北市的空氣品質"}'

# 批次
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": ["台北市的空氣品質", "youbike 站點"]}'

# 建立索引時指定 passage 前綴
curl -s http://taipei-city-dashboard-embedding:8080/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"input": ["長描述文字"], "prefix": "passage: "}'
```

### 2.2 服務健康狀態

| 項目 | 內容 |
| --- | --- |
| 方法 | `GET` |
| 路徑 | `/healthz` |
| 說明 | 回報服務狀態與目前生效的設定值 |

供 Kubernetes startup / liveness / readiness probe 使用，後端無須主動呼叫。

回應範例（HTTP 200）：

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

---

## 3. 使用限制

| 項目 | 限制值 | 超過限制之行為 |
| --- | ---: | --- |
| 單次請求筆數 | 512 | 回應 `400` |
| 單筆字元數 | 8,192 | 回應 `400` |
| 單筆 token 數 | 512 | **自動截斷，不另行告知** |

關於 token 截斷：token 數上限為模型 `max_position_embeddings` 所限制。
超過時服務仍回應 `200`，但僅取前 512 個 token 進行運算。
呼叫端可透過 `usage.prompt_tokens` 是否等於 `512` 判斷輸入是否遭截斷。

以中文估算約 1.7 字元／token，即單筆約 880 個中文字即達上限。

---

## 4. 效能指標

### 4.1 實測數據

測試環境：SIT，1 replica，CPU limit 2000m，`ORT_INTRA_THREADS=2`。

| 情境 | 回應時間 | 處理量 |
| --- | ---: | ---: |
| 單筆查詢 | 25 ms | 39 texts/s |
| 32 筆（短文字） | 292 ms | 110 texts/s |
| 32 筆（長描述） | 1,520 ms | 21 texts/s |
| 300 筆（長短混合） | 10.0 s | 30 texts/s |

### 4.2 逾時設定建議

| 呼叫情境 | 建議逾時 | 說明 |
| --- | ---: | --- |
| 使用者查詢（單筆） | 3 秒 | 一般回應時間為 25 ms |
| 索引重建（批次） | 60 秒 | 300 筆約需 10 秒，餘裕供冷啟動使用 |

服務冷啟動需載入約 1.1 GB 之 ONNX 模型，約需 20–30 秒。
Kubernetes `startupProbe` 於此期間會阻擋流量，惟滾動更新期間建議呼叫端仍實作單次重試。

### 4.3 批次處理機制

服務接收批次請求後，內部處理程序如下：

1. 對全部輸入進行 tokenize，依 token 數排序
2. 每 32 筆為一組送入 ONNX Runtime，各組僅 padding 至該組最長長度
3. 依原始輸入順序重組結果

依長度分組可避免長短文字混合時，短文字被 padding 至最長者長度而耗費不必要之運算。
實測 32 筆短文字與 32 筆長文字混合處理，由 3,001 ms 降至 1,644 ms。

分組亦使記憶體用量與請求筆數脫鉤，送出 512 筆與 32 筆之峰值記憶體相同。

批次與單筆處理所產生之向量逐位相同（實測 50 筆混合長度，`max abs diff = 0.0`），
呼叫端可依實作便利性自行決定是否合併請求。

---

## 5. 串接注意事項

### 5.1 前綴由服務端統一處理

e5 模型要求輸入帶有前綴。**本服務已負責加入前綴，呼叫端不應自行加入。**

既有後端於 `app/models/qdrant.go:155` 有下列寫死之前綴：

```go
text := "query: " + inputText
```

改用本服務時應移除此行，直接傳入原始文字。若未移除，實際輸入將成為
`"query: query: 原始文字"`，產生之向量與正確結果之餘弦相似度為 `0.9939`
（實測值）。此情況不會產生錯誤，但足以影響檢索排序，且不易察覺。

如需自行控制前綴，請使用 `prefix` 參數：

| 用途 | 傳入值 |
| --- | --- |
| 查詢（預設） | 不傳 `prefix` |
| 不加任何前綴 | `"prefix": ""` |
| 建立索引 | `"prefix": "passage: "` |

實測 `{"input": "query: 空氣品質", "prefix": ""}` 與 `{"input": "空氣品質"}`
所產生之向量 `max abs diff = 0.0`，行為可預期。

### 5.2 回應順序

`data[i].index` 保證對應 `input[i]`。服務內部雖依長度重排以最佳化運算，
回傳前已還原原始順序。建議呼叫端仍依 `index` 欄位對應，以策安全。

### 5.3 向量正規化

`embedding` 已完成 L2 正規化，可直接寫入 Qdrant，呼叫端無須再次正規化。

---

## 6. 後端調整指引

### 6.1 環境設定

`EMBEDDING_URL` 由 Helm chart 自動注入，後端無須進行任何部署設定。

`helm-chart/templates/backend-deployment.yaml` 於 `embedding.enabled` 為 `true` 時，
自動由 Helm release 名稱推導服務位址並注入後端 Deployment：

```yaml
- name: EMBEDDING_URL
  value: "http://taipei-city-dashboard-embedding:8080"
```

此值未納入 GitHub Secret，因其為叢集內部 DNS 名稱，非機密資訊，
且 SIT 與 PROD 環境相同。如需指向其他位址，於 `values-*.yaml` 之
`backend.env` 設定 `EMBEDDING_URL` 即可覆寫。

後端讀取方式：

```go
// global/global.go
type EmbeddingConfig struct {
	Url string
}

Embedding = EmbeddingConfig{
	Url: getEnv("EMBEDDING_URL", "http://taipei-city-dashboard-embedding:8080"),
}
```

網路連通性已於 SIT 驗證：自後端 Pod 直接存取 `/healthz` 即可連通，
同 namespace 無須額外設定 NetworkPolicy。

### 6.2 `GenVector()` 改寫

回傳型別 `[]float32` 維持不變，既有兩處呼叫端
（`app/models/componentConfig.go:263`、`app/services/qdrant.go:115`）無須調整。

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

	vectors := make([][]float32, len(texts))
	for _, d := range out.Data {
		if d.Index < 0 || d.Index >= len(texts) {
			return nil, fmt.Errorf("embedding returned out-of-range index %d", d.Index)
		}
		vectors[d.Index] = d.Embedding
	}
	return vectors, nil
}

// 前綴由服務端處理，此處不再自行加入 "query: "
func GenVector(inputText string) ([]float32, error) {
	vs, err := genVectors([]string{inputText})
	if err != nil {
		return nil, err
	}
	return vs[0], nil
}
```

### 6.3 索引重建改用批次

`app/services/qdrant.go` 之 `generateVectors()`（第 89 行）目前於迴圈中
逐筆呼叫 `GenVector`。建議改為先蒐集全部 `combinedText`，
每 512 筆為一組呼叫 `genVectors`，索引重建效率可提升約 2.8 倍。

### 6.4 可移除之項目

| 檔案／位置 | 移除內容 |
| --- | --- |
| `Dockerfile` | `model_export` stage、ONNX Runtime 下載、`COPY --from=model_export` |
| 專案根目錄 | `export_model.py`、`export_model_docker.py`、`lm_model/`、`onnxruntime/` |
| `go.mod` | `github.com/yalue/onnxruntime_go`、`github.com/sugarme/tokenizer` |
| `global/global.go` | `LMConfig`、`LMSession`、`LMTokenizer` |
| `app/models/qdrant.go` | `InitLmSession()`、`InitTokenizer()` |
| `app/app.go:47-48` | `models.InitLmSession()`、`models.InitTokenizer()` 呼叫 |
| `app/app.go:89-90` | `global.LMSession.Destroy()`、`ort.DestroyEnvironment()` |
| Helm / Secret | `LM_MODEL_PATH` 環境變數 |

移除後後端 image 可減少約 1.1 GB，且記憶體無須常駐模型。

---

## 附錄 A：相容性驗證紀錄

改用本服務不會改變任何檢索結果。下列項目均於 SIT 環境對正式 Qdrant 資料驗證：

| 驗證項目 | 結果 |
| --- | --- |
| `model.onnx` SHA-256 與後端 Pod 比對 | 完全相同 |
| `tokenizer.json` SHA-256 與後端 Pod 比對 | 完全相同 |
| `cos(Qdrant 既有向量 #174, 本服務重新計算)` | `1.00000002` |
| 三組查詢之 top-5 分數與排序，與線上後端 `POST /api/v1/vector/component` 比對 | 小數第 4 位完全相同 |
| 同一文字之單筆與批次處理結果比對 | `max abs diff = 0.0` |

### A.1 `ADD_SPECIAL_TOKENS` 設定說明

本服務 `ADD_SPECIAL_TOKENS` 預設為 `false`，原因如下。

既有後端使用之 `github.com/sugarme/tokenizer` 套件，其 `EncodeSingle()`
實際上**不會加入 `<s>` / `</s>` 特殊 token**，與 `app/models/qdrant.go:157`
註解所述「預設 addSpecialTokens = true」不符。以相同 `tokenizer.json`
逐一比對 token id 已確認：

```
sugarme EncodeSingle(text).GetIds()
  ==
HF tokenizers encode(text, add_special_tokens=False).ids
```

Qdrant 現有 collection 係依此行為建立，故本服務預設一致以維持相容。

此設定偏離 e5 模型訓練時之輸入格式，檢索品質略有影響：同一段文字以兩種方式
計算之向量餘弦相似度約 `0.987`，實測會使 top-5 之第 4、5 名項目變動。

如需修正，須將 `ADD_SPECIAL_TOKENS` 設為 `true`，**並以本服務重建 Qdrant collection**。
查詢端與索引端必須同時調整，僅調整單邊會使兩者落於不同向量空間。
此事項與後端串接無關，可另行安排。

---

## 附錄 B：既有實作已知問題

本問題係拆分服務期間發現，與本次串接無關，惟建議優先處理。

### B.1 問題說明

`app/controllers/componentConfig.go:330` 之 `query` 參數為使用者可控且未設長度限制：

```go
query := c.PostForm("query")   // 無長度檢查
```

該值傳入 `app/models/qdrant.go` 之 `GenVector()` 後，未經截斷即建立對應長度之
tensor 送入 ONNX Runtime。惟模型 `max_position_embeddings` 為 514，
超過時推論將失敗。

### B.2 驗證結果

於獨立臨時 Pod 使用相同 `model.onnx` 實測：

| 輸入 token 數 | 結果 |
| ---: | --- |
| 6 | 正常 |
| 284 | 正常 |
| 804 | `InvalidArgument: Non-zero status code returned while running Gather node.`<br>`Name:'/embeddings/position_embeddings/Gather'`<br>`indices element out of data bounds, idx=514 must be within the inclusive range [-514,513]` |

而 `app/models/qdrant.go:215` 對此錯誤之處理方式為：

```go
if err := session.Run(inputTensors, outputTensors); err != nil {
    log.Fatalf("session.Run error: %v", err)
}
```

`log.Fatalf` 將呼叫 `os.Exit(1)`，導致**後端 process 直接結束**，而非回應 HTTP 500。

### B.3 影響範圍

以中文約 1.7 字元／token 估算，`query` 超過約 880 個中文字即達觸發條件。
此情境無須惡意輸入即可觸發——使用者將長篇文字貼入搜尋欄位即可能導致後端 Pod 結束並重啟。
`/api/v1/vector/component` 端點亦未設置認證。

`GenVector()` 內另有 5 處 `log.Fatalf`（第 159、166、176、189、205 行），
均位於請求處理路徑，同樣為 process 層級結束而非錯誤回傳。

### B.4 驗證範圍聲明

上述 ONNX Runtime 錯誤訊息係於獨立臨時 Pod 使用相同模型檔實測所得，
**未對線上後端服務進行實際觸發測試**，以避免造成服務中斷。
「後端 process 將結束」一節係依 `log.Fatalf` 之語意推論，未經實際驗證。

### B.5 處理建議

改用本服務後即已解決：本服務於 `MAX_SEQ_LEN=512` 自動截斷，
超過 `MAX_CHARS=8192` 字元回應 `400`，所有錯誤均以 HTTP 狀態碼回傳，
不會導致 process 結束。

若短期內尚不進行串接，最小修正範圍為：

1. 於 controller 對 `query` 加入長度上限檢查
2. 將 `GenVector()` 內全部 `log.Fatalf` 改為 `return nil, fmt.Errorf(...)`

---

## 附錄 C：服務參數

下列參數由 Helm chart 設定，呼叫端無須調整，列出供查閱。

| 環境變數 | 預設值 | 說明 |
| --- | --- | --- |
| `LM_MODEL_PATH` | `/opt/lm_model/onnx-e5` | 模型檔目錄，映像檔內已備妥 |
| `E5_PREFIX` | `query: ` | 預設 e5 前綴 |
| `ADD_SPECIAL_TOKENS` | `false` | 是否加入 `<s>` / `</s>`，調整前請詳閱附錄 A.1 |
| `MAX_BATCH` | `512` | 單次請求筆數上限 |
| `MICRO_BATCH` | `32` | 內部單次推論筆數 |
| `MAX_SEQ_LEN` | `512` | token 數上限，超過即截斷 |
| `MAX_CHARS` | `8192` | 單筆字元數上限 |
| `ORT_INTRA_THREADS` | `2` | ONNX Runtime 執行緒數 |

`ORT_INTRA_THREADS` 須與 `embedding.resources.limits.cpu` 一併考量，
設定過高將因 cgroup throttling 反致效能下降。現行設定為 CPU limit 2000m 搭配 2 執行緒。

---

## 附錄 D：部署狀態

| 環境 | Helm 設定 | 狀態 |
| --- | --- | --- |
| SIT | `embedding.enabled: true` | 已部署，可進行串接測試 |
| PROD | `embedding.enabled: false` | 待後端完成串接後啟用 |

PROD 啟用時，`EMBEDDING_URL` 將由 Helm chart 自動注入，無須額外設定。
