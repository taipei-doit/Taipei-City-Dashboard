package models

import (
	"TaipeiCityDashboardBE/global"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)


type QdrantQueryRequest struct {
	Query          []float32 `json:"query"`
	Limit          int       `json:"limit"`
	ScoreThreshold float32   `json:"score_threshold,omitempty"`
	WithPayload    bool      `json:"with_payload"`
}

type QdrantPoint struct {
	Score   float64                `json:"score"`
	Payload map[string]interface{} `json:"payload"`
}

type QdrantQueryResponse struct {
	Result struct {
		Points []QdrantPoint `json:"points"`
	} `json:"result"`
	Status string  `json:"status"`
	Time   float64 `json:"time"`
}

func queryQdrant(queryVector []float32, limit int, scoreThreshold float64) (QdrantQueryResponse, error) {
	var result QdrantQueryResponse

	QdrantConfig := global.Qdrant

	reqBody := QdrantQueryRequest{
		Query:          queryVector,
		Limit:          limit,
		ScoreThreshold: float32(scoreThreshold),
		WithPayload:    true,
	}

	bodyBytes, err := json.Marshal(reqBody)
	if err != nil {
		return result, fmt.Errorf("marshal request body error: %w", err)
	}

	url := fmt.Sprintf("%s/collections/%s/points/query", QdrantConfig.Url, QdrantConfig.Collection)

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return result, fmt.Errorf("new request error: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("api-key", QdrantConfig.ApiKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return result, fmt.Errorf("http request error: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		// 如果想看錯誤內容，也可以在這裡讀一次 body
		b, _ := io.ReadAll(resp.Body)
		return result, fmt.Errorf("qdrant returned status %s, body=%s", resp.Status, string(b))
	}

	// 先把原始回應整包讀出來（方便 debug）
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, fmt.Errorf("read response body error: %w", err)
	}

	// fmt.Println("=== Qdrant 原始回應 ===")
	// fmt.Println(string(respBody))
	// fmt.Println("=======================")

	if err := json.Unmarshal(respBody, &result); err != nil {
		return result, fmt.Errorf("decode response error: %w", err)
	}

	return result, nil
}

// embeddingQueryClient 用於單筆使用者搜尋（短 timeout）
var embeddingQueryClient = &http.Client{Timeout: 3 * time.Second}

// embeddingBatchClient 用於索引重建批次呼叫（長 timeout）
var embeddingBatchClient = &http.Client{Timeout: 60 * time.Second}

// embeddingResponse 對應 Embedding 微服務的回應格式
type embeddingResponse struct {
	Data []struct {
		Index     int       `json:"index"`
		Embedding []float32 `json:"embedding"`
	} `json:"data"`
}

// GenVectors 批次將多筆文字轉換為 768 維向量，供索引重建使用。
// 前綴由 Embedding 微服務統一處理，呼叫端不需自行加入 "query: " 或 "passage: "。
// 回傳的向量已完成 L2 正規化，可直接寫入 Qdrant。
func GenVectors(texts []string) ([][]float32, error) {
	if len(texts) == 0 {
		return nil, fmt.Errorf("GenVectors: texts must not be empty")
	}
	if global.Embedding.Url == "" {
		return nil, fmt.Errorf("GenVectors: EMBEDDING_URL is not configured")
	}

	body, err := json.Marshal(map[string]any{
		"input":  texts,
		"prefix": "passage: ",
	})
	if err != nil {
		return nil, fmt.Errorf("GenVectors: marshal request: %w", err)
	}

	resp, err := embeddingBatchClient.Post(
		global.Embedding.Url+"/v1/embeddings",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, fmt.Errorf("GenVectors: request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("GenVectors: embedding service returned %s: %s", resp.Status, b)
	}

	var out embeddingResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("GenVectors: decode response: %w", err)
	}
	if len(out.Data) != len(texts) {
		return nil, fmt.Errorf("GenVectors: expected %d vectors, got %d", len(texts), len(out.Data))
	}

	vectors := make([][]float32, len(texts))
	for _, d := range out.Data {
		if d.Index < 0 || d.Index >= len(texts) {
			return nil, fmt.Errorf("GenVectors: out-of-range index %d in response", d.Index)
		}
		vectors[d.Index] = d.Embedding
	}
	return vectors, nil
}

// GenVector 單筆將文字轉換為 768 維向量，供使用者語意搜尋使用。
// 前綴由 Embedding 微服務統一處理（預設 "query: "），呼叫端不需自行加入。
// 回傳的向量已完成 L2 正規化，可直接用於 Qdrant 查詢。
func GenVector(inputText string) ([]float32, error) {
	if global.Embedding.Url == "" {
		return nil, fmt.Errorf("GenVector: EMBEDDING_URL is not configured")
	}

	body, err := json.Marshal(map[string]any{
		"input": inputText,
	})
	if err != nil {
		return nil, fmt.Errorf("GenVector: marshal request: %w", err)
	}

	resp, err := embeddingQueryClient.Post(
		global.Embedding.Url+"/v1/embeddings",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, fmt.Errorf("GenVector: request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("GenVector: embedding service returned %s: %s", resp.Status, b)
	}

	var out embeddingResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("GenVector: decode response: %w", err)
	}
	if len(out.Data) == 0 {
		return nil, fmt.Errorf("GenVector: no embedding returned")
	}

	return out.Data[0].Embedding, nil
}